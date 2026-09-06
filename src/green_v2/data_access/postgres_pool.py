from __future__ import annotations

from typing import Any

from psycopg.conninfo import make_conninfo
from psycopg_pool import ConnectionPool

from green_v2.config import Settings


class PostgresConnectionPool:
    def __init__(self, settings: Settings) -> None:
        conninfo = make_conninfo(
            host=settings.db_host,
            port=settings.db_port,
            dbname=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
        )
        self._pool = ConnectionPool(
            conninfo=conninfo,
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
            open=False,
        )

    def connect(self) -> None:
        self._pool.open(wait=True)

    def acquire(self) -> Any:
        return self._pool.getconn()

    def release(self, connection: Any) -> None:
        self._pool.putconn(connection)

    def is_ready(self) -> bool:
        connection = self.acquire()
        try:
            connection.execute("SELECT 1;")
            return True
        except Exception:  # noqa: BLE001
            return False
        finally:
            connection.rollback()
            self.release(connection)

    def close(self) -> None:
        self._pool.close()
