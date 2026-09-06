from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

from green_v2.data_access import telemetry_sql
from green_v2.domain.parsed_telemetry import MetricReading, ParsedTelemetryMessage


class PostgresTelemetryRepository:
    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def insert_raw_message(self, message: ParsedTelemetryMessage) -> bool:
        raw = message.raw_message
        parameters = {
            "message_id": raw["message_id"],
            "station_id": raw["station_id"],
            "station_name": raw.get("station_name"),
            "device_id": raw["device_id"],
            "protocol_type": raw["protocol_type"],
            "protocol_version": raw.get("protocol_version", "v1"),
            "group_name": raw.get("group_name") or "default",
            "message_type": raw.get("message_type", "telemetry"),
            "sequence": raw["sequence"],
            "collected_at": raw["collected_at"],
            "received_at": raw["received_at"],
            "payload_json": Jsonb(raw),
            "ingest_status": "parsed" if message.parse_status == "success" else "rejected",
            "parse_status": message.parse_status,
            "parse_error": message.parse_error,
        }
        result = self._connection.execute(telemetry_sql.INSERT_RAW_MESSAGE, parameters)
        return result.fetchone() is not None

    def upsert_runtime(self, message: ParsedTelemetryMessage) -> None:
        raw = message.raw_message
        existing = self._connection.execute(
            telemetry_sql.SELECT_RUNTIME,
            (raw["station_id"],),
        ).fetchone()
        runtime = _runtime_payload(message.parsed_payload)
        previous_status = existing[0] if existing else None
        parameters = {
            "station_id": raw["station_id"],
            "station_name": raw.get("station_name"),
            "status": (
                "recovered"
                if previous_status in {"offline", "suspected_offline"}
                else "online"
            ),
            "last_seen_at": raw["received_at"],
            "last_heartbeat_at": runtime.get("last_heartbeat_at")
            or (existing[1] if existing else None),
            "last_message_id": raw["message_id"],
            "last_sequence": raw["sequence"],
            "last_uplink_ip": raw.get("uplink_ip"),
            "backlog_count": runtime.get(
                "backlog_count",
                existing[2] if existing else 0,
            )
            or 0,
            "parser_lag_seconds": message.parser_lag_seconds,
        }
        self._connection.execute(telemetry_sql.UPSERT_RUNTIME, parameters)

    def insert_metrics(self, message: ParsedTelemetryMessage) -> None:
        rows = [_metric_row(message, metric) for metric in message.metrics]
        if not rows:
            return
        with self._connection.cursor() as cursor:
            cursor.executemany(telemetry_sql.INSERT_HISTORY, rows)
            cursor.executemany(telemetry_sql.UPSERT_CURRENT, rows)


def _metric_row(
    message: ParsedTelemetryMessage,
    metric: MetricReading,
) -> tuple[Any, ...]:
    raw = message.raw_message
    return (
        raw["station_id"],
        metric.source_type,
        metric.source_id,
        metric.metric_key,
        metric.value_double,
        metric.value_text,
        raw["collected_at"],
        raw["message_id"],
    )


def _runtime_payload(parsed_payload: dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(parsed_payload, dict):
        runtime = parsed_payload.get("runtime_status")
        if isinstance(runtime, dict):
            return runtime
    return {}
