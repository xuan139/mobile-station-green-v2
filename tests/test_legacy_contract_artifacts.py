from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_COMMIT = "23b8274a2a708f9b8d4de2a8c46df2dc541bca6d"
EXPECTED_UNITS = {
    "mobile-station-ingress.service": 18081,
    "mobile-station-parser-worker.service": 18082,
    "mobile-station-db-writer.service": 18083,
    "mobile-station-alert-notify.service": 18084,
    "mobile-station-api.service": 18085,
    "mobile-station-alert-rules-worker.service": 18087,
    "mobile-station-green-power-energy-worker.service": 18088,
    "mobile-station-mode-schedule-worker.service": 18089,
    "mobile-station-command-lifecycle-worker.service": 18090,
}
EXPECTED_SERVICE_ROOTS = {
    "alert_notify",
    "alert_rules_worker",
    "api",
    "command_lifecycle_worker",
    "db_writer",
    "green_power_energy_worker",
    "ingress",
    "mode_schedule_worker",
    "parser_worker",
}


def load_json(relative: str) -> Any:
    return json.loads((CONTRACTS / relative).read_text(encoding="utf-8"))


def test_api_route_inventory_is_stable_and_dual_prefixed() -> None:
    inventory = load_json("openapi/v1-route-inventory.json")
    assert inventory["api_prefixes"] == ["/api/v1", "/v1"]
    assert inventory["source"]["commit"] == EXPECTED_COMMIT
    pairs = [(route["method"], route["path"]) for route in inventory["routes"]]
    assert len(pairs) == len(set(pairs))
    assert all(method in {"GET", "POST", "PUT", "DELETE"} for method, _ in pairs)
    required = {
        ("POST", "/auth/login"),
        ("GET", "/overview/stations"),
        ("GET", "/stations/alarm-markers"),
        ("POST", "/stations/{station_id}/commands"),
        ("PUT", "/mode-switch-schedule"),
        ("POST", "/history/query"),
    }
    assert required <= set(pairs)


def test_green_telemetry_fixtures_preserve_legacy_values() -> None:
    raw = load_json("mq/green-telemetry-raw-v1.json")
    parsed = load_json("mq/green-telemetry-parsed-v1.json")
    assert raw["protocol_type"] == "green_power_v20260428"
    assert raw["payload"]["address"] == 0x1E0
    assert raw["payload"]["count"] == len(raw["payload"]["registers"]) == 41
    assert parsed["raw_message"] == raw
    metrics = parsed["parsed_payload"]["metric_groups"][0]["metrics"]
    assert metrics["ac_input_voltage"] == 220.0
    assert metrics["ac_output_power"] == 1500.0
    assert metrics["soc_total"] == 81.23
    assert metrics["soh_total"] == 97.5
    assert metrics["power_w"] == 12.3


def test_ack_fixtures_keep_message_correlation_and_command_lease() -> None:
    ack_v1 = load_json("mq/ingress-ack-v1.json")
    ack_v2 = load_json("mq/ingress-ack-command-v2.json")
    for ack in (ack_v1, ack_v2):
        assert ack["message_type"] == "ack"
        assert ack["message_id"] == "test-green-power-main"
        assert ack["station_id"] == "GP-REAL-002"
        assert ack["sequence"] == 1
    command = ack_v2["pending_command"]
    assert command["delivery_protocol_version"] == 2
    assert command["attempt_count"] == 1
    assert command["delivery_lease_until"]
    assert command["expire_at"]


def test_source_schema_manifest_is_explicitly_offline() -> None:
    manifest = load_json("database/source-schema-manifest.json")
    assert manifest["live_schema_verified"] is False
    assert manifest["source"]["commit"] == EXPECTED_COMMIT
    assert len(manifest["static_sql_files"]) == 6
    fragments = [
        fragment
        for source in manifest["runtime_ddl_sources"]
        for fragment in source["ddl_fragments"]
    ]
    assert len(fragments) >= 5
    assert all(SHA256.fullmatch(fragment["sha256"]) for fragment in fragments)


def test_deployment_manifests_cover_expected_green_services_and_cron() -> None:
    systemd = load_json("deployment/systemd-source-manifest.json")
    assert systemd["live_systemd_verified"] is False
    observed = {item["unit"]: item["health_port"] for item in systemd["units"]}
    assert observed == EXPECTED_UNITS
    assert all(any(candidate["exists"] for candidate in item["candidates"]) for item in systemd["units"])
    cron = load_json("deployment/cron-source-manifest.json")
    assert cron["live_cron_verified"] is False
    assert {"rollup-5m", "rollup-15m", "rollup-1h", "prune"} <= set(cron["modes"])
    assert SHA256.fullmatch(cron["sha256"])


def test_source_file_hash_manifest_is_well_formed() -> None:
    manifest = load_json("source/source-file-hashes.json")
    assert manifest["source"]["commit"] == EXPECTED_COMMIT
    paths = [item["path"] for item in manifest["files"]]
    assert paths == sorted(set(paths))
    assert len(paths) >= 25
    assert all(SHA256.fullmatch(item["sha256"]) for item in manifest["files"])
    service_roots = {
        path.split("/")[2]
        for path in paths
        if path.startswith("cloud/services/")
    }
    assert service_roots == EXPECTED_SERVICE_ROOTS
