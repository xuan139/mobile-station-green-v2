from __future__ import annotations

import http.client
import json

from green_v2.runtime.health_server import HealthServer


def request(port: int, path: str) -> tuple[int, dict]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    connection.request("GET", path)
    response = connection.getresponse()
    payload = json.loads(response.read())
    connection.close()
    return response.status, payload


def test_health_server_reports_live_and_dynamic_readiness() -> None:
    ready = False
    server = HealthServer("127.0.0.1", 0, "test-service", "1.0", lambda: ready)
    server.start()
    try:
        assert request(server.port, "/health/live")[0] == 200
        assert request(server.port, "/health/ready")[0] == 503
        ready = True
        status, payload = request(server.port, "/health/ready")
        assert status == 200
        assert payload["status"] == "ready"
    finally:
        server.stop()


def test_unstarted_health_server_can_be_closed() -> None:
    server = HealthServer("127.0.0.1", 0, "test-service", "1.0", lambda: True)
    server.stop()
