#!/usr/bin/env python3
"""
MOSS Ultra-Small-Web HTTP Server
--------------------------------
Serves only:
 - Markdown files (.md)
 - JSON metadata files (.json)

Always from ./content/
"""

import http.server
import socketserver
import os
import mimetypes
import logging

logging.basicConfig(level=logging.INFO, format='[SERVER] %(message)s')

CONTENT_DIR = "content"
HOST = "0.0.0.0"
PORT = 80   # HTTP default


class MossRequestHandler(http.server.SimpleHTTPRequestHandler):

    # Override base path
    def translate_path(self, path):
        # Remove leading slash
        path = path.lstrip("/")

        if path == "":
            path = "index.md"

        full = os.path.join(CONTENT_DIR, path)
        return full

    def do_GET(self):
        full_path = self.translate_path(self.path)

        # Only allow .md or .json
        if not (full_path.endswith(".md") or full_path.endswith(".json")):
            self.send_error(403, "Only .md and .json allowed")
            return

        if not os.path.exists(full_path):
            logging.info(f"File not found: {full_path}")
            self.send_error(404, "Not found")
            return

        logging.info(f"Serving: {full_path}")

        mime, _ = mimetypes.guess_type(full_path)
        if mime is None:
            mime = "text/plain; charset=utf-8"

        try:
            with open(full_path, "rb") as f:
                data = f.read()
        except Exception as e:
            logging.error(f"Error reading file: {e}")
            self.send_error(500, "Internal server error")
            return

        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run():
    logging.info(f"Serving HTTP on {HOST}:{PORT} from /{CONTENT_DIR}")

    with socketserver.TCPServer((HOST, PORT), MossRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logging.info("Shutting down...")


if __name__ == "__main__":
    run()
