from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class CostEntry:
    """Normalised cost row — every connector produces these."""
    provider: str
    account_id: str
    service: str
    region: str
    resource_id: str
    tags: dict
    cost_usd: Decimal
    usage_date: date
