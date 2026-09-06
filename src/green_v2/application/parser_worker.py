from __future__ import annotations

import logging
from dataclasses import dataclass

from green_v2.application.parse_telemetry import ParseTelemetry
from green_v2.messaging.ports import JsonConsumer


@dataclass(frozen=True)
class ParserWorkerRunner:
    consumer: JsonConsumer
    use_case: ParseTelemetry
    raw_queue: str

    def run_once(self) -> bool:
        delivery, message = self.consumer.get_one(self.raw_queue)
        if delivery is None or message is None:
            return False
        try:
            self.use_case.execute(delivery, message)
        except Exception:  # noqa: BLE001
            logging.getLogger(__name__).exception("parser delivery processing failed")
        return True
