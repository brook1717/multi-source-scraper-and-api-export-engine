from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class ScrapedRecord(Base):
    """Stores scraped data with idempotency guarantees."""

    __tablename__ = "scraped_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_url = Column(String, nullable=False, unique=True, index=True)
    data_hash = Column(String, nullable=False, unique=True)
    payload = Column(JSONB, nullable=False)
    scraped_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    status = Column(String, nullable=False, default="success")

    __table_args__ = (
        Index("ix_scraped_records_data_hash", "data_hash", unique=True),
    )

    def __repr__(self) -> str:
        return f"<ScrapedRecord(id={self.id}, source_url='{self.source_url}', status='{self.status}')>"
