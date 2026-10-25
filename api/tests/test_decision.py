import copy
import unittest
from datetime import date
from unittest.mock import patch

from app.services.decision import build_decision, load_snapshot
from app.services.prepare_data import freeze_forecast, hourly_actuals


class DataPreparationTests(unittest.TestCase):
    def test_forecast_freezes_before_cutoff(self):
        rows = [
            {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-14T07:30:00Z", "generation": 15834},
            {"startTime": "2026-01-15T00:00:00Z", "publishTime": "2026-01-14T09:30:00Z", "generation": 15828},
        ]
        frozen = freeze_forecast(rows, date(2026, 1, 14))
        self.assertEqual(frozen["2026-01-15T00:00:00Z"]["forecast_mw"], 15834)

    def test_actual_half_hours_become_hourly_average(self):
        rows = [
            {"fuelType": "WIND", "startTime": "2026-01-15T00:00:00Z", "generation": 14602},
            {"fuelType": "WIND", "startTime": "2026-01-15T00:30:00Z", "generation": 14311},
        ]
        actual = hourly_actuals(rows, date(2026, 1, 15))
        self.assertEqual(actual["2026-01-15T00:00:00Z"], 14456.5)


class DecisionTests(unittest.TestCase):
    def test_january_one_risk_does_not_use_january_two_actuals(self):
        original = load_snapshot()
        changed = copy.deepcopy(original)
        changed["actuals"]["2026-01-02"] = {
            hour: value + 5000 for hour, value in changed["actuals"]["2026-01-02"].items()
        }
        before = build_decision(date(2026, 1, 1))
        with patch("app.services.decision.load_snapshot", return_value=changed):
            after = build_decision(date(2026, 1, 1))
        self.assertEqual(before.risk, after.risk)
        self.assertEqual(before.hours[0].downside_mw, after.hours[0].downside_mw)
        self.assertNotEqual(before.realized, after.realized)

    def test_all_january_decisions_have_complete_delivery_days(self):
        for day in range(1, 32):
            decision = build_decision(date(2026, 1, day))
            self.assertEqual(len(decision.hours), 24)
            self.assertEqual(decision.risk.completed_days, 56)
            self.assertTrue(all(hour.actual_mw is not None for hour in decision.hours))


if __name__ == "__main__":
    unittest.main()
