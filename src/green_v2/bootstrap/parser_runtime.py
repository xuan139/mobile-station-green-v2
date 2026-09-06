from __future__ import annotations

import threading

from green_v2.application.parse_telemetry import ParseTelemetry
from green_v2.application.parser_worker import ParserWorkerRunner
from green_v2.config import Settings
from green_v2.messaging.rabbitmq import RabbitMqConsumer, RabbitMqPublisher
from green_v2.runtime.health_server import HealthServer
from green_v2.runtime.signals import install_thread_stop


def run() -> None:
    settings = Settings.from_env("parser_worker")
    consumer = RabbitMqConsumer(settings)
    publisher = RabbitMqPublisher(settings)
    use_case = ParseTelemetry(
        publisher,
        consumer,
        settings.mq_queue_parsed,
        settings.mq_queue_failed,
    )
    runner = ParserWorkerRunner(consumer, use_case, settings.mq_queue_raw)
    health = HealthServer(
        settings.health_bind_host,
        settings.health_bind_port,
        "green-v2-parser-worker",
        settings.app_version,
        lambda: consumer.is_ready() and publisher.is_ready(),
    )
    stop_event = threading.Event()
    install_thread_stop(stop_event)
    try:
        consumer.connect()
        publisher.connect()
        health.start()
        while not stop_event.is_set():
            if not runner.run_once():
                stop_event.wait(settings.worker_poll_seconds)
    finally:
        health.stop()
        publisher.close()
        consumer.close()
