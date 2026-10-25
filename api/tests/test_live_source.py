import unittest
from datetime import date, timedelta

import httpx

from app.adapters.elexon import ElexonAdapter
from app.services.decision_service import DecisionService
from app.settings import get_settings


class ElexonCacheTests(unittest.IsolatedAsyncioTestCase):
    async def test_same_dataset_and_day_reuses_one_provider_call(self):
        requests = []

        def respond(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(200, json={"data": [{"generation": 1000}]})

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            source = ElexonAdapter(client)
            day = date(2026, 1, 14)
            self.assertEqual(await source.forecasts_published_on(day), await source.forecasts_published_on(day))
            self.assertEqual(await source.wind_actuals_on(day), await source.wind_actuals_on(day))
            self.assertEqual(len(requests), 2)
            await source.forecasts_published_on(day + timedelta(days=1))
            self.assertEqual(len(requests), 3)
            await source.close_cache()


class FakeGenerationSource:
    async def forecasts_published_on(self, day: date) -> list[dict]:
        delivery = day + timedelta(days=1)
        return [
            {
                "startTime": f"{delivery.isoformat()}T{hour:02d}:00:00Z",
                "publishTime": f"{day.isoformat()}T08:30:00Z",
                "generation": 2000 + hour,
            }
            for hour in range(24)
        ]

    async def wind_actuals_on(self, day: date) -> list[dict]:
        return [
            {
                "startTime": f"{day.isoformat()}T{hour:02d}:{minute:02d}:00Z",
                "fuelType": "WIND",
                "generation": 1900 + hour,
            }
            for hour in range(24)
            for minute in (0, 30)
        ]


class LiveDecisionTests(unittest.IsolatedAsyncioTestCase):
    async def test_service_builds_a_decision_from_live_source_rows(self):
        settings = get_settings().model_copy(update={"lookback_days": 1})
        service = DecisionService(FakeGenerationSource(), settings)
        decision = await service.get_decision(date(2026, 1, 1))
        self.assertEqual(decision.risk.completed_days, 1)
        self.assertEqual(len(decision.hours), 24)
        self.assertEqual(decision.hours[0].forecast_mw, 2000)
        self.assertEqual(decision.hours[0].actual_mw, 1900)
        self.assertEqual(decision.hours[0].error_mw, 100)
        self.assertTrue(decision.retrieved_at)
