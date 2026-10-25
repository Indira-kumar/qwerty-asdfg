from abc import ABC, abstractmethod
from datetime import date


class GenerationSource(ABC):
    """Boundary around the external generation data provider."""

    @abstractmethod
    async def forecasts_published_on(self, day: date) -> list[dict]: ...

    @abstractmethod
    async def wind_actuals_on(self, day: date) -> list[dict]: ...
