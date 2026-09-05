from __future__ import annotations

import json
from pathlib import Path

import pytest

from green_v2.domain.telemetry_message import validate_telemetry_message
from green_v2.parser.green_power import parse_telemetry


ROOT = Path(__file__).resolve().parents[1]


def fixture(name: str) -> dict:
    path = ROOT / "contracts" / "mq" / name
    return json.loads(path.read_text(encoding="utf-8"))


def test_main_status_matches_frozen_legacy_parsed_payload() -> None:
    raw = fixture("green-telemetry-raw-v1.json")
    expected = fixture("green-telemetry-parsed-v1.json")
    parsed = parse_telemetry(raw)
    assert parsed["parsed_payload"] == expected["parsed_payload"]
    assert parsed["message_id"] == raw["message_id"]
    assert parsed["protocol_version"] == "v1"


def test_unknown_green_point_is_preserved_as_raw_passthrough() -> None:
    raw = fixture("green-telemetry-raw-v1.json")
    raw["payload"] = {"function_code": 4, "address": 999, "count": 1, "registers": [7]}
    parsed = parse_telemetry(raw)
    metrics = parsed["parsed_payload"]["metric_groups"][0]["metrics"]
    assert metrics == {"raw_passthrough": raw["payload"]}


def test_top_level_modbus_fields_remain_backward_compatible() -> None:
    raw = fixture("green-telemetry-raw-v1.json")
    payload = raw.pop("payload")
    raw.update(payload)
    normalized = validate_telemetry_message(raw)
    assert normalized["payload"] == payload
    assert "registers" not in normalized


def test_invalid_sequence_is_rejected() -> None:
    raw = fixture("green-telemetry-raw-v1.json")
    raw["sequence"] = 0
    with pytest.raises(ValueError, match="sequence must be a positive integer"):
        parse_telemetry(raw)
