import json
import socket
import threading
import unittest
import unittest.mock
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


class IdleShutdown(unittest.TestCase):
    """The server stops once no page has checked in for IDLE_CHECKS checks, unless a run is working."""

    def fake(self, statuses):
        runner = type('Runner', (), {'active': lambda self: [
            type('T', (), {'status': s})() for s in statuses]})()
        server = type('Server', (), {'last_seen': 1.0, 'runner': runner, 'stopped': False})()
        server.shutdown = lambda: setattr(server, 'stopped', True)
        return server

    def test_idle_window_stops_server(self):
        server = self.fake([])
        with unittest.mock.patch.object(launcher, 'CHECK_SECONDS', 0),                 unittest.mock.patch.object(launcher, 'IDLE_CHECKS', 3):
            launcher._watch(server)
        self.assertTrue(server.stopped)

    def test_running_task_keeps_server_alive(self):
        server = self.fake(['running'])
        checks = []

        def sleep(_):
            checks.append(1)
            if len(checks) > 10:  # then the run finishes
                server.runner.active = lambda: []
        with unittest.mock.patch.object(launcher, 'CHECK_SECONDS', 0),                 unittest.mock.patch.object(launcher, 'IDLE_CHECKS', 3),                 unittest.mock.patch.object(launcher.time, 'sleep', sleep):
            launcher._watch(server)
        self.assertGreater(len(checks), 10)
        self.assertTrue(server.stopped)


if __name__ == '__main__':
    unittest.main()
