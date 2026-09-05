from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PublishedMessage:
    queue_name: str
    payload: dict[str, Any]


@dataclass
class InMemoryMessageBus:
    published: list[PublishedMessage] = field(default_factory=list)
    events: list[tuple[str, object]] = field(default_factory=list)
    fail_queue: str | None = None

    def publish(self, queue_name: str, payload: dict[str, Any]) -> None:
        self.events.append(("publish", queue_name))
        if queue_name == self.fail_queue:
            raise RuntimeError(f"publish failed: {queue_name}")
        self.published.append(PublishedMessage(queue_name, deepcopy(payload)))

    def ack(self, delivery: object) -> bool:
        self.events.append(("ack", delivery))
        return True

    def nack(self, delivery: object, requeue: bool = True) -> bool:
        self.events.append(("nack", (delivery, requeue)))
        return True

    def messages_for(self, queue_name: str) -> list[dict[str, Any]]:
        return [item.payload for item in self.published if item.queue_name == queue_name]
