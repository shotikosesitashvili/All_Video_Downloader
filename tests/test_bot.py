import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch
import bot


def fixture():
    message = NS(reply_text=AsyncMock(), reply_document=AsyncMock(), reply_audio=AsyncMock())
    query = NS(answer=AsyncMock(), data='abc:720', message=message)
    update = NS(effective_chat=NS(type='private'), effective_user=NS(id=123),
                callback_query=query, effective_message=message)
    context = NS(user_data={'video': {'key': 'abc', 'created': time.monotonic(),
        'qualities': ['720', 'audio'], 'url': 'https://example.com/v', 'title': 'Test'}})
    return update, context, message


class BotTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        bot.BUSY.clear()

    async def test_access_default_closed(self):
        update, context, message = fixture()
        with patch.object(bot, 'ALLOWED', set()), patch.object(bot, 'worker', new_callable=AsyncMock) as job:
            await bot.receive(update, context)
            job.assert_not_called()
            message.reply_text.assert_awaited_once()

    async def test_expired_menu(self):
        update, context, message = fixture()
        context.user_data['video']['created'] -= 901
        with patch.object(bot, 'ALLOWED', {123}), patch.object(bot, 'worker', new_callable=AsyncMock) as job:
            await bot.download(update, context)
            job.assert_not_called()

    async def test_old_menu(self):
        update, context, message = fixture()
        update.callback_query.data = 'old:720'
        with patch.object(bot, 'ALLOWED', {123}), patch.object(bot, 'worker', new_callable=AsyncMock) as job:
            await bot.download(update, context)
            job.assert_not_called()

    async def test_download_and_cleanup(self):
        update, context, message = fixture()
        captured = []
        async def fake_worker(mode, url, folder, quality):
            path = Path(folder) / 'media.mp4'
            path.write_bytes(b'fake test media')
            captured.append(path)
            return {'file': str(path)}
        with patch.object(bot, 'ALLOWED', {123}), patch.object(bot, 'worker', side_effect=fake_worker):
            await bot.download(update, context)
        message.reply_document.assert_awaited_once()
        self.assertFalse(captured[0].exists())
        self.assertNotIn(123, bot.BUSY)

    async def test_failure_releases_user(self):
        update, context, message = fixture()
        with patch.object(bot, 'ALLOWED', {123}), patch.object(bot, 'worker', side_effect=ValueError):
            await bot.download(update, context)
        self.assertNotIn(123, bot.BUSY)
        message.reply_document.assert_not_called()

    async def test_oversize_not_sent(self):
        update, context, message = fixture()
        async def fake_worker(mode, url, folder, quality):
            path = Path(folder) / 'media.mp4'
            path.write_bytes(b'x' * 20)
            return {'file': str(path)}
        with patch.object(bot, 'ALLOWED', {123}), patch.object(bot, 'LIMIT', 10), patch.object(bot, 'worker', side_effect=fake_worker):
            await bot.download(update, context)
        message.reply_document.assert_not_called()
