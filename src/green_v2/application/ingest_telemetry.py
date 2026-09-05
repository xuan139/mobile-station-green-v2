from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from green_v2.domain.ack_message import build_ack
from green_v2.domain.telemetry_message import utc_now_iso, validate_telemetry_message
from green_v2.messaging.ports import JsonPublisher


CommandClaim = Callable[[str, int | None], Mapping[str, Any] | None]


@dataclass(frozen=True)
class IngestTelemetry:
    publisher: JsonPublisher
    raw_queue: str
    clock: Callable[[], str] = utc_now_iso
    claim_command: CommandClaim | None = None

    def execute(self, message: Mapping[str, Any]) -> dict[str, Any]:
        normalized = validate_telemetry_message(message, self.clock)
        self.publisher.publish(self.raw_queue, normalized)
        pending_command = self._claim_pending_command(normalized)
        return build_ack(
            normalized,
            status="ok",
            received_at=self.clock(),
            pending_command=pending_command,
        )

    def reject(self, message: Mapping[str, Any] | None, error: Exception) -> dict[str, Any]:
        return build_ack(
            message,
            status="reject",
            received_at=self.clock(),
            error_code="INVALID_PAYLOAD",
            error_message=str(error),
        )

    def _claim_pending_command(self, message: Mapping[str, Any]) -> Mapping[str, Any] | None:
        if self.claim_command is None:
            return None
        return self.claim_command(str(message["station_id"]), int(message["sequence"]))
