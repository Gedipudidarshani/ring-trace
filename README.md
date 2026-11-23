# RingTrace: Evidence-Grounded Financial Crime Investigation with Adversarial Case Stress-Testing

**Trace the flow. Challenge the hypothesis. Verify the evidence.**

RingTrace is a post-alert financial crime investigation and decision-support system. It transforms raw alerts and transaction networks into structured, evidence-tested investigation files before human compliance review.

---

## 🌟 Why RingTrace?

Traditional transaction monitoring flags suspicious patterns (e.g. MuleHunter, rules, graph anomalies), but an **alert is not an investigation**. When AI is applied to AML reporting, generative LLMs often act as overconfident storytellers—hallucinating connections, ignoring legitimate business explanations, and masking critical data gaps.

**RingTrace changes the paradigm:**
1. **Facts & Interpretations Separated:** Transaction records and computed graph metrics are immutable facts; typology labels are hypotheses.
2. **Mandatory Adversarial Challenge:** A dedicated **Defender Agent** tests legitimate alternative hypotheses (e.g. recurring payroll, supplier settlements) using read-only evidence queries.
3. **5-Dimension Case Evidence Stress-Testing:**
   - **Stress Test 1: Provenance Integrity** (Deterministic check of IDs, amounts, accounts, timestamps)
   - **Stress Test 2: Temporal Consistency** (Time-respecting causal paths, sequence validity)
   - **Stress Test 3: Competing Hypothesis Coverage** (Tests suspicious vs alternative explanations)
   - **Stress Test 4: Contradiction & Missing Context** (Explicitly flags unverified assumptions and unknowns)
   - **Stress Test 5: Pivotal-Evidence Sensitivity** (Diagnostic test: removes a pivotal record to evaluate case fragility)
4. **Case Evidence Robustness Profile (CERP):** Replaces deceptive single "risk scores" with an actionable multi-dimensional profile (Verified, Challenged, Unknown, Sensitive).
5. **Deterministic Claim Validator:** Rejects claims referencing non-existent records or violating temporal chronology.
6. **Human-in-the-Loop Governance:** Generates reviewable recommendations (`ESCALATE_FOR_HUMAN_REVIEW`, `CLOSURE_REVIEW`, `INSUFFICIENT_EVIDENCE`, `REQUEST_MORE_INFORMATION`) without ever autonomously taking enforcement actions.

---

## 🏗️ System Architecture

```text
Synthetic Transactions / Alert Subgraph
               │
               ▼
┌──────────────────────────────────────────────┐
│  Temporal Transaction Graph & Pattern Engine │
│  (Cycles, Layering Chains, Fan-In/Out, Rapid)│
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│   Evidence Pack & Provenance Snapshot        │
│   (Immutable records, paths, graph metrics)  │
└──────────────────────┬───────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌───────────────┐             ┌───────────────┐
│  Prosecutor   │             │   Defender    │
│  (Suspicious) │             │ (Alternative) │
└───────┬───────┘             └───────┬───────┘
        │                             │
        └──────────────┬──────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│    Evidence Stress-Test & Validation Engine  │
│  - Provenance Check   - Chronology Check     │
│  - Contradiction Check- Sensitivity Check    │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│          Reconciliation Agent                │
│    (Balanced synthesis, highlights gaps)     │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│    Case Evidence Robustness Profile (CERP)   │
│         & Human Analyst Workspace            │
└──────────────────────────────────────────────┘
```

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10+ (FastAPI, Uvicorn, Pydantic)
- Modern web browser

### Running the Prototype
Run the complete server and interactive analyst interface:

```powershell
# Using Python 3.12
& "C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe" run_demo.py
```

Then open your browser to:
- **Analyst Investigation Workspace:** `http://127.0.0.1:8080`
- **Interactive API Documentation:** `http://127.0.0.1:8080/docs`

### Running the Test Suite
```powershell
& "C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe" -m unittest discover tests -v
```

---

## 📊 Benchmark Evaluation: Planted-Defect Stress Testing

RingTrace includes a built-in evaluation harness benchmarking **RingTrace** against:
1. **Detector-Only Baseline:** Rule/graph anomaly flags only.
2. **Single-Agent Baseline:** Unchallenged generative LLM investigator.
3. **RingTrace Adversarial System:** Full bounded workflow with deterministic stress tests.

Tested against planted defects (fabricated transaction IDs, impossible timestamps, amount alterations, and missing context), RingTrace demonstrates:
- **100% rejection** of fabricated citations (via deterministic validator)
- **100% detection** of temporal chronology violations
- **Explicit disclosure** of missing data fields and pivotal transaction dependencies
- Zero ungrounded criminal accusations.

---

## 👥 Team Twilight (K! Hacks 4.0)
- Track: Agentic AI / FinTech
- Institution: Saveetha Engineering College
