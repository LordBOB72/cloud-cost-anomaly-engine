from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()


@router.get("/anomalies")
async def list_anomalies(
    provider: str | None = None,
    resolved: bool = False,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    filters = "WHERE resolved = :resolved"
    params: dict = {"resolved": resolved, "limit": min(limit, 500)}
    if provider:
        filters += " AND provider = :provider"
        params["provider"] = provider

    rows = await db.execute(
        text(f"""
            SELECT id, provider, account_id, service, region, usage_date,
                   actual_cost, expected_cost, stddev, confidence, resolved, detected_at
            FROM anomalies
            {filters}
            ORDER BY confidence DESC, detected_at DESC
            LIMIT :limit
        """),
        params,
    )
    return [dict(r) for r in rows.mappings()]


@router.post("/anomalies/{anomaly_id}/resolve")
async def resolve_anomaly(anomaly_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(
        text("UPDATE anomalies SET resolved = true WHERE id = :id"),
        {"id": anomaly_id},
    )
    await db.commit()
    return {"status": "resolved"}


@router.post("/anomalies/detect", status_code=202)
async def trigger_detection(background: BackgroundTasks):
    """Manual trigger for anomaly detection — useful after a fresh ingestion."""
    from app.anomaly.detector import run_detection
    background.add_task(run_detection)
    return {"status": "triggered"}
