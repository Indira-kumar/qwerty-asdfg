from datetime import date, timedelta

import httpx
from async_lru import alru_cache

from app.adapters.base import GenerationSource
from app.settings import get_settings


class ElexonAdapter(GenerationSource):
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        settings = get_settings()
        self._cached_forecasts = alru_cache(
            maxsize=settings.elexon_cache_maxsize,
            ttl=settings.elexon_cache_ttl_seconds,
        )(self._fetch_forecasts_published_on)
        self._cached_actuals = alru_cache(
            maxsize=settings.elexon_cache_maxsize,
            ttl=settings.elexon_cache_ttl_seconds,
        )(self._fetch_wind_actuals_on)

    async def _get(self, dataset: str, params: dict[str, str]) -> list[dict]:
        base_url = get_settings().elexon_base_url.rstrip("/")
        response = await self.client.get(f"{base_url}/{dataset}/stream", params=params)
        response.raise_for_status()
        payload = response.json()
        return payload["data"] if isinstance(payload, dict) else payload

    async def forecasts_published_on(self, day: date) -> list[dict]:
        return await self._cached_forecasts(day)

    async def _fetch_forecasts_published_on(self, day: date) -> list[dict]:
        return await self._get(
            "WINDFOR",
            {
                "publishDateTimeFrom": f"{day.isoformat()}T00:00:00Z",
                "publishDateTimeTo": f"{(day + timedelta(days=1)).isoformat()}T00:00:00Z",
            },
        )

    async def wind_actuals_on(self, day: date) -> list[dict]:
        return await self._cached_actuals(day)

    async def _fetch_wind_actuals_on(self, day: date) -> list[dict]:
        return await self._get(
            "FUELHH",
            {
                "settlementDateFrom": day.isoformat(),
                "settlementDateTo": day.isoformat(),
                "fuelType": "WIND",
            },
        )

    async def close_cache(self) -> None:
        await self._cached_forecasts.cache_close()
        await self._cached_actuals.cache_close()
