import json
import socket
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app import launcher


def _serve(body):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            data = body.encode()
            self.send_response(200)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


class LauncherTest(unittest.TestCase):
    def test_find_browser_returns_path_or_none(self):
        self.assertIsInstance(launcher.find_browser(), (str, type(None)))

    def test_probe_free_port(self):
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0))
            port = s.getsockname()[1]
        self.assertIsNone(launcher.probe(port))

    def test_probe_other_server(self):
        for body in ('<html>not candor</html>', json.dumps({'app': 'qualia'}), '[1]'):
            server = _serve(body)
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            self.assertEqual(launcher.probe(server.server_address[1]), 'other', body)

    def test_probe_candor(self):
        server = _serve(json.dumps({'app': 'candor'}))
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.assertEqual(launcher.probe(server.server_address[1]), 'candor')


if __name__ == '__main__':
    unittest.main()
