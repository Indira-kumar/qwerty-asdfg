"""Validated application configuration, loaded once from the environment."""

from datetime import date
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        extra="ignore",
        frozen=True,
    )

    elexon_base_url: str = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:8088"]
    elexon_timeout_seconds: float = Field(default=45.0, gt=0)
    elexon_concurrency: int = Field(default=8, ge=1)
    decision_cutoff_hour_utc: int = Field(default=9, ge=0, le=23)
    lookback_days: int = Field(default=21, ge=1)
    planning_coverage_target: float = Field(default=0.8, gt=0, lt=1)
    first_decision_date: date = date(2026, 1, 1)
    last_decision_date: date = date(2026, 1, 31)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
