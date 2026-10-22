"""Local preview: serve the site and rebuild it whenever content changes.

    python3 _src/serve.py            http://127.0.0.1:8765/  (admin: /admin/)

The admin panel's "Work with Local Repository" mode writes straight into
_src/content/ in this folder; this server notices and rebuilds the pages, so a
browser refresh shows the change. Nothing is committed or pushed.
"""
import argparse
import functools
import http.server
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCHED = [ROOT / "_src/content", ROOT / "assets/images/uploads"]


def snapshot() -> dict:
    files = {}
    for folder in WATCHED:
        if folder.exists():
            for path in folder.rglob("*"):
                if path.is_file():
                    files[path] = path.stat().st_mtime_ns
    return files


def rebuild():
    result = subprocess.run([sys.executable, str(ROOT / "_src/build.py")], capture_output=True, text=True)
    stamp = time.strftime("%H:%M:%S")
    output = (result.stdout + result.stderr).strip()
    print(f"[{stamp}] rebuild: {output}" if result.returncode == 0 else f"[{stamp}] BUILD FAILED:\n{output}", flush=True)


def watch(interval: float):
    seen = snapshot()
    while True:
        time.sleep(interval)
        current = snapshot()
        if current != seen:
            time.sleep(0.3)  # let a multi-file save finish
            seen = snapshot()
            rebuild()


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".yml": "text/yaml", ".webp": "image/webp"}

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    rebuild()
    threading.Thread(target=watch, args=(1.0,), daemon=True).start()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), functools.partial(Handler, directory=str(ROOT)))
    print(f"serving http://127.0.0.1:{args.port}/  (admin panel: http://127.0.0.1:{args.port}/admin/)", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
