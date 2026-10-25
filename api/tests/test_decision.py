import copy
import unittest
from datetime import date
from unittest.mock import patch

from app.services.decision import build_decision, build_overview, load_snapshot, planning_level
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
        self.assertEqual(before.confidence_score, after.confidence_score)
        self.assertEqual(before.downside_mwh, after.downside_mwh)
        self.assertEqual(before.hours[0].downside_mw, after.hours[0].downside_mw)
        self.assertNotEqual(before.realized, after.realized)

    def test_daily_planning_level_uses_daily_errors_and_narrows_january_nine_gap(self):
        decision = build_decision(date(2026, 1, 8))
        self.assertEqual(decision.risk.coverage_target, 0.80)
        self.assertEqual(decision.risk.lookback_days, 21)
        self.assertGreater(decision.downside_mwh, 238_000)
        self.assertLess(decision.downside_mwh, 240_000)
        self.assertAlmostEqual(
            decision.downside_mwh,
            decision.forecast_mwh * (1 - decision.risk.planning_error_rate),
        )
        self.assertGreater(decision.downside_mwh, sum(hour.downside_mw for hour in decision.hours))

    def test_percentage_allowance_scales_with_forecast(self):
        self.assertAlmostEqual(planning_level(100, [0.1, 0.2], 0.5), 85)
        self.assertAlmostEqual(planning_level(200, [0.1, 0.2], 0.5), 170)

    def test_january_daily_coverage_matches_recalibrated_level(self):
        overview = build_overview()
        self.assertEqual(overview.evaluated_days, 31)
        self.assertAlmostEqual(overview.downside_coverage, 24 / 31)

    def test_overview_stops_at_selected_decision_date(self):
        through = date(2026, 1, 9)
        overview = build_overview(through)
        self.assertEqual(overview.through_date, through)
        self.assertEqual(len(overview.days), 9)
        self.assertEqual(overview.days[-1].decision_date, through)
        self.assertEqual(overview.evaluated_days, 9)
        self.assertEqual(len(overview.heatmap), 9 * 24)

    def test_all_january_decisions_have_complete_delivery_days(self):
        for day in range(1, 32):
            decision = build_decision(date(2026, 1, day))
            self.assertEqual(len(decision.hours), 24)
            self.assertEqual(decision.risk.completed_days, 21)
            self.assertTrue(all(hour.actual_mw is not None for hour in decision.hours))


if __name__ == "__main__":
    unittest.main()
