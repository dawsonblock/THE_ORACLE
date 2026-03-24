#!/usr/bin/env python3
"""
THE ORACLE - UI Server
Serves the web UI and handles static files
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8080
DIRECTORY = Path(__file__).parent


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)
    
    def end_headers(self):
        # Add CORS headers for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()


def main():
    os.chdir(DIRECTORY)
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🔮 THE ORACLE UI Server")
        print(f"Serving at http://localhost:{PORT}")
        print(f"Press Ctrl+C to stop")
        print()
        httpd.serve_forever()


if __name__ == "__main__":
    main()
