import copy
import unittest
from datetime import date, timedelta

from app.services.decision_service import build_decision, build_overview, planning_level
from app.services.prepare_data import freeze_forecast, hourly_actuals


def example_generation_data() -> dict:
    """Complete synthetic hours make calculation tests independent of Elexon uptime."""
    forecasts: dict[str, dict] = {}
    actuals: dict[str, dict] = {}
    decision_day = date(2025, 12, 10)
    while decision_day <= date(2026, 1, 31):
        delivery_day = decision_day + timedelta(days=1)
        forecast_hours = {}
        actual_hours = {}
        for hour in range(24):
            start = f"{delivery_day.isoformat()}T{hour:02d}:00:00Z"
            forecast_mw = 2500.0 + 75 * (decision_day.toordinal() % 7) + 15 * hour
            actual_mw = forecast_mw * (0.92 + 0.02 * (decision_day.toordinal() % 5)) + 3 * hour
            forecast_hours[start] = {
                "forecast_mw": forecast_mw,
                "publish_time": f"{decision_day.isoformat()}T08:30:00Z",
            }
            actual_hours[start] = actual_mw
        forecasts[decision_day.isoformat()] = forecast_hours
        actuals[delivery_day.isoformat()] = actual_hours
        decision_day += timedelta(days=1)
    return {
        "source": "Synthetic WINDFOR and FUELHH/WIND",
        "retrieved_at": "2026-10-25T00:00:00Z",
        "forecasts": forecasts,
        "actuals": actuals,
    }


class DataPreparationTests(unittest.TestCase):
    def test_forecast_freezes_before_cutoff(self):
        rows = [
            {
                "startTime": "2026-01-15T00:00:00Z",
                "publishTime": "2026-01-14T07:30:00Z",
                "generation": 15834,
            },
            {
                "startTime": "2026-01-15T00:00:00Z",
                "publishTime": "2026-01-14T09:30:00Z",
                "generation": 15828,
            },
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
    @classmethod
    def setUpClass(cls):
        cls.data = example_generation_data()

    def test_january_one_risk_does_not_use_january_two_actuals(self):
        changed = copy.deepcopy(self.data)
        changed["actuals"]["2026-01-02"] = {
            hour: value + 5000 for hour, value in changed["actuals"]["2026-01-02"].items()
        }
        before = build_decision(date(2026, 1, 1), self.data)
        after = build_decision(date(2026, 1, 1), changed)
        self.assertEqual(before.risk, after.risk)
        self.assertEqual(before.confidence_score, after.confidence_score)
        self.assertEqual(before.downside_mwh, after.downside_mwh)
        self.assertEqual(before.hours[0].downside_mw, after.hours[0].downside_mw)
        self.assertNotEqual(before.realized, after.realized)

    def test_daily_planning_level_uses_daily_errors(self):
        decision = build_decision(date(2026, 1, 8), self.data)
        self.assertEqual(decision.risk.coverage_target, 0.80)
        self.assertEqual(decision.risk.lookback_days, 21)
        self.assertAlmostEqual(
            decision.downside_mwh,
            decision.forecast_mwh * (1 - decision.risk.planning_error_rate),
        )

    def test_percentage_allowance_scales_with_forecast(self):
        self.assertAlmostEqual(planning_level(100, [0.1, 0.2], 0.5), 85)
        self.assertAlmostEqual(planning_level(200, [0.1, 0.2], 0.5), 170)

    def test_overview_stops_at_selected_decision_date(self):
        through = date(2026, 1, 9)
        overview = build_overview(through, self.data)
        self.assertEqual(overview.through_date, through)
        self.assertEqual(len(overview.days), 9)
        self.assertEqual(overview.days[-1].decision_date, through)
        self.assertEqual(overview.evaluated_days, 9)
        self.assertEqual(len(overview.heatmap), 9 * 24)

    def test_all_january_decisions_have_complete_delivery_days(self):
        for day in range(1, 32):
            decision = build_decision(date(2026, 1, day), self.data)
            self.assertEqual(len(decision.hours), 24)
            self.assertEqual(decision.risk.completed_days, 21)
            self.assertTrue(all(hour.actual_mw is not None for hour in decision.hours))


if __name__ == "__main__":
    unittest.main()
