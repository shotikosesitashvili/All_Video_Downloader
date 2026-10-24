"""Disposable downloader process; Telegram token is removed from its environment."""
import json
import sys
from pathlib import Path
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
from core import choices, format_selector, validate_url


class QuietLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass


def run():
    mode, raw_url, directory, quality, limit = sys.argv[1:]
    url, folder, max_bytes = validate_url(raw_url), Path(directory).resolve(), int(limit)

    def guard(status):
        used = sum(p.stat().st_size for p in folder.iterdir() if p.is_file())
        if status.get('downloaded_bytes', 0) > max_bytes or used > max_bytes * 3:
            raise DownloadError('FILE_TOO_LARGE')

    def reject(info, *, incomplete=False):
        if info.get('is_live') or info.get('live_status') == 'is_live':
            return 'Live broadcasts are not supported'
        if info.get('_type') in {'playlist', 'multi_video'}:
            return 'Playlists are not supported'

    opts = {'quiet': True, 'logger': QuietLogger(), 'noplaylist': True,
            'socket_timeout': 20, 'retries': 2, 'fragment_retries': 2,
            'cachedir': False, 'extract_flat': 'in_playlist', 'playlistend': 1, 'restrictfilenames': True, 'match_filter': reject,
            'js_runtimes': {'node': {}}, 'outtmpl': str(folder / 'media.%(ext)s')}
    if mode == 'download':
        opts.update(format=format_selector(quality), max_filesize=max_bytes,
                    progress_hooks=[guard], merge_output_format='mkv')
        if quality == 'audio':
            opts['postprocessors'] = [{'key': 'FFmpegExtractAudio',
                                      'preferredcodec': 'mp3', 'preferredquality': '192'}]
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info or info.get('_type') in {'playlist', 'multi_video'}:
            raise ValueError('No single video')
        if mode == 'download':
            info = ydl.process_ie_result(info, download=True)
    if not info or info.get('_type') in {'playlist', 'multi_video'}:
        raise ValueError('No single video')
    result = {'title': (info.get('title') or 'Video')[:180], 'heights': choices(info)}
    if mode == 'download':
        extensions = {'.mp4', '.mkv', '.webm', '.mp3', '.m4a', '.ogg', '.mov', '.flv', '.avi', '.ts'}
        files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in extensions]
        if len(files) != 1 or files[0].stat().st_size > max_bytes:
            raise ValueError('No complete file or FILE_TOO_LARGE')
        result['file'] = str(files[0])
    print(json.dumps(result))


if __name__ == '__main__':
    try:
        run()
    except Exception:
        print(json.dumps({'error': 'download_failed'}))
        sys.exit(1)
