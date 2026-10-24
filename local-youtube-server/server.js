-
const express = require('express');
const path = require('node:path');
const os = require('node:os');
const fs = require('node:fs/promises');
const ytdlp = require('youtube-dl-exec');
const ffmpegPath = require('ffmpeg-static');
const app = express();
const PORT = Number(process.env.PORT || 5000);
const HOST = process.env.HOST || '127.0.0.1';
const UI_FILE = path.join(__dirname, 'templates', 'index.html');

app.disable('x-powered-by');
app.use(express.json({ limit: '16kb' }));

const YOUTUBE_HOSTS = new Set(['youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com', 'youtu.be', 'www.youtu.be']);
function validYouTubeUrl(value) {
  if (typeof value !== 'string' || value.length > 4000) return false;
  try {
    const url = new URL(value.trim());
    return ['http:', 'https:'].includes(url.protocol) && YOUTUBE_HOSTS.has(url.hostname.toLowerCase());
  } catch { return false; }
}
function baseOptions() {
  return { noPlaylist: true, noWarnings: true, noProgress: true, socketTimeout: 20, retries: 2, jsRuntimes: 'node', ...(ffmpegPath ? { ffmpegLocation: ffmpegPath } : {}) };
}
function userError(error) {
  const message = String(error?.stderr || error?.message || '').toLowerCase();
  if (['sign in', 'login required', 'confirm you', 'not a bot', 'http error 403'].some((x) => message.includes(x))) return 'YouTube ამ სერვერის მოთხოვნას ბლოკავს ან ავტორიზაციას ითხოვს. სცადე მოგვიანებით ან სხვა საჯარო ვიდეო.';
  if (message.includes('requested format is not available')) return 'არჩეული ხარისხი ამ ვიდეოსთვის მიუწვდომელია. თავიდან მოძებნე ვიდეო და აირჩიე სხვა ხარისხი.';
  if (message.includes('ffmpeg')) return 'FFmpeg ვერ გაეშვა. თავიდან დააყენე პაკეტები ბრძანებით: npm install.';
  return 'ვიდეოს დამუშავება ვერ მოხერხდა. გადაამოწმე საჯარო ბმული და სცადე ხელახლა.';
}
async function inspect(url) {
  const raw = await ytdlp(url, { ...baseOptions(), dumpSingleJson: true, skipDownload: true });
  const data = typeof raw === 'string' ? JSON.parse(raw) : raw;
  if (!data || data.is_live || ['playlist', 'multi_video'].includes(data._type)) throw new Error('Single public video required');
  const heights = [...new Set((data.formats || []).filter((f) => f.height && f.vcodec !== 'none')
    .filter((f) => ffmpegPath || (f.acodec && f.acodec !== 'none')).map((f) => Number(f.height)))].sort((a, b) => b - a);
  return { title: data.title || 'ვიდეო', thumbnail: data.thumbnail || null, channel: data.uploader || data.channel || null, duration: data.duration || null, heights, has_ffmpeg: Boolean(ffmpegPath) };
}
app.get('/', async (_req, res) => {
  try { await fs.access(UI_FILE); res.sendFile(UI_FILE); }
  catch { res.status(500).send('ვერ ვიპოვე templates/index.html. შეინახე არსებული UI ამ მისამართზე.'); }
});
app.get('/api/health', (_req, res) => res.json({ ok: true, service: 'clipstack-youtube-js' }));
app.post('/api/info', async (req, res) => {
  const url = typeof req.body?.url === 'string' ? req.body.url.trim() : '';
  if (!validYouTubeUrl(url)) return res.status(400).json({ error: 'გთხოვ, შეიყვანე სწორი YouTube ბმული.' });
  try { return res.json(await inspect(url)); }
  catch (error) {
    console.warn('YouTube info request failed:', error?.name || 'Error');
    return res.status(422).json({ error: userError(error) });
  }
});
app.post('/api/download', async (req, res) => {
  const url = typeof req.body?.url === 'string' ? req.body.url.trim() : '';
  const mode = req.body?.mode || 'video';
  const height = Math.max(1, Math.min(4320, Number.parseInt(req.body?.height, 10) || 720));
  if (!validYouTubeUrl(url) || !['video', 'audio'].includes(mode)) return res.status(400).json({ error: 'ბმული ან ფორმატი არასწორია.' });
  let tempDir;
  try {
    tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'clipstack-'));
    const output = path.join(tempDir, '%(title).80s.%(ext)s');
    const modeOptions = mode === 'audio'
      ? (ffmpegPath ? { format: 'bestaudio/best', extractAudio: true, audioFormat: 'mp3', audioQuality: '192K' } : { format: 'bestaudio[ext=m4a]/bestaudio' })
      : (ffmpegPath ? { format: 'bv*[height<=' + height + ']+ba/b[height<=' + height + ']/b', mergeOutputFormat: 'mp4' } : { format: 'b[height<=' + height + '][ext=mp4]/b[height<=' + height + ']/b' });
    await ytdlp(url, { ...baseOptions(), output, ...modeOptions });
    const files = (await fs.readdir(tempDir)).filter((name) => !name.endsWith('.part') && !name.endsWith('.ytdl'));
    const preferredExt = mode === 'audio' && ffmpegPath ? '.mp3' : mode === 'video' && ffmpegPath ? '.mp4' : null;
    const preferred = preferredExt ? files.filter((name) => path.extname(name).toLowerCase() === preferredExt) : [];
    const candidates = preferred.length ? preferred : files;
    if (!candidates.length) throw new Error('Downloaded media file was not created');
    let selected = candidates[0];
    let selectedSize = -1;
    for (const name of candidates) {
      const stat = await fs.stat(path.join(tempDir, name));
      if (stat.isFile() && stat.size > selectedSize) { selected = name; selectedSize = stat.size; }
    }
    res.download(path.join(tempDir, selected), selected, async (error) => {
      await fs.rm(tempDir, { recursive: true, force: true });
      if (error && !res.headersSent) res.status(500).json({ error: 'ფაილის გაგზავნა ვერ მოხერხდა.' });
    });
  } catch (error) {
    if (tempDir) await fs.rm(tempDir, { recursive: true, force: true });
    console.warn('YouTube download failed:', error?.name || 'Error');
    return res.status(422).json({ error: userError(error) });
  }
});
app.use((error, _req, res, _next) => {
  if (error?.type === 'entity.too.large') return res.status(413).json({ error: 'მოთხოვნა ძალიან დიდია.' });
  console.error('Request failed:', error?.name || 'Error');
  return res.status(500).json({ error: 'სერვერის შეცდომა.' });
});
app.listen(PORT, HOST, () => {
  console.log('Clipstack YouTube JS მზადაა: http://' + HOST + ':' + PORT);
  console.log('FFmpeg: ' + (ffmpegPath || 'ვერ მოიძებნა; გამოიყენება წყაროზე არსებული ფორმატები'));
});