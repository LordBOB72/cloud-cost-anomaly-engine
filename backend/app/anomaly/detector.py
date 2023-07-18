import logging
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import text

from app.config import settings
from app.db.session import SessionLocal

log = logging.getLogger(__name__)


async def run_detection():
    """
    For each (provider, account, service, region) group, compute a rolling
    mean + stddev over the past N days and flag any day that exceeds
    mean + (z_threshold * stddev).
    """
    async with SessionLocal() as db:
        baseline_end   = date.today() - timedelta(days=1)
        baseline_start = baseline_end - timedelta(days=settings.baseline_days)

        rows = await db.execute(
            text("""
                SELECT
                    provider, account_id, service, region, usage_date,
                    cost_usd,
                    AVG(cost_usd) OVER w  AS mean,
                    STDDEV(cost_usd) OVER w AS stddev
                FROM cost_records
                WHERE usage_date BETWEEN :start AND :end
                WINDOW w AS (
                    PARTITION BY provider, account_id, service, region
                    ORDER BY usage_date
                    ROWS BETWEEN :window PRECEDING AND 1 PRECEDING
                )
            """),
            {
                "start":  baseline_start.isoformat(),
                "end":    baseline_end.isoformat(),
                "window": settings.baseline_days,
            },
        )

        anomalies = []
        for row in rows.mappings():
            mean   = row["mean"]
            stddev = row["stddev"]
            cost   = row["cost_usd"]

            if mean is None or stddev is None or float(stddev) == 0:
                continue

            z = (float(cost) - float(mean)) / float(stddev)
            if z < settings.anomaly_z_threshold:
                continue

            # confidence: cap at 99, scale linearly between threshold and threshold+3
            confidence = min(99.0, ((z - settings.anomaly_z_threshold) / 3.0) * 100)

            anomalies.append({
                "provider":      row["provider"],
                "account_id":    row["account_id"],
                "service":       row["service"],
                "region":        row["region"] or "",
                "usage_date":    row["usage_date"],
                "actual_cost":   float(cost),
                "expected_cost": float(mean),
                "stddev":        float(stddev),
                "confidence":    round(confidence, 2),
            })

        if anomalies:
            await db.execute(
                text("""
                    INSERT INTO anomalies
                      (provider, account_id, service, region, usage_date,
                       actual_cost, expected_cost, stddev, confidence)
                    VALUES
                      (:provider, :account_id, :service, :region, :usage_date,
                       :actual_cost, :expected_cost, :stddev, :confidence)
                    ON CONFLICT DO NOTHING
                """),
                anomalies,
            )
            await db.commit()
            log.info("detected %d anomalies", len(anomalies))

            await _alert_if_needed(anomalies)


async def _alert_if_needed(anomalies: list[dict]):
    import httpx
    from app.config import settings

    if not settings.alert_webhook_url:
        return

    high = [a for a in anomalies if a["confidence"] >= 80]
    if not high:
        return

    lines = [
        f"• {a['provider'].upper()} {a['service']} ({a['region']}) on {a['usage_date']}: "
        f"${a['actual_cost']:.2f} vs expected ${a['expected_cost']:.2f} "
        f"({a['confidence']:.0f}% confidence)"
        for a in high[:10]
    ]
    text_body = "🔴 *Cost anomalies detected*\n" + "\n".join(lines)

    # retry up to 3 times before giving up
    for attempt in range(1, 4):
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                r = await client.post(settings.alert_webhook_url, json={"text": text_body})
                if r.status_code < 300:
                    return
        except Exception as e:
            log.warning("alert attempt %d failed: %s", attempt, e)
