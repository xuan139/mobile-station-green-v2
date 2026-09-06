from __future__ import annotations

from typing import Any

from green_v2.data_access.postgres_pool import PostgresConnectionPool
from green_v2.data_access.telemetry_repository import PostgresTelemetryRepository


class PostgresTelemetryUnitOfWork:
    def __init__(self, pool: PostgresConnectionPool) -> None:
        self._pool = pool
        self._connection: Any = None
        self._committed = False
        self.telemetry: PostgresTelemetryRepository

    def __enter__(self) -> PostgresTelemetryUnitOfWork:
        self._connection = self._pool.acquire()
        self.telemetry = PostgresTelemetryRepository(self._connection)
        return self

    def commit(self) -> None:
        self._connection.commit()
        self._committed = True

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._connection is None:
            return
        if not self._committed:
            self._connection.rollback()
        self._pool.release(self._connection)
        self._connection = None


class PostgresTelemetryUnitOfWorkFactory:
    def __init__(self, pool: PostgresConnectionPool) -> None:
        self._pool = pool

    def __call__(self) -> PostgresTelemetryUnitOfWork:
        return PostgresTelemetryUnitOfWork(self._pool)
