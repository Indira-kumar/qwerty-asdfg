import json
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

from app.schemas.decision import DaySummary, DecisionResponse, HeatmapPoint, HourPoint, Metrics, OverviewResponse, RiskContext

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "january_2026.json"


@lru_cache(maxsize=1)
def load_snapshot() -> dict:
    return json.loads(DATA_PATH.read_text())


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def build_decision(decision_day: date) -> DecisionResponse:
    if not date(2026, 1, 1) <= decision_day <= date(2026, 1, 31):
        raise ValueError("Decision date must be in January 2026")
    data = load_snapshot()
    delivery_day = decision_day + timedelta(days=1)
    forecast = data["forecasts"].get(decision_day.isoformat(), {})
    actual = data["actuals"].get(delivery_day.isoformat(), {})

    errors_by_hour: dict[int, list[float]] = {hour: [] for hour in range(24)}
    baseline_errors: list[float] = []
    completed_days = 0
    for lag in range(1, 57):
        historical_delivery = decision_day - timedelta(days=lag)
        historical_decision = historical_delivery - timedelta(days=1)
        old_forecast = data["forecasts"].get(historical_decision.isoformat(), {})
        old_actual = data["actuals"].get(historical_delivery.isoformat(), {})
        day_has_pairs = False
        for key, entry in old_forecast.items():
            if key not in old_actual:
                continue
            error = entry["forecast_mw"] - old_actual[key]
            errors_by_hour[int(key[11:13])].append(error)
            baseline_errors.append(error)
            day_has_pairs = True
        completed_days += day_has_pairs

    points = []
    observed_errors = []
    for key, entry in sorted(forecast.items()):
        hour = int(key[11:13])
        errors = errors_by_hour[hour]
        predicted = entry["forecast_mw"]
        downside = max(0, predicted - max(percentile(errors, 0.9), 0)) if errors else None
        upside = max(predicted, predicted - percentile(errors, 0.1)) if errors else None
        measured = actual.get(key)
        signed_error = predicted - measured if measured is not None else None
        if signed_error is not None:
            observed_errors.append(signed_error)
        points.append(HourPoint(
            start_time=key,
            forecast_mw=predicted,
            downside_mw=downside,
            upside_mw=upside,
            actual_mw=measured,
            error_mw=signed_error,
            publish_time=entry["publish_time"],
            history_count=len(errors),
        ))

    def metrics(values: list[float]) -> Metrics | None:
        if not values:
            return None
        return Metrics(
            mae_mw=sum(abs(x) for x in values) / len(values),
            bias_mw=sum(values) / len(values),
            rmse_mw=(sum(x * x for x in values) / len(values)) ** 0.5,
            observations=len(values),
        )

    covered = [p.actual_mw >= p.downside_mw for p in points if p.actual_mw is not None and p.downside_mw is not None]
    return DecisionResponse(
        decision_date=decision_day,
        delivery_date=delivery_day,
        cutoff_time=f"{decision_day.isoformat()}T09:00:00Z",
        source=data["source"],
        prepared_at=data["prepared_at"],
        forecast_mwh=sum(p.forecast_mw for p in points),
        downside_mwh=sum(p.downside_mw for p in points if p.downside_mw is not None) if points else None,
        actual_mwh=sum(p.actual_mw for p in points if p.actual_mw is not None) if points else None,
        downside_coverage=sum(covered) / len(covered) if covered else None,
        risk=RiskContext(
            lookback_days=56,
            completed_days=completed_days,
            method="Per-hour empirical 90th percentile of overforecast error from prior completed days",
            baseline=metrics(baseline_errors),
        ),
        realized=metrics(observed_errors),
        hours=points,
    )


@lru_cache(maxsize=1)
def build_overview() -> OverviewResponse:
    decisions = [build_decision(date(2026, 1, day)) for day in range(1, 32)]
    errors = [hour.error_mw for decision in decisions for hour in decision.hours if hour.error_mw is not None]
    covered = [hour.actual_mw >= hour.downside_mw for decision in decisions for hour in decision.hours if hour.actual_mw is not None and hour.downside_mw is not None]
    return OverviewResponse(
        days=[DaySummary(
            decision_date=d.decision_date,
            delivery_date=d.delivery_date,
            forecast_mwh=d.forecast_mwh,
            actual_mwh=d.actual_mwh,
            mae_mw=d.realized.mae_mw if d.realized else None,
            downside_coverage=d.downside_coverage,
        ) for d in decisions],
        heatmap=[HeatmapPoint(decision_date=d.decision_date, hour=int(h.start_time[11:13]), error_mw=h.error_mw) for d in decisions for h in d.hours],
        january_mae_mw=sum(abs(x) for x in errors) / len(errors) if errors else None,
        january_bias_mw=sum(errors) / len(errors) if errors else None,
        downside_coverage=sum(covered) / len(covered) if covered else None,
        evaluated_hours=len(errors),
    )
