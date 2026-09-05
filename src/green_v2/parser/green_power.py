from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from green_v2.domain.telemetry_message import utc_now_iso, validate_telemetry_message
from green_v2.parser.main_status import MAIN_STATUS_ADDRESS, parse_main_status


def parse_telemetry(
    message: Mapping[str, Any],
    clock: Callable[[], str] = utc_now_iso,
) -> dict[str, Any]:
    normalized = validate_telemetry_message(message, clock)
    payload = normalized["payload"]
    metric_groups = _parse_metric_groups(
        int(payload["function_code"]),
        int(payload["address"]),
        payload,
        normalized["device_id"],
    )
    return {
        "message_id": normalized["message_id"],
        "station_id": normalized["station_id"],
        "station_name": normalized.get("station_name"),
        "device_id": normalized["device_id"],
        "protocol_type": normalized["protocol_type"],
        "protocol_version": normalized.get("protocol_version", "v1"),
        "group_name": normalized.get("group_name"),
        "message_type": normalized["message_type"],
        "sequence": normalized["sequence"],
        "collected_at": normalized["collected_at"],
        "received_at": normalized["received_at"],
        "payload": normalized["payload"],
        "parsed_payload": {"metric_groups": metric_groups},
    }


def _parse_metric_groups(
    function_code: int,
    address: int,
    payload: dict[str, Any],
    device_id: str,
) -> list[dict[str, Any]]:
    if function_code == 4 and address == MAIN_STATUS_ADDRESS:
        return [parse_main_status(payload["registers"], device_id)]
    return [
        {
            "source_type": "device",
            "source_id": device_id,
            "metrics": {"raw_passthrough": payload},
        }
    ]
