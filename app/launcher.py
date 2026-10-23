"""Double-click entry point: Candor in its own browser app window; it stops once the window is closed.

Adapted from the launcher of the owner's Qualia (MIT)."""

import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# A windowless (pythonw) launch has no console, so messages need a dialog instead of stderr.
_CONSOLE = sys.stderr is not None
_PROGRAMS = {'edge': 'Microsoft/Edge/Application/msedge.exe', 'chrome': 'Google/Chrome/Application/chrome.exe'}
_MAC_APPS = ('/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
             '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
_COMMANDS = ('msedge', 'microsoft-edge', 'google-chrome', 'chromium', 'chromium-browser')
# Open pages check in at least every 15 s (browsers slow hidden windows to about once a minute).
# Counting checks instead of clock time means a sleeping laptop never counts as idle.
CHECK_SECONDS = 10
IDLE_CHECKS = 18  # ponytail: ~3 awake minutes without page contact; shorten if users want faster exit


def _default_browser():
    """'chrome' or 'edge' when that is the Windows default browser, else None."""
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\Shell\Associations'
                            r'\UrlAssociations\https\UserChoice') as key:
            program = winreg.QueryValueEx(key, 'ProgId')[0]
    except (ImportError, OSError):
        return None
    return 'chrome' if program.startswith('ChromeHTML') else 'edge' if program.startswith('MSEdgeHTM') else None


def find_browser():
    """Edge or Chrome, whose app mode gives Candor a window without tabs or address bar.

    The person's default browser wins when it is one of the two; otherwise Edge, which every
    Windows 10/11 PC has."""
    order = ('chrome', 'edge') if _default_browser() == 'chrome' else ('edge', 'chrome')
    roots = [os.environ.get(name) for name in ('ProgramFiles(x86)', 'ProgramFiles', 'LOCALAPPDATA')]
    paths = [Path(root, _PROGRAMS[browser]) for browser in order for root in roots if root]
    for path in [*paths, *map(Path, _MAC_APPS)]:
        if path.is_file():
            return str(path)
    return next((found for name in _COMMANDS if (found := shutil.which(name))), None)


def probe(port):
    """'candor' if Candor already serves the port, 'other' if another program does, None if free."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f'http://127.0.0.1:{port}/api/ping', timeout=2) as response:
            return 'candor' if json.loads(response.read(4096)).get('app') == 'candor' else 'other'
    except urllib.request.HTTPError:
        return 'other'
    except OSError:
        return None
    except (ValueError, AttributeError):  # not JSON, or not a JSON object
        return 'other'


def _notify(message):
    if os.name == 'nt' and not _CONSOLE:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, 'Candor', 0x40)
    else:
        print(message, file=sys.stderr)


def _open(url):
    browser = find_browser()
    if browser:
        # The person's normal browser profile: no first-run or sign-in prompts for a new profile.
        subprocess.Popen([browser, f'--app={url}', '--window-size=1280,860'])
    else:
        webbrowser.open(url)


def _watch(server):
    seen, idle = server.last_seen, 0
    while idle < IDLE_CHECKS:
        time.sleep(CHECK_SECONDS)
        # A run still working (an application takes 10-15 minutes) finishes even if the window closed.
        working = any(task.status in ('queued', 'running', 'cancelling') for task in server.runner.active())
        idle = 0 if server.last_seen != seen or working else idle + 1
        seen = server.last_seen
    server.shutdown()


def main():
    try:
        _run()
    except Exception as error:  # a windowless launch must never fail silently
        _notify(f'Candor could not start: {error}')
        if _CONSOLE:
            raise


def _run():
    os.chdir(ROOT)
    log = ROOT / 'state' / 'candor-app.log'
    if not _CONSOLE:
        # Keep a log for troubleshooting a windowless launch.
        log.parent.mkdir(exist_ok=True)
        sys.stdout = sys.stderr = open(log, 'a', encoding='utf-8')
    try:
        port = int(os.environ.get('CANDOR_PORT') or 8770)
    except ValueError:
        return _notify('The CANDOR_PORT setting must be a number, such as 8771.')
    url = f'http://127.0.0.1:{port}'
    state = probe(port)
    if state == 'candor':
        return _open(url)
    if state == 'other':
        return _notify(f'Another program is using port {port}, which Candor needs. Close that program '
                       'and open Candor again, or ask someone to set CANDOR_PORT to another number such as 8771.')
    from app.server import create_server

    try:
        server = create_server(ROOT, port)
    except OSError as error:
        return _notify(f'Candor could not start on port {port} ({error}). See {log} for details.')
    threading.Thread(target=_watch, args=(server,), daemon=True).start()
    _open(url)
    server.serve_forever()


if __name__ == '__main__':
    main()
