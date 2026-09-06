from __future__ import annotations

import os
from unittest import TestCase, mock

from green_v2.config import Settings


class SettingsTests(TestCase):
    def test_defaults_are_isolated(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            settings = Settings.from_env()
        self.assertEqual(settings.db_name, "mobile_station_green_v2")
        self.assertEqual(settings.mq_vhost, "/green-v2")
        self.assertEqual(settings.api_bind_port, 28000)
        self.assertEqual(settings.ingress_bind_port, 29000)
        self.assertEqual(settings.health_bind_port, 28080)
        self.assertEqual(settings.worker_prefetch, 50)

    def test_service_health_ports_are_isolated(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            ingress = Settings.from_env("ingress")
            parser = Settings.from_env("parser_worker")
            writer = Settings.from_env("db_writer")
        self.assertEqual(ingress.health_bind_port, 28081)
        self.assertEqual(parser.health_bind_port, 28082)
        self.assertEqual(writer.health_bind_port, 28083)

    def test_rejects_old_database(self) -> None:
        with mock.patch.dict(os.environ, {"DB_NAME": "mobile_station"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "舊系統"):
                Settings.from_env()

    def test_rejects_old_mq_vhost(self) -> None:
        with mock.patch.dict(os.environ, {"MQ_VHOST": "/ms"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "舊系統"):
                Settings.from_env()
