from __future__ import annotations

import asyncio

from green_v2.application.ingest_telemetry import IngestTelemetry
from green_v2.config import Settings
from green_v2.ingestion.tcp_server import TcpIngressServer
from green_v2.messaging.rabbitmq import RabbitMqPublisher
from green_v2.runtime.health_server import HealthServer
from green_v2.runtime.signals import install_async_stop


async def run() -> None:
    settings = Settings.from_env("ingress")
    publisher = RabbitMqPublisher(settings)
    use_case = IngestTelemetry(publisher, settings.mq_queue_raw)
    ingress = TcpIngressServer(settings, use_case)
    health = HealthServer(
        settings.health_bind_host,
        settings.health_bind_port,
        "green-v2-ingress",
        settings.app_version,
        lambda: ingress.is_ready() and publisher.is_ready(),
    )
    stop_event = asyncio.Event()
    install_async_stop(stop_event)
    try:
        publisher.connect()
        await ingress.start()
        health.start()
        await stop_event.wait()
    finally:
        await ingress.close()
        health.stop()
        publisher.close()
