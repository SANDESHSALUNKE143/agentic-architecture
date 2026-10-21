"""
Fixture public site for the allowlisted web connector.

Serves two fixed JSON pages. The agent is allowed to fetch stats.example,
which the process maps to this origin. No credentials are accepted.

Run: the site service in compose, listening on port 8080.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGES = {
    "/cities/pune": {"summary": "Public site note: Pune listings increased this quarter."},
    "/cities/mumbai": {"summary": "Public site note: Mumbai listings were unchanged."},
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        """Keep the fixture quiet. Paths are fixed and contain no credentials."""
        return

    def do_GET(self):
        body = PAGES.get(self.path)
        if body is None:
            raw = b'{"detail":"not found"}'
            self.send_response(404)
        else:
            raw = json.dumps(body).encode()
            self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
