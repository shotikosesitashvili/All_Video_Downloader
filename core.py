import ipaddress
import socket
from urllib.parse import urlsplit


def validate_url(value):
    value = value.strip()
    p = urlsplit(value)
    if (p.scheme not in {'http', 'https'} or not p.hostname or p.username
            or p.password or p.port not in {None, 80, 443}):
        raise ValueError('Public HTTP/HTTPS URL required')
    addresses = socket.getaddrinfo(p.hostname, p.port or 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Private network URL rejected')
    return value


def choices(info):
    return sorted({int(f['height']) for f in info.get('formats', [])
                   if f.get('height') and f.get('vcodec') != 'none'})


def format_selector(quality):
    if quality == 'audio':
        return 'bestaudio/best'
    if quality == 'best':
        return 'bv*+ba/b'
    h = int(quality)
    if not 1 <= h <= 16384:
        raise ValueError('Invalid quality')
    return f'bv*[height<={h}]+ba/b[height<={h}]'
