import json
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

from app.schemas.decision_schema import DaySummary, DecisionResponse, HeatmapPoint, HourPoint, Metrics, OverviewResponse, RiskContext
from app.settings import get_settings

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


def planning_level(forecast: float, historical_error_rates: list[float], q: float) -> float | None:
    if not historical_error_rates:
        return None
    allowance = max(0, percentile(historical_error_rates, q))
    return max(0, forecast * (1 - allowance))


def build_decision(decision_day: date) -> DecisionResponse:
    settings = get_settings()
    if not settings.first_decision_date <= decision_day <= settings.last_decision_date:
        raise ValueError("Decision date must be in January 2026")
    data = load_snapshot()
    delivery_day = decision_day + timedelta(days=1)
    forecast = data["forecasts"].get(decision_day.isoformat(), {})
    actual = data["actuals"].get(delivery_day.isoformat(), {})

    error_rates_by_hour: dict[int, list[float]] = {hour: [] for hour in range(24)}
    baseline_errors: list[float] = []
    daily_error_rates: list[float] = []
    daily_absolute_percentage_errors: list[float] = []
    for lag in range(1, settings.lookback_days + 1):
        historical_delivery = decision_day - timedelta(days=lag)
        historical_decision = historical_delivery - timedelta(days=1)
        old_forecast = data["forecasts"].get(historical_decision.isoformat(), {})
        old_actual = data["actuals"].get(historical_delivery.isoformat(), {})
        day_pairs: list[tuple[float, float]] = []
        for key, entry in old_forecast.items():
            if key not in old_actual:
                continue
            predicted, measured = entry["forecast_mw"], old_actual[key]
            error = predicted - measured
            if predicted > 0:
                error_rates_by_hour[int(key[11:13])].append(error / predicted)
            baseline_errors.append(error)
            day_pairs.append((predicted, measured))
        if len(day_pairs) == 24:
            daily_error = sum(predicted - measured for predicted, measured in day_pairs)
            forecast_energy = sum(predicted for predicted, _ in day_pairs)
            actual_energy = sum(measured for _, measured in day_pairs)
            if forecast_energy > 0:
                daily_error_rates.append(daily_error / forecast_energy)
            if actual_energy > 0:
                daily_absolute_percentage_errors.append(abs(daily_error) / actual_energy)

    points = []
    observed_errors = []
    for key, entry in sorted(forecast.items()):
        hour = int(key[11:13])
        error_rates = error_rates_by_hour[hour]
        predicted = entry["forecast_mw"]
        downside = planning_level(predicted, error_rates, settings.planning_coverage_target)
        upside = max(predicted, predicted * (1 - percentile(error_rates, 1 - settings.planning_coverage_target))) if error_rates else None
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
            history_count=len(error_rates),
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

    forecast_mwh = sum(p.forecast_mw for p in points)
    actual_mwh = sum(p.actual_mw for p in points if p.actual_mw is not None) if points else None
    planning_error_rate = max(0, percentile(daily_error_rates, settings.planning_coverage_target)) if daily_error_rates else None
    downside_mwh = planning_level(forecast_mwh, daily_error_rates, settings.planning_coverage_target)
    historical_daily_mape = (
        sum(daily_absolute_percentage_errors) / len(daily_absolute_percentage_errors)
        if daily_absolute_percentage_errors else None
    )
    covered = [p.actual_mw >= p.downside_mw for p in points if p.actual_mw is not None and p.downside_mw is not None]
    return DecisionResponse(
        decision_date=decision_day,
        delivery_date=delivery_day,
        cutoff_time=f"{decision_day.isoformat()}T{settings.decision_cutoff_hour_utc:02d}:00:00Z",
        source=data["source"],
        prepared_at=data["prepared_at"],
        forecast_mwh=forecast_mwh,
        confidence_score=max(0, min(100, round(100 * (1 - historical_daily_mape)))) if historical_daily_mape is not None else None,
        downside_mwh=downside_mwh,
        actual_mwh=actual_mwh,
        downside_coverage=sum(covered) / len(covered) if covered else None,
        risk=RiskContext(
            lookback_days=settings.lookback_days,
            completed_days=len(daily_error_rates),
            method="80th percentile of signed percentage forecast error from prior completed days; daily rates set the daily planning level and same-hour rates set the chart band",
            coverage_target=settings.planning_coverage_target,
            planning_error_rate=planning_error_rate,
            historical_daily_mape=historical_daily_mape,
            baseline=metrics(baseline_errors),
        ),
        realized=metrics(observed_errors),
        hours=points,
    )


@lru_cache(maxsize=31)
def build_overview(through: date = date(2026, 1, 31)) -> OverviewResponse:
    settings = get_settings()
    if not settings.first_decision_date <= through <= settings.last_decision_date:
        raise ValueError("Decision date must be in January 2026")
    decisions = [build_decision(date(2026, 1, day)) for day in range(settings.first_decision_date.day, through.day + 1)]
    errors = [hour.error_mw for decision in decisions for hour in decision.hours if hour.error_mw is not None]
    covered_days = [
        decision.actual_mwh >= decision.downside_mwh
        for decision in decisions
        if decision.actual_mwh is not None and decision.downside_mwh is not None
    ]
    return OverviewResponse(
        through_date=through,
        days=[DaySummary(
            decision_date=d.decision_date,
            delivery_date=d.delivery_date,
            forecast_mwh=d.forecast_mwh,
            actual_mwh=d.actual_mwh,
            mae_mw=d.realized.mae_mw if d.realized else None,
            downside_coverage=d.downside_coverage,
        ) for d in decisions],
        heatmap=[HeatmapPoint(decision_date=d.decision_date, hour=int(h.start_time[11:13]), error_mw=h.error_mw) for d in decisions for h in d.hours],
        mean_absolute_error_mw=sum(abs(x) for x in errors) / len(errors) if errors else None,
        mean_bias_mw=sum(errors) / len(errors) if errors else None,
        downside_coverage=sum(covered_days) / len(covered_days) if covered_days else None,
        evaluated_days=len(covered_days),
        evaluated_hours=len(errors),
    )
