"""Build a compact, reproducible snapshot from the two Elexon feeds."""

import asyncio
import json
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import httpx

from app.adapters.elexon import ElexonAdapter

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "january_2026.json"
FIRST_DECISION = date(2025, 11, 5)
LAST_DECISION = date(2026, 1, 31)


def dates_inclusive(first: date, last: date):
    day = first
    while day <= last:
        yield day
        day += timedelta(days=1)


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def freeze_forecast(rows: list[dict], decision_day: date) -> dict[str, dict]:
    """Latest available publication per target hour at 09:00 UTC."""
    cutoff = datetime.combine(decision_day, time(9), timezone.utc)
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


async def build_snapshot() -> dict:
    semaphore = asyncio.Semaphore(8)
    async with httpx.AsyncClient(timeout=45, follow_redirects=True) as client:
        source = ElexonAdapter(client)

        async def load_forecasts(day: date):
            async with semaphore:
                return day.isoformat(), await source.forecasts_published_on(day)

        async def load_actuals(day: date):
            async with semaphore:
                return day.isoformat(), await source.wind_actuals_on(day)

        forecast_days = list(dates_inclusive(FIRST_DECISION - timedelta(days=1), LAST_DECISION))
        actual_days = list(dates_inclusive(FIRST_DECISION + timedelta(days=1), LAST_DECISION + timedelta(days=1)))
        forecast_pairs = await asyncio.gather(*(load_forecasts(day) for day in forecast_days))
        actual_pairs = await asyncio.gather(*(load_actuals(day) for day in actual_days))

    published = dict(forecast_pairs)
    actual = dict(actual_pairs)
    frozen = {}
    for day in dates_inclusive(FIRST_DECISION, LAST_DECISION):
        rows = published.get((day - timedelta(days=1)).isoformat(), []) + published[day.isoformat()]
        frozen[day.isoformat()] = freeze_forecast(rows, day)

    hourly = {day: hourly_actuals(rows, date.fromisoformat(day)) for day, rows in actual.items()}
    for decision_day, hours in frozen.items():
        delivery_day = (date.fromisoformat(decision_day) + timedelta(days=1)).isoformat()
        measured = hourly[delivery_day]
        if len(hours) != 24 or len(measured) != 24 or set(hours) != set(measured):
            raise ValueError(f"Incomplete hourly Elexon data for decision {decision_day}")

    return {
        "source": "Elexon BMRS WINDFOR and FUELHH/WIND",
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "cutoff_utc": "09:00",
        "forecasts": frozen,
        "actuals": hourly,
    }


if __name__ == "__main__":
    snapshot = asyncio.run(build_snapshot())
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(snapshot, separators=(",", ":")))
    print(f"Saved {DATA_PATH} ({len(snapshot['forecasts'])} decisions)")
