"""SQLite-backed persistence utilities for candidate profiles."""

from __future__ import annotations

import crypt
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


class AuthenticationError(StorageError):
    """Raised when login credentials are invalid."""


@dataclass
class Candidate:
    id: int
    nome: str
    email: str
    telefone: str
    area_interesse: str
    recebe_alertas: bool
    curriculo_path: Optional[str]
    criado_em: str
    atualizado_em: str

    def to_payload(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "telefone": self.telefone,
            "areaInteresse": self.area_interesse,
            "recebeAlertas": self.recebe_alertas,
            "curriculoPath": self.curriculo_path,
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
                area_interesse TEXT NOT NULL,
                telefone TEXT,
                recebe_alertas INTEGER NOT NULL DEFAULT 1,
                curriculo_path TEXT,
                senha_hash TEXT NOT NULL,
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()

        _ensure_schema(conn)


def _ensure_schema(conn: sqlite3.Connection) -> None:
    """Bring legacy databases to the current schema."""

    conn.row_factory = sqlite3.Row
    columns = {row["name"]: row for row in conn.execute("PRAGMA table_info(candidates)").fetchall()}

    if "area_interesse" not in columns and "area" in columns:
        conn.execute("ALTER TABLE candidates ADD COLUMN area_interesse TEXT")
        conn.execute("UPDATE candidates SET area_interesse = area WHERE area_interesse IS NULL")

    if "recebe_alertas" not in columns and "deseja_alertas" in columns:
        conn.execute("ALTER TABLE candidates ADD COLUMN recebe_alertas INTEGER NOT NULL DEFAULT 1")
        conn.execute(
            "UPDATE candidates SET recebe_alertas = deseja_alertas WHERE recebe_alertas IS NULL"
        )

    if "curriculo_path" not in columns and "curriculo" in columns:
        conn.execute("ALTER TABLE candidates ADD COLUMN curriculo_path TEXT")
        conn.execute(
            "UPDATE candidates SET curriculo_path = curriculo WHERE curriculo_path IS NULL"
        )

    if "criado_em" in columns and columns["criado_em"]["type"].upper() != "DATETIME":
        conn.execute("ALTER TABLE candidates RENAME TO candidates_legacy")
        conn.execute(
            """
            CREATE TABLE candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                area_interesse TEXT NOT NULL,
                telefone TEXT,
                recebe_alertas INTEGER NOT NULL DEFAULT 1,
                curriculo_path TEXT,
                senha_hash TEXT NOT NULL,
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            INSERT INTO candidates (id, nome, email, area_interesse, telefone, recebe_alertas, curriculo_path, senha_hash, criado_em, atualizado_em)
            SELECT id, nome, email, COALESCE(area_interesse, area), telefone, COALESCE(recebe_alertas, deseja_alertas, 1), COALESCE(curriculo_path, curriculo), senha_hash, criado_em, atualizado_em
            FROM candidates_legacy
            """
        )
        conn.execute("DROP TABLE candidates_legacy")

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
        area_interesse=row["area_interesse"],
        recebe_alertas=bool(row["recebe_alertas"]),
        curriculo_path=row["curriculo_path"],
        criado_em=row["criado_em"],
        atualizado_em=row["atualizado_em"],
    )


def create_or_update_candidate(
    payload: Dict[str, Any],
    *,
    resume_filename: Optional[str] = None,
    resume_data: Optional[bytes] = None,
) -> Dict[str, Any]:
    """Persist candidate data, creating or updating based on the e-mail."""

    required_fields = ("nome", "email", "area_interesse")
    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        raise ValidationError(
            "Os campos a seguir são obrigatórios para salvar o cadastro: " + ", ".join(missing)
        )

    initialize_database()

    email = payload["email"].strip()
    senha = payload.get("senha", "").strip()
    nome = payload["nome"].strip()
    telefone = payload.get("telefone", "").strip()
    area_interesse = payload["area_interesse"].strip()
    recebe_alertas = 1 if payload.get("recebe_alertas") else 0

    with sqlite3.connect(_get_database_path()) as conn:
        conn.row_factory = sqlite3.Row
        existing = conn.execute("SELECT * FROM candidates WHERE email = ?", (email,)).fetchone()

        resume_path = _store_resume(
            resume_filename,
            resume_data,
            existing["curriculo_path"] if existing else None,
        )

        senha_hash = existing["senha_hash"] if existing else None

        if existing:
            if senha:
                senha_hash = _hash_password(senha)
        else:
            if not senha:
                raise ValidationError(
                    "Defina uma senha para criar seu cadastro e acessar recomendações personalizadas."
                )
            senha_hash = _hash_password(senha)

        conn.execute(
            "PRAGMA foreign_keys = ON"
        )  # pragma: no cover - harmless on current schema but future proof

        if existing:
            conn.execute(
                """
                UPDATE candidates
                SET nome = ?, telefone = ?, area_interesse = ?, recebe_alertas = ?, curriculo_path = ?, senha_hash = ?, atualizado_em = CURRENT_TIMESTAMP
                WHERE email = ?
                """,
                (nome, telefone, area_interesse, recebe_alertas, resume_path, senha_hash, email),
            )
        else:
            conn.execute(
                """
                INSERT INTO candidates (nome, email, telefone, area_interesse, recebe_alertas, curriculo_path, senha_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (nome, email, telefone, area_interesse, recebe_alertas, resume_path, senha_hash),
            )
        conn.commit()

        updated = conn.execute("SELECT * FROM candidates WHERE email = ?", (email,)).fetchone()

    return _row_to_candidate(updated).to_payload()


def get_candidate_by_email(email: str) -> Optional[Dict[str, Any]]:
    if not email:
        return None

    initialize_database()

    with sqlite3.connect(_get_database_path()) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM candidates WHERE email = ?", (email.strip(),)).fetchone()

    return _row_to_candidate(row).to_payload() if row else None


def validate_login(email: str, senha_plana: str) -> Dict[str, Any]:
    """Validate the provided credentials and return the candidate payload."""

    email = (email or "").strip()
    senha_plana = (senha_plana or "").strip()

    if not email or not senha_plana:
        raise ValidationError("Informe e-mail e senha para continuar.")

    initialize_database()

    with sqlite3.connect(_get_database_path()) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM candidates WHERE email = ?", (email,)).fetchone()

    if not row or not row["senha_hash"]:
        raise AuthenticationError("Credenciais inválidas. Verifique e tente novamente.")

    if not _verify_password(senha_plana, row["senha_hash"]):
        raise AuthenticationError("Credenciais inválidas. Verifique e tente novamente.")

    return _row_to_candidate(row).to_payload()


def _hash_password(password: str) -> str:
    password = password.strip()
    if len(password) < 6:
        raise ValidationError("A senha deve ter pelo menos 6 caracteres.")

    salt = crypt.mksalt(crypt.METHOD_BLOWFISH)
    hashed = crypt.crypt(password, salt)
    if not hashed:
        raise StorageError("Não foi possível gerar o hash da senha no momento.")
    return hashed


def _verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash:
        return False

    computed = crypt.crypt(password.strip(), stored_hash)
    if not computed:
        return False

    try:
        return secrets.compare_digest(computed, stored_hash)
    except Exception:  # pragma: no cover - extremely defensive
        return computed == stored_hash

