import os
import socket
import sys
import time
import unittest
from unittest.mock import AsyncMock, patch
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api import security
from api.index import app, summarize


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'DOWNLOAD_SECRET': 'a'*64})
        self.env.start()
    def tearDown(self):
        self.env.stop()
    def test_session_cookies_are_encrypted(self):
        import base64
        cookies = [{'name': 'tt_chain_token', 'value': 'test-private-cookie',
                    'domain': '.tiktok.com', 'path': '/', 'secure': True, 'expires': None}]
        token = security.sign({'url': 'https://media.tiktok.com/video', 'cookies': cookies})
        self.assertTrue(token.startswith('v2.'))
        decoded = base64.urlsafe_b64decode(token[3:] + '=' * (-len(token[3:]) % 4))
        self.assertNotIn(b'test-private-cookie', decoded)
        self.assertEqual(security.verify(token)['cookies'], cookies)

    def test_cookie_scope_preserved(self):
        import requests
        session = requests.Session()
        session.trust_env = False
        security.restore_cookies(session, [{'name': 'tt_chain_token', 'value': 'sample',
            'domain': '.tiktok.com', 'path': '/', 'secure': True, 'expires': None}])
        for url, expected in [('https://v16-webapp-prime.tiktok.com/video', True),
                              ('https://example.com/video', False),
                              ('http://v16-webapp-prime.tiktok.com/video', False)]:
            prepared = session.prepare_request(requests.Request('GET', url))
            self.assertEqual('tt_chain_token=sample' in prepared.headers.get('Cookie', ''), expected)

    def test_cookies_survive_quality_selection(self):
        fmt = dict(id='720',url='https://media.tiktok.com/video',headers={},height=720,size=123,
                   ext='mp4',video=True,audio=True,vcodec='avc1',fps=30,abr=128,
                   cookies=[{'name': 'tt_chain_token', 'value': 'sample', 'domain': '.tiktok.com'}])
        info = {'title': 'Title', 'source': 'TikTok', 'duration': 12, 'formats': [fmt]}
        payload = security.verify(summarize(info)['options'][0]['video']['token'])
        self.assertEqual(payload['cookies'], fmt['cookies'])

    def test_existing_signed_menu_still_verifies(self):
        import base64, hashlib, hmac, json
        payload = {'url': 'https://example.com/video', 'exp': int(time.time()) + 60}
        raw = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        sig = hmac.new(security.secret(), raw.encode(), hashlib.sha256).hexdigest()
        self.assertEqual(security.verify(raw + '.' + sig)['url'], payload['url'])

    def test_signed_roundtrip(self):
        self.assertEqual(security.verify(security.sign({'url':'https://example.com/a'}))['url'], 'https://example.com/a')
    def test_tamper_rejected(self):
        token = security.sign({'url':'https://example.com/a'})
        with self.assertRaises(ValueError):
            security.verify(token[:-1]+('0' if token[-1]!='0' else '1'))
    def test_expiry(self):
        token = security.sign({'url':'https://example.com/a'})
        with patch('api.security.time.time', return_value=time.time()+1300):
            with self.assertRaises(ValueError):
                security.verify(token)
    def test_missing_secret_closed(self):
        with patch.dict(os.environ, {'DOWNLOAD_SECRET':''}):
            with self.assertRaises(RuntimeError):
                security.sign({'url':'https://example.com'})
    def test_bad_urls(self):
        for url in ['file:///etc/passwd','ftp://example.com','https://u:p@example.com','http://example.com:22']:
            with self.assertRaises(ValueError):
                security.public_url(url)
    def test_private_dns(self):
        with patch('api.security.socket.getaddrinfo',return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',80))]):
            with self.assertRaises(ValueError):
                security.public_url('http://example.com')
    def test_combined_and_adaptive(self):
        def fmt(h, video, audio, ext, codec='avc1'):
            return dict(id=str(h),url='https://example.com/media',headers={},height=h,size=123,
                        ext=ext,video=video,audio=audio,vcodec=codec,fps=30,abr=128)
        info={'title':'Title','source':'Test','duration':12,
              'formats':[fmt(720,True,False,'mp4'),fmt(360,True,True,'mp4'),fmt(None,False,True,'m4a')]}
        data=summarize(info)
        self.assertEqual([o['label'] for o in data['options']],['720p','360p'])
        self.assertIsNotNone(data['options'][0]['audio'])
        self.assertIsNone(data['options'][1]['audio'])
        security.verify(data['options'][0]['video']['token'])


class APITests(unittest.IsolatedAsyncioTestCase):
    async def request(self, action, data, origin=None):
        import httpx
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            return await client.post('/api/index?action='+action,json=data,headers={'Origin':origin} if origin else {})
    async def test_foreign_origin(self):
        r=await self.request('inspect',{'url':'https://example.com'},'https://evil.example')
        self.assertEqual(r.status_code,403)
    async def test_invalid_token(self):
        with patch.dict(os.environ,{'DOWNLOAD_SECRET':'x'*64}):
            r=await self.request('chunk',{'token':'bad','offset':0})
        self.assertEqual(r.status_code,422)
    async def test_private_inspect_failure(self):
        with patch('api.index.isolated',side_effect=ValueError):
            r=await self.request('inspect',{'url':'http://127.0.0.1'})
        self.assertEqual(r.status_code,422)
    async def test_chunk_payload_is_bounded(self):
        import base64
        with patch.dict(os.environ,{'DOWNLOAD_SECRET':'x'*64}):
            token=security.sign({'url':'https://example.com/a'})
            with patch('api.index.isolated',new_callable=AsyncMock,return_value={'data':base64.b64encode(b'abc').decode(),'done':True,'total':3}):
                r=await self.request('chunk',{'token':token,'offset':0})
        self.assertEqual(r.content,b'abc')
        self.assertEqual(r.headers['x-download-done'],'1')
    async def test_unaligned_offset(self):
        with patch.dict(os.environ,{'DOWNLOAD_SECRET':'x'*64}):
            token=security.sign({'url':'https://example.com/a'})
            with patch('api.index.isolated',new_callable=AsyncMock) as worker:
                r=await self.request('chunk',{'token':token,'offset':1})
                worker.assert_not_called()
        self.assertEqual(r.status_code,422)

