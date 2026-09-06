from __future__ import annotations

from green_v2.application.db_writer import DbWriterRunner
from green_v2.messaging.memory import InMemoryMessageBus


class OneMessageBus(InMemoryMessageBus):
    def __init__(self, message: dict[str, object]) -> None:
        super().__init__()
        self.message = message

    def get_one(self, queue_name: str):
        self.events.append(("get", queue_name))
        message, self.message = self.message, None
        return ("delivery-1", message) if message is not None else (None, None)


class PersistenceStub:
    def __init__(self, events: list[tuple[str, object]], error: Exception | None = None) -> None:
        self.events = events
        self.error = error

    def execute(self, message: dict[str, object]) -> bool:
        self.events.append(("commit", message.get("attempt")))
        if self.error:
            raise self.error
        return True


def test_ack_occurs_only_after_successful_commit() -> None:
    bus = OneMessageBus({"attempt": 0})
    runner = _runner(bus, PersistenceStub(bus.events))
    assert runner.run_once() is True
    assert bus.events == [("get", "parsed"), ("commit", 0), ("ack", "delivery-1")]


def test_failed_write_republishes_before_ack() -> None:
    bus = OneMessageBus({"attempt": 0})
    runner = _runner(bus, PersistenceStub(bus.events, RuntimeError("database unavailable")))
    assert runner.run_once() is True
    assert bus.events == [
        ("get", "parsed"),
        ("commit", 0),
        ("publish", "parsed"),
        ("ack", "delivery-1"),
    ]
    assert bus.messages_for("parsed")[0]["attempt"] == 1


def test_exhausted_write_is_published_to_dlq() -> None:
    bus = OneMessageBus({"attempt": 3})
    runner = _runner(bus, PersistenceStub(bus.events, RuntimeError("invalid row")))
    runner.run_once()
    assert bus.events[-2:] == [("publish", "dlq"), ("ack", "delivery-1")]
    assert bus.messages_for("dlq")[0]["attempt"] == 4


def test_failed_retry_publish_nacks_original_delivery() -> None:
    bus = OneMessageBus({"attempt": 0})
    bus.fail_queue = "parsed"
    runner = _runner(bus, PersistenceStub(bus.events, RuntimeError("database unavailable")))
    runner.run_once()
    assert bus.events[-2:] == [("publish", "parsed"), ("nack", ("delivery-1", True))]


def _runner(bus: OneMessageBus, persistence: PersistenceStub) -> DbWriterRunner:
    return DbWriterRunner(bus, bus, persistence, "parsed", "dlq", 3)
