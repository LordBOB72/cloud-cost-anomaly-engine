from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import StreamingResponse
import io
import csv

from app.ingestion.pipeline import run_ingestion
from app.anomaly.detector import run_detection

router = APIRouter()


@router.post("/ingestion/trigger", status_code=202)
async def trigger_ingestion(days_back: int = 1, background: BackgroundTasks = None):
    """Manually kick off a billing ingestion for the last N days."""
    background.add_task(run_ingestion, days_back)
    background.add_task(run_detection)
    return {"status": "triggered", "days_back": days_back}


@router.get("/export/anomalies.csv")
async def export_anomalies_csv(provider: str | None = None):
    from app.db.session import SessionLocal
    from sqlalchemy import text

    async with SessionLocal() as db:
        params: dict = {}
        where = ""
        if provider:
            where = "WHERE provider = :provider"
            params["provider"] = provider

        rows = await db.execute(
            text(f"""
                SELECT provider, account_id, service, region, usage_date,
                       actual_cost, expected_cost, confidence, detected_at
                FROM anomalies {where}
                ORDER BY detected_at DESC
            """),
            params,
        )
        data = rows.mappings().all()

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=[
        "provider", "account_id", "service", "region", "usage_date",
        "actual_cost", "expected_cost", "confidence", "detected_at",
    ])
    writer.writeheader()
    for row in data:
        writer.writerow(dict(row))

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=anomalies.csv"},
    )
