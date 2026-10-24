import asyncio
import base64
import json
import os
import signal
import sys
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from .security import CHUNK, MAX_MEDIA, sign, verify

app = FastAPI()
ROOT = Path(__file__).resolve().parent


async def isolated(args, timeout=40):
    env = {k: v for k, v in os.environ.items()
           if not any(word in k.upper() for word in ('TOKEN', 'SECRET', 'PASSWORD', 'KEY'))}
    proc = await asyncio.create_subprocess_exec(
        sys.executable, str(ROOT / 'media_worker.py'),
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL, env=env,
        **({'start_new_session': True} if os.name != 'nt' else {}))
    try:
        out, _ = await asyncio.wait_for(proc.communicate(json.dumps(args).encode()), timeout)
        result = json.loads(out)
        if proc.returncode or 'error' in result:
            raise ValueError(result.get('error', 'source_unavailable'))
        return result
    finally:
        if proc.returncode is None:
            if os.name != 'nt':
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                proc.kill()
            await proc.wait()


def media_option(f):
    return {'token': sign({'url': f['url'], 'headers': f['headers']}),
            'ext': f['ext'], 'size': f['size'], 'video': f['video'], 'audio': f['audio'],
            'height': f['height'], 'vcodec': f['vcodec']}


def summarize(info):
    formats = info['formats']
    audio = max((f for f in formats if f['audio'] and not f['video']),
                key=lambda f: (f['ext'] == 'm4a', f['abr']), default=None)
    videos = {}
    for f in formats:
        if not f['video'] or (not f['audio'] and not audio):
            continue
        h = int(f['height'] or 0)
        score = (f['audio'], f['ext'] == 'mp4', f['vcodec'].startswith('avc'), f['fps'])
        if h not in videos or score > videos[h][0]:
            videos[h] = (score, f)
    options = []
    for h, (_, f) in sorted(videos.items(), reverse=True):
        if len(options) >= 10:
            break
        item = {'label': f'{h}p' if h else 'Original', 'video': media_option(f),
                'audio': media_option(audio) if not f['audio'] else None}
        options.append(item)
    if audio is None:
        audio = max((f for f in formats if f['audio']), key=lambda f: f['size'] or 0, default=None)
    return {'title': info['title'], 'source': info['source'], 'duration': info['duration'],
            'options': options, 'audio': media_option(audio) if audio else None, 'maxBytes': MAX_MEDIA}


@app.get('/api/index')
@app.get('/')
async def health():
    return {'ok': True, 'service': 'clipstack'}


@app.post('/api/index')
@app.post('/')
async def api(request: Request):
    origin = request.headers.get('origin')
    local_dev = (not os.environ.get('VERCEL') and urlsplit(origin or '').hostname in {'localhost', '127.0.0.1'}
                 and request.url.hostname in {'localhost', '127.0.0.1'})
    if origin and not local_dev and urlsplit(origin).netloc != request.headers.get('host'):
        return JSONResponse({'error': 'Cross-origin request rejected'}, status_code=403)
    if int(request.headers.get('content-length', '0')) > 40000:
        return JSONResponse({'error': 'Request too large'}, status_code=413)
    try:
        body = await request.body()
        if len(body) > 40000:
            raise ValueError('Request too large')
        data = json.loads(body)
        action = request.query_params.get('action')
        if action == 'inspect':
            url = data.get('url', '')
            if not isinstance(url, str) or len(url) > 4000:
                raise ValueError('Invalid URL')
            result = summarize(await isolated({'action': 'inspect', 'url': url}))
            if not result['options'] and not result['audio']:
                raise ValueError('No downloadable format')
            return JSONResponse(result, headers={'Cache-Control': 'no-store'})
        if action == 'chunk':
            media = verify(data.get('token'))
            offset = data.get('offset', 0)
            if not isinstance(offset, int) or offset < 0 or offset >= MAX_MEDIA or offset % CHUNK:
                raise ValueError('Invalid byte range')
            result = await isolated({'action': 'chunk', 'media': media, 'offset': offset}, timeout=35)
            content = base64.b64decode(result['data'])
            return Response(content, media_type='application/octet-stream', headers={
                'Cache-Control': 'no-store', 'X-Download-Done': '1' if result['done'] else '0',
                'X-Download-Total': str(result.get('total') or 0)})
        raise ValueError('Unknown action')
    except RuntimeError:
        return JSONResponse({'error': 'საიტის პარამეტრი აკლია. ადმინისტრატორმა უნდა დაამატოს DOWNLOAD_SECRET.'}, status_code=503)
    except (ValueError, KeyError, TypeError, OSError, asyncio.TimeoutError) as exc:
        messages = {
            'provider_blocked': 'პლატფორმამ ჰოსტინგის მოთხოვნა დაბლოკა ან ავტორიზაციას ითხოვს. ეს ვიდეო ამ სერვერიდან მიუწვდომელია. სცადე სხვა საჯარო ბმული.',
            'javascript_required': 'ამ ვიდეოსთვის საჭირო დამუშავება ჰოსტინგზე მიუწვდომელია. სცადე სხვა ვიდეო ან პლატფორმა.'
        }
        return JSONResponse({'error': messages.get(str(exc), 'ვიდეო მიუწვდომელია ან საიტმა მოთხოვნა დაბლოკა. სცადე სხვა საჯარო ბმული. თუ ჩამოტვირთვა დაიწყო, ხელახლა შეამოწმე ბმული.')}, status_code=422)
