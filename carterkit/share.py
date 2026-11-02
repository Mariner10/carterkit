"""`carterkit share <layout.json>`: serve a layout on the LAN for a few minutes and
show a QR of ``carter://import?url=...`` so the phone can import it."""
from __future__ import annotations

import http.server
import json
import socket
import threading
import urllib.parse
from typing import Optional

from . import qr

SERVE_SECONDS = 600


def lan_ip() -> str:
    """Best-effort LAN address (no packets are sent); falls back to loopback."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def import_link(url: str) -> str:
    return "carter://import?url=" + urllib.parse.quote(url, safe=":/")


def _handler(body: bytes):
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.split("?")[0] != "/layout.json":
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass
    return H


def serve(body: bytes, *, host: str = "0.0.0.0", port: int = 0):
    """Start the server in a thread; returns (server, port)."""
    srv = http.server.ThreadingHTTPServer((host, port), _handler(body))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def share(path: str, *, https_url: Optional[str] = None, seconds: float = SERVE_SECONDS,
          out=print, ip: Optional[str] = None) -> int:
    import carterkit
    try:
        with open(path, "rb") as f:
            raw = f.read()
        layout = json.loads(raw)
    except (OSError, ValueError) as e:
        out(f"cannot read {path}: {e}")
        return 1
    findings = carterkit.validate_layout(layout)
    errors = [f for f in findings if f["severity"] == "error"]
    if errors:
        out(carterkit.format_findings(findings))
        out("fix the errors above before sharing")
        return 1
    srv = None
    if https_url:
        url = https_url
    else:
        srv, port = serve(raw)
        url = f"http://{ip or lan_ip()}:{port}/layout.json"
    link = import_link(url)
    out(qr.encode(link).ascii())
    out(link)
    if srv is None:
        return 0
    out(f"serving for {int(seconds // 60)} min; Ctrl-C to stop")
    try:
        threading.Event().wait(seconds)
    except KeyboardInterrupt:
        pass
    finally:
        srv.shutdown()
        srv.server_close()
    return 0
