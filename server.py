#!/usr/bin/env python3
import http.server
import socketserver
import os
import logging

PORT = 1987
CONTENT_DIR = "content"

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Sirve archivos solo desde CONTENT_DIR
        # Path: /index.md → content/index.md
        path = path.lstrip('/')
        full_path = os.path.join(os.getcwd(), CONTENT_DIR, path)
        return full_path

    def log_message(self, format, *args):
        logging.info(format % args)

def main():
    logging.basicConfig(level=logging.INFO, format='[SERVER] %(message)s')

    handler = CustomHandler
    with socketserver.TCPServer(("localhost", PORT), handler) as httpd:
        logging.info(f"Serving at http://localhost:{PORT}/")
        httpd.serve_forever()

if __name__ == "__main__":
    main()
