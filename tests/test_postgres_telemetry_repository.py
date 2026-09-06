from __future__ import annotations

import json
import os
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict

from green_v2.application.telemetry_persistence import PersistParsedTelemetry
from green_v2.config import Settings
from green_v2.data_access.migration_runner import apply_migrations
from green_v2.data_access.postgres_pool import PostgresConnectionPool
from green_v2.data_access.telemetry_uow import PostgresTelemetryUnitOfWorkFactory


ROOT = Path(__file__).resolve().parents[1]
DSN_ENV = "GREEN_V2_TEST_DATABASE_DSN"


@pytest.fixture(scope="module")
def database():
    dsn = os.getenv(DSN_ENV)
    if not dsn:
        pytest.skip(f"{DSN_ENV} is required")
    parameters = conninfo_to_dict(dsn)
    db_name = str(parameters.get("dbname") or "")
    if not db_name.startswith("mobile_station_green_v2_test_"):
        raise RuntimeError("integration database must use the Green V2 test prefix")
    settings = replace(
        Settings.from_env(),
        db_host=str(parameters.get("host") or "127.0.0.1"),
        db_port=int(parameters.get("port") or 5432),
        db_name=db_name,
        db_user=str(parameters.get("user") or os.getenv("USER")),
        db_password=str(parameters.get("password") or ""),
        db_pool_min_size=1,
        db_pool_max_size=2,
    )
    pool = PostgresConnectionPool(settings)
    pool.connect()
    first_result = apply_migrations(pool, ROOT / "migrations")
    assert first_result in ([], ["0001_telemetry_core"])
    assert apply_migrations(pool, ROOT / "migrations") == []
    yield dsn, pool
    pool.close()


@pytest.fixture(autouse=True)
def clean_tables(database) -> None:
    dsn, _pool = database
    with psycopg.connect(dsn) as connection:
        connection.execute(
            "TRUNCATE telemetry_history, telemetry_current, station_runtime_status, raw_message;"
        )


def test_idempotency_history_current_and_runtime(database) -> None:
    dsn, pool = database
    persist = PersistParsedTelemetry(PostgresTelemetryUnitOfWorkFactory(pool))
    first = _contract()
    latest = _changed(first, "message-2", 2, 60, 221.0)
    older = _changed(first, "message-3", 3, -60, 219.0)
    for item in (first, latest, latest, older):
        persist.execute(item)

    with psycopg.connect(dsn) as connection:
        assert connection.execute("SELECT COUNT(*) FROM raw_message;").fetchone() == (3,)
        assert connection.execute("SELECT COUNT(*) FROM telemetry_history;").fetchone() == (63,)
        current = connection.execute(
            "SELECT metric_value_double, source_message_id FROM telemetry_current "
            "WHERE metric_key = 'ac_input_voltage';"
        ).fetchone()
        runtime = connection.execute(
            "SELECT last_message_id, last_sequence, parser_lag_seconds "
            "FROM station_runtime_status;"
        ).fetchone()
    assert current == (221.0, "message-2")
    assert runtime == ("message-2", 3, 1)


def test_database_error_rolls_back_raw_message(database) -> None:
    dsn, pool = database
    envelope = _contract()
    envelope["raw_message"]["message_id"] = "rollback-message"
    envelope["raw_message"]["sequence"] = 50
    envelope["parsed_payload"]["runtime_status"] = {"backlog_count": -1}
    persist = PersistParsedTelemetry(PostgresTelemetryUnitOfWorkFactory(pool))
    with pytest.raises(psycopg.errors.CheckViolation):
        persist.execute(envelope)
    with psycopg.connect(dsn) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM raw_message WHERE message_id = 'rollback-message';"
        ).fetchone()
    assert count == (0,)


def _contract() -> dict:
    path = ROOT / "contracts" / "mq" / "green-telemetry-parsed-v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _changed(source: dict, message_id: str, sequence: int, seconds: int, voltage: float) -> dict:
    item = deepcopy(source)
    raw = item["raw_message"]
    collected = datetime.fromisoformat(raw["collected_at"]) + timedelta(seconds=seconds)
    received = datetime.fromisoformat(raw["received_at"]) + timedelta(seconds=seconds)
    raw.update(
        message_id=message_id,
        sequence=sequence,
        collected_at=collected.isoformat(),
        received_at=received.isoformat(),
    )
    item["parsed_payload"]["metric_groups"][0]["metrics"]["ac_input_voltage"] = voltage
    return item
