from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from green_v2.application.telemetry_persistence import PersistParsedTelemetry
from green_v2.messaging.ports import JsonConsumer, JsonPublisher


@dataclass(frozen=True)
class DbWriterRunner:
    consumer: JsonConsumer
    publisher: JsonPublisher
    persistence: PersistParsedTelemetry
    parsed_queue: str
    dlq_queue: str
    max_retries: int

    def run_once(self) -> bool:
        delivery, message = self.consumer.get_one(self.parsed_queue)
        if delivery is None or message is None:
            return False
        try:
            self.persistence.execute(message)
        except Exception as error:  # noqa: BLE001
            logging.getLogger(__name__).exception("db writer persistence failed")
            self._handle_failure(delivery, message, error)
            return True
        if not self.consumer.ack(delivery):
            logging.getLogger(__name__).warning("db writer could not ACK committed delivery")
        return True

    def _handle_failure(
        self,
        delivery: object,
        message: dict[str, Any],
        error: Exception,
    ) -> None:
        retry_message = dict(message)
        retry_message["attempt"] = _next_attempt(message.get("attempt"))
        retry_message["last_error"] = str(error)
        target = self._retry_target(int(retry_message["attempt"]))
        try:
            self.publisher.publish(target, retry_message)
        except Exception:  # noqa: BLE001
            self.consumer.nack(delivery, requeue=True)
            return
        self.consumer.ack(delivery)

    def _retry_target(self, attempt: int) -> str:
        return self.dlq_queue if attempt > self.max_retries else self.parsed_queue


def _next_attempt(value: object) -> int:
    try:
        return int(value) + 1
    except (TypeError, ValueError):
        return 1
