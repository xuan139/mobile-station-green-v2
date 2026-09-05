from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import Any


GREEN_POWER_PROTOCOL = "green_power_v20260428"
TELEMETRY_MESSAGE_TYPE = "telemetry"
REGISTER_FUNCTION_CODES = {3, 4}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_telemetry_message(
    message: Mapping[str, Any],
    clock: Callable[[], str] = utc_now_iso,
) -> dict[str, Any]:
    if not isinstance(message, Mapping):
        raise TypeError("message must be an object")

    normalized = dict(message)
    normalized.setdefault("message_type", TELEMETRY_MESSAGE_TYPE)
    normalized.setdefault("collected_at", clock())
    normalized.setdefault("received_at", clock())
    normalized.setdefault("protocol_version", "v1")
    normalized.setdefault("station_name", normalized.get("station_id"))
    normalized["payload"] = _normalize_payload(normalized)
    normalized["sequence"] = _build_sequence(normalized)
    return normalized


def validate_telemetry_message(
    message: Mapping[str, Any],
    clock: Callable[[], str] = utc_now_iso,
) -> dict[str, Any]:
    normalized = normalize_telemetry_message(message, clock)
    normalized["message_type"] = _normalize_token(normalized["message_type"])
    normalized["protocol_type"] = _normalize_token(normalized.get("protocol_type", ""))
    if normalized["message_type"] != TELEMETRY_MESSAGE_TYPE:
        raise ValueError(f"unsupported message_type: {normalized['message_type']}")
    if normalized["protocol_type"] != GREEN_POWER_PROTOCOL:
        raise ValueError(f"unsupported protocol_type: {normalized['protocol_type']}")
    _validate_identity(normalized)
    _validate_modbus_payload(normalized["payload"])
    return normalized


def _normalize_payload(message: dict[str, Any]) -> dict[str, Any]:
    raw_payload = message.get("payload")
    if raw_payload is None:
        raw_payload = {}
    if not isinstance(raw_payload, Mapping):
        raise ValueError("payload must be an object")
    payload = dict(raw_payload)
    for key in ("function_code", "address", "count", "registers", "bits"):
        if key in message and key not in payload:
            payload[key] = message.pop(key)
    return payload


def _normalize_token(value: Any) -> str:
    lowered = str(value or "").strip().lower()
    return re.sub(r"[^a-z0-9_]+", "", lowered)


def _build_sequence(message: Mapping[str, Any]) -> int:
    raw = message.get("sequence")
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str) and raw.isdigit():
        return int(raw)
    seed = str(message.get("message_id", utc_now_iso())).encode("utf-8")
    return int(hashlib.sha1(seed).hexdigest()[:15], 16)


def _validate_identity(message: Mapping[str, Any]) -> None:
    for field in ("message_id", "station_id", "device_id"):
        if not str(message.get(field, "")).strip():
            raise ValueError(f"{field} is required")
    if int(message["sequence"]) <= 0:
        raise ValueError("sequence must be a positive integer")


def _validate_modbus_payload(payload: Mapping[str, Any]) -> None:
    for field in ("function_code", "address", "count"):
        if field not in payload:
            raise ValueError(f"payload.{field} is required")
    function_code = int(payload["function_code"])
    if function_code == 2 and not isinstance(payload.get("bits"), list):
        raise ValueError("payload.bits must be an array for function_code=2")
    if function_code in REGISTER_FUNCTION_CODES and not isinstance(payload.get("registers"), list):
        raise ValueError("payload.registers must be an array for function_code=3/4")
    if function_code not in REGISTER_FUNCTION_CODES | {2}:
        raise ValueError(f"unsupported function_code: {function_code}")
