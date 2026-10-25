from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.elexon import ElexonAdapter
from app.routers.decision_router import router as decisions_router
from app.services.decision_service import DecisionService
from app.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    async with httpx.AsyncClient(
        timeout=settings.elexon_timeout_seconds, follow_redirects=True
    ) as client:
        source = ElexonAdapter(client)
        app.state.decision_service = DecisionService(source, settings)
        yield
        await source.close_cache()


app = FastAPI(title="Windward API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().allowed_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(decisions_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
