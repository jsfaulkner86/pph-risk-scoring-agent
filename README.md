<div align="center">

<br />

# 🩸 PPH Risk Scoring Agent

**Postpartum hemorrhage kills 70,000 mothers a year worldwide.**  
**Most of those deaths are preventable.**  
**Epic's native risk scoring runs on a 10–15 minute batch cycle.**

This agent rebuilds that workflow as a **real-time, stateful LangGraph pipeline** —  
evaluating risk continuously, firing on clinical events, not a cron schedule.

<br />

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Stateful%20Graph-FF6B35?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![AWHONN](https://img.shields.io/badge/AWHONN%2FACOG-Aligned-E91E8C?style=flat-square)]()
[![HIPAA](https://img.shields.io/badge/HIPAA-Compliant%20Design-6E93B0?style=flat-square)]()
[![Epic](https://img.shields.io/badge/Epic-FHIR%20R4%20Integration%20Path-C8102E?style=flat-square)]()
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

<br />

[Architecture](#system-architecture) · [Scoring Model](#pph-risk-scoring-framework) · [Epic Integration](#epic-production-integration-path) · [Quick Start](#local-development) · [Failure Modes](#known-failure-modes)

<br />

</div>

---

## The Real Problem

I spent 14 years architecting clinical workflows across 12 enterprise Epic health systems. At Beaumont Health, I coordinated workflows for **17,000 births per year** — and I watched the same gap exist at every site:

> **Epic's PPH risk scoring is a batch job.** It runs every 10–15 minutes. 30+ static rules, manually maintained by clinical informatics. When a patient's risk profile changes intrapartum — chorioamnionitis, prolonged labor, operative delivery — the system doesn't know until the next poll cycle.

In obstetrics, 15 minutes is a long time.

This agent is what I would have built inside Epic if the platform let me. It's a real-time, event-driven, fully auditable LangGraph state machine that fires **on patient data events, not a clock.**

---

## What's Different Here

| Epic Native Scoring | This Agent |
|---|---|
| Batch job, 10–15 min cycle | Event-driven, fires on data change |
| 30+ static rules, manual maintenance | Dynamic AWHONN/ACOG logic, parameterized weights |
| No intrapartum modifier recalculation | Continuous score updates as delivery context changes |
| Audit trail: none by default | Append-only HIPAA event log on every state transition |
| Alert: In-Basket message, delayed | Tier-gated alert routing, immediate on HIGH |
| Clinician override: undocumented | `score_overridden_by_clinician` event — first-class audit record |

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

- **Real-time over batch** — fires on patient data events, not a 10–15 minute cron. Risk tier changes surface immediately.
- **Immutable event trail** — every score computation and tier assignment is a permanent audit record. Clinicians can reconstruct exactly what the system knew, and when, for any delivery encounter.
- **Clinician override is a first-class event** — `score_overridden_by_clinician` captures override reason. A high override rate is a signal to retrain, not to suppress.
- **Alert routing is tier-gated** — LOW generates no alert. MEDIUM triggers nursing protocol. HIGH triggers OB physician notification immediately.
- **Stateful across intrapartum updates** — LangGraph thread state persists antepartum context as delivery modifiers layer in. No restarting the score from scratch.

---

## PPH Risk Scoring Framework

Aligned with AWHONN and ACOG consensus guidelines.

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
| 0–1 | 🟢 LOW | Routine monitoring |
| 2–3 | 🟡 MEDIUM | IV access, T&S, nursing PPH protocol |
| 4+ | 🔴 HIGH | Large-bore IV ×2, type & crossmatch, OB notify, uterotonic ready |

---

## Audit Event Lifecycle

Every state transition writes an immutable event. No silent operations.

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
| **Pattern** | ReAct + Stateful State Machine | Risk evaluation loop with conditional branching on tier assignment |
| **LLM** | OpenAI GPT-4o | Clinical reasoning for risk factor interpretation and intervention language generation |
| **Audit Store** | PostgreSQL + asyncpg | Append-only event log with risk factor array indexing |
| **Language** | Python 3.11+ | Async-native; type hints throughout; Pydantic v2 models |

---

## Compliance Posture

- **HIPAA:** `patient_id` stored as de-identified token. Never log raw MRN, name, or DOB. For production Epic FHIR integration, use SMART-on-FHIR Backend Services with a signed BAA.
- **JCAHO NPSG.16.01.03:** Maternal early warning criteria require documented response. The `intervention_recommended` + `care_team_notified` audit events satisfy the documentation requirement that a response occurred.
- **Clinician Override Documentation:** `score_overridden_by_clinician` with `override_reason` text satisfies the requirement that clinical overrides of automated decision support tools be documented.
- **CAB/Change Management:** Before replacing or augmenting Epic's native PPH scoring, this agent requires CMIO and patient safety committee sign-off. Present `get_risk_tier_distribution()` and `get_clinician_override_rate()` data to the committee.

---

## Known Failure Modes

Production healthcare AI needs an honest failure mode table. Here's mine.

| Failure Mode | Impact | Mitigation |
|---|---|---|
| Incomplete intrapartum data | Score computed without delivery modifiers | Validate data completeness before scoring; flag missing fields |
| Alert fatigue on MEDIUM tier | Nurses disable or ignore notifications | Tune MEDIUM-tier alert frequency; review override rate monthly |
| Epic batch job running in parallel | Duplicate or conflicting scores | Coordinate with Epic build team — disable legacy batch job in pilot units first |
| LangGraph thread state loss | Intrapartum update loses antepartum context | PostgreSQL checkpoint store required; validate thread continuity on resume |

---

## Epic Production Integration Path

| Integration Point | FHIR Resource | Notes |
|---|---|---|
| Patient demographics + OB history | `Patient`, `Condition` | Via [`ehr-mcp`](https://github.com/jsfaulkner86/ehr-mcp) `get_patient_context` tool |
| Vitals and labs | `Observation` (LOINC codes) | Continuous monitoring via `search_fhir` |
| Delivery event triggers | `Encounter` status change | Webhook from Epic ADT feed |
| Care team notification | `Task` | Creates In-Basket work item for OB provider |
| Alert documentation | `Communication` | Writes back to patient chart |

This agent is designed to pair with **[ehr-mcp](https://github.com/jsfaulkner86/ehr-mcp)** — a framework-agnostic FHIR interoperability layer that provides the `get_patient_context` tool as a normalized FHIR bundle.

---

## Local Development

```bash
git clone https://github.com/jsfaulkner86/pph-risk-scoring-agent
cd pph-risk-scoring-agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Initialize audit log
psql $DATABASE_URL -f audit/migrations/001_create_pph_risk_audit_log.sql

# Run agent
python main.py

# Run tests
pytest tests/ -v
```

### Environment Variables

```env
OPENAI_API_KEY=your_key_here
DATABASE_URL=postgresql://user:pass@localhost:5432/pph_db
AUDIT_LOG_ENABLED=true
HIPAA_MODE=true    # Enforces de-identified patient_id only
```

---

## Roadmap

- [ ] Epic FHIR live patient data integration via `ehr-mcp`
- [ ] Continuous post-delivery monitoring agent (4h, 8h, 24h intervals)
- [ ] Alert routing to Epic In-Basket via `Task` FHIR write-back
- [ ] Model recalibration pipeline using clinician override data
- [ ] LangSmith tracing integration for production observability

---

## If You're Building Healthcare AI

If this pattern is useful to you, a ⭐ helps others find it.

If you're a women's health tech founder navigating EHR integrations, prior auth automation, or clinical AI deployment — this is the kind of system I architect at [The Faulkner Group](https://thefaulknergroupadvisors.com).

---

<div align="center">

*Part of The Faulkner Group's healthcare agentic AI portfolio → [github.com/jsfaulkner86](https://github.com/jsfaulkner86)*

*Built from 14 years and 12 Epic enterprise health system deployments — 17,000 births/year coordinated, now codified in Python.*

</div>
