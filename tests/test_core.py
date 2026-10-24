import socket
import unittest
from unittest.mock import patch
from core import choices, format_selector, validate_url


class CoreTests(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(format_selector('audio'), 'bestaudio/best')
        self.assertEqual(format_selector('best'), 'bv*+ba/b')
        self.assertEqual(format_selector('720'), 'bv*[height<=720]+ba/b[height<=720]')

    def test_invalid_quality(self):
        for value in ('0', '-10', '999999', 'oops'):
            with self.assertRaises(ValueError):
                format_selector(value)

    def test_quality_list(self):
        self.assertEqual(choices({'formats': [
            {'height': 720, 'vcodec': 'h264'}, {'height': 360, 'vcodec': 'h264'},
            {'height': 720, 'vcodec': 'vp9'}, {'height': 1080, 'vcodec': 'none'},
            {'vcodec': 'none'}]}), [360, 720])

    def test_url_scheme_credentials_port(self):
        for value in ('file:///etc/passwd', 'ftp://example.com/a', 'https://a:b@example.com',
                      'https://example.com:22/a', 'hello', 'http://example.com:bad'):
            with self.assertRaises(ValueError):
                validate_url(value)

    def test_private_ips_and_mixed_dns(self):
        for address in ('127.0.0.1', '10.0.0.1', '169.254.169.254', '::1', '192.168.1.1'):
            with patch('core.socket.getaddrinfo', return_value=[
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 443)),
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', (address, 443))]):
                with self.assertRaises(ValueError):
                    validate_url('https://example.com/video')

    def test_public_url(self):
        with patch('core.socket.getaddrinfo', return_value=[
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('8.8.8.8', 443))]):
            self.assertEqual(validate_url(' https://example.com/v '), 'https://example.com/v')


if __name__ == '__main__':
    unittest.main()
