"""Reproduce the December calibration and January backtest comparison."""

from datetime import date, timedelta

from app.services.decision_service import load_snapshot, percentile, planning_level


def daily_energy(snapshot: dict, decision_day: date) -> tuple[float, float] | None:
    forecast = snapshot["forecasts"].get(decision_day.isoformat(), {})
    actual = snapshot["actuals"].get((decision_day + timedelta(days=1)).isoformat(), {})
    if len(forecast) != 24 or set(forecast) != set(actual):
        return None
    return sum(entry["forecast_mw"] for entry in forecast.values()), sum(actual.values())


def evaluate(first: date, last: date, lookback_days: int, error_percentile: float, relative: bool) -> tuple[int, int, float, float]:
    snapshot = load_snapshot()
    covered = 0
    buffers: list[float] = []
    shortfalls: list[float] = []
    day = first
    while day <= last:
        current = daily_energy(snapshot, day)
        # The newest historical delivery day is yesterday, so its buying
        # decision was two calendar days before today's buying decision.
        history = [daily_energy(snapshot, day - timedelta(days=lag + 1)) for lag in range(1, lookback_days + 1)]
        if current is None or any(pair is None for pair in history):
            raise ValueError(f"Incomplete calibration history for {day}")
        forecast, actual = current
        errors = [old_forecast - old_actual for old_forecast, old_actual in history]
        if relative:
            rates = [error / old_forecast for error, (old_forecast, _) in zip(errors, history)]
            level = planning_level(forecast, rates, error_percentile)
        else:
            level = max(0, forecast - max(0, percentile(errors, error_percentile)))
        covered += actual >= level
        buffers.append((forecast - level) / 1000)
        shortfalls.append(max(0, level - actual) / 1000)
        day += timedelta(days=1)
    return len(buffers), covered, sum(buffers) / len(buffers), sum(shortfalls) / len(shortfalls)


if __name__ == "__main__":
    candidates = [
        ("Previous: 56-day absolute / 75%", 56, 0.75, False),
        ("Selected: 21-day percentage / 80%", 21, 0.80, True),
        ("Longer: 56-day percentage / 80%", 56, 0.80, True),
        ("Cautious: 21-day percentage / 85%", 21, 0.85, True),
    ]
    for name, days, quantile, relative in candidates:
        print(name)
        for label, first, last in [
            ("December validation", date(2025, 12, 1), date(2025, 12, 31)),
            ("January backtest", date(2026, 1, 1), date(2026, 1, 31)),
        ]:
            count, covered, buffer, shortfall = evaluate(first, last, days, quantile, relative)
            print(f"  {label}: {covered}/{count} days covered; {buffer:.1f} GWh mean buffer; {shortfall:.1f} GWh mean shortfall")
