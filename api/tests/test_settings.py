import os
import unittest
from unittest.mock import patch

from app.settings import Settings, get_settings


class SettingsTests(unittest.TestCase):
    def test_settings_are_reused(self):
        self.assertIs(get_settings(), get_settings())

    def test_environment_overrides_are_validated(self):
        with patch.dict(
            os.environ,
            {
                "LOOKBACK_DAYS": "14",
                "ALLOWED_ORIGINS": '["https://example.com"]',
            },
        ):
            settings = Settings(_env_file=None)
        self.assertEqual(settings.lookback_days, 14)
        self.assertEqual(settings.allowed_origins, ["https://example.com"])
