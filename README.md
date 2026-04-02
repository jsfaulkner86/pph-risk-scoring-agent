# PPH Risk Scoring Agent

> **LangGraph** — Real production maternal health workflow rebuilt as a stateful, auditable agentic system

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)]()
[![LangGraph](https://img.shields.io/badge/LangGraph-FF6B35?style=flat-square)]()
[![Maternal Health](https://img.shields.io/badge/Maternal-Health-pink?style=flat-square)]()
[![Healthcare AI](https://img.shields.io/badge/Healthcare-AI-red?style=flat-square)]()

Built by [The Faulkner Group](https://thefaulknergroupadvisors.com) — directly informed by production maternal health workflows across Epic enterprise deployments.

---

## Problem Statement

Postpartum hemorrhage (PPH) is the leading cause of preventable maternal mortality. Current Epic-embedded PPH risk scoring runs as a batch job on a 10–15 minute polling interval, evaluated by 30+ static rules that require constant manual maintenance by clinical informatics teams. When a patient's risk profile changes intrapartum, the system doesn't know until the next batch cycle.

This agent rebuilds that workflow as a real-time, stateful LangGraph pipeline — evaluating risk continuously, applying dynamic clinical logic, and triggering interventions as risk tier changes, not on a cron schedule.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Patient Clinical Data                         │
│     vitals · labs · OB history · delivery context · meds         │
│     (simulated input or Epic FHIR R4 in production)              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                LangGraph Risk Scoring State Machine              │
│                                                                  │
│  [intake]                                                        │
│     │                                                            │
│     ▼                                                            │
│  [evaluate_risk_factors]          AWHONN/ACOG criteria applied   │
│     │                                                            │
│     ▼                                                            │
│  [compute_baseline_score]         weighted cumulative score      │
│     │                                                            │
│     ▼                                                            │
│  [assess_delivery_context]        intrapartum modifiers applied  │
│     │                                                            │
│     ▼                                                            │
│  [assign_risk_tier]               low | medium | high            │
│     │                                                            │
│     ▼                                                            │
│  [recommend_intervention]         tier-specific protocol         │
│     │                                                            │
│     │ high tier?                                                 │
│     ▼                                                            │
│  [trigger_alert]  ──▶  [notify_care_team]   ──▶  [audit_log]    │
└─────────────────────────────────────────────────────────────────┘
          │ Append-only HIPAA audit log on every state transition
          ▼
┌─────────────────────────────────────────────────────────────────┐
│  PostgreSQL: pph_risk_audit_log (append-only)                    │
└─────────────────────────────────────────────────────────────────┘
```

### Core Design Principles

- **Real-time over batch** — this agent fires on patient data events, not a 10–15 minute cron. Risk tier changes surface immediately.
- **Immutable event trail** — every score computation and tier assignment is a permanent audit record. Clinicians can reconstruct exactly what the system knew, and when, for any delivery encounter.
- **Clinician override is a first-class event** — `score_overridden_by_clinician` captures override reason. A high override rate is a signal to retrain, not to suppress.
- **Alert routing is tier-gated** — LOW tier generates no alert. MEDIUM triggers nursing protocol. HIGH triggers OB physician notification immediately.

---

## PPH Risk Scoring Framework

This agent implements a scoring model aligned with AWHONN and ACOG consensus guidelines:

### Antepartum Risk Factors

| Risk Factor | Score Weight |
|---|---|
| Prior PPH | +2 |
| Placenta previa / accreta | +3 |
| Multiple gestation | +1 |
| Grand multiparity (≥5) | +1 |
| Uterine anomaly | +1 |
| Anticoagulation therapy | +2 |
| Pre-existing anemia (Hgb <10) | +1 |

### Intrapartum Modifiers

| Event | Score Modifier |
|---|---|
| Prolonged labor (>18h) | +1 |
| Chorioamnionitis | +2 |
| Magnesium sulfate use | +1 |
| General anesthesia | +1 |
| Operative delivery (forceps/vacuum) | +1 |

### Risk Tier Assignment

| Cumulative Score | Risk Tier | Intervention Protocol |
|---|---|---|
| 0–1 | LOW | Routine monitoring |
| 2–3 | MEDIUM | IV access, T&S, nursing PPH protocol |
| 4+ | HIGH | Large-bore IV ×2, type & crossmatch, OB notify, uterotonic ready |

---

## Audit Event Lifecycle

```
patient_intake_received
    └── risk_factor_evaluated (0–n per factor)
            └── baseline_score_computed
                    └── delivery_context_assessed
                            └── intrapartum_score_updated
                                    └── risk_tier_assigned
                                            └── intervention_recommended
                                            └── alert_triggered (if tier = HIGH)
                                            └── care_team_notified
                                            └── score_overridden_by_clinician
                                            └── scoring_failed
```

---

## Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Agent Orchestration** | LangGraph | Stateful graph — each node maps to a discrete scoring step; state persists across intrapartum updates |
| **LLM** | OpenAI GPT-4o | Clinical reasoning for risk factor interpretation and intervention language generation |
| **Audit Store** | PostgreSQL + asyncpg | Append-only event log with risk factor array indexing |
| **Language** | Python 3.11+ | Async-native; type hints throughout |

---

## Compliance Posture

- **HIPAA:** `patient_id` stored as de-identified token. Never log raw MRN, name, or DOB. For production Epic FHIR integration, use SMART-on-FHIR Backend Services with a signed BAA.
- **JCAHO NPSG.16.01.03:** Maternal early warning criteria require documented response. The `intervention_recommended` + `care_team_notified` audit events satisfy the documentation requirement that a response occurred.
- **Clinician Override Documentation:** `score_overridden_by_clinician` with `override_reason` text satisfies the requirement that clinical overrides of automated decision support tools be documented.
- **CAB/Change Management:** Before replacing or augmenting Epic’s native PPH scoring, this agent requires CMIO and patient safety committee sign-off. Present `get_risk_tier_distribution()` and `get_clinician_override_rate()` data to the committee.

---

## Known Failure Modes

| Failure Mode | Impact | Mitigation |
|---|---|---|
| Incomplete intrapartum data | Risk score computed without delivery modifiers | Validate data completeness before scoring; flag missing fields |
| Alert fatigue on MEDIUM tier | Nurses disable or ignore notifications | Tune MEDIUM-tier alert frequency; review override rate monthly |
| Epic batch job running in parallel | Duplicate or conflicting scores | Coordinate with Epic build team — disable legacy batch job in pilot units first |
| LangGraph thread state loss | Intrapartum score update loses antepartum context | PostgreSQL checkpoint store required; validate thread continuity on resume |

---

## Epic Production Integration Path

| Integration Point | FHIR Resource | Notes |
|---|---|---|
| Patient demographics + OB history | `Patient`, `Condition` | Via `ehr-mcp` `get_patient_context` tool |
| Vitals and labs | `Observation` (LOINC codes) | Continuous monitoring via `search_fhir` |
| Delivery event triggers | `Encounter` status change | Webhook from Epic ADT feed |
| Care team notification | `Task` | Creates In-Basket work item for OB provider |
| Alert documentation | `Communication` | Writes back to patient chart |

---

## Local Development

```bash
git clone https://github.com/jsfaulkner86/pph-risk-scoring-agent
cd pph-risk-scoring-agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

psql $DATABASE_URL -f audit/migrations/001_create_pph_risk_audit_log.sql

python main.py
pytest tests/ -v
```

---

## What's Next

- Epic FHIR integration for live patient data via `ehr-mcp`
- Continuous monitoring agent for post-delivery risk tracking (4h, 8h, 24h)
- Alert routing to Epic In-Basket via `Task` FHIR resource write-back
- Model recalibration pipeline using clinician override data

---

*Part of The Faulkner Group’s healthcare agentic AI portfolio → [github.com/jsfaulkner86](https://github.com/jsfaulkner86)*
