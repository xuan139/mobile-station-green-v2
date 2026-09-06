from __future__ import annotations

import json
import threading
from collections.abc import Callable
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class HealthServer:
    def __init__(
        self,
        host: str,
        port: int,
        service_name: str,
        version: str,
        readiness_check: Callable[[], bool],
    ) -> None:
        handler = _build_handler(service_name, version, readiness_check)
        self._server = ThreadingHTTPServer((host, port), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._started = False

    @property
    def port(self) -> int:
        return int(self._server.server_address[1])

    def start(self) -> None:
        self._thread.start()
        self._started = True

    def stop(self) -> None:
        if self._started:
            self._server.shutdown()
        self._server.server_close()
        if self._started:
            self._thread.join(timeout=5)
        self._started = False


def _build_handler(
    service_name: str,
    version: str,
    readiness_check: Callable[[], bool],
) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health/live":
                self._write(HTTPStatus.OK, {"service": service_name, "status": "ok", "version": version})
                return
            if self.path == "/health/ready":
                ready = _is_ready(readiness_check)
                status = HTTPStatus.OK if ready else HTTPStatus.SERVICE_UNAVAILABLE
                self._write(status, {"service": service_name, "status": "ready" if ready else "not_ready"})
                return
            self._write(HTTPStatus.NOT_FOUND, {"error": "not_found"})

        def _write(self, status: HTTPStatus, payload: dict[str, str]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    return Handler


def _is_ready(check: Callable[[], bool]) -> bool:
    try:
        return bool(check())
    except Exception:  # noqa: BLE001
        return False
