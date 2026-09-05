from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from green_v2.messaging.ports import DeliveryAcknowledger, JsonPublisher
from green_v2.parser.green_power import parse_telemetry


@dataclass(frozen=True)
class ParseTelemetry:
    publisher: JsonPublisher
    acknowledger: DeliveryAcknowledger
    parsed_queue: str
    failed_queue: str

    def execute(self, delivery: object, raw_message: dict[str, Any]) -> dict[str, Any]:
        try:
            parsed = parse_telemetry(raw_message)
            envelope = self._success_envelope(raw_message, parsed["parsed_payload"])
            target_queue = self.parsed_queue
        except Exception as error:  # noqa: BLE001
            envelope = self._failed_envelope(raw_message, error)
            target_queue = self.failed_queue

        try:
            self.publisher.publish(target_queue, envelope)
        except Exception:  # noqa: BLE001
            self.acknowledger.nack(delivery, requeue=True)
            raise
        self.acknowledger.ack(delivery)
        return envelope

    @staticmethod
    def _success_envelope(
        raw_message: dict[str, Any],
        parsed_payload: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "raw_message": raw_message,
            "parsed_payload": parsed_payload,
            "parse_status": "success",
            "parse_error": None,
            "attempt": 0,
        }

    @staticmethod
    def _failed_envelope(raw_message: dict[str, Any], error: Exception) -> dict[str, Any]:
        return {
            "raw_message": raw_message,
            "parsed_payload": None,
            "parse_status": "failed",
            "parse_error": str(error),
            "attempt": 0,
        }
