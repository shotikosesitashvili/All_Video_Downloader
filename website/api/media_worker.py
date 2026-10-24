import base64
import json
import os
import re
import shutil
import sys
from pathlib import Path
from security import CHUNK, MAX_MEDIA, guard_network, public_url

guard_network()


def inspect(url):
    from yt_dlp import YoutubeDL
    class Quiet:
        def debug(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass
    node = shutil.which('node')
    if not node and Path('/nodejs/bin/node').is_file():
        node = '/nodejs/bin/node'
    opts = dict(quiet=True, logger=Quiet(), cachedir=False, noplaylist=True,
                extract_flat='in_playlist', playlistend=1, socket_timeout=12,
                retries=1, skip_download=True, proxy='',
                js_runtimes={'node': {'path': node}} if node else {})
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(public_url(url), download=False)
    if not info or info.get('_type') in {'playlist', 'multi_video'} or info.get('is_live'):
        raise ValueError('Single public video required')
    formats = []
    for f in info.get('formats', []):
        if (f.get('protocol') not in {'http', 'https'} or f.get('has_drm')
                or f.get('fragments') or not f.get('url')):
            continue
        if f.get('filesize', 0) and f['filesize'] > MAX_MEDIA:
            continue
        if not f['url'].startswith(('https://', 'http://')):
            continue
        headers = dict(info.get('http_headers') or {}, **(f.get('http_headers') or {}))
        headers = {k: str(v) for k, v in headers.items() if k.lower() in {'user-agent', 'referer', 'origin'}}
        formats.append({'id': str(f['format_id']), 'url': f['url'], 'headers': headers,
            'height': f.get('height'), 'size': f.get('filesize') or f.get('filesize_approx'),
            'ext': f.get('ext', 'bin'), 'video': f.get('vcodec') != 'none' and f.get('ext') not in {'mp3', 'm4a', 'ogg', 'opus', 'wav'},
            'audio': f.get('acodec') != 'none', 'vcodec': f.get('vcodec') or '',
            'abr': f.get('abr') or 0, 'fps': f.get('fps') or 0})
    return {'title': (info.get('title') or 'Video')[:200],
            'source': info.get('extractor_key') or 'Web', 'duration': info.get('duration'),
            'formats': formats}


def chunk(payload, offset):
    import requests
    offset = int(offset)
    if offset < 0 or offset >= MAX_MEDIA or offset % CHUNK:
        raise ValueError('Invalid byte range')
    url = public_url(payload['url'])
    headers = dict(payload.get('headers') or {})
    headers.update({'Range': f'bytes={offset}-{offset + CHUNK - 1}', 'Accept-Encoding': 'identity'})
    with requests.Session() as session:
        session.trust_env = False
        with session.get(url, headers=headers, stream=True, timeout=(8, 20), allow_redirects=True) as response:
            if response.status_code == 416:
                return {'done': True, 'data': '', 'total': offset}
            response.raise_for_status()
            total = None
            if response.status_code == 206:
                match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+|\*)', response.headers.get('Content-Range', ''))
                if not match or int(match[1]) != offset or int(match[2]) >= offset + CHUNK:
                    raise ValueError('Bad byte range from source')
                if match[3] != '*':
                    total = int(match[3])
            elif offset != 0:
                raise ValueError('Source does not support byte ranges')
            else:
                length = response.headers.get('Content-Length')
                if length and int(length) > CHUNK:
                    raise ValueError('Source does not support byte ranges')
                total = int(length) if length else None
            if total is not None and total > MAX_MEDIA:
                raise ValueError('Video exceeds 64 MB')
            data = bytearray()
            for part in response.iter_content(65536):
                data.extend(part)
                if len(data) > CHUNK:
                    raise ValueError('Source exceeds range limit')
            done = response.status_code == 200 or len(data) < CHUNK or (total is not None and offset + len(data) >= total)
            return {'data': base64.b64encode(data).decode(), 'total': total, 'done': done}


if __name__ == '__main__':
    try:
        args = json.load(sys.stdin)
        result = inspect(args['url']) if args['action'] == 'inspect' else chunk(args['media'], args['offset'])
        print(json.dumps(result))
    except Exception as exc:
        text = str(exc).lower()
        code = ('provider_blocked' if any(x in text for x in ('not a bot', 'confirm you', 'sign in', 'login required', 'http error 403'))
                else 'javascript_required' if 'javascript' in text else 'source_unavailable')
        print(json.dumps({'error': code}))
        sys.exit(1)
