import glob
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import yt_dlp
from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16_384
TEMP_ROOT = Path(__file__).resolve().parent / "temp"
TEMP_ROOT.mkdir(exist_ok=True)


def find_ffmpeg():
    candidates = [shutil.which("ffmpeg")]
    try:
        import imageio_ffmpeg
        candidates.append(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        pass

    for candidate in candidates:
        if not candidate:
            continue
        try:
            subprocess.run(
                [candidate, "-version"],
                capture_output=True,
                check=True,
                timeout=10,
            )
            return candidate
        except Exception:
            continue
    return None


FFMPEG = find_ffmpeg()
HAS_FFMPEG = FFMPEG is not None
print("ffmpeg:", FFMPEG or "ვერ მოიძებნა; ვიდეოს გაერთიანება მიუწვდომელია")

YT_RE = re.compile(r"^https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)/", re.I)


def valid_url(url):
    return isinstance(url, str) and len(url) <= 4000 and bool(YT_RE.match(url.strip()))


def ytdlp_options():
    options = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 20,
        "retries": 2,
        "cachedir": False,
    }
    if FFMPEG:
        options["ffmpeg_location"] = FFMPEG
    return options


def user_error(exc):
    text = str(exc).lower()
    if any(word in text for word in ("sign in", "login required", "confirm you", "not a bot")):
        return "YouTube ამ კავშირს დროებით ბლოკავს. სცადე მოგვიანებით ან სხვა საჯარო ვიდეო."
    if "ffmpeg" in text:
        return "FFmpeg ვერ მოიძებნა. დახურე პროგრამა და ხელახლა გაუშვი start.bat, რომ საჭირო პაკეტები დაყენდეს."
    if "requested format is not available" in text:
        return "არჩეული ხარისხი ვიდეოსთვის მიუწვდომელია. ხელახლა მოძებნე ვიდეო და აირჩიე სხვა ხარისხი."
    return "ვიდეოს ჩამოტვირთვა ვერ მოხერხდა. გადაამოწმე საჯარო ბმული და სცადე ხელახლა."


@app.errorhandler(Exception)
def handle_error(exc):
    if isinstance(exc, HTTPException):
        return exc
    app.logger.exception("Unhandled local server error")
    if request.path.startswith("/api/"):
        return jsonify(error="სერვერის შეცდომა. გადაამოწმე start.bat-ის ფანჯარაში შეტყობინება."), 500
    return "სერვერის შეცდომა. გადაამოწმე start.bat-ის ფანჯარაში შეტყობინება.", 500


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["POST"])
def info():
    body = request.get_json(silent=True) or {}
    url = body.get("url", "").strip()
    if not valid_url(url):
        return jsonify(error="გთხოვ, შეიყვანე სწორი YouTube ბმული."), 400

    try:
        with yt_dlp.YoutubeDL(ytdlp_options() | {"skip_download": True}) as ydl:
            data = ydl.extract_info(url, download=False)
    except Exception as exc:
        app.logger.warning("YouTube info request failed: %s", type(exc).__name__)
        return jsonify(error=user_error(exc)), 422

    def usable(fmt):
        if not fmt.get("height") or fmt.get("vcodec") == "none":
            return False
        return HAS_FFMPEG or fmt.get("acodec") not in (None, "none")

    heights = sorted(
        {fmt["height"] for fmt in data.get("formats", []) if usable(fmt)},
        reverse=True,
    )
    return jsonify(
        title=data.get("title"),
        thumbnail=data.get("thumbnail"),
        channel=data.get("uploader"),
        duration=data.get("duration"),
        heights=heights,
        has_ffmpeg=HAS_FFMPEG,
    )


@app.route("/api/download", methods=["POST"])
def download():
    body = request.get_json(silent=True) or {}
    url = body.get("url", "").strip()
    mode = body.get("mode", "video")
    try:
        height = max(1, min(4320, int(body.get("height") or 720)))
    except (TypeError, ValueError):
        return jsonify(error="ვიდეოს ხარისხი არასწორია."), 400

    if not valid_url(url) or mode not in {"video", "audio"}:
        return jsonify(error="ბმული ან ფორმატი არასწორია."), 400

    temp_dir = tempfile.mkdtemp(prefix="clipstack_", dir=TEMP_ROOT)
    opts = ytdlp_options()
    opts["outtmpl"] = os.path.join(temp_dir, "%(title).80s.%(ext)s")

    if mode == "audio":
        if HAS_FFMPEG:
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        else:
            opts["format"] = "bestaudio[ext=m4a]/bestaudio"
    elif HAS_FFMPEG:
        opts["format"] = f"bv*[height<={height}]+ba/b[height<={height}]/b"
        opts["merge_output_format"] = "mp4"
    else:
        opts["format"] = f"b[height<={height}][ext=mp4]/b[height<={height}]/b"

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        candidates = [
            Path(path) for path in glob.glob(os.path.join(temp_dir, "*"))
            if os.path.isfile(path) and not path.endswith((".part", ".ytdl"))
        ]
        preferred_ext = ".mp3" if mode == "audio" and HAS_FFMPEG else ".mp4" if mode == "video" and HAS_FFMPEG else None
        if preferred_ext:
            preferred = [path for path in candidates if path.suffix.lower() == preferred_ext]
            if preferred:
                candidates = preferred
        if not candidates:
            raise RuntimeError("Downloaded media file was not created")
        file_path = max(candidates, key=lambda path: path.stat().st_size)
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        app.logger.warning("YouTube download failed: %s", type(exc).__name__)
        return jsonify(error=user_error(exc)), 422

    response = send_file(
        file_path,
        as_attachment=True,
        download_name=file_path.name,
        conditional=True,
    )
    response.call_on_close(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
    return response


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)


