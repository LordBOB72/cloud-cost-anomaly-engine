from datetime import date
from decimal import Decimal
from typing import Iterator

from azure.identity import ClientSecretCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import (
    QueryDefinition, QueryTimePeriod, TimeframeType,
    QueryDataset, QueryAggregation, QueryGrouping
)

from app.config import settings
from app.connectors.base import CostEntry


class AzureConnector:
    def _client(self):
        cred = ClientSecretCredential(
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id,
            client_secret=settings.azure_client_secret,
        )
        return CostManagementClient(cred)

    def fetch(self, start: date, end: date) -> Iterator[CostEntry]:
        if not settings.azure_subscription_id:
            return

        client = self._client()
        scope = f"/subscriptions/{settings.azure_subscription_id}"

        query = QueryDefinition(
            type="ActualCost",
            timeframe=TimeframeType.CUSTOM,
            time_period=QueryTimePeriod(from_property=start, to=end),
            dataset=QueryDataset(
                granularity="Daily",
                aggregation={"totalCost": QueryAggregation(name="Cost", function="Sum")},
                grouping=[
                    QueryGrouping(type="Dimension", name="ServiceName"),
                    QueryGrouping(type="Dimension", name="ResourceLocation"),
                ],
            ),
        )

        result = client.query.usage(scope, query)
        cols = [c.name for c in result.columns]

        for row in result.rows:
            r = dict(zip(cols, row))
            amount = Decimal(str(r.get("Cost", 0)))
            if amount == 0:
                continue
            # Azure returns date as int YYYYMMDD
            raw_date = str(r.get("UsageDate", str(start).replace("-", "")))
            usage_date = date(int(raw_date[:4]), int(raw_date[4:6]), int(raw_date[6:8]))
            yield CostEntry(
                provider="azure",
                account_id=settings.azure_subscription_id,
                service=r.get("ServiceName", "unknown"),
                region=r.get("ResourceLocation", ""),
                resource_id="",
                tags={},
                cost_usd=amount,
                usage_date=usage_date,
            )
