from __future__ import annotations

from green_v2.domain.parsed_telemetry import ParsedTelemetryMessage


def test_builds_typed_metrics_and_parser_lag() -> None:
    message = ParsedTelemetryMessage.from_envelope(
        {
            "raw_message": _raw_message(),
            "parsed_payload": {
                "metric_groups": [
                    {
                        "source_type": "battery_pack",
                        "source_id": "pack-1",
                        "metrics": {
                            "soc": 81.5,
                            "alarm": False,
                            "mode": "summer",
                            "detail": {"code": 3},
                            "missing": None,
                        },
                    }
                ]
            },
            "parse_status": "success",
            "parse_error": None,
        }
    )
    assert message.parser_lag_seconds == 3
    assert [(item.metric_key, item.value_double, item.value_text) for item in message.metrics] == [
        ("soc", 81.5, None),
        ("alarm", 0.0, None),
        ("mode", None, "summer"),
        ("detail", None, '{"code": 3}'),
    ]


def test_failed_parse_has_no_metrics() -> None:
    message = ParsedTelemetryMessage.from_envelope(
        {
            "raw_message": _raw_message(),
            "parsed_payload": {"metric_groups": [{"metrics": {"value": 1}}]},
            "parse_status": "failed",
            "parse_error": "invalid payload",
        }
    )
    assert message.metrics == ()
    assert message.parse_error == "invalid payload"


def _raw_message() -> dict[str, object]:
    return {
        "message_id": "message-1",
        "station_id": "station-1",
        "device_id": "device-1",
        "protocol_type": "green_power_v20260428",
        "sequence": 1,
        "collected_at": "2026-09-06T10:00:00+08:00",
        "received_at": "2026-09-06T10:00:03+08:00",
    }
