#!/usr/bin/env python3
"""Simple local server for Data Viewer.

- Serves static files from current directory.
- Provides /proxy?url=<remote_text_url> to bypass browser CORS for txt loading.
"""

from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

HOST = "127.0.0.1"
PORT = 8010


class ViewerHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/proxy":
            self._handle_proxy(parsed.query)
            return

        if parsed.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def _handle_proxy(self, query: str) -> None:
        params = parse_qs(query)
        target = (params.get("url") or [""])[0].strip()
        if not target:
            self.send_error(400, "Missing 'url' query parameter")
            return

        try:
            req = Request(
                target,
                headers={
                    "User-Agent": "DataViewer/1.0",
                    "Accept": "text/plain,*/*;q=0.8",
                },
            )
            with urlopen(req, timeout=20) as resp:
                payload = resp.read()
                status = getattr(resp, "status", 200) or 200
        except Exception as exc:  # noqa: BLE001
            message = str(exc).encode("utf-8", errors="replace")
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(message)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(message)
            return

        self.send_response(status)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), ViewerHandler)
    print(f"Data Viewer server running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
