"""SQLite-backed persistence utilities for candidate profiles."""

from __future__ import annotations

import base64
import binascii
import hashlib
import os
import re
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

try:  # pragma: no cover - prefer native bcrypt when available
    import bcrypt as _bcrypt_lib
except ImportError:  # pragma: no cover - constrained envs can fall back later
    _bcrypt_lib = None

try:  # pragma: no cover - legacy fallback for pre-bcrypt hashes
    import crypt as _legacy_crypt
except ImportError:  # pragma: no cover - Windows may not ship crypt
    _legacy_crypt = None

_FALLBACK_PREFIX = "pbkdf2_sha256"
_FALLBACK_ITERATIONS = 390000

DATA_DIR_ENV = "IDEAL_DATA_DIR"
ADMIN_EMAIL_ENV = "IDEAL_ADMIN_EMAIL"
ADMIN_PASSWORD_ENV = "IDEAL_ADMIN_PASSWORD"


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
    is_admin: bool

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
            "isAdmin": self.is_admin,
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
                is_admin INTEGER NOT NULL DEFAULT 0,
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_email TEXT NOT NULL,
                job_id TEXT NOT NULL,
                job_title TEXT,
                status TEXT NOT NULL DEFAULT 'em_analise',
                criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(candidate_email) REFERENCES candidates(email) ON DELETE CASCADE
            )
            """
        )
        conn.commit()

        _ensure_schema(conn)
        _ensure_default_admin(conn)


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

    if "is_admin" not in columns:
        conn.execute("ALTER TABLE candidates ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")

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


def _ensure_default_admin(conn: sqlite3.Connection) -> None:
    """Create or refresh a default admin account when configured."""

    email = os.getenv(ADMIN_EMAIL_ENV, "admin@idealempregos.test").strip()
    password = os.getenv(ADMIN_PASSWORD_ENV, "admin123").strip()

    if not email or not password:
        return

    conn.row_factory = sqlite3.Row
    existing = conn.execute("SELECT * FROM candidates WHERE email = ?", (email,)).fetchone()

    if existing:
        conn.execute(
            """
            UPDATE candidates
            SET is_admin = 1, atualizado_em = CURRENT_TIMESTAMP
            WHERE email = ?
            """,
            (email,),
        )
        conn.commit()
        return

    senha_hash = _hash_password(password)
    conn.execute(
        """
        INSERT INTO candidates (nome, email, telefone, area_interesse, recebe_alertas, curriculo_path, senha_hash, is_admin)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            "Administrador Ideal Empregos",
            email,
            "",
            "administracao",
            0,
            None,
            senha_hash,
        ),
    )
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
        is_admin=bool(row["is_admin"]),
    )


def _row_to_application(row: sqlite3.Row) -> Dict[str, Any]:
    keys = row.keys()
    nome = row["nome"] if "nome" in keys else ""
    area = row["area_interesse"] if "area_interesse" in keys else ""

    return {
        "id": row["id"],
        "jobId": row["job_id"],
        "jobTitle": row["job_title"] or "",
        "status": row["status"],
        "criadoEm": row["criado_em"],
        "atualizadoEm": row["atualizado_em"],
        "candidate": {
            "email": row["candidate_email"],
            "nome": nome,
            "areaInteresse": area,
        },
    }


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


def is_admin(email: str) -> bool:
    if not email:
        return False

    initialize_database()

    with sqlite3.connect(_get_database_path()) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT is_admin FROM candidates WHERE email = ?", (email.strip(),)
        ).fetchone()
    return bool(row["is_admin"]) if row else False


def upsert_application(candidate_email: str, job_id: str, job_title: str = "") -> Dict[str, Any]:
    candidate_email = (candidate_email or "").strip()
    job_id = (job_id or "").strip()
    job_title = (job_title or "").strip()

    if not candidate_email or not job_id:
        raise ValidationError("Informe o e-mail do candidato e o identificador da vaga.")

    initialize_database()

    with sqlite3.connect(_get_database_path()) as conn:
        conn.row_factory = sqlite3.Row
        candidate = conn.execute(
            "SELECT email, area_interesse, nome FROM candidates WHERE email = ?",
            (candidate_email,),
        ).fetchone()
        if not candidate:
            raise ValidationError("Nenhum cadastro foi encontrado para o e-mail informado.")

        existing = conn.execute(
            "SELECT * FROM applications WHERE candidate_email = ? AND job_id = ?",
            (candidate_email, job_id),
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE applications
                SET job_title = ?, status = 'em_analise', atualizado_em = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (job_title, existing["id"]),
            )
            app_id = existing["id"]
        else:
            conn.execute(
                """
                INSERT INTO applications (candidate_email, job_id, job_title)
                VALUES (?, ?, ?)
                """,
                (candidate_email, job_id, job_title),
            )
            app_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        conn.commit()

        row = conn.execute(
            """
            SELECT a.*, c.nome, c.area_interesse
            FROM applications a
            JOIN candidates c ON c.email = a.candidate_email
            WHERE a.id = ?
            """,
            (app_id,),
        ).fetchone()

    return _row_to_application(row)


def list_applications() -> list[Dict[str, Any]]:
    initialize_database()
    with sqlite3.connect(_get_database_path()) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT a.*, c.nome, c.area_interesse
            FROM applications a
            JOIN candidates c ON c.email = a.candidate_email
            ORDER BY a.criado_em DESC
            """
        ).fetchall()
    return [_row_to_application(row) for row in rows]


def update_application_status(application_id: int, status: str) -> Dict[str, Any]:
    allowed = {"em_analise", "aceito", "recusado"}
    if status not in allowed:
        raise ValidationError("Status inválido. Use em_analise, aceito ou recusado.")

    initialize_database()

    with sqlite3.connect(_get_database_path()) as conn:
        conn.row_factory = sqlite3.Row
        existing = conn.execute(
            "SELECT * FROM applications WHERE id = ?",
            (application_id,),
        ).fetchone()

        if not existing:
            raise ValidationError("Nenhuma candidatura foi encontrada para o identificador informado.")

        conn.execute(
            """
            UPDATE applications
            SET status = ?, atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, application_id),
        )
        conn.commit()

        row = conn.execute(
            """
            SELECT a.*, c.nome, c.area_interesse
            FROM applications a
            JOIN candidates c ON c.email = a.candidate_email
            WHERE a.id = ?
            """,
            (application_id,),
        ).fetchone()

    return _row_to_application(row)


def _hash_password(password: str) -> str:
    password = password.strip()
    if len(password) < 6:
        raise ValidationError("A senha deve ter pelo menos 6 caracteres.")

    if _bcrypt_lib:
        try:
            hashed = _bcrypt_lib.hashpw(password.encode("utf-8"), _bcrypt_lib.gensalt())
        except ValueError as exc:  # pragma: no cover - bcrypt internal edge case
            raise StorageError("Não foi possível gerar o hash da senha no momento.") from exc
        return hashed.decode("utf-8")

    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _FALLBACK_ITERATIONS
    )
    token = "$".join(
        (
            _FALLBACK_PREFIX,
            str(_FALLBACK_ITERATIONS),
            base64.b64encode(salt).decode("utf-8"),
            base64.b64encode(derived).decode("utf-8"),
        )
    )
    return token


def _verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash:
        return False

    password = (password or "").strip()
    if not password:
        return False

    if _bcrypt_lib and stored_hash.startswith("$2"):
        try:
            return _bcrypt_lib.checkpw(
                password.encode("utf-8"), stored_hash.encode("utf-8")
            )
        except (ValueError, TypeError):
            pass

    if stored_hash.startswith(_FALLBACK_PREFIX + "$"):
        try:
            _, iterations, salt_b64, derived_b64 = stored_hash.split("$", 3)
            iterations = int(iterations)
            salt = base64.b64decode(salt_b64)
            derived = base64.b64decode(derived_b64)
        except (ValueError, TypeError, binascii.Error):
            return False

        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, iterations
        )
        try:
            return secrets.compare_digest(candidate, derived)
        except Exception:  # pragma: no cover - extremely defensive
            return candidate == derived

    if _legacy_crypt and stored_hash.startswith("$"):
        computed = _legacy_crypt.crypt(password, stored_hash)
        if not computed:
            return False
        try:
            return secrets.compare_digest(computed, stored_hash)
        except Exception:  # pragma: no cover - extremely defensive
            return computed == stored_hash

    return False

