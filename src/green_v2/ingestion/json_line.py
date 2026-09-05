from __future__ import annotations

import json
from typing import Any

from green_v2.application.ingest_telemetry import IngestTelemetry


def handle_json_line(raw_line: bytes, use_case: IngestTelemetry) -> bytes:
    incoming: dict[str, Any] | None = None
    try:
        decoded = json.loads(raw_line.decode("utf-8"))
        incoming = decoded if isinstance(decoded, dict) else None
        if incoming is None:
            raise TypeError("message must be an object")
        response = use_case.execute(incoming)
    except Exception as error:  # noqa: BLE001
        response = use_case.reject(incoming, error)
    return (json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8")
