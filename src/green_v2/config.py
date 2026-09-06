from __future__ import annotations

import os
from dataclasses import dataclass


def _text(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value is not None else default


def _integer(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


@dataclass(frozen=True)
class Settings:
    app_env: str
    app_version: str
    log_level: str
    api_bind_host: str
    api_bind_port: int
    ingress_bind_host: str
    ingress_bind_port: int
    health_bind_host: str
    health_bind_port: int
    ingress_max_connections: int
    ingress_read_timeout_seconds: int
    ingress_max_line_bytes: int
    ingress_publish_concurrency: int
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    db_pool_min_size: int
    db_pool_max_size: int
    mq_host: str
    mq_port: int
    mq_vhost: str
    mq_user: str
    mq_password: str
    mq_queue_raw: str
    mq_queue_parsed: str
    mq_queue_failed: str
    mq_queue_dlq: str
    worker_prefetch: int
    worker_poll_seconds: int
    db_writer_max_retries: int

    @classmethod
    def from_env(cls, service_name: str = "api") -> "Settings":
        health_ports = {"ingress": 28081, "parser_worker": 28082, "db_writer": 28083}
        settings = cls(
            app_env=_text("APP_ENV", "local"),
            app_version=_text("APP_VERSION", "0.1.0"),
            log_level=_text("LOG_LEVEL", "INFO"),
            api_bind_host=_text("API_BIND_HOST", "127.0.0.1"),
            api_bind_port=_integer("API_BIND_PORT", 28000),
            ingress_bind_host=_text("INGRESS_BIND_HOST", "127.0.0.1"),
            ingress_bind_port=_integer("INGRESS_BIND_PORT", 29000),
            health_bind_host=_text("HEALTH_BIND_HOST", "127.0.0.1"),
            health_bind_port=_integer("HEALTH_BIND_PORT", health_ports.get(service_name, 28080)),
            ingress_max_connections=_integer("INGRESS_MAX_CONNECTIONS", 1000),
            ingress_read_timeout_seconds=_integer("INGRESS_READ_TIMEOUT_SECONDS", 15),
            ingress_max_line_bytes=_integer("INGRESS_MAX_LINE_BYTES", 32768),
            ingress_publish_concurrency=_integer("INGRESS_PUBLISH_CONCURRENCY", 64),
            db_host=_text("DB_HOST", "127.0.0.1"),
            db_port=_integer("DB_PORT", 55432),
            db_name=_text("DB_NAME", "mobile_station_green_v2"),
            db_user=_text("DB_USER", "green_v2"),
            db_password=_text("DB_PASSWORD", ""),
            db_pool_min_size=_integer("DB_POOL_MIN_SIZE", 1),
            db_pool_max_size=_integer("DB_POOL_MAX_SIZE", 10),
            mq_host=_text("MQ_HOST", "127.0.0.1"),
            mq_port=_integer("MQ_PORT", 55672),
            mq_vhost=_text("MQ_VHOST", "/green-v2"),
            mq_user=_text("MQ_USER", "green_v2"),
            mq_password=_text("MQ_PASSWORD", ""),
            mq_queue_raw=_text("MQ_QUEUE_RAW", "green_v2.raw.telemetry"),
            mq_queue_parsed=_text("MQ_QUEUE_PARSED", "green_v2.parsed.telemetry"),
            mq_queue_failed=_text("MQ_QUEUE_FAILED", "green_v2.failed"),
            mq_queue_dlq=_text("MQ_QUEUE_DLQ", "green_v2.dlq"),
            worker_prefetch=_integer("WORKER_PREFETCH", 50),
            worker_poll_seconds=_integer("WORKER_POLL_SECONDS", 1),
            db_writer_max_retries=_integer("DB_WRITER_MAX_RETRIES", 3),
        )
        settings.assert_isolated()
        return settings

    def assert_isolated(self) -> None:
        errors: list[str] = []
        if self.db_name == "mobile_station":
            errors.append("DB_NAME 不得使用舊系統 mobile_station")
        if self.mq_vhost == "/ms":
            errors.append("MQ_VHOST 不得使用舊系統 /ms")
        if self.api_bind_port == 18000:
            errors.append("API_BIND_PORT 不得使用舊系統 18000")
        if self.ingress_bind_port == 19000:
            errors.append("INGRESS_BIND_PORT 不得使用舊系統 19000")
        if self.db_pool_min_size < 1:
            errors.append("DB_POOL_MIN_SIZE 必須大於 0")
        if self.db_pool_max_size < self.db_pool_min_size:
            errors.append("DB_POOL_MAX_SIZE 不得小於 DB_POOL_MIN_SIZE")
        if self.worker_prefetch < 1:
            errors.append("WORKER_PREFETCH 必須大於 0")
        if self.db_writer_max_retries < 1:
            errors.append("DB_WRITER_MAX_RETRIES 必須大於 0")
        if self.ingress_max_connections < 1:
            errors.append("INGRESS_MAX_CONNECTIONS 必須大於 0")
        if self.ingress_max_line_bytes < 128:
            errors.append("INGRESS_MAX_LINE_BYTES 不得小於 128")
        if errors:
            raise RuntimeError("；".join(errors))
