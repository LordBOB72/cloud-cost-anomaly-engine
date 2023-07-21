import logging
from datetime import date, timedelta

from sqlalchemy import text

from app.db.session import SessionLocal

log = logging.getLogger(__name__)


async def run_recommendations():
    """
    Very simple heuristic pass — flags services with zero spend in the last
    7 days but non-zero spend in the prior 30, as potentially idle.
    Reserved instance and right-sizing hints would come from provider-specific
    APIs (AWS Trusted Advisor, GCP Recommender, Azure Advisor).
    """
    async with SessionLocal() as db:
        today    = date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=37)

        # idle: had spend 8-37 days ago but nothing in the last 7
        idle_rows = await db.execute(
            text("""
                WITH recent AS (
                    SELECT provider, account_id, service, region
                    FROM cost_records
                    WHERE usage_date >= :week_ago
                    GROUP BY provider, account_id, service, region
                ),
                older AS (
                    SELECT provider, account_id, service, region,
                           SUM(cost_usd) AS total
                    FROM cost_records
                    WHERE usage_date BETWEEN :month_ago AND :week_ago
                    GROUP BY provider, account_id, service, region
                )
                SELECT o.provider, o.account_id, o.service, o.region, o.total
                FROM older o
                LEFT JOIN recent r USING (provider, account_id, service, region)
                WHERE r.provider IS NULL
                  AND o.total > 5
            """),
            {"week_ago": week_ago.isoformat(), "month_ago": month_ago.isoformat()},
        )

        recs = []
        for row in idle_rows.mappings():
            recs.append({
                "provider":    row["provider"],
                "account_id":  row["account_id"],
                "resource_id": f"{row['service']}/{row['region']}",
                "category":    "idle",
                "description": (
                    f"{row['service']} in {row['region'] or 'global'} had no spend "
                    f"in the last 7 days but cost ${float(row['total']):.2f} in the prior 30."
                ),
                "savings_usd": float(row["total"]) / 30,  # rough monthly equivalent
            })

        if recs:
            await db.execute(
                text("""
                    INSERT INTO recommendations
                      (provider, account_id, resource_id, category, description, savings_usd)
                    VALUES
                      (:provider, :account_id, :resource_id, :category, :description, :savings_usd)
                    ON CONFLICT DO NOTHING
                """),
                recs,
            )
            await db.commit()
            log.info("generated %d recommendations", len(recs))
