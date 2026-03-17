# PPH Risk Scoring Agent

A LangGraph state machine translating a real Postpartum 
Hemorrhage risk assessment workflow I architected.

## Why This Project Is Different
This isn't a tutorial demo. This is a clinical workflow 
I designed and deployed in production — now rebuilt as an 
agentic state machine. The domain knowledge is real. 
The stakes it was designed around were real.

## The Original Workflow (Epic EHR)
- Ingested antepartum clinical data at admission
- Scored 30+ hemorrhage risk factors with weighted logic
- Triggered autonomous alerts to nursing and charge teams
- Embedded JCAHO compliance checkpoints with audit trail

## The Agentic Translation
| EHR Workflow Component | LangGraph Equivalent |
|---|---|
| Risk factor ingestion | Input node with structured data parser |
| Weighted scoring logic | Decision node with conditional edges |
| Alert escalation | Tool-calling node triggering notifications |
| Audit trail | State persistence across all nodes |
| Exception handling | Fallback edges with human-in-the-loop |

## Tech Stack
- LangGraph
- PydanticAI (data validation)
- Python
- Mock clinical data only — no real PHI

## Why LangGraph Over CrewAI
PPH scoring is a deterministic, stateful workflow with 
strict conditional branching — exactly what LangGraph's 
node/edge architecture was built for. The state must 
persist and be auditable at every step.

## Status
🔨 In Progress — target completion May 2026
Part of IBM RAG & Agentic AI Professional certification
