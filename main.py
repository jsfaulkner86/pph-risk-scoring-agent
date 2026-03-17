from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

# ── DATA MODEL ─────────────────────────────────────────

class PatientClinicalData(BaseModel):
    patient_id: str
    prior_pph: bool
    multiple_gestation: bool
    placenta_previa: bool
    hematocrit_below_30: bool
    platelet_count_below_100k: bool
    fibroid_uterus: bool
    prior_uterine_surgery: bool
    grand_multiparity: bool  # 5+ prior deliveries
    magnesium_sulfate: bool
    chorioamnionitis: bool
    prolonged_labor: bool

class AgentState(TypedDict):
    patient_data: dict
    risk_score: int
    risk_level: str
    triggered_factors: list
    alert_sent: bool
    audit_log: list
    recommendation: str

# ── RISK SCORING MAP ───────────────────────────────────

RISK_WEIGHTS = {
    "prior_pph": 3,
    "multiple_gestation": 2,
    "placenta_previa": 3,
    "hematocrit_below_30": 2,
    "platelet_count_below_100k": 2,
    "fibroid_uterus": 1,
    "prior_uterine_surgery": 1,
    "grand_multiparity": 1,
    "magnesium_sulfate": 1,
    "chorioamnionitis": 2,
    "prolonged_labor": 1
}

# ── NODE 1: INGEST & VALIDATE ──────────────────────────

def ingest_patient_data(state: AgentState) -> AgentState:
    log = state.get("audit_log", [])
    log.append("STEP 1: Patient data ingested and validated")
    state["audit_log"] = log
    return state

# ── NODE 2: SCORE RISK FACTORS ─────────────────────────

def score_risk_factors(state: AgentState) -> AgentState:
    data = state["patient_data"]
    score = 0
    triggered = []

    for factor, weight in RISK_WEIGHTS.items():
        if data.get(factor, False):
            score += weight
            triggered.append(f"{factor} (+{weight})")

    state["risk_score"] = score
    state["triggered_factors"] = triggered
    state["audit_log"].append(f"STEP 2: Risk scored — {score} points from {len(triggered)} factors")
    return state

# ── NODE 3: CLASSIFY RISK LEVEL ────────────────────────

def classify_risk_level(state: AgentState) -> AgentState:
    score = state["risk_score"]

    if score == 0:
        level = "LOW"
    elif 1 <= score <= 3:
        level = "MEDIUM"
    else:
        level = "HIGH"

    state["risk_level"] = level
    state["audit_log"].append(f"STEP 3: Risk classified as {level}")
    return state

# ── NODE 4A: HIGH RISK ALERT ───────────────────────────

def send_high_risk_alert(state: AgentState) -> AgentState:
    print(f"\n🚨 HIGH RISK ALERT — Patient {state['patient_data']['patient_id']}")
    print(f"Score: {state['risk_score']} | Factors: {state['triggered_factors']}")
    state["alert_sent"] = True
    state["recommendation"] = "Activate PPH hemorrhage cart. Notify charge nurse and attending immediately. Type & Screen ordered."
    state["audit_log"].append("STEP 4: HIGH RISK — Alert sent to charge nurse and attending")
    return state

# ── NODE 4B: MEDIUM RISK ALERT ─────────────────────────

def send_medium_risk_alert(state: AgentState) -> AgentState:
    print(f"\n⚠️ MEDIUM RISK — Patient {state['patient_data']['patient_id']}")
    print(f"Score: {state['risk_score']} | Factors: {state['triggered_factors']}")
    state["alert_sent"] = True
    state["recommendation"] = "Notify bedside nurse. Ensure IV access. Monitor closely post-delivery."
    state["audit_log"].append("STEP 4: MEDIUM RISK — Bedside nurse notified")
    return state

# ── NODE 4C: LOW RISK ──────────────────────────────────

def log_low_risk(state: AgentState) -> AgentState:
    print(f"\n✅ LOW RISK — Patient {state['patient_data']['patient_id']}")
    state["alert_sent"] = False
    state["recommendation"] = "Standard monitoring protocol. Reassess if clinical picture changes."
    state["audit_log"].append("STEP 4: LOW RISK — Standard protocol, no alert required")
    return state

# ── ROUTING LOGIC ──────────────────────────────────────

def route_by_risk(state: AgentState) -> Literal["high_risk", "medium_risk", "low_risk"]:
    level = state["risk_level"]
    if level == "HIGH":
        return "high_risk"
    elif level == "MEDIUM":
        return "medium_risk"
    else:
        return "low_risk"

# ── BUILD GRAPH ────────────────────────────────────────

def build_pph_agent():
    graph = StateGraph(AgentState)

    graph.add_node("ingest", ingest_patient_data)
    graph.add_node("score", score_risk_factors)
    graph.add_node("classify", classify_risk_level)
    graph.add_node("high_risk", send_high_risk_alert)
    graph.add_node("medium_risk", send_medium_risk_alert)
    graph.add_node("low_risk", log_low_risk)

    graph.set_entry_point("ingest")
    graph.add_edge("ingest", "score")
    graph.add_edge("score", "classify")
    graph.add_conditional_edges("classify", route_by_risk, {
        "high_risk": "high_risk",
        "medium_risk": "medium_risk",
        "low_risk": "low_risk"
    })
    graph.add_edge("high_risk", END)
    graph.add_edge("medium_risk", END)
    graph.add_edge("low_risk", END)

    return graph.compile()

# ── MAIN ──────────────────────────────────────────────

if __name__ == "__main__":
    # Mock patient — high risk scenario
    patient = {
        "patient_id": "PT-00421",
        "prior_pph": True,
        "multiple_gestation": False,
        "placenta_previa": True,
        "hematocrit_below_30": True,
        "platelet_count_below_100k": False,
        "fibroid_uterus": False,
        "prior_uterine_surgery": True,
        "grand_multiparity": False,
        "magnesium_sulfate": False,
        "chorioamnionitis": False,
        "prolonged_labor": True
    }

    agent = build_pph_agent()
    final_state = agent.invoke({
        "patient_data": patient,
        "audit_log": []
    })

    print("\n── AUDIT TRAIL ──")
    for entry in final_state["audit_log"]:
        print(f"  {entry}")
    print(f"\n── RECOMMENDATION ──\n  {final_state['recommendation']}")
