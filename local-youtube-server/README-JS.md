# Clipstack YouTube backend (Node.js)

This is a Node.js replacement for the standalone Flask YouTube service. Copy server.js and package.json into the existing local-youtube-server folder and keep its existing templates/index.html there. The HTML already calls /api/info and /api/download.

## Run on Windows

1. Install Node.js 22 or newer and Python 3.9 or newer.
2. Open PowerShell in the local-youtube-server folder.
3. Run npm install, then npm start.
4. Open http://127.0.0.1:5000.

youtube-dl-exec is a Node.js wrapper around the yt-dlp executable and needs Python during installation. ffmpeg-static supplies FFmpeg for merging separate video/audio tracks and MP3 conversion. yt-dlp also needs a recent JavaScript runtime for YouTube challenge support.

## VPS hosting

Set HOST=0.0.0.0 and PORT to the port supplied by the host. Put the app behind HTTPS and add access controls and rate limits before making it public.

Changing Python to Node.js does not change the hosting provider outgoing IP address. If YouTube blocks that server, the same provider_blocked error can still occur. Use only videos you own or have permission to save.