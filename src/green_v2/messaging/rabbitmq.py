from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from typing import Any

import pika
from pika import exceptions as pika_exceptions

from green_v2.config import Settings


HEARTBEAT_SECONDS = 300
BLOCKED_TIMEOUT_SECONDS = 300
SOCKET_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class DeliveryHandle:
    delivery_tag: int
    generation: int


class RabbitMqPublisher:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = threading.Lock()
        self._connection: pika.BlockingConnection | None = None
        self._channel: Any = None

    def publish(self, queue_name: str, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        with self._lock:
            for attempt in range(2):
                try:
                    channel = self._ensure_channel()
                    channel.basic_publish(
                        exchange="",
                        routing_key=queue_name,
                        body=encoded,
                        properties=pika.BasicProperties(
                            content_type="application/json",
                            delivery_mode=2,
                        ),
                    )
                    return
                except (pika_exceptions.AMQPError, OSError, BrokenPipeError):
                    self._reset()
                    if attempt == 1:
                        raise

    def close(self) -> None:
        with self._lock:
            self._reset()

    def connect(self) -> None:
        with self._lock:
            self._ensure_channel()

    def is_ready(self) -> bool:
        return self._is_open()

    def _ensure_channel(self) -> Any:
        if self._is_open():
            return self._channel
        settings = self._settings
        parameters = pika.ConnectionParameters(
            host=settings.mq_host,
            port=settings.mq_port,
            virtual_host=settings.mq_vhost,
            credentials=pika.PlainCredentials(settings.mq_user, settings.mq_password),
            heartbeat=HEARTBEAT_SECONDS,
            blocked_connection_timeout=BLOCKED_TIMEOUT_SECONDS,
            socket_timeout=SOCKET_TIMEOUT_SECONDS,
        )
        self._connection = pika.BlockingConnection(parameters)
        self._channel = self._connection.channel()
        for queue_name in _queue_names(settings):
            self._channel.queue_declare(queue=queue_name, durable=True)
        return self._channel

    def _is_open(self) -> bool:
        return bool(
            self._connection is not None
            and self._connection.is_open
            and self._channel is not None
            and self._channel.is_open
        )

    def _reset(self) -> None:
        if self._channel is not None:
            _close_safely(self._channel)
        self._channel = None
        if self._connection is not None:
            _close_safely(self._connection)
        self._connection = None


class RabbitMqDeliveryAcknowledger:
    def __init__(self, channel: Any) -> None:
        self._channel = channel

    def ack(self, delivery: object) -> bool:
        self._channel.basic_ack(delivery_tag=delivery)
        return True

    def nack(self, delivery: object, requeue: bool = True) -> bool:
        self._channel.basic_nack(delivery_tag=delivery, requeue=requeue)
        return True


class RabbitMqConsumer:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._connection: pika.BlockingConnection | None = None
        self._channel: Any = None
        self._generation = 0

    def connect(self) -> None:
        if self.is_ready():
            return
        settings = self._settings
        parameters = pika.ConnectionParameters(
            host=settings.mq_host,
            port=settings.mq_port,
            virtual_host=settings.mq_vhost,
            credentials=pika.PlainCredentials(settings.mq_user, settings.mq_password),
            heartbeat=HEARTBEAT_SECONDS,
            blocked_connection_timeout=BLOCKED_TIMEOUT_SECONDS,
            socket_timeout=SOCKET_TIMEOUT_SECONDS,
        )
        self._connection = pika.BlockingConnection(parameters)
        self._channel = self._connection.channel()
        self._generation += 1
        for queue_name in _queue_names(settings):
            self._channel.queue_declare(queue=queue_name, durable=True)
        self._channel.basic_qos(prefetch_count=settings.worker_prefetch)

    def get_one(self, queue_name: str) -> tuple[DeliveryHandle | None, dict[str, Any] | None]:
        for attempt in range(2):
            try:
                self.connect()
                method, _properties, body = self._channel.basic_get(queue=queue_name, auto_ack=False)
                if method is None or body is None:
                    return None, None
                payload = json.loads(body.decode("utf-8"))
                return DeliveryHandle(method.delivery_tag, self._generation), payload
            except (pika_exceptions.AMQPError, OSError, BrokenPipeError, ValueError):
                self._reset()
                if attempt == 1:
                    raise
        return None, None

    def ack(self, delivery: object) -> bool:
        handle = self._coerce(delivery)
        if not self._is_active(handle):
            return False
        try:
            self._channel.basic_ack(delivery_tag=handle.delivery_tag)
            return True
        except (pika_exceptions.AMQPError, OSError, BrokenPipeError, ValueError):
            self._reset()
            return False

    def nack(self, delivery: object, requeue: bool = True) -> bool:
        handle = self._coerce(delivery)
        if not self._is_active(handle):
            return False
        try:
            self._channel.basic_nack(delivery_tag=handle.delivery_tag, requeue=requeue)
            return True
        except (pika_exceptions.AMQPError, OSError, BrokenPipeError, ValueError):
            self._reset()
            return False

    def is_ready(self) -> bool:
        return bool(
            self._connection is not None
            and self._connection.is_open
            and self._channel is not None
            and self._channel.is_open
        )

    def close(self) -> None:
        self._reset()

    def _coerce(self, delivery: object) -> DeliveryHandle:
        if isinstance(delivery, DeliveryHandle):
            return delivery
        return DeliveryHandle(int(delivery), self._generation)

    def _is_active(self, delivery: DeliveryHandle) -> bool:
        return delivery.generation == self._generation and self.is_ready()

    def _reset(self) -> None:
        if self._channel is not None:
            _close_safely(self._channel)
        self._channel = None
        if self._connection is not None:
            _close_safely(self._connection)
        self._connection = None

def _queue_names(settings: Settings) -> tuple[str, str, str]:
    return settings.mq_queue_raw, settings.mq_queue_parsed, settings.mq_queue_failed


def _close_safely(target: Any) -> None:
    try:
        if getattr(target, "is_open", True):
            target.close()
    except Exception:  # noqa: BLE001
        pass
