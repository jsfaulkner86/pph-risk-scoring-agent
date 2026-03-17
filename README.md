# PPH Risk Scoring Agent

> **LangGraph** — Real production maternal health workflow rebuilt as an agentic system

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)]()
[![LangGraph](https://img.shields.io/badge/LangGraph-FF6B35?style=flat-square)]()
[![Maternal Health](https://img.shields.io/badge/Maternal-Health-pink?style=flat-square)]()
[![Healthcare AI](https://img.shields.io/badge/Healthcare-AI-red?style=flat-square)]()

## The Problem

Postpartum hemorrhage (PPH) is a leading cause of maternal mortality — and it's largely preventable with early risk identification. Traditional EHR risk scoring is static and reactive. This agent models the clinical decision process as a dynamic, stateful workflow.

## What It Does

A stateful agent built with LangGraph that:
- Ingests patient clinical data (vitals, labs, history, delivery context)
- Traverses a risk assessment state machine modeled after real clinical protocols
- Produces a tiered risk score with clinical reasoning
- Recommends intervention thresholds based on scoring output

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | LangGraph |
| State Management | LangGraph StateGraph |
| LLM | OpenAI GPT-4 |
| Language | Python 3.11+ |

## Getting Started

```bash
git clone https://github.com/jsfaulkner86/pph-risk-scoring-agent
cd pph-risk-scoring-agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## Environment Variables

```
OPENAI_API_KEY=your_key_here
```

## Background

Built by [John Faulkner](https://linkedin.com/in/johnathonfaulkner), Agentic AI Architect and founder of [The Faulkner Group](https://thefaulknergroupadvisors.com). This project is directly informed by production maternal health workflows observed across Epic EHR enterprise implementations.

## What's Next
- Epic FHIR integration for live patient data ingestion
- Continuous monitoring agent for post-delivery risk tracking
- Alert routing to care team based on risk tier

---
*Part of a portfolio of healthcare agentic AI systems. See all projects at [github.com/jsfaulkner86](https://github.com/jsfaulkner86)*
