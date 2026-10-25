from datetime import date

from pydantic import BaseModel


class Metrics(BaseModel):
    mae_mw: float
    bias_mw: float
    rmse_mw: float
    observations: int


class RiskContext(BaseModel):
    lookback_days: int
    completed_days: int
    method: str
    baseline: Metrics | None


class HourPoint(BaseModel):
    start_time: str
    forecast_mw: float
    downside_mw: float | None
    upside_mw: float | None
    actual_mw: float | None
    error_mw: float | None
    publish_time: str
    history_count: int


class DecisionResponse(BaseModel):
    decision_date: date
    delivery_date: date
    cutoff_time: str
    source: str
    prepared_at: str
    forecast_mwh: float
    downside_mwh: float | None
    actual_mwh: float | None
    downside_coverage: float | None
    risk: RiskContext
    realized: Metrics | None
    hours: list[HourPoint]


class DaySummary(BaseModel):
    decision_date: date
    delivery_date: date
    forecast_mwh: float
    actual_mwh: float | None
    mae_mw: float | None
    downside_coverage: float | None


class HeatmapPoint(BaseModel):
    decision_date: date
    hour: int
    error_mw: float | None


class OverviewResponse(BaseModel):
    days: list[DaySummary]
    heatmap: list[HeatmapPoint]
    january_mae_mw: float | None
    january_bias_mw: float | None
    downside_coverage: float | None
    evaluated_hours: int
