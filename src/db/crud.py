import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import ScrapedRecord
from src.logger import setup_logger

logger = setup_logger(__name__)


def _compute_hash(url: str, payload: dict) -> str:
    """Generate a deterministic SHA-256 hash from the URL and payload."""
    raw = json.dumps({"url": url, "payload": payload}, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def upsert_record(
    session: AsyncSession,
    url: str,
    payload: dict,
    status: str = "success",
) -> ScrapedRecord:
    """Insert or update a scraped record using PostgreSQL ON CONFLICT.

    Idempotent: if a record with the same source_url exists, it updates
    the payload, data_hash, scraped_at, and status. Otherwise it inserts
    a new row.
    """
    now = datetime.now(timezone.utc)
    data_hash = _compute_hash(url, payload)

    stmt = pg_insert(ScrapedRecord).values(
        source_url=url,
        data_hash=data_hash,
        payload=payload,
        scraped_at=now,
        status=status,
    )

    stmt = stmt.on_conflict_do_update(
        index_elements=["source_url"],
        set_={
            "payload": stmt.excluded.payload,
            "data_hash": stmt.excluded.data_hash,
            "scraped_at": stmt.excluded.scraped_at,
            "status": stmt.excluded.status,
        },
    )

    await session.execute(stmt)
    await session.commit()

    # Fetch and return the upserted record
    result = await session.execute(
        select(ScrapedRecord).where(ScrapedRecord.source_url == url)
    )
    record = result.scalar_one()
    logger.info("Upserted record: %s (hash=%s)", url, data_hash[:12])
    return record
