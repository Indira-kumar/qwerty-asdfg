from datetime import date

from fastapi import APIRouter, HTTPException

from app.schemas.decision import DecisionResponse, OverviewResponse
from app.services.decision import build_decision, build_overview

router = APIRouter(prefix="/api/decisions", tags=["decisions"])


@router.get("", response_model=OverviewResponse)
def get_overview() -> OverviewResponse:
    try:
        return build_overview()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Elexon snapshot has not been prepared") from exc


@router.get("/{decision_date}", response_model=DecisionResponse)
def get_decision(decision_date: date) -> DecisionResponse:
    try:
        return build_decision(decision_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Elexon snapshot has not been prepared") from exc
