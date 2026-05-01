"""
Idempotent column-level + enum-level migrations for runtime use without Alembic.

`Base.metadata.create_all` only creates missing TABLES; it cannot add columns or
extend Postgres ENUM types. As Trusyn evolves we add new fields and new enum
values; this helper runs:
  - `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` for each known column delta
  - `ALTER TYPE ... ADD VALUE IF NOT EXISTS` for each known enum value addition

Postgres supports both IF NOT EXISTS forms (since 9.6); SQLite does not, so we
catch and log on SQLite.

Note: ALTER TYPE ... ADD VALUE cannot run inside a multi-statement transaction
on Postgres < 12. We use AUTOCOMMIT for that statement specifically to be safe.

Add a new entry here whenever you add a column / new enum value to an existing
model.
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


# (enum_type_name, new_value)
# SQLAlchemy `Enum(PyEnum)` serializes enum members by their NAME (uppercase),
# not their .value. So Postgres enum labels are uppercase too.
ENUM_VALUE_ADDITIONS: List[Tuple[str, str]] = [
    ("recipienttype", "GOOGLE_SAFEBROWSING"),
    ("recipienttype", "URLSCAN"),
    ("recipienttype", "THREATFOX"),
    ("recipienttype", "MICROSOFT_SMARTSCREEN"),
    ("reportstatus", "PENDING"),
    ("reportstatus", "FORM_ONLY"),
    ("reportstatus", "ACTIONED"),
    ("reportstatus", "DECLINED"),
    ("reportstatus", "FAILED"),
]


async def _run_column_additions(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        for table, column, ddl in COLUMN_ADDITIONS:
            try:
                await conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {ddl}"
                ))
                logger.info("Migration ensured: %s.%s", table, column)
            except Exception as exc:
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


async def _run_enum_additions(engine: AsyncEngine) -> None:
    """ALTER TYPE ... ADD VALUE must run in autocommit mode (it cannot be
    rolled back). We open a fresh connection per statement with isolation
    AUTOCOMMIT to bypass the implicit transaction."""
    for enum_name, value in ENUM_VALUE_ADDITIONS:
        try:
            async with engine.connect() as conn:
                ac_conn = await conn.execution_options(
                    isolation_level="AUTOCOMMIT"
                )
                await ac_conn.execute(text(
                    f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value}'"
                ))
                logger.info("Enum ensured: %s += %s", enum_name, value)
        except Exception as exc:
            msg = str(exc).lower()
            if "already exists" in msg or "does not exist" in msg:
                continue
            logger.warning("Enum migration skipped %s += %s: %s",
                           enum_name, value, exc)


async def run_idempotent_migrations(engine: AsyncEngine) -> None:
    await _run_column_additions(engine)
    await _run_enum_additions(engine)
