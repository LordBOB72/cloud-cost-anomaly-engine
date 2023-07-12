import json
import logging
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.aws import AwsConnector
from app.connectors.gcp import GcpConnector
from app.connectors.azure import AzureConnector
from app.connectors.base import CostEntry
from app.db.session import SessionLocal

log = logging.getLogger(__name__)


async def run_ingestion(days_back: int = 1):
    """Pull yesterday's costs from all configured providers and upsert into cost_records."""
    end   = date.today()
    start = end - timedelta(days=days_back)

    entries: list[CostEntry] = []

    for connector_cls in [AwsConnector, GcpConnector, AzureConnector]:
        try:
            connector = connector_cls()
            entries.extend(connector.fetch(start, end))
        except Exception as e:
            log.error("ingestion failed for %s: %s", connector_cls.__name__, e)

    if not entries:
        log.info("no cost entries to ingest")
        return

    async with SessionLocal() as db:
        await _upsert(db, entries)
        await db.commit()

    log.info("ingested %d cost records", len(entries))


async def _upsert(db: AsyncSession, entries: list[CostEntry]):
    # bulk upsert — postgres doesn't like null here, coerce empty strings
    await db.execute(
        text("""
            INSERT INTO cost_records
              (provider, account_id, service, region, resource_id, tags, cost_usd, usage_date)
            VALUES
              (:provider, :account_id, :service, :region, :resource_id, :tags::jsonb, :cost_usd, :usage_date)
            ON CONFLICT (provider, account_id, service, region, usage_date)
            DO UPDATE SET cost_usd = EXCLUDED.cost_usd, ingested_at = NOW()
        """),
        [
            {
                "provider":    e.provider,
                "account_id":  e.account_id,
                "service":     e.service,
                "region":      e.region or "",
                "resource_id": e.resource_id or "",
                "tags":        json.dumps(e.tags),
                "cost_usd":    float(e.cost_usd),
                "usage_date":  e.usage_date.isoformat(),
            }
            for e in entries
        ],
    )
