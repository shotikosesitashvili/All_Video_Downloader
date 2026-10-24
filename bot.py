import asyncio
import json
import logging
import os
import secrets
import shutil
import signal
import sys
import tempfile
import time
from pathlib import Path
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
TOKEN = os.getenv('BOT_TOKEN', '')
ALLOWED = {int(x.strip()) for x in os.getenv('ALLOWED_USER_IDS', '').split(',') if x.strip()}
LIMIT_MB = min(49, max(1, int(os.getenv('MAX_FILE_MB', '49'))))
LIMIT = LIMIT_MB * 1_000_000
TIMEOUT = max(30, int(os.getenv('JOB_TIMEOUT_SECONDS', '600')))
BUSY = set()
SLOTS = asyncio.Semaphore(2)


def permitted(update):
    return update.effective_chat.type == 'private' and update.effective_user.id in ALLOWED


async def worker(mode, url, folder, quality='best'):
    env = {k: v for k, v in os.environ.items() if k not in {'BOT_TOKEN', 'ALLOWED_USER_IDS'}}
    proc = await asyncio.create_subprocess_exec(
        sys.executable, str(ROOT / 'worker.py'), mode, url, folder, quality, str(LIMIT),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, env=env,
        **({'start_new_session': True} if os.name != 'nt' else {}))
    try:
        output, _ = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
        if proc.returncode:
            raise ValueError('Extraction failed')
        result = json.loads(output)
        if 'error' in result:
            raise ValueError('Extraction failed')
        return result
    finally:
        if proc.returncode is None:
            if os.name == 'nt':
                killer = await asyncio.create_subprocess_exec('taskkill', '/PID', str(proc.pid), '/T', '/F',
                    stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
                await killer.wait()
            else:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            await proc.wait()


async def start(update, context):
    await update.effective_message.reply_text(
        'გამარჯობა! გამომიგზავნე YouTube, TikTok, Facebook, Instagram ან სხვა მხარდაჭერილი საიტის ვიდეოს ბმული. '
        f'შემდეგ აირჩიე ხარისხი ან MP3.\nფაილის ლიმიტი: {LIMIT_MB} MB.\n'
        'მხოლოდ საჯარო ვიდეოები; ყველა საიტი მხარდაჭერილი არ არის.\n'
        '/id — შენი Telegram ID\n/help — დახმარება\n'
        'გამოიყენე მხოლოდ იმ მასალისთვის, რომლის ჩამოტვირთვის უფლებაც გაქვს.')


async def identity(update, context):
    if update.effective_chat.type == 'private':
        await update.effective_message.reply_text(f'შენი Telegram ID: {update.effective_user.id}')


async def receive(update, context):
    message = update.effective_message
    if not permitted(update):
        await message.reply_text('წვდომისთვის დაამატე შენი /id სერვერის .env ფაილის ALLOWED_USER_IDS ველში.')
        return
    uid = update.effective_user.id
    if uid in BUSY:
        await message.reply_text('წინა მოთხოვნა ჯერ მუშავდება. დაელოდე დასრულებას.')
        return
    BUSY.add(uid)
    try:
        status = await message.reply_text('ვამოწმებ ვიდეოს… საჭიროების შემთხვევაში დაელოდე რიგს.')
        async with SLOTS:
            with tempfile.TemporaryDirectory(prefix='video-bot-') as folder:
                info = await worker('inspect', message.text.strip(), folder)
        key = secrets.token_hex(5)
        context.user_data['video'] = {'key': key, 'url': message.text.strip(),
            'created': time.monotonic(), 'title': info['title'],
            'qualities': ['best', 'audio'] + [str(h) for h in info['heights']]}
        buttons = [InlineKeyboardButton(f'{h}p-მდე', callback_data=f'{key}:{h}') for h in info['heights']]
        rows = [buttons[i:i+3] for i in range(0, len(buttons), 3)]
        rows.append([InlineKeyboardButton('საუკეთესო', callback_data=f'{key}:best'),
                     InlineKeyboardButton('MP3 🎵', callback_data=f'{key}:audio')])
        await status.edit_text(f"{info['title']}\nაირჩიე ხარისხი (მაქს. {LIMIT_MB} MB):",
                               reply_markup=InlineKeyboardMarkup(rows))
    except (ValueError, OSError, asyncio.TimeoutError):
        await message.reply_text('ვიდეო ვერ წავიკითხე. შეამოწმე ბმული. შესაძლოა ვიდეო იყოს პირადი, შეზღუდული ან საიტი დროებით არ მუშაობდეს.')
    finally:
        BUSY.discard(uid)


async def download(update, context):
    query = update.callback_query
    await query.answer()
    if not permitted(update):
        return
    uid = update.effective_user.id
    item = context.user_data.get('video')
    key, _, quality = query.data.partition(':')
    if not item or item['key'] != key or time.monotonic() - item['created'] > 900 or quality not in item['qualities']:
        await query.message.reply_text('მენიუს ვადა ამოიწურა. გამოგზავნე ბმული თავიდან.')
        return
    if uid in BUSY:
        await query.message.reply_text('მოთხოვნა უკვე მუშავდება.')
        return
    BUSY.add(uid)
    try:
        status = await query.message.reply_text('ჩამოტვირთვა… საჭიროების შემთხვევაში დაელოდე რიგს.')
        async with SLOTS:
            with tempfile.TemporaryDirectory(prefix='video-bot-') as folder:
                result = await worker('download', item['url'], folder, quality)
                path = Path(result['file'])
                if path.parent.resolve() != Path(folder).resolve() or path.stat().st_size > LIMIT:
                    raise ValueError('Invalid file')
                await status.edit_text('ფაილს ვაგზავნი…')
                with path.open('rb') as media:
                    if quality == 'audio':
                        await query.message.reply_audio(media, title=item['title'], read_timeout=120, write_timeout=120)
                    else:
                        await query.message.reply_document(media, filename='video' + path.suffix,
                            caption=item['title'], read_timeout=120, write_timeout=120)
        await status.edit_text('მზადაა ✅ სხვა ხარისხისთვის ისევ დააჭირე ღილაკს.')
    except (ValueError, OSError, asyncio.TimeoutError):
        await query.message.reply_text(f'ვერ ჩამოვტვირთე: შესაძლოა ფაილი {LIMIT_MB} MB-ზე დიდია, საიტმა დაბლოკა ან დრო ამოიწურა. აირჩიე დაბალი ხარისხი ან მოკლე ვიდეო.')
    finally:
        BUSY.discard(uid)


async def error_handler(update, context):
    logging.error('Bot operation failed (%s)', type(context.error).__name__)
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text('დროებითი შეცდომაა. სცადე ხელახლა.')
        except Exception:
            pass


def main():
    if not TOKEN or TOKEN == 'PASTE_BOTFATHER_TOKEN_HERE':
        raise SystemExit('ჩასვი BotFather-ის ტოკენი .env ფაილში: BOT_TOKEN=...')
    if not shutil.which('ffmpeg'):
        raise SystemExit('FFmpeg is required. Use Docker or install FFmpeg and add it to PATH.')
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    app = Application.builder().token(TOKEN).concurrent_updates(8).build()
    app.add_handler(CommandHandler(['start', 'help'], start))
    app.add_handler(CommandHandler('id', identity))
    app.add_handler(CallbackQueryHandler(download))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, receive))
    app.add_error_handler(error_handler)
    app.run_polling(allowed_updates=['message', 'callback_query'])


if __name__ == '__main__':
    main()
