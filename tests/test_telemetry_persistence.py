from __future__ import annotations

import pytest

from green_v2.application.telemetry_persistence import PersistParsedTelemetry

from test_parsed_telemetry import _raw_message


class FakeRepository:
    def __init__(self, events: list[str], inserted: bool = True, fail_metrics: bool = False) -> None:
        self.events = events
        self.inserted = inserted
        self.fail_metrics = fail_metrics

    def insert_raw_message(self, message) -> bool:
        self.events.append("insert_raw")
        return self.inserted

    def upsert_runtime(self, message) -> None:
        self.events.append("upsert_runtime")

    def insert_metrics(self, message) -> None:
        self.events.append("insert_metrics")
        if self.fail_metrics:
            raise RuntimeError("metric write failed")


class FakeUnitOfWork:
    def __init__(self, repository: FakeRepository, events: list[str]) -> None:
        self.telemetry = repository
        self.events = events
        self.committed = False

    def __enter__(self):
        self.events.append("begin")
        return self

    def commit(self) -> None:
        self.events.append("commit")
        self.committed = True

    def __exit__(self, exc_type, exc, traceback) -> None:
        if not self.committed:
            self.events.append("rollback")


def envelope() -> dict[str, object]:
    return {
        "raw_message": _raw_message(),
        "parsed_payload": {"metric_groups": [{"metrics": {"voltage": 220}}]},
        "parse_status": "success",
        "parse_error": None,
    }


def test_commits_raw_runtime_and_metrics_as_one_use_case() -> None:
    events: list[str] = []
    repository = FakeRepository(events)
    use_case = PersistParsedTelemetry(lambda: FakeUnitOfWork(repository, events))
    assert use_case.execute(envelope()) is True
    assert events == ["begin", "insert_raw", "upsert_runtime", "insert_metrics", "commit"]


def test_duplicate_raw_message_commits_without_downstream_writes() -> None:
    events: list[str] = []
    repository = FakeRepository(events, inserted=False)
    use_case = PersistParsedTelemetry(lambda: FakeUnitOfWork(repository, events))
    assert use_case.execute(envelope()) is False
    assert events == ["begin", "insert_raw", "commit"]


def test_failure_rolls_back_the_whole_unit_of_work() -> None:
    events: list[str] = []
    repository = FakeRepository(events, fail_metrics=True)
    use_case = PersistParsedTelemetry(lambda: FakeUnitOfWork(repository, events))
    with pytest.raises(RuntimeError, match="metric write failed"):
        use_case.execute(envelope())
    assert events == ["begin", "insert_raw", "upsert_runtime", "insert_metrics", "rollback"]
