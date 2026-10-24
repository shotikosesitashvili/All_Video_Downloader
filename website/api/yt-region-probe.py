import base64
import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from media_worker import chunk, inspect

VIDEO = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            info = inspect(VIDEO)
            videos = [item for item in info["formats"] if item["video"]]
            chosen = max(videos, key=lambda item: (item["height"] or 0, item["audio"], item["ext"] == "mp4"))
            sample = chunk(chosen, 0)
            result = {
                "ok": bool(sample["data"]),
                "title": info["title"],
                "quality": chosen["height"],
                "formatCount": len(info["formats"]),
                "firstChunkBytes": len(base64.b64decode(sample["data"])),
            }
        except Exception as exc:
            text = str(exc).lower()
            if any(word in text for word in ("login required", "sign in", "confirm you", "not a bot")):
                code = "provider_blocked"
            elif "javascript" in text:
                code = "javascript_required"
            elif "403" in text:
                code = "http_403"
            else:
                code = "source_unavailable"
            result = {"ok": False, "errorType": type(exc).__name__, "code": code}
        body = json.dumps(result).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
