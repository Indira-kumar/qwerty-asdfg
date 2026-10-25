"""Align live Elexon forecasts and actuals into decision-time hourly data."""

import asyncio
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone

from app.adapters.base import GenerationSource
from app.settings import Settings, get_settings


class DataUnavailableError(RuntimeError):
    """Elexon did not return a complete delivery day."""


def dates_inclusive(first: date, last: date):
    day = first
    while day <= last:
        yield day
        day += timedelta(days=1)


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def freeze_forecast(
    rows: list[dict], decision_day: date, cutoff_hour_utc: int | None = None
) -> dict[str, dict]:
    """Latest available publication per target hour at 09:00 UTC."""
    cutoff_hour = cutoff_hour_utc if cutoff_hour_utc is not None else get_settings().decision_cutoff_hour_utc
    cutoff = datetime.combine(decision_day, time(cutoff_hour), timezone.utc)
    delivery_day = decision_day + timedelta(days=1)
    chosen: dict[str, dict] = {}
    for row in rows:
        target = parse_timestamp(row["startTime"])
        published = parse_timestamp(row["publishTime"])
        if target.date() != delivery_day or published > cutoff:
            continue
        key = target.isoformat().replace("+00:00", "Z")
        if key not in chosen or published > parse_timestamp(chosen[key]["publish_time"]):
            chosen[key] = {"forecast_mw": float(row["generation"]), "publish_time": row["publishTime"]}
    return dict(sorted(chosen.items()))


def hourly_actuals(rows: list[dict], day: date) -> dict[str, float]:
    buckets: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row.get("fuelType") != "WIND":
            continue
        start = parse_timestamp(row["startTime"])
        if start.date() != day:
            continue
        hour = start.replace(minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")
        buckets[hour].append(float(row["generation"]))
    return {hour: sum(values) / 2 for hour, values in sorted(buckets.items()) if len(values) == 2}


async def load_generation_data(
    source: GenerationSource,
    first_decision: date,
    last_decision: date,
    settings: Settings,
) -> dict:
    """Fetch each publication/settlement day once, then align the requested span."""
    first_required_decision = first_decision - timedelta(days=settings.lookback_days + 1)
    semaphore = asyncio.Semaphore(settings.elexon_concurrency)

    async def load_forecasts(day: date):
        async with semaphore:
            return day.isoformat(), await source.forecasts_published_on(day)

    async def load_actuals(day: date):
        async with semaphore:
            return day.isoformat(), await source.wind_actuals_on(day)

    forecast_days = list(dates_inclusive(first_required_decision - timedelta(days=1), last_decision))
    # Settlement dates and UTC days differ during British Summer Time.
    # The next settlement date can contain the final UTC hour of a day.
    actual_days = list(dates_inclusive(first_required_decision + timedelta(days=1), last_decision + timedelta(days=2)))
    forecast_pairs, actual_pairs = await asyncio.gather(
        asyncio.gather(*(load_forecasts(day) for day in forecast_days)),
        asyncio.gather(*(load_actuals(day) for day in actual_days)),
    )

    published = dict(forecast_pairs)
    actual = dict(actual_pairs)
    frozen = {}
    for day in dates_inclusive(first_required_decision, last_decision):
        rows = published.get((day - timedelta(days=1)).isoformat(), []) + published[day.isoformat()]
        frozen[day.isoformat()] = freeze_forecast(rows, day, settings.decision_cutoff_hour_utc)

    hourly = {
        day.isoformat(): hourly_actuals(
            actual[day.isoformat()] + actual[(day + timedelta(days=1)).isoformat()], day
        )
        for day in dates_inclusive(first_required_decision + timedelta(days=1), last_decision + timedelta(days=1))
    }
    for decision_day, hours in frozen.items():
        delivery_day = (date.fromisoformat(decision_day) + timedelta(days=1)).isoformat()
        measured = hourly[delivery_day]
        if len(hours) != 24 or len(measured) != 24 or set(hours) != set(measured):
            raise DataUnavailableError(f"Incomplete hourly Elexon data for decision {decision_day}")

    return {
        "source": "Elexon BMRS WINDFOR and FUELHH/WIND",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "cutoff_utc": f"{settings.decision_cutoff_hour_utc:02d}:00",
        "forecasts": frozen,
        "actuals": hourly,
    }
