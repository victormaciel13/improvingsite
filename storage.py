"""SQLite-backed persistence utilities for candidate profiles."""

from __future__ import annotations

import hashlib
import os
import re
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

DATA_DIR_ENV = "IDEAL_DATA_DIR"


class StorageError(RuntimeError):
    """Base class for storage-related exceptions."""


class ValidationError(StorageError):
    """Raised when incoming data is invalid or incomplete."""


@dataclass
class Candidate:
    id: int
    nome: str
    email: str
    telefone: str
    area: str
    deseja_alertas: bool
    curriculo: Optional[str]
    criado_em: str
    atualizado_em: str

    def to_payload(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "telefone": self.telefone,
            "area": self.area,
            "desejaAlertas": self.deseja_alertas,
            "curriculo": self.curriculo,
            "criadoEm": self.criado_em,
            "atualizadoEm": self.atualizado_em,
        }


def _get_data_dir() -> Path:
    override = os.getenv(DATA_DIR_ENV)
    if override:
        data_dir = Path(override).expanduser().resolve()
    else:
        data_dir = Path(__file__).resolve().parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _get_database_path() -> Path:
    return _get_data_dir() / "site.db"


def _get_uploads_dir() -> Path:
    uploads = _get_data_dir() / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    return uploads


def initialize_database() -> None:
    """Ensure the SQLite database and tables exist."""

    db_path = _get_database_path()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                telefone TEXT,
                area TEXT NOT NULL,
                deseja_alertas INTEGER NOT NULL DEFAULT 0,
                curriculo TEXT,
                senha_hash TEXT NOT NULL,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL
            )
            """
        )
        conn.commit()

        _ensure_schema(conn)


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Ensure optional columns exist for older databases."""

    conn.row_factory = sqlite3.Row
    columns = {
        row["name"]: row for row in conn.execute("PRAGMA table_info(candidates)").fetchall()
    }

    if "senha_hash" not in columns:
        conn.execute("ALTER TABLE candidates ADD COLUMN senha_hash TEXT")
        conn.execute("UPDATE candidates SET senha_hash = '' WHERE senha_hash IS NULL")
        conn.commit()


def _normalize_filename(filename: str) -> str:
    filename = filename.strip().replace("\x00", "")
    name = Path(filename).name
    sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return sanitized or "curriculo"


def _store_resume(filename: Optional[str], data: Optional[bytes], previous: Optional[str]) -> Optional[str]:
    if not filename or not data:
        return previous

    uploads_dir = _get_uploads_dir()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    normalized = _normalize_filename(filename)
    target_name = f"{timestamp}_{normalized}"
    target_path = uploads_dir / target_name
    target_path.write_bytes(data)

    if previous:
        try:
            old_path = (_get_data_dir() / previous).resolve()
            uploads_root = _get_uploads_dir().resolve()
            if uploads_root in old_path.parents or old_path == uploads_root:
                if old_path.exists():
                    old_path.unlink()
        except OSError:
            pass

    return str(Path("uploads") / target_name)


def _row_to_candidate(row: sqlite3.Row) -> Candidate:
    return Candidate(
        id=row["id"],
        nome=row["nome"],
        email=row["email"],
        telefone=row["telefone"] or "",
        area=row["area"],
        deseja_alertas=bool(row["deseja_alertas"]),
        curriculo=row["curriculo"],
        criado_em=row["criado_em"],
        atualizado_em=row["atualizado_em"],
    )


def save_candidate(payload: Dict[str, Any], *, resume_filename: Optional[str] = None, resume_data: Optional[bytes] = None) -> Dict[str, Any]:
    """Create or update a candidate and return the stored representation."""

    required_fields = ("nome", "email", "area")
    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        raise ValidationError(
            "Os campos a seguir são obrigatórios para salvar o cadastro: " + ", ".join(missing)
        )

    initialize_database()

    now = datetime.now(timezone.utc).isoformat()
    email = payload["email"].strip()
    senha = payload.get("senha", "").strip()

    with sqlite3.connect(_get_database_path()) as conn:
        conn.row_factory = sqlite3.Row
        existing = conn.execute("SELECT * FROM candidates WHERE email = ?", (email,)).fetchone()

        resume_path = _store_resume(resume_filename, resume_data, existing["curriculo"] if existing else None)

        deseja_alertas = 1 if payload.get("deseja_alertas") else 0
        telefone = payload.get("telefone", "").strip()
        nome = payload["nome"].strip()
        area = payload["area"].strip()

        senha_hash = existing["senha_hash"] if existing else ""

        if existing:
            if senha:
                senha_hash = _hash_password(senha)
        else:
            if not senha:
                raise ValidationError("Defina uma senha para criar seu cadastro e acessar recomendações personalizadas.")
            senha_hash = _hash_password(senha)

        if existing:
            conn.execute(
                """
                UPDATE candidates
                SET nome = ?, telefone = ?, area = ?, deseja_alertas = ?, curriculo = ?, senha_hash = ?, atualizado_em = ?
                WHERE email = ?
                """,
                (nome, telefone, area, deseja_alertas, resume_path, senha_hash, now, email),
            )
            conn.commit()
            updated = conn.execute("SELECT * FROM candidates WHERE email = ?", (email,)).fetchone()
        else:
            conn.execute(
                """
                INSERT INTO candidates (nome, email, telefone, area, deseja_alertas, curriculo, senha_hash, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (nome, email, telefone, area, deseja_alertas, resume_path, senha_hash, now, now),
            )
            conn.commit()
            updated = conn.execute("SELECT * FROM candidates WHERE email = ?", (email,)).fetchone()

    candidate = _row_to_candidate(updated)
    return candidate.to_payload()


def get_candidate_by_email(email: str) -> Optional[Dict[str, Any]]:
    initialize_database()

    with sqlite3.connect(_get_database_path()) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM candidates WHERE email = ?", (email.strip(),)).fetchone()

    if not row:
        return None

    return _row_to_candidate(row).to_payload()


def authenticate_candidate(email: str, password: str) -> Dict[str, Any]:
    """Return the candidate payload if the credentials are valid."""

    if not email or not password:
        raise ValidationError("Informe e-mail e senha para acessar seu perfil.")

    initialize_database()

    with sqlite3.connect(_get_database_path()) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM candidates WHERE email = ?", (email.strip(),)).fetchone()

    if not row or not row["senha_hash"]:
        raise ValidationError("Nenhum cadastro foi encontrado para o e-mail informado.")

    if not _verify_password(password, row["senha_hash"]):
        raise ValidationError("Senha inválida. Verifique seus dados e tente novamente.")

    return _row_to_candidate(row).to_payload()


def _hash_password(password: str) -> str:
    password = password.strip()
    if len(password) < 6:
        raise ValidationError("A senha deve ter pelo menos 6 caracteres.")

    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 600_000)
    return f"{salt}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    if not stored:
        return False

    try:
        salt, digest_hex = stored.split("$", 1)
    except ValueError:
        return False

    computed = hashlib.pbkdf2_hmac("sha256", password.strip().encode("utf-8"), salt.encode("utf-8"), 600_000)
    return secrets.compare_digest(digest_hex, computed.hex())

