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
import json
import socket
import sys
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import TCPServer, ThreadingMixIn
from typing import Optional
from urllib.parse import unquote

import cgi

import storage


class ThreadedTCPServer(ThreadingMixIn, TCPServer):
    daemon_threads = True


class ProjectHTTPRequestHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves static assets and candidate APIs."""

    def __init__(self, *args, **kwargs):
        project_root = Path(__file__).resolve().parent
        super().__init__(*args, directory=str(project_root), **kwargs)

    # ---- Helpers -----------------------------------------------------

    def log_error(self, format: str, *args) -> None:  # noqa: A003 - matching base signature
        """Route server errors to stderr so they appear in the console."""

        sys.stderr.write("ERROR: " + (format % args) + "\n")

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        response = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    # ---- API handlers ------------------------------------------------

    def do_POST(self) -> None:  # noqa: D401 - behavior documented via helper
        if self.path == "/api/candidates":
            self._handle_save_candidate()
            return

        if self.path == "/api/login":
            self._handle_login()
            return

        super().do_POST()

    def do_GET(self) -> None:
        if self.path.startswith("/api/candidates/"):
            email = unquote(self.path.split("/api/candidates/", 1)[1])
            self._handle_get_candidate(email)
            return

        super().do_GET()

    def _parse_candidate_payload(self) -> tuple[dict, Optional[str], Optional[bytes]]:
        content_type = self.headers.get("Content-Type", "")

        if "multipart/form-data" in content_type:
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": content_type,
                    "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
                },
                keep_blank_values=True,
            )

            payload = {
                "nome": form.getfirst("nome", "").strip(),
                "email": form.getfirst("email", "").strip(),
                "telefone": form.getfirst("telefone", "").strip(),
                "area_interesse": form.getfirst("area", "").strip(),
                "recebe_alertas": form.getfirst("alertas") == "sim",
                "senha": form.getfirst("senha", "").strip(),
            }

            resume_field = form["curriculo"] if "curriculo" in form else None
            if getattr(resume_field, "file", None):
                resume_filename = resume_field.filename or ""
                resume_data = resume_field.file.read()
            else:
                resume_filename = None
                resume_data = None

            return payload, resume_filename, resume_data

        if "application/json" in content_type:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            try:
                data = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError as exc:  # pragma: no cover - guardrail
                raise storage.ValidationError("Não foi possível interpretar os dados enviados.") from exc

            payload = {
                "nome": str(data.get("nome", "")).strip(),
                "email": str(data.get("email", "")).strip(),
                "telefone": str(data.get("telefone", "")).strip(),
                "area_interesse": (
                    str(
                        data.get(
                            "area_interesse",
                            data.get("areaInteresse", data.get("area", "")),
                        )
                    ).strip()
                ),
                "recebe_alertas": bool(
                    data.get("recebe_alertas")
                    or data.get("recebeAlertas")
                    or data.get("alertas")
                ),
                "senha": str(data.get("senha", "")).strip(),
            }
            return payload, None, None

        raise storage.ValidationError("Tipo de conteúdo não suportado para o cadastro.")

    def _handle_save_candidate(self) -> None:
        try:
            payload, resume_filename, resume_data = self._parse_candidate_payload()
            candidate = storage.create_or_update_candidate(
                payload,
                resume_filename=resume_filename,
                resume_data=resume_data,
            )
        except storage.ValidationError as exc:
            self._send_json({"message": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        except storage.AuthenticationError as exc:
            self._send_json({"message": str(exc)}, status=HTTPStatus.UNAUTHORIZED)
            return
        except Exception as exc:  # pragma: no cover - defensive guard
            self.log_error("%s", str(exc))
            self._send_json(
                {"message": "Não foi possível salvar o cadastro no momento. Tente novamente mais tarde."},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return

        self._send_json({"candidate": candidate, "message": "Cadastro salvo com sucesso."})

    def _handle_get_candidate(self, email: str) -> None:
        if not email:
            self._send_json({"message": "Informe um e-mail para consultar o cadastro."}, status=HTTPStatus.BAD_REQUEST)
            return

        candidate = storage.get_candidate_by_email(email)
        if not candidate:
            self._send_json(
                {"message": "Nenhum cadastro foi encontrado para o e-mail informado."},
                status=HTTPStatus.NOT_FOUND,
            )
            return

        self._send_json({"candidate": candidate})

    def _handle_login(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)

        try:
            data = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json({"message": "Formato de login inválido."}, status=HTTPStatus.BAD_REQUEST)
            return

        email = str(data.get("email", "")).strip()
        password = str(data.get("senha", "")).strip()

        try:
            candidate = storage.validate_login(email, password)
        except storage.ValidationError as exc:
            self._send_json({"message": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return
        except storage.AuthenticationError as exc:
            self._send_json({"message": str(exc)}, status=HTTPStatus.UNAUTHORIZED)
            return
        except Exception as exc:  # pragma: no cover - defensive guard
            self.log_error("%s", str(exc))
            self._send_json(
                {"message": "Não foi possível validar seu login no momento."},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return

        self._send_json({"candidate": candidate, "message": "Login realizado com sucesso."})


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

    storage.initialize_database()

    with ThreadedTCPServer(("", port), handler) as httpd:
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
