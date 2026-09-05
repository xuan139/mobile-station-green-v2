from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def build_ack(
    message: Mapping[str, Any] | None,
    *,
    status: str,
    received_at: str,
    error_code: str | None = None,
    error_message: str | None = None,
    pending_command: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    ack: dict[str, Any] = {
        "message_type": "ack",
        "status": status,
        "received_at": received_at,
    }
    if message:
        for field in ("message_id", "station_id", "sequence"):
            if message.get(field) is not None:
                ack[field] = message[field]
    if error_code:
        ack["error_code"] = error_code
    if error_message:
        ack["error_message"] = error_message
    if pending_command:
        ack["pending_command"] = dict(pending_command)
    return ack
