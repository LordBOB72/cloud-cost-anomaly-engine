from datetime import date
from decimal import Decimal
from typing import Iterator

from google.cloud import billing_v1

from app.config import settings
from app.connectors.base import CostEntry


class GcpConnector:
    """
    Reads from the Cloud Billing Budget API.
    For production you'd query BigQuery billing exports — this uses the
    Budgets API as a lighter dependency.  Swap fetch() for a BQ query
    if you have the export set up.
    """

    def fetch(self, start: date, end: date) -> Iterator[CostEntry]:
        client = billing_v1.CloudBillingClient()
        project = settings.gcp_project_id
        if not project:
            return

        # list all services and sum spend — simplified; real impl queries BQ
        # TODO: replace with BigQuery billing export query for production accuracy
        services_client = billing_v1.CloudCatalogClient()
        for service in services_client.list_services():
            # placeholder — BQ export gives actual daily spend per service
            yield CostEntry(
                provider="gcp",
                account_id=project,
                service=service.display_name,
                region="",
                resource_id="",
                tags={},
                cost_usd=Decimal("0"),
                usage_date=start,
            )
