from datetime import date

import httpx
from fastapi import APIRouter, HTTPException, Request, status as HTTP_STATUS

from app.schemas.decision_schema import DecisionResponse, OverviewResponse
from app.services.prepare_data import DataUnavailableError

router = APIRouter(prefix="/api/decisions", tags=["decisions"])


@router.get("", response_model=OverviewResponse)
async def get_overview(request: Request, through: date = date(2026, 1, 31)) -> OverviewResponse:
    try:
        return await request.app.state.decision_service.get_overview(through)
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except (httpx.HTTPError, DataUnavailableError) as exc:
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Elexon data is temporarily unavailable",
        ) from exc


@router.get("/{decision_date}", response_model=DecisionResponse)
async def get_decision(request: Request, decision_date: date) -> DecisionResponse:
    try:
        return await request.app.state.decision_service.get_decision(decision_date)
    except ValueError as exc:
        raise HTTPException(status_code=HTTP_STATUS.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except (httpx.HTTPError, DataUnavailableError) as exc:
        raise HTTPException(
            status_code=HTTP_STATUS.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Elexon data is temporarily unavailable",
        ) from exc
