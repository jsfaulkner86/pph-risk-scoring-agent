"""Tests for PPH risk scoring audit layer."""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock
from audit.models import PPHAuditEvent, PPHAuditEventType, PPHRiskTier
from audit.logger import PPHAuditLogger


def test_audit_event_model():
    event = PPHAuditEvent(
        event_type=PPHAuditEventType.RISK_TIER_ASSIGNED,
        patient_id="P-TOKEN-001",
        encounter_id="ENC-001",
        risk_score=4,
        risk_tier=PPHRiskTier.HIGH,
        risk_factors_present=["placenta previa", "prior PPH", "multiple gestation"],
        intervention_recommended="Active management — OB notify, uterotonic ready",
    )
    assert event.id is not None
    assert event.risk_tier == PPHRiskTier.HIGH
    assert len(event.risk_factors_present) == 3


@pytest.mark.asyncio
async def test_logger_never_raises_without_pool():
    logger = PPHAuditLogger(dsn="postgresql://test")
    logger._pool = None
    await logger.log(PPHAuditEvent(
        event_type=PPHAuditEventType.SCORING_FAILED,
        encounter_id="ENC-FAIL",
        error_detail="Test failure",
    ))


@pytest.mark.asyncio
async def test_logger_writes_risk_tier():
    logger = PPHAuditLogger(dsn="postgresql://test")
    mock_conn = AsyncMock()
    mock_pool = AsyncMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    logger._pool = mock_pool
    await logger.log_risk_tier_assigned(
        patient_id="P-001",
        encounter_id="ENC-001",
        risk_score=2,
        risk_tier=PPHRiskTier.MEDIUM,
        risk_factors_present=["prior cesarean"],
        intervention_recommended="Monitoring protocol B",
    )
    mock_conn.execute.assert_called_once()
