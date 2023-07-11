from sqlalchemy import Column, String, Numeric, Date, DateTime, Boolean, Text, JSON, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.db.session import Base


class CostRecord(Base):
    __tablename__ = "cost_records"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider    = Column(String(10), nullable=False)
    account_id  = Column(String(128), nullable=False)
    service     = Column(String(256), nullable=False)
    region      = Column(String(64), default="")
    resource_id = Column(String(512))
    tags        = Column(JSON, default=dict)
    cost_usd    = Column(Numeric(14, 4), nullable=False)
    usage_date  = Column(Date, nullable=False)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("provider", "account_id", "service", "region", "usage_date",
                         name="uq_cost_records_key"),
    )


class Anomaly(Base):
    __tablename__ = "anomalies"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider        = Column(String(10), nullable=False)
    account_id      = Column(String(128), nullable=False)
    service         = Column(String(256), nullable=False)
    region          = Column(String(64))
    usage_date      = Column(Date, nullable=False)
    actual_cost     = Column(Numeric(14, 4), nullable=False)
    expected_cost   = Column(Numeric(14, 4), nullable=False)
    stddev          = Column(Numeric(14, 4))
    confidence      = Column(Numeric(5, 2))
    resolved        = Column(Boolean, default=False)
    detected_at     = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("provider", "account_id", "service", "region", "usage_date",
                         name="uq_anomaly_key"),
    )


class Budget(Base):
    __tablename__ = "budgets"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name        = Column(String(256), nullable=False, unique=True)
    provider    = Column(String(10))
    account_id  = Column(String(128))
    tag_key     = Column(String(128))
    tag_value   = Column(String(256))
    amount_usd  = Column(Numeric(14, 2), nullable=False)
    period      = Column(String(10), default="monthly")
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


class Recommendation(Base):
    __tablename__ = "recommendations"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider    = Column(String(10), nullable=False)
    account_id  = Column(String(128))
    resource_id = Column(String(512))
    category    = Column(String(64))
    description = Column(Text)
    savings_usd = Column(Numeric(14, 2))
    dismissed   = Column(Boolean, default=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
