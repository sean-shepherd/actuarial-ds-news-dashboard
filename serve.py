#!/usr/bin/env python3
"""Local helper that makes the dashboard's Refresh button actually work.

    python3 serve.py              # serve at http://127.0.0.1:8787/ ; Refresh commits locally
    python3 serve.py --push       # Refresh also pushes, so the live site updates
    python3 serve.py --port 9000  # different port

SECURITY: binds to loopback (127.0.0.1) only, and deliberately so — POST /api/refresh
executes ./refresh.sh. Do not change the bind address or put this behind a tunnel or
reverse proxy; anyone who could reach it could run that script.

Stdlib only. Ctrl-C to stop.
"""

import argparse
import json
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOG = ROOT / ".refresh.log"

# Guarded by _lock. state is one of: idle, running, done, failed.
_lock = threading.Lock()
_job = {"state": "idle", "last": ""}


def _last_meaningful_line():
    """Most recent non-empty line of the refresh log, for the status readout."""
    try:
        lines = [ln.strip() for ln in LOG.read_text(errors="replace").splitlines() if ln.strip()]
    except OSError:
        return ""
    return lines[-1][:200] if lines else ""


def _run_refresh(push):
    cmd = ["./refresh.sh"] if push else ["./refresh.sh", "--no-push"]
    try:
        with LOG.open("w") as log:
            rc = subprocess.call(cmd, cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT)
    except OSError as exc:
        with _lock:
            _job.update(state="failed", last="could not start refresh.sh: %s" % exc)
        return

    with _lock:
        _job.update(
            state="done" if rc == 0 else "failed",
            last=_last_meaningful_line() or ("exit code %d" % rc),
        )


class Handler(SimpleHTTPRequestHandler):
    push = False

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        # The page is regenerated in place, so a cached copy would hide the new items.
        if self.path.endswith((".html", "/")):
            self.send_header("Cache-Control", "no-store")
        SimpleHTTPRequestHandler.end_headers(self)

    def do_POST(self):
        if self.path.rstrip("/") != "/api/refresh":
            self.send_error(404)
            return
        with _lock:
            if _job["state"] == "running":
                self._json({"state": "busy"})
                return
            _job.update(state="running", last="starting")
        threading.Thread(target=_run_refresh, args=(self.push,), daemon=True).start()
        self._json({"state": "running"})

    def do_GET(self):
        if self.path.rstrip("/") == "/api/refresh/status":
            with _lock:
                state, last = _job["state"], _job["last"]
            if state == "running":
                last = _last_meaningful_line() or last
            self._json({"state": state, "last": last})
            return
        SimpleHTTPRequestHandler.do_GET(self)

    def log_message(self, fmt, *args):
        if not self.path.startswith("/api/"):
            return  # static hits are noise; API calls are worth seeing
        SimpleHTTPRequestHandler.log_message(self, fmt, *args)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--push", action="store_true",
                    help="let Refresh push to origin, updating the live GitHub Pages site")
    args = ap.parse_args()

    Handler.push = args.push
    handler = partial(Handler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)

    print("Dashboard:  http://127.0.0.1:%d/" % args.port)
    print("Refresh:    %s" % ("fetch, rebuild, commit, and PUSH (live site updates)" if args.push
                              else "fetch, rebuild, and commit locally (use --push to go live)"))
    print("Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
