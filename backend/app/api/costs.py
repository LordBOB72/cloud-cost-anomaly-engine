from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()


@router.get("/costs/summary")
async def cost_summary(
    provider: str | None = None,
    account_id: str | None = None,
    start: date = Query(default=None),
    end: date = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Total spend grouped by provider+service for the requested period."""
    from datetime import timedelta
    if not end:
        end = date.today()
    if not start:
        start = end - timedelta(days=30)

    filters = "WHERE usage_date BETWEEN :start AND :end"
    params: dict = {"start": start.isoformat(), "end": end.isoformat()}
    if provider:
        filters += " AND provider = :provider"
        params["provider"] = provider
    if account_id:
        filters += " AND account_id = :account_id"
        params["account_id"] = account_id

    rows = await db.execute(
        text(f"""
            SELECT provider, account_id, service, region,
                   SUM(cost_usd) AS total_cost
            FROM cost_records
            {filters}
            GROUP BY provider, account_id, service, region
            ORDER BY total_cost DESC
            LIMIT 200
        """),
        params,
    )
    return [dict(r) for r in rows.mappings()]


@router.get("/costs/daily")
async def daily_costs(
    provider: str | None = None,
    account_id: str | None = None,
    service: str | None = None,
    start: date = Query(default=None),
    end: date = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    from datetime import timedelta
    if not end:
        end = date.today()
    if not start:
        start = end - timedelta(days=30)

    filters = "WHERE usage_date BETWEEN :start AND :end"
    params: dict = {"start": start.isoformat(), "end": end.isoformat()}
    if provider:
        filters += " AND provider = :provider"
        params["provider"] = provider
    if account_id:
        filters += " AND account_id = :account_id"
        params["account_id"] = account_id
    if service:
        filters += " AND service = :service"
        params["service"] = service

    rows = await db.execute(
        text(f"""
            SELECT usage_date, provider, SUM(cost_usd) AS total_cost
            FROM cost_records
            {filters}
            GROUP BY usage_date, provider
            ORDER BY usage_date
        """),
        params,
    )
    return [dict(r) for r in rows.mappings()]


@router.get("/costs/accounts")
async def list_accounts(db: AsyncSession = Depends(get_db)):
    rows = await db.execute(
        text("SELECT DISTINCT provider, account_id FROM cost_records ORDER BY provider, account_id")
    )
    return [dict(r) for r in rows.mappings()]
