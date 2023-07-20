from datetime import date, timedelta
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.db.session import get_db

router = APIRouter()


class BudgetCreate(BaseModel):
    name: str
    provider: str | None = None
    account_id: str | None = None
    tag_key: str | None = None
    tag_value: str | None = None
    amount_usd: Decimal
    period: str = "monthly"


@router.get("/budgets")
async def list_budgets(db: AsyncSession = Depends(get_db)):
    rows = await db.execute(text("SELECT * FROM budgets ORDER BY name"))
    budgets = [dict(r) for r in rows.mappings()]

    # annotate each budget with current burn
    for b in budgets:
        burn = await _current_burn(db, b)
        b["current_spend"] = float(burn)
        b["burn_pct"] = round(float(burn) / float(b["amount_usd"]) * 100, 1) if b["amount_usd"] else 0

    return budgets


@router.post("/budgets", status_code=201)
async def create_budget(body: BudgetCreate, db: AsyncSession = Depends(get_db)):
    row = await db.execute(
        text("""
            INSERT INTO budgets (name, provider, account_id, tag_key, tag_value, amount_usd, period)
            VALUES (:name, :provider, :account_id, :tag_key, :tag_value, :amount_usd, :period)
            RETURNING id
        """),
        body.model_dump(),
    )
    await db.commit()
    return {"id": str(row.scalar())}


@router.delete("/budgets/{budget_id}", status_code=204)
async def delete_budget(budget_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(text("DELETE FROM budgets WHERE id = :id"), {"id": budget_id})
    await db.commit()


async def _current_burn(db: AsyncSession, budget: dict) -> Decimal:
    today  = date.today()
    # monthly = current month-to-date, quarterly = current quarter-to-date
    if budget["period"] == "monthly":
        start = today.replace(day=1)
    else:
        q_start_month = ((today.month - 1) // 3) * 3 + 1
        start = today.replace(month=q_start_month, day=1)

    filters = "WHERE usage_date >= :start"
    params: dict = {"start": start.isoformat()}
    if budget.get("provider"):
        filters += " AND provider = :provider"
        params["provider"] = budget["provider"]
    if budget.get("account_id"):
        filters += " AND account_id = :account_id"
        params["account_id"] = budget["account_id"]
    if budget.get("tag_key") and budget.get("tag_value"):
        filters += " AND tags->>:tag_key = :tag_value"
        params["tag_key"]   = budget["tag_key"]
        params["tag_value"] = budget["tag_value"]

    result = await db.execute(
        text(f"SELECT COALESCE(SUM(cost_usd), 0) FROM cost_records {filters}"),
        params,
    )
    return result.scalar() or Decimal(0)
