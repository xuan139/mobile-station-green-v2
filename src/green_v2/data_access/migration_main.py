from __future__ import annotations

from pathlib import Path

from green_v2.config import Settings
from green_v2.data_access.migration_runner import apply_migrations
from green_v2.data_access.postgres_pool import PostgresConnectionPool


def main() -> int:
    settings = Settings.from_env("migration")
    pool = PostgresConnectionPool(settings)
    pool.connect()
    migration_dir = Path(__file__).resolve().parents[3] / "migrations"
    try:
        applied = apply_migrations(pool, migration_dir)
        print("applied migrations:", ", ".join(applied) if applied else "none")
    finally:
        pool.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
