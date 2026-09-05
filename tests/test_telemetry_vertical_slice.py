from __future__ import annotations

import json
from pathlib import Path

import pytest

from green_v2.application.ingest_telemetry import IngestTelemetry
from green_v2.application.parse_telemetry import ParseTelemetry
from green_v2.ingestion.json_line import handle_json_line
from green_v2.messaging.memory import InMemoryMessageBus


ROOT = Path(__file__).resolve().parents[1]
RAW_QUEUE = "green_v2.raw.telemetry"
PARSED_QUEUE = "green_v2.parsed.telemetry"
FAILED_QUEUE = "green_v2.failed"
NOW = "2026-06-24T14:21:01.100000+08:00"


def fixture(name: str) -> dict:
    path = ROOT / "contracts" / "mq" / name
    return json.loads(path.read_text(encoding="utf-8"))


def build_ingress(bus: InMemoryMessageBus, claim_command=None) -> IngestTelemetry:
    return IngestTelemetry(bus, RAW_QUEUE, lambda: NOW, claim_command)


def build_parser(bus: InMemoryMessageBus) -> ParseTelemetry:
    return ParseTelemetry(bus, bus, PARSED_QUEUE, FAILED_QUEUE)


def test_ingress_to_parser_vertical_flow_preserves_contract_and_order() -> None:
    bus = InMemoryMessageBus()
    raw = fixture("green-telemetry-raw-v1.json")
    response = handle_json_line(json.dumps(raw).encode(), build_ingress(bus))
    ack = json.loads(response)
    assert ack == fixture("ingress-ack-v1.json")

    published_raw = bus.messages_for(RAW_QUEUE)[0]
    assert published_raw["protocol_version"] == "v1"
    envelope = build_parser(bus).execute("delivery-1", published_raw)
    expected = fixture("green-telemetry-parsed-v1.json")
    assert envelope["parsed_payload"] == expected["parsed_payload"]
    assert bus.events == [
        ("publish", RAW_QUEUE),
        ("publish", PARSED_QUEUE),
        ("ack", "delivery-1"),
    ]


def test_pending_command_is_claimed_only_after_raw_publish() -> None:
    bus = InMemoryMessageBus()
    observed: list[tuple[str, object]] = bus.events

    def claim(station_id: str, sequence: int | None) -> dict:
        observed.append(("claim", (station_id, sequence)))
        return {"command_id": "cmd-contract-001"}

    ack = build_ingress(bus, claim).execute(fixture("green-telemetry-raw-v1.json"))
    assert ack["pending_command"] == {"command_id": "cmd-contract-001"}
    assert observed[0] == ("publish", RAW_QUEUE)
    assert observed[1][0] == "claim"


def test_invalid_json_line_returns_reject_without_publish() -> None:
    bus = InMemoryMessageBus()
    response = handle_json_line(b"not-json", build_ingress(bus))
    ack = json.loads(response)
    assert ack["message_type"] == "ack"
    assert ack["status"] == "reject"
    assert ack["error_code"] == "INVALID_PAYLOAD"
    assert bus.published == []


def test_parse_failure_publishes_failed_envelope_before_ack() -> None:
    bus = InMemoryMessageBus()
    raw = fixture("green-telemetry-raw-v1.json")
    raw["payload"]["registers"] = [1]
    envelope = build_parser(bus).execute(22, raw)
    assert envelope["parse_status"] == "failed"
    assert envelope["parsed_payload"] is None
    assert bus.events == [("publish", FAILED_QUEUE), ("ack", 22)]


def test_publish_failure_nacks_for_redelivery() -> None:
    bus = InMemoryMessageBus(fail_queue=PARSED_QUEUE)
    with pytest.raises(RuntimeError, match="publish failed"):
        build_parser(bus).execute(23, fixture("green-telemetry-raw-v1.json"))
    assert bus.events == [
        ("publish", PARSED_QUEUE),
        ("nack", (23, True)),
    ]
