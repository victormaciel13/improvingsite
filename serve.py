#!/usr/bin/env python3
"""Simple development server for the static landing page.

This script wraps Python's built-in HTTP server to serve the project
files on ``localhost`` so the page can be reviewed in a browser while we
iterate on the design. By default, it serves on port 8000 and opens the
site automatically in the default browser.
"""
from __future__ import annotations

import argparse
import contextlib
import socket
import webbrowser
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import TCPServer
from typing import Optional


class ProjectHTTPRequestHandler(SimpleHTTPRequestHandler):
    """HTTP handler that always serves files from the project root."""

    def __init__(self, *args, **kwargs):
        project_root = Path(__file__).resolve().parent
        super().__init__(*args, directory=str(project_root), **kwargs)


def find_available_port(preferred_port: int) -> int:
    """Return an available port, falling back if the preferred is busy."""

    with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        try:
            sock.bind(("", preferred_port))
            return preferred_port
        except OSError:
            sock.bind(("", 0))
            return sock.getsockname()[1]


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the site locally")
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the development server on (default: 8000)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the browser after starting",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    port = find_available_port(args.port)

    handler = ProjectHTTPRequestHandler

    with TCPServer(("", port), handler) as httpd:
        httpd.allow_reuse_address = True
        url = f"http://localhost:{port}/"

        print(f"Serving landing page at {url}\nPress Ctrl+C to stop the server.")

        if not args.no_browser:
            webbrowser.open(url)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server…")
        finally:
            httpd.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
