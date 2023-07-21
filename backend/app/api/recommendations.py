from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()


@router.get("/recommendations")
async def list_recommendations(
    provider: str | None = None,
    category: str | None = None,
    dismissed: bool = False,
    db: AsyncSession = Depends(get_db),
):
    filters = "WHERE dismissed = :dismissed"
    params: dict = {"dismissed": dismissed}
    if provider:
        filters += " AND provider = :provider"
        params["provider"] = provider
    if category:
        filters += " AND category = :category"
        params["category"] = category

    rows = await db.execute(
        text(f"""
            SELECT * FROM recommendations
            {filters}
            ORDER BY savings_usd DESC NULLS LAST
        """),
        params,
    )
    return [dict(r) for r in rows.mappings()]


@router.post("/recommendations/{rec_id}/dismiss", status_code=204)
async def dismiss(rec_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(
        text("UPDATE recommendations SET dismissed = true WHERE id = :id"),
        {"id": rec_id},
    )
    await db.commit()


@router.post("/recommendations/refresh", status_code=202)
async def refresh_recommendations(background: BackgroundTasks):
    from app.recommendations.engine import run_recommendations
    background.add_task(run_recommendations)
    return {"status": "triggered"}
