"""Audit event models for the PPH Risk Scoring Agent."""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PPHAuditEventType(str, Enum):
    PATIENT_INTAKE_RECEIVED = "patient_intake_received"
    RISK_FACTOR_EVALUATED = "risk_factor_evaluated"
    BASELINE_SCORE_COMPUTED = "baseline_score_computed"
    DELIVERY_CONTEXT_ASSESSED = "delivery_context_assessed"
    INTRAPARTUM_SCORE_UPDATED = "intrapartum_score_updated"
    RISK_TIER_ASSIGNED = "risk_tier_assigned"
    INTERVENTION_RECOMMENDED = "intervention_recommended"
    ALERT_TRIGGERED = "alert_triggered"
    CARE_TEAM_NOTIFIED = "care_team_notified"
    SCORE_OVERRIDDEN_BY_CLINICIAN = "score_overridden_by_clinician"
    SCORING_FAILED = "scoring_failed"


class PPHRiskTier(str, Enum):
    LOW = "low"           # score 0–1
    MEDIUM = "medium"     # score 2–3
    HIGH = "high"         # score 4+
    UNKNOWN = "unknown"


class PPHAuditEvent(BaseModel):
    """Immutable audit record for a single PPH risk scoring event."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    event_type: PPHAuditEventType
    patient_id: Optional[str] = None        # de-identified token; never raw MRN
    encounter_id: Optional[str] = None
    thread_id: Optional[str] = None         # LangGraph thread
    risk_score: Optional[int] = None        # cumulative risk score
    risk_tier: Optional[PPHRiskTier] = None
    risk_factors_present: Optional[list[str]] = None
    intervention_recommended: Optional[str] = None
    alert_level: Optional[str] = None       # INFO | WARNING | CRITICAL
    clinician_override: bool = False
    override_reason: Optional[str] = None
    error_detail: Optional[str] = None
    metadata: Optional[dict] = None


AUDIT_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS pph_risk_audit_log (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type               TEXT NOT NULL,
    patient_id               TEXT,
    encounter_id             TEXT,
    thread_id                TEXT,
    risk_score               INTEGER,
    risk_tier                TEXT,
    risk_factors_present     TEXT[],
    intervention_recommended TEXT,
    alert_level              TEXT,
    clinician_override       BOOLEAN NOT NULL DEFAULT FALSE,
    override_reason          TEXT,
    error_detail             TEXT,
    metadata                 JSONB
);

CREATE INDEX IF NOT EXISTS idx_pph_audit_event_type   ON pph_risk_audit_log (event_type);
CREATE INDEX IF NOT EXISTS idx_pph_audit_patient      ON pph_risk_audit_log (patient_id);
CREATE INDEX IF NOT EXISTS idx_pph_audit_encounter    ON pph_risk_audit_log (encounter_id);
CREATE INDEX IF NOT EXISTS idx_pph_audit_risk_tier    ON pph_risk_audit_log (risk_tier);
CREATE INDEX IF NOT EXISTS idx_pph_audit_created_at   ON pph_risk_audit_log (created_at DESC);

COMMENT ON TABLE pph_risk_audit_log IS
    'Immutable append-only HIPAA audit trail for all PPH risk scoring events. Never UPDATE or DELETE rows.';
"""
