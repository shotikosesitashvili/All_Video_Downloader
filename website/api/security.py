import base64
import hashlib
import hmac
import ipaddress
import json
import os
import socket
import time
from urllib.parse import urlsplit
from Cryptodome.Cipher import AES

CHUNK = 2 * 1024 * 1024
MAX_MEDIA = 64 * 1024 * 1024


def public_url(value):
    if not isinstance(value, str) or len(value) > 16000:
        raise ValueError('Invalid URL')
    p = urlsplit(value.strip())
    if p.scheme not in {'https', 'http'} or not p.hostname or p.username or p.password or p.port not in {None, 80, 443}:
        raise ValueError('Public HTTP/HTTPS URL required')
    addresses = socket.getaddrinfo(p.hostname, p.port or (443 if p.scheme == 'https' else 80), type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Private network is blocked')
    return value.strip()


def secret():
    key = os.environ.get('DOWNLOAD_SECRET', '')
    if len(key) < 32:
        raise RuntimeError('DOWNLOAD_SECRET must contain at least 32 characters')
    return key.encode()


def encryption_key():
    return hashlib.sha256(b'clipstack-capability-v2\x00' + secret()).digest()


def sign(payload):
    payload = dict(payload, exp=int(time.time()) + 1200)
    nonce = os.urandom(12)
    cipher = AES.new(encryption_key(), AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(json.dumps(payload, separators=(',', ':')).encode())
    return 'v2.' + base64.urlsafe_b64encode(nonce + tag + ciphertext).decode().rstrip('=')


def verify(token):
    if not isinstance(token, str) or len(token) > 32000:
        raise ValueError('Invalid token')
    if token.startswith('v2.'):
        raw = token[3:]
        sealed = base64.urlsafe_b64decode(raw + '=' * (-len(raw) % 4))
        if len(sealed) < 29 or base64.urlsafe_b64encode(sealed).decode().rstrip('=') != raw:
            raise ValueError('Invalid token')
        cipher = AES.new(encryption_key(), AES.MODE_GCM, nonce=sealed[:12])
        payload = json.loads(cipher.decrypt_and_verify(sealed[28:], sealed[12:28]))
    else:
        raw, sig = token.rsplit('.', 1)
        expected = hmac.new(secret(), raw.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise ValueError('Invalid signature')
        payload = json.loads(base64.urlsafe_b64decode(raw + '=' * (-len(raw) % 4)))
    if payload['exp'] <= time.time():
        raise ValueError('expired_token')
    return payload


def cookie_records(jar, url):
    return [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path,
             'secure': c.secure, 'expires': c.expires}
            for c in jar.get_cookies_for_url(url)]


def restore_cookies(session, cookies):
    for c in cookies:
        session.cookies.set(c['name'], c['value'], domain=c['domain'], path=c.get('path') or '/',
                            secure=bool(c.get('secure')), expires=c.get('expires'))


def guard_network():
    original_dns = socket.getaddrinfo
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def check(address):
        if isinstance(address, tuple) and not ipaddress.ip_address(address[0].split('%')[0]).is_global:
            raise OSError('Private network blocked')

    def dns(*args, **kwargs):
        addresses = original_dns(*args, **kwargs)
        for item in addresses:
            check(item[4])
        return addresses

    def connect(sock, address):
        if isinstance(address, tuple):
            check(address)
        return original_connect(sock, address)

    def connect_ex(sock, address):
        check(address)
        return original_connect_ex(sock, address)

    socket.getaddrinfo = dns
    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    for key in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy'):
        os.environ.pop(key, None)

