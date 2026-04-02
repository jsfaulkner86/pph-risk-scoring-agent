-- Migration: 001_create_pph_risk_audit_log
-- Immutable HIPAA audit trail for PPH risk scoring events.
-- This table must never have UPDATE or DELETE granted on it.

CREATE TABLE IF NOT EXISTS pph_risk_audit_log (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type               TEXT NOT NULL,
    patient_id               TEXT,          -- de-identified token; never raw MRN
    encounter_id             TEXT,
    thread_id                TEXT,
    risk_score               INTEGER,       -- cumulative AWHONN/ACOG PPH risk score
    risk_tier                TEXT,          -- low | medium | high | unknown
    risk_factors_present     TEXT[],        -- documented risk factors at scoring time
    intervention_recommended TEXT,
    alert_level              TEXT,          -- INFO | WARNING | CRITICAL
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
    'Immutable append-only HIPAA audit trail for all PPH risk scoring and alert events. Never UPDATE or DELETE rows.';
