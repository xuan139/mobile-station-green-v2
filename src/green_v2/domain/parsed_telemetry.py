from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class MetricReading:
    source_type: str
    source_id: str
    metric_key: str
    value_double: float | None
    value_text: str | None


@dataclass(frozen=True)
class ParsedTelemetryMessage:
    raw_message: dict[str, Any]
    parsed_payload: dict[str, Any] | None
    parse_status: str
    parse_error: str | None
    metrics: tuple[MetricReading, ...]
    parser_lag_seconds: int

    @classmethod
    def from_envelope(cls, envelope: Mapping[str, Any]) -> ParsedTelemetryMessage:
        raw_message = _required_mapping(envelope, "raw_message")
        _require_raw_fields(raw_message)
        parse_status = str(envelope.get("parse_status") or "").strip().lower()
        if parse_status not in {"success", "failed"}:
            raise ValueError("parse_status must be success or failed")
        parsed_payload = envelope.get("parsed_payload")
        if parsed_payload is not None and not isinstance(parsed_payload, Mapping):
            raise ValueError("parsed_payload must be an object or null")
        parsed = dict(parsed_payload) if isinstance(parsed_payload, Mapping) else None
        metrics = tuple(_extract_metrics(raw_message, parsed)) if parse_status == "success" else ()
        return cls(
            raw_message=raw_message,
            parsed_payload=parsed,
            parse_status=parse_status,
            parse_error=_optional_text(envelope.get("parse_error")),
            metrics=metrics,
            parser_lag_seconds=_diff_seconds(
                str(raw_message["collected_at"]),
                str(raw_message["received_at"]),
            ),
        )


def _required_mapping(envelope: Mapping[str, Any], field: str) -> dict[str, Any]:
    value = envelope.get(field)
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    return dict(value)


def _require_raw_fields(raw_message: Mapping[str, Any]) -> None:
    required = (
        "message_id",
        "station_id",
        "device_id",
        "protocol_type",
        "sequence",
        "collected_at",
        "received_at",
    )
    missing = [
        field
        for field in required
        if raw_message.get(field) is None or raw_message.get(field) == ""
    ]
    if missing:
        raise ValueError(f"raw_message missing fields: {', '.join(missing)}")


def _extract_metrics(
    raw_message: Mapping[str, Any],
    parsed_payload: Mapping[str, Any] | None,
) -> list[MetricReading]:
    readings: list[MetricReading] = []
    for group in _metric_groups(raw_message, parsed_payload):
        values = group.get("metrics")
        if not isinstance(values, Mapping):
            continue
        source_type = str(group.get("source_type") or "device")
        source_id = str(group.get("source_id") or raw_message["device_id"])
        for metric_key, value in values.items():
            reading = _reading(source_type, source_id, str(metric_key), value)
            if reading is not None:
                readings.append(reading)
    return readings


def _metric_groups(
    raw_message: Mapping[str, Any],
    parsed_payload: Mapping[str, Any] | None,
) -> list[Mapping[str, Any]]:
    if parsed_payload is None:
        return []
    groups = parsed_payload.get("metric_groups")
    if isinstance(groups, list):
        return [group for group in groups if isinstance(group, Mapping)]
    legacy = {
        key: value
        for key, value in parsed_payload.items()
        if key not in {"runtime_status", "alarm_event"}
    }
    if not legacy:
        return []
    return [{"source_type": "device", "source_id": raw_message["device_id"], "metrics": legacy}]


def _reading(
    source_type: str,
    source_id: str,
    metric_key: str,
    value: Any,
) -> MetricReading | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return MetricReading(source_type, source_id, metric_key, float(value), None)
    if isinstance(value, (int, float)):
        return MetricReading(source_type, source_id, metric_key, float(value), None)
    text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
    return MetricReading(source_type, source_id, metric_key, None, text)


def _diff_seconds(start_text: str, end_text: str) -> int:
    start = _parse_datetime(start_text)
    end = _parse_datetime(end_text)
    return max(0, int((end - start).total_seconds()))


def _parse_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def _optional_text(value: Any) -> str | None:
    return None if value is None else str(value)
