from datetime import date, timedelta
from decimal import Decimal
from typing import Iterator

import boto3

from app.config import settings
from app.connectors.base import CostEntry


class AwsConnector:
    def __init__(self):
        self._client = boto3.client(
            "ce",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
        )

    def fetch(self, start: date, end: date) -> Iterator[CostEntry]:
        # Cost Explorer max range is 1 year; pagination handles large ranges
        response = self._client.get_cost_and_usage(
            TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
            Granularity="DAILY",
            GroupBy=[
                {"Type": "DIMENSION", "Key": "SERVICE"},
                {"Type": "DIMENSION", "Key": "REGION"},
            ],
            Metrics=["UnblendedCost"],
        )

        account_id = boto3.client("sts").get_caller_identity()["Account"]

        for result in response.get("ResultsByTime", []):
            day = date.fromisoformat(result["TimePeriod"]["Start"])
            for group in result.get("Groups", []):
                service = group["Keys"][0]
                region  = group["Keys"][1] if len(group["Keys"]) > 1 else ""
                amount  = Decimal(group["Metrics"]["UnblendedCost"]["Amount"])
                if amount == 0:
                    continue
                yield CostEntry(
                    provider="aws",
                    account_id=account_id,
                    service=service,
                    region=region,
                    resource_id="",
                    tags={},
                    cost_usd=amount,
                    usage_date=day,
                )
