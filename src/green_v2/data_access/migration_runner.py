from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from green_v2.data_access.postgres_pool import PostgresConnectionPool


CREATE_MIGRATION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migration (
    version TEXT PRIMARY KEY,
    checksum_sha256 TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def apply_migrations(pool: PostgresConnectionPool, directory: Path) -> list[str]:
    connection = pool.acquire()
    try:
        connection.execute(CREATE_MIGRATION_TABLE)
        connection.commit()
        applied: list[str] = []
        for path in sorted(directory.glob("[0-9]*.sql")):
            if _apply_one(connection, path):
                applied.append(path.stem)
        return applied
    finally:
        pool.release(connection)


def _apply_one(connection: Any, path: Path) -> bool:
    version = path.stem
    content = path.read_text(encoding="utf-8")
    checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
    existing = connection.execute(
        "SELECT checksum_sha256 FROM schema_migration WHERE version = %s;",
        (version,),
    ).fetchone()
    if existing:
        if existing[0] != checksum:
            connection.rollback()
            raise RuntimeError(f"migration checksum mismatch: {version}")
        connection.rollback()
        return False
    try:
        connection.execute(content)
        connection.execute(
            "INSERT INTO schema_migration (version, checksum_sha256) VALUES (%s, %s);",
            (version, checksum),
        )
        connection.commit()
        return True
    except Exception:
        connection.rollback()
        raise
