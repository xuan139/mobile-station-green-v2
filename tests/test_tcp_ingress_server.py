from __future__ import annotations

import asyncio
import json
import os
from dataclasses import replace
from pathlib import Path
from unittest import mock

from green_v2.application.ingest_telemetry import IngestTelemetry
from green_v2.config import Settings
from green_v2.ingestion.tcp_server import TcpIngressServer
from green_v2.messaging.memory import InMemoryMessageBus


ROOT = Path(__file__).resolve().parents[1]


def settings_for_test(**changes) -> Settings:
    with mock.patch.dict(os.environ, {}, clear=True):
        settings = Settings.from_env("ingress")
    return replace(settings, ingress_bind_port=0, ingress_read_timeout_seconds=2, **changes)


def raw_fixture() -> dict:
    path = ROOT / "contracts" / "mq" / "green-telemetry-raw-v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


async def exchange(server: TcpIngressServer, payload: bytes) -> dict:
    reader, writer = await asyncio.open_connection("127.0.0.1", server.port)
    writer.write(payload + b"\n")
    await writer.drain()
    response = json.loads(await reader.readline())
    writer.close()
    await writer.wait_closed()
    return response


def test_tcp_server_accepts_json_line_and_returns_ack() -> None:
    async def scenario() -> None:
        bus = InMemoryMessageBus()
        use_case = IngestTelemetry(bus, "green_v2.raw.telemetry", lambda: "2026-01-01T00:00:00Z")
        server = TcpIngressServer(settings_for_test(), use_case)
        await server.start()
        try:
            response = await exchange(server, json.dumps(raw_fixture()).encode())
            assert response["status"] == "ok"
            assert len(bus.messages_for("green_v2.raw.telemetry")) == 1
        finally:
            await server.close()

    asyncio.run(scenario())


def test_tcp_server_rejects_oversized_line() -> None:
    async def scenario() -> None:
        bus = InMemoryMessageBus()
        use_case = IngestTelemetry(bus, "raw", lambda: "2026-01-01T00:00:00Z")
        server = TcpIngressServer(settings_for_test(ingress_max_line_bytes=128), use_case)
        await server.start()
        try:
            response = await exchange(server, b"{" + b"x" * 300 + b"}")
            assert response["status"] == "reject"
            assert response["error_code"] == "PAYLOAD_TOO_LARGE"
        finally:
            await server.close()

    asyncio.run(scenario())
