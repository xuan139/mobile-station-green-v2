from __future__ import annotations

import asyncio
import json

from green_v2.application.ingest_telemetry import IngestTelemetry
from green_v2.config import Settings
from green_v2.ingestion.json_line import handle_json_line


class TcpIngressServer:
    def __init__(self, settings: Settings, use_case: IngestTelemetry) -> None:
        self._settings = settings
        self._use_case = use_case
        self._server: asyncio.Server | None = None
        self._active_connections = 0
        self._publish_limit = asyncio.Semaphore(settings.ingress_publish_concurrency)

    @property
    def port(self) -> int:
        if self._server is None or not self._server.sockets:
            raise RuntimeError("ingress server is not started")
        return int(self._server.sockets[0].getsockname()[1])

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client,
            host=self._settings.ingress_bind_host,
            port=self._settings.ingress_bind_port,
            limit=self._settings.ingress_max_line_bytes + 1,
        )

    async def close(self) -> None:
        if self._server is None:
            return
        self._server.close()
        await self._server.wait_closed()
        self._server = None

    def is_ready(self) -> bool:
        return self._server is not None and self._server.is_serving()

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        self._active_connections += 1
        try:
            if self._active_connections > self._settings.ingress_max_connections:
                return
            try:
                await self._read_lines(reader, writer)
            except asyncio.TimeoutError:
                return
        finally:
            self._active_connections -= 1
            writer.close()
            await writer.wait_closed()

    async def _read_lines(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        while True:
            try:
                raw_line = await asyncio.wait_for(
                    reader.readline(),
                    timeout=self._settings.ingress_read_timeout_seconds,
                )
            except ValueError:
                response = self._use_case.reject(
                    None,
                    ValueError("payload_too_large"),
                    "PAYLOAD_TOO_LARGE",
                )
                await self._write_response(writer, response)
                return
            if not raw_line:
                return
            if len(raw_line) > self._settings.ingress_max_line_bytes:
                response = self._use_case.reject(
                    None,
                    ValueError("payload_too_large"),
                    "PAYLOAD_TOO_LARGE",
                )
                await self._write_response(writer, response)
                continue
            async with self._publish_limit:
                encoded = await asyncio.to_thread(handle_json_line, raw_line, self._use_case)
            writer.write(encoded)
            await writer.drain()

    @staticmethod
    async def _write_response(writer: asyncio.StreamWriter, response: dict) -> None:
        writer.write((json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8"))
        await writer.drain()
