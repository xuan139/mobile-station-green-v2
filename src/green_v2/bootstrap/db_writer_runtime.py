from __future__ import annotations

import threading

from green_v2.application.db_writer import DbWriterRunner
from green_v2.application.telemetry_persistence import PersistParsedTelemetry
from green_v2.config import Settings
from green_v2.data_access.postgres_pool import PostgresConnectionPool
from green_v2.data_access.telemetry_uow import PostgresTelemetryUnitOfWorkFactory
from green_v2.messaging.rabbitmq import RabbitMqConsumer, RabbitMqPublisher
from green_v2.runtime.health_server import HealthServer
from green_v2.runtime.signals import install_thread_stop


def run() -> None:
    settings = Settings.from_env("db_writer")
    pool = PostgresConnectionPool(settings)
    consumer = RabbitMqConsumer(settings)
    publisher = RabbitMqPublisher(settings)
    persistence = PersistParsedTelemetry(PostgresTelemetryUnitOfWorkFactory(pool))
    runner = DbWriterRunner(
        consumer,
        publisher,
        persistence,
        settings.mq_queue_parsed,
        settings.mq_queue_dlq,
        settings.db_writer_max_retries,
    )
    health = HealthServer(
        settings.health_bind_host,
        settings.health_bind_port,
        "green-v2-db-writer",
        settings.app_version,
        lambda: pool.is_ready() and consumer.is_ready() and publisher.is_ready(),
    )
    stop_event = threading.Event()
    install_thread_stop(stop_event)
    try:
        pool.connect()
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
        pool.close()
