# Clipstack website

Georgian video downloader built for Vercel Hobby. The original Telegram bot remains in the repository root.

## Deploy

Import this GitHub repository in Vercel, set **Root Directory = website**, choose Vite, and set DOWNLOAD_SECRET to a random string of at least 32 characters. Deploy with the free Hobby plan. No BotFather token, paid API, database or paid plan is required.

The website discovers formats using yt-dlp. Each source URL receives a signed capability expiring after 20 minutes. Files are fetched in bounded 2 MiB byte ranges. Each API request is bounded to 40 seconds of extraction or 35 seconds per fetch; the configured Vercel maximum is 60 seconds. Video/audio streams are limited to 64 MiB each. Formats that require HLS/DASH fragment assembly are excluded; direct HTTP formats only. Sources that do not honor Range can only transfer a file smaller than one chunk.

MP3 conversion and audio/video merging run in the user's browser using ffmpeg.wasm; the approximately 31 MB processing module is loaded only when needed. Existing codecs are copied into MP4 when compatible, otherwise MKV. MP3 is encoded at 192 kbps. The device needs enough memory; mobile browsers may struggle. Keep the page open during downloads.

## Development

```bash
npm ci
npm run build
pip install -r requirements.txt
# Set DOWNLOAD_SECRET to a random development-only value in your environment.
uvicorn api.index:app --host 127.0.0.1 --port 8001
# In another terminal:
npm run dev
```

## Verification

```bash
pip install httpx
python -m unittest discover -s tests -v
npm run build
```

Tests cover token signing/tampering/expiry, network URL rejection, quality selection, byte-range validation, and API responses. Live provider behavior depends on their current restrictions.

## Operational limits

This is a small free-tier utility, not an unrestricted public download service. Hosting traffic and function quotas apply. Use only content you have permission to download. YouTube and social platforms may block cloud IPs; changing the UI or deployment does not bypass these restrictions. YouTube extraction also depends on availability of a supported JS runtime in the Python environment. yt-dlp bundled EJS is installed; a Node runtime is used if present.

No video library or extraction history is persisted. Data passes through bounded subprocesses and browser memory; platform request logs can still exist. Initial URLs, redirect DNS resolutions and outgoing socket IPs are checked in disposable workers; private/local/link-local IPs are denied. Capabilities are signed, not encrypted: they are not a place for credentials. Cookies and user credentials are not supported.

The API has no durable public rate limiter. Vercel Firewall rate limits should be enabled before broad public promotion. Free Hobby allowances do not guarantee unlimited availability; do not upgrade billing or buy services to compensate without approval.
