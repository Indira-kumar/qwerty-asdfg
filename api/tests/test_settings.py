import os
import unittest
from pathlib import Path
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

    def test_example_environment_matches_code_defaults(self):
        example = Path(__file__).resolve().parents[1] / ".env.example"
        defaults = Settings(_env_file=None)
        documented = Settings(_env_file=example)
        self.assertEqual(documented, defaults)
