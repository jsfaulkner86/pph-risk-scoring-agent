"""Append-only audit logger for PPH risk scoring events."""
import os
import json
import logging
import asyncpg
from typing import Optional
from .models import PPHAuditEvent, PPHAuditEventType, PPHRiskTier

logger = logging.getLogger(__name__)


class PPHAuditLogger:
    """
    Append-only HIPAA-compliant audit logger for maternal risk scoring.
    Never raises — a failed audit write must not interrupt a live delivery workflow.
    """

    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or os.getenv("DATABASE_URL", "")
        self._pool: Optional[asyncpg.Pool] = None

    async def init(self) -> None:
        self._pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=5)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def log(self, event: PPHAuditEvent) -> None:
        if not self._pool:
            logger.warning("PPHAuditLogger not initialized — event dropped: %s", event.event_type)
            return
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO pph_risk_audit_log (
                        id, created_at, event_type, patient_id, encounter_id,
                        thread_id, risk_score, risk_tier, risk_factors_present,
                        intervention_recommended, alert_level,
                        clinician_override, override_reason, error_detail, metadata
                    ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
                    """,
                    event.id, event.created_at, event.event_type.value,
                    event.patient_id, event.encounter_id, event.thread_id,
                    event.risk_score, event.risk_tier.value if event.risk_tier else None,
                    event.risk_factors_present, event.intervention_recommended,
                    event.alert_level, event.clinician_override, event.override_reason,
                    event.error_detail,
                    json.dumps(event.metadata) if event.metadata else None,
                )
        except Exception as e:
            logger.error("PPH audit write failed [%s]: %s", event.encounter_id, e)

    async def log_risk_tier_assigned(
        self,
        patient_id: str,
        encounter_id: str,
        risk_score: int,
        risk_tier: PPHRiskTier,
        risk_factors_present: list[str],
        intervention_recommended: str,
        thread_id: Optional[str] = None,
    ) -> None:
        await self.log(PPHAuditEvent(
            event_type=PPHAuditEventType.RISK_TIER_ASSIGNED,
            patient_id=patient_id,
            encounter_id=encounter_id,
            thread_id=thread_id,
            risk_score=risk_score,
            risk_tier=risk_tier,
            risk_factors_present=risk_factors_present,
            intervention_recommended=intervention_recommended,
        ))

    async def log_clinician_override(
        self,
        patient_id: str,
        encounter_id: str,
        override_reason: str,
        original_tier: PPHRiskTier,
    ) -> None:
        await self.log(PPHAuditEvent(
            event_type=PPHAuditEventType.SCORE_OVERRIDDEN_BY_CLINICIAN,
            patient_id=patient_id,
            encounter_id=encounter_id,
            risk_tier=original_tier,
            clinician_override=True,
            override_reason=override_reason,
        ))


audit_logger = PPHAuditLogger()
