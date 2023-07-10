from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.session import init_db
from app.api import costs, anomalies, budgets, recommendations, ingestion
from app.ingestion.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield


app = FastAPI(title="Cloud Cost Anomaly Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(costs.router,           prefix="/api/v1", tags=["costs"])
app.include_router(anomalies.router,       prefix="/api/v1", tags=["anomalies"])
app.include_router(budgets.router,         prefix="/api/v1", tags=["budgets"])
app.include_router(recommendations.router, prefix="/api/v1", tags=["recommendations"])
app.include_router(ingestion.router,       prefix="/api/v1", tags=["ingestion"])


@app.get("/health")
async def health():
    return {"ok": True}
