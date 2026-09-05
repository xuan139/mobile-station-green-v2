from __future__ import annotations

from typing import Any, Protocol


class JsonPublisher(Protocol):
    def publish(self, queue_name: str, payload: dict[str, Any]) -> None: ...


class DeliveryAcknowledger(Protocol):
    def ack(self, delivery: object) -> bool: ...

    def nack(self, delivery: object, requeue: bool = True) -> bool: ...
