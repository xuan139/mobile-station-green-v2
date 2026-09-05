#!/usr/bin/env python3
"""Capture reproducible, offline contracts from a legacy Green source tree."""

from __future__ import annotations

import argparse
import ast
import configparser
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


GREEN_UNITS = {
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

GREEN_SERVICE_DIRS = (
    "alert_notify",
    "alert_rules_worker",
    "api",
    "command_lifecycle_worker",
    "db_writer",
    "green_power_energy_worker",
    "ingress",
    "mode_schedule_worker",
    "parser_worker",
)

STATIC_SCHEMA_GLOB = "cloud/db/*.sql"
RUNTIME_DDL_SOURCES = (
    "cloud/common/db.py",
    "cloud/data_access/access_control.py",
    "cloud/data_access/alarm_records.py",
    "cloud/data_access/green_energy.py",
    "cloud/data_access/station_directory.py",
)
HASHED_COMMON_FILES = (
    "cloud/common/config.py",
    "cloud/common/db.py",
    "cloud/common/mq.py",
    "cloud/common/parser.py",
    "cloud/common/station_agent.py",
)
CRON_SCRIPT = "cloud/scripts/manage_telemetry_history_storage.sh"
DDL_PATTERN = re.compile(
    r"\b(CREATE|ALTER|DROP)\s+(TABLE|INDEX|TYPE|VIEW|FUNCTION|TRIGGER)\b",
    re.IGNORECASE,
)
EXCLUDED_DDL_MARKERS = ("hourly_summary",)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--archive-sha256", required=True)
    return parser.parse_args()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


def extract_ddl_literals(path: Path) -> list[dict[str, Any]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    fragments: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        normalized = normalize_sql(node.value)
        lowered = normalized.lower()
        if not DDL_PATTERN.search(normalized):
            continue
        if any(marker in lowered for marker in EXCLUDED_DDL_MARKERS):
            continue
        fragments.append(
            {
                "line": node.lineno,
                "sha256": sha256_bytes(normalized.encode("utf-8")),
                "statement_kinds": sorted(
                    {f"{a.upper()} {b.upper()}" for a, b in DDL_PATTERN.findall(normalized)}
                ),
            }
        )
    return fragments


def database_manifest(root: Path, source: dict[str, Any]) -> dict[str, Any]:
    sql_files = [
        {
            "path": str(path.relative_to(root)),
            "sha256": sha256_file(path),
        }
        for path in sorted(root.glob(STATIC_SCHEMA_GLOB))
    ]
    runtime_sources = []
    for relative in RUNTIME_DDL_SOURCES:
        path = root / relative
        fragments = extract_ddl_literals(path)
        runtime_sources.append(
            {
                "path": relative,
                "source_sha256": sha256_file(path),
                "ddl_fragments": fragments,
            }
        )
    return {
        "capture_kind": "offline_source_schema_fingerprint",
        "live_schema_verified": False,
        "source": source,
        "static_sql_files": sql_files,
        "runtime_ddl_sources": runtime_sources,
        "limitations": [
            "此清單只證明來源檔內容，不代表 AWS 實際資料庫 schema。",
            "正式相容驗收仍須另行擷取唯讀 live schema fingerprint。",
        ],
    }


def read_systemd(path: Path) -> dict[str, dict[str, str]]:
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    parser.read(path, encoding="utf-8")
    return {section: dict(parser[section]) for section in parser.sections()}


def systemd_candidate(root: Path, relative: str, health_port: int) -> dict[str, Any]:
    path = root / relative
    if not path.exists():
        return {"path": relative, "exists": False}
    sections = read_systemd(path)
    service = sections.get("Service", {})
    return {
        "path": relative,
        "exists": True,
        "sha256": sha256_file(path),
        "description": sections.get("Unit", {}).get("Description"),
        "working_directory": service.get("WorkingDirectory"),
        "environment_file": service.get("EnvironmentFile"),
        "exec_start": service.get("ExecStart"),
        "health_port": health_port,
    }


def systemd_manifest(root: Path, source: dict[str, Any]) -> dict[str, Any]:
    units = []
    for unit, health_port in GREEN_UNITS.items():
        candidates = [
            systemd_candidate(root, f"cloud/deploy/systemd/{unit}", health_port),
            systemd_candidate(root, f"deploy/cloud/aws/systemd/{unit}", health_port),
        ]
        units.append({"unit": unit, "health_port": health_port, "candidates": candidates})
    return {
        "capture_kind": "offline_systemd_source_manifest",
        "live_systemd_verified": False,
        "source": source,
        "units": units,
        "limitations": [
            "兩套來源範本可能漂移；本階段不指定其中一套為正式部署真相。",
            "AWS 實際 unit、執行目錄及 Python 路徑仍須另行唯讀核對。",
        ],
    }


def cron_modes(content: str) -> list[str]:
    return re.findall(r"^\s{2}([a-z0-9-]+)\)\s*$", content, flags=re.MULTILINE)


def cron_manifest(root: Path, source: dict[str, Any]) -> dict[str, Any]:
    path = root / CRON_SCRIPT
    content = path.read_text(encoding="utf-8")
    return {
        "capture_kind": "offline_cron_source_manifest",
        "live_cron_verified": False,
        "source": source,
        "script": CRON_SCRIPT,
        "sha256": sha256_file(path),
        "modes": cron_modes(content),
        "required_semantics": [
            "advisory transaction lock",
            "atomic rollup and watermark commit",
            "idempotent rerun",
            "sample_count conservation",
        ],
    }


def relevant_source_paths(root: Path) -> Iterable[Path]:
    for service_dir in GREEN_SERVICE_DIRS:
        yield from (root / "cloud/services" / service_dir).rglob("*.py")
    yield from (root / "cloud/data_access").glob("*.py")
    yield from (root / "cloud/db").glob("*.sql")
    for relative in HASHED_COMMON_FILES:
        yield root / relative
    yield root / CRON_SCRIPT
    for unit in GREEN_UNITS:
        for base in ("cloud/deploy/systemd", "deploy/cloud/aws/systemd"):
            path = root / base / unit
            if path.exists():
                yield path


def source_hash_manifest(root: Path, source: dict[str, Any]) -> dict[str, Any]:
    unique_paths = sorted(set(relevant_source_paths(root)))
    return {
        "capture_kind": "offline_source_file_hashes",
        "source": source,
        "files": [
            {"path": str(path.relative_to(root)), "sha256": sha256_file(path)}
            for path in unique_paths
        ],
    }


def main() -> int:
    args = parse_args()
    root = args.legacy_root.resolve()
    output = args.output_root.resolve()
    source = {
        "commit": args.source_commit,
        "archive_sha256": args.archive_sha256,
        "repository_ref": "origin/dev",
    }
    write_json(output / "contracts/database/source-schema-manifest.json", database_manifest(root, source))
    write_json(output / "contracts/deployment/systemd-source-manifest.json", systemd_manifest(root, source))
    write_json(output / "contracts/deployment/cron-source-manifest.json", cron_manifest(root, source))
    write_json(output / "contracts/source/source-file-hashes.json", source_hash_manifest(root, source))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
