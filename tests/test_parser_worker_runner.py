from __future__ import annotations

import json
from pathlib import Path

from green_v2.application.parse_telemetry import ParseTelemetry
from green_v2.application.parser_worker import ParserWorkerRunner
from green_v2.messaging.memory import InMemoryMessageBus


ROOT = Path(__file__).resolve().parents[1]


class OneMessageConsumer(InMemoryMessageBus):
    def __init__(self, message: dict | None) -> None:
        super().__init__()
        self.message = message

    def get_one(self, queue_name: str):
        self.events.append(("get", queue_name))
        if self.message is None:
            return None, None
        message, self.message = self.message, None
        return "delivery-1", message


def raw_fixture() -> dict:
    path = ROOT / "contracts" / "mq" / "green-telemetry-raw-v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_runner_processes_exactly_one_delivery() -> None:
    consumer = OneMessageConsumer(raw_fixture())
    use_case = ParseTelemetry(consumer, consumer, "parsed", "failed")
    runner = ParserWorkerRunner(consumer, use_case, "raw")
    assert runner.run_once() is True
    assert runner.run_once() is False
    assert consumer.events == [
        ("get", "raw"),
        ("publish", "parsed"),
        ("ack", "delivery-1"),
        ("get", "raw"),
    ]


def test_runner_keeps_running_after_publish_failure() -> None:
    consumer = OneMessageConsumer(raw_fixture())
    consumer.fail_queue = "parsed"
    use_case = ParseTelemetry(consumer, consumer, "parsed", "failed")
    runner = ParserWorkerRunner(consumer, use_case, "raw")
    assert runner.run_once() is True
    assert consumer.events == [
        ("get", "raw"),
        ("publish", "parsed"),
        ("nack", ("delivery-1", True)),
    ]
