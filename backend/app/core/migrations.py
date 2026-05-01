"""
Idempotent column-level migrations for runtime use without Alembic.

`Base.metadata.create_all` only creates missing TABLES; it cannot add columns to
existing tables. As Trusyn evolves we add new columns; this helper runs
`ALTER TABLE ... ADD COLUMN IF NOT EXISTS` for each known schema delta. Postgres
supports IF NOT EXISTS natively (since 9.6); SQLite (used in some dev setups)
does not, so we catch and log on SQLite.

Add a new entry here whenever you add a column to an existing model.
"""

import logging
from typing import List, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


logger = logging.getLogger(__name__)


# (table, column, sql-type-with-default)
COLUMN_ADDITIONS: List[Tuple[str, str, str]] = [
    ("brands", "country_restrictions", "TEXT DEFAULT 'Worldwide'"),
    ("reports", "recipient_form_url", "VARCHAR"),
    ("reports", "recipient_name", "VARCHAR"),
    ("reports", "subject", "VARCHAR"),
    ("reports", "message_id", "VARCHAR"),
    ("reports", "error_message", "TEXT"),
]


async def run_idempotent_migrations(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        for table, column, ddl in COLUMN_ADDITIONS:
            try:
                # Postgres-flavored ADD COLUMN IF NOT EXISTS
                await conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {ddl}"
                ))
                logger.info("Migration ensured: %s.%s", table, column)
            except Exception as exc:
                # SQLite path or older Postgres without IF NOT EXISTS: try
                # without IF NOT EXISTS, swallow if already exists.
                try:
                    await conn.execute(text(
                        f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"
                    ))
                    logger.info("Migration applied (no IF NOT EXISTS): %s.%s",
                                table, column)
                except Exception as exc2:
                    msg = str(exc2).lower()
                    if "duplicate" in msg or "already exists" in msg:
                        continue
                    logger.warning(
                        "Migration skipped for %s.%s: %s",
                        table, column, exc2,
                    )
