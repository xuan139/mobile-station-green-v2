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

    def test_rejects_old_database(self) -> None:
        with mock.patch.dict(os.environ, {"DB_NAME": "mobile_station"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "舊系統"):
                Settings.from_env()

    def test_rejects_old_mq_vhost(self) -> None:
        with mock.patch.dict(os.environ, {"MQ_VHOST": "/ms"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "舊系統"):
                Settings.from_env()

