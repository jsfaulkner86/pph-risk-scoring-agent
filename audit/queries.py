"""Read-side analytics for PPH risk scoring audit data."""
import os
import asyncpg
from datetime import datetime, timedelta
from typing import Optional


class PPHAuditQueryService:

    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or os.getenv("DATABASE_URL", "")
        self._pool: Optional[asyncpg.Pool] = None

    async def init(self) -> None:
        self._pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=3)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def get_encounter_trail(self, encounter_id: str) -> list[dict]:
        """Full risk scoring event trail for a single delivery encounter."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM pph_risk_audit_log WHERE encounter_id=$1 ORDER BY created_at ASC",
                encounter_id,
            )
            return [dict(r) for r in rows]

    async def get_risk_tier_distribution(
        self, since: Optional[datetime] = None
    ) -> list[dict]:
        """Breakdown of risk tier assignments over time — maternal quality metric."""
        since = since or (datetime.utcnow() - timedelta(days=30))
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT risk_tier, COUNT(*) AS count,
                       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pct
                FROM pph_risk_audit_log
                WHERE event_type='risk_tier_assigned' AND created_at >= $1
                GROUP BY risk_tier ORDER BY count DESC
                """,
                since,
            )
            return [dict(r) for r in rows]

    async def get_top_risk_factors(
        self, since: Optional[datetime] = None
    ) -> list[dict]:
        """Most frequently documented risk factors — population health signal."""
        since = since or (datetime.utcnow() - timedelta(days=90))
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT factor, COUNT(*) AS frequency
                FROM pph_risk_audit_log,
                     UNNEST(risk_factors_present) AS factor
                WHERE created_at >= $1
                GROUP BY factor ORDER BY frequency DESC
                """,
                since,
            )
            return [dict(r) for r in rows]

    async def get_clinician_override_rate(
        self, since: Optional[datetime] = None
    ) -> dict:
        """Override rate — high rates signal model miscalibration or training gaps."""
        since = since or (datetime.utcnow() - timedelta(days=30))
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) FILTER (WHERE event_type='risk_tier_assigned')            AS total_scored,
                    COUNT(*) FILTER (WHERE event_type='score_overridden_by_clinician') AS overrides,
                    COUNT(*) FILTER (WHERE event_type='alert_triggered')               AS alerts_fired,
                    COUNT(*) FILTER (WHERE event_type='scoring_failed')                AS failed
                FROM pph_risk_audit_log WHERE created_at >= $1
                """,
                since,
            )
            return dict(row)
