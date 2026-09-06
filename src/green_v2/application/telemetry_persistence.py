from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from green_v2.domain.parsed_telemetry import ParsedTelemetryMessage


class TelemetryRepository(Protocol):
    def insert_raw_message(self, message: ParsedTelemetryMessage) -> bool: ...

    def upsert_runtime(self, message: ParsedTelemetryMessage) -> None: ...

    def insert_metrics(self, message: ParsedTelemetryMessage) -> None: ...


class TelemetryUnitOfWork(Protocol):
    telemetry: TelemetryRepository

    def __enter__(self) -> TelemetryUnitOfWork: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None: ...

    def commit(self) -> None: ...


class TelemetryUnitOfWorkFactory(Protocol):
    def __call__(self) -> TelemetryUnitOfWork: ...


@dataclass(frozen=True)
class PersistParsedTelemetry:
    unit_of_work: TelemetryUnitOfWorkFactory

    def execute(self, envelope: dict[str, object]) -> bool:
        message = ParsedTelemetryMessage.from_envelope(envelope)
        with self.unit_of_work() as work:
            inserted = work.telemetry.insert_raw_message(message)
            if inserted:
                work.telemetry.upsert_runtime(message)
                if message.parse_status == "success":
                    work.telemetry.insert_metrics(message)
            work.commit()
        return inserted
