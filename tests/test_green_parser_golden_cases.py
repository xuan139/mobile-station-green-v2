from __future__ import annotations

import json
from pathlib import Path

import pytest

from green_v2.parser.green_power import parse_telemetry


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "mq" / "green-parser-golden-cases-v1.json"
CASES = json.loads(CONTRACT.read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case", CASES, ids=[case["name"] for case in CASES])
def test_green_parser_matches_legacy_golden_case(case: dict) -> None:
    actual = parse_telemetry(case["input"])["parsed_payload"]
    assert actual == case["expected_parsed_payload"]


def test_golden_contract_covers_every_green_parser_route() -> None:
    names = {case["name"] for case in CASES}
    expected = {
        *(f"pack-metrics-{base}" for base in ("000", "050", "0a0", "0f0", "140", "190")),
        *(f"pack-alarms-{base}" for base in ("000", "050", "0a0", "0f0", "140", "190")),
        "controller-bits-1f0",
        "control-schedule-000",
        "extra-control-046",
        "raw-passthrough",
    }
    assert names == expected
