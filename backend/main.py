"""
RingTrace: FastAPI Backend Application
Exposes REST endpoints for case ingestion, temporal graph inspection,
bounded investigation execution, deterministic stress testing, CERP reporting,
and human analyst review.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import os

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from backend.models.schemas import (
    Transaction,
    EvidencePack,
    InvestigationRunResult,
    CERPReport,
    AuditEvent
)
from backend.data.sample_cases import get_all_preset_cases
from backend.evidence.evidence_pack import EvidencePackBuilder
from backend.agents.orchestrator import InvestigationOrchestrator
from backend.graph.temporal_graph import TemporalTransactionGraph
from backend.graph.detectors import CandidatePatternDetector
from backend.evaluation.benchmark import BenchmarkRunner

app = FastAPI(
    title="RingTrace API",
    description="Evidence-Grounded Financial Crime Investigation with Adversarial Case Stress-Testing",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory case storage for prototype
CASE_DATABASE: Dict[str, Dict[str, Any]] = {}
INVESTIGATION_RESULTS: Dict[str, InvestigationRunResult] = {}
HUMAN_REVIEWS: Dict[str, Dict[str, Any]] = {}


def initialize_preset_cases():
    """Populates the in-memory database with the curated synthetic scenarios."""
    presets = get_all_preset_cases()
    for cid, case_data in presets.items():
        CASE_DATABASE[cid] = {
            "case_id": cid,
            "title": case_data["title"],
            "description": case_data["description"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "transactions": case_data["transactions"],
            "status": "READY_FOR_INVESTIGATION"
        }


initialize_preset_cases()


# Request Schemas
class CreateCaseRequest(BaseModel):
    case_id: str
    title: str
    description: str
    transactions: List[Transaction]


class HumanReviewRequest(BaseModel):
    decision: str  # ESCALATED_TO_FIU, CLOSED_FALSE_POSITIVE, INFORMATION_REQUESTED, ESCALATED_SENIOR_ANALYST
    analyst_name: str
    analyst_notes: str


# Endpoints
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "RingTrace Post-Alert Investigation Engine",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/cases")
def list_cases():
    """Lists all available cases with summary metadata."""
    summary_list = []
    for cid, c in CASE_DATABASE.items():
        has_run = cid in INVESTIGATION_RESULTS
        run_res = INVESTIGATION_RESULTS.get(cid)
        summary_list.append({
            "case_id": cid,
            "title": c["title"],
            "description": c["description"],
            "transaction_count": len(c["transactions"]),
            "investigation_status": "INVESTIGATED" if has_run else "PENDING",
            "suggested_workflow_status": run_res.cerp.suggested_workflow_status if has_run else None,
            "human_review_status": HUMAN_REVIEWS.get(cid, {}).get("decision", "PENDING_REVIEW")
        })
    return summary_list


@app.post("/api/cases")
def create_case(payload: CreateCaseRequest):
    """Creates a new case from raw transaction records."""
    if payload.case_id in CASE_DATABASE:
        raise HTTPException(status_code=400, detail=f"Case '{payload.case_id}' already exists.")
    
    CASE_DATABASE[payload.case_id] = {
        "case_id": payload.case_id,
        "title": payload.title,
        "description": payload.description,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "transactions": payload.transactions,
        "status": "READY_FOR_INVESTIGATION"
    }
    return {"message": f"Case '{payload.case_id}' created successfully.", "transaction_count": len(payload.transactions)}


@app.get("/api/cases/{case_id}")
def get_case(case_id: str):
    """Retrieves full case details including transactions."""
    if case_id not in CASE_DATABASE:
        raise HTTPException(status_code=404, detail="Case not found.")
    return CASE_DATABASE[case_id]


@app.get("/api/cases/{case_id}/graph")
def get_case_graph(case_id: str):
    """
    Returns graph representation formatted for Cytoscape.js or web visualizations:
    nodes (accounts) and directed edges (transactions) with flow amounts and timestamps.
    """
    if case_id not in CASE_DATABASE:
        raise HTTPException(status_code=404, detail="Case not found.")
    
    txs = CASE_DATABASE[case_id]["transactions"]
    graph = TemporalTransactionGraph(txs)
    
    nodes = []
    for acc in graph.get_account_nodes():
        node_stats = graph.nodes[acc.account_id]
        nodes.append({
            "id": acc.account_id,
            "label": acc.account_id,
            "account_type": acc.account_type,
            "risk_tier": acc.risk_tier,
            "total_in": round(node_stats["total_in"], 2),
            "total_out": round(node_stats["total_out"], 2),
            "in_degree": node_stats["in_degree"],
            "out_degree": node_stats["out_degree"]
        })

    edges = []
    for tx in txs:
        edges.append({
            "id": tx.transaction_id,
            "source": tx.source_account,
            "target": tx.destination_account,
            "amount": tx.amount,
            "currency": tx.currency,
            "timestamp": tx.timestamp,
            "memo": tx.narrative_memo or "",
            "is_planted_defect": tx.is_planted_defect
        })

    return {
        "case_id": case_id,
        "nodes": nodes,
        "edges": edges,
        "total_volume": sum(t.amount for t in txs)
    }


@app.post("/api/cases/{case_id}/investigate")
def run_investigation(case_id: str):
    """
    Executes the bounded adversarial investigation workflow:
    Planner -> Prosecutor -> Defender -> Validator -> Stress Engine -> Reconciler -> CERP.
    """
    if case_id not in CASE_DATABASE:
        raise HTTPException(status_code=404, detail="Case not found.")

    txs = CASE_DATABASE[case_id]["transactions"]
    orchestrator = InvestigationOrchestrator(case_id, txs)
    result = orchestrator.run_investigation()
    
    # Store result in memory
    INVESTIGATION_RESULTS[case_id] = result
    CASE_DATABASE[case_id]["status"] = "INVESTIGATED"

    return result


@app.get("/api/cases/{case_id}/evidence")
def get_evidence_pack(case_id: str):
    """Retrieves frozen evidence pack for a case."""
    if case_id in INVESTIGATION_RESULTS:
        return INVESTIGATION_RESULTS[case_id].evidence_pack
    elif case_id in CASE_DATABASE:
        # Build fresh snapshot if not already investigated
        txs = CASE_DATABASE[case_id]["transactions"]
        return EvidencePackBuilder.build_evidence_pack(case_id, txs)
    else:
        raise HTTPException(status_code=404, detail="Case not found.")


@app.get("/api/cases/{case_id}/report")
def get_case_report(case_id: str):
    """Retrieves the Case Evidence Robustness Profile (CERP) report."""
    if case_id not in INVESTIGATION_RESULTS:
        # Auto-run if not yet run
        if case_id in CASE_DATABASE:
            run_investigation(case_id)
        else:
            raise HTTPException(status_code=404, detail="Case not found.")
            
    res = INVESTIGATION_RESULTS[case_id]
    review = HUMAN_REVIEWS.get(case_id)
    if review:
        res.cerp.human_review_status = "REVIEWED"
        res.cerp.human_analyst_decision = review["decision"]
        res.cerp.human_analyst_notes = review["analyst_notes"]
        res.cerp.reviewed_at = review["timestamp"]

    return res.cerp


@app.get("/api/cases/{case_id}/audit")
def get_case_audit(case_id: str):
    """Retrieves ordered audit events for the case."""
    if case_id not in INVESTIGATION_RESULTS:
        raise HTTPException(status_code=404, detail="Investigation has not been run for this case yet.")
    return INVESTIGATION_RESULTS[case_id].audit_events


@app.post("/api/cases/{case_id}/review")
def record_human_review(case_id: str, payload: HumanReviewRequest):
    """Records human compliance analyst determination."""
    if case_id not in CASE_DATABASE:
        raise HTTPException(status_code=404, detail="Case not found.")

    review_record = {
        "case_id": case_id,
        "decision": payload.decision,
        "analyst_name": payload.analyst_name,
        "analyst_notes": payload.analyst_notes,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    HUMAN_REVIEWS[case_id] = review_record

    # Log to audit trail if investigation exists
    if case_id in INVESTIGATION_RESULTS:
        INVESTIGATION_RESULTS[case_id].audit_events.append(AuditEvent(
            event_id=f"AUDIT-REV-{len(INVESTIGATION_RESULTS[case_id].audit_events)+1:03d}",
            case_id=case_id,
            timestamp=review_record["timestamp"],
            actor=f"analyst:{payload.analyst_name}",
            action="HUMAN_REVIEW_DECISION_RECORDED",
            details={
                "decision": payload.decision,
                "notes": payload.analyst_notes
            }
        ))
        INVESTIGATION_RESULTS[case_id].cerp.human_review_status = "REVIEWED"
        INVESTIGATION_RESULTS[case_id].cerp.human_analyst_decision = payload.decision
        INVESTIGATION_RESULTS[case_id].cerp.human_analyst_notes = payload.analyst_notes
        INVESTIGATION_RESULTS[case_id].cerp.reviewed_at = review_record["timestamp"]

    return {"message": "Human review recorded successfully.", "review": review_record}


@app.post("/api/cases/{case_id}/perturb")
def simulate_perturbation(case_id: str, excluded_tx_id: str = Body(..., embed=True)):
    """
    Interactive diagnostic tool: Simulates excluding a specific transaction
    and computes the real-time delta on pattern detection and graph topology.
    """
    if case_id not in CASE_DATABASE:
        raise HTTPException(status_code=404, detail="Case not found.")

    all_txs = CASE_DATABASE[case_id]["transactions"]
    remaining_txs = [t for t in all_txs if t.transaction_id != excluded_tx_id]

    graph_orig = TemporalTransactionGraph(all_txs)
    patterns_orig = CandidatePatternDetector(graph_orig).detect_all_patterns()

    graph_pert = TemporalTransactionGraph(remaining_txs)
    patterns_pert = CandidatePatternDetector(graph_pert).detect_all_patterns()

    return {
        "case_id": case_id,
        "excluded_transaction_id": excluded_tx_id,
        "original_pattern_count": len(patterns_orig),
        "perturbed_pattern_count": len(patterns_pert),
        "original_patterns": [p.pattern_type for p in patterns_orig],
        "remaining_patterns": [p.pattern_type for p in patterns_pert],
        "patterns_broken": [
            p.title for p in patterns_orig 
            if p.pattern_type not in [p2.pattern_type for p2 in patterns_pert]
        ]
    }


@app.get("/api/benchmark/run")
def run_benchmark():
    """Runs the 3-arm comparative evaluation benchmark against planted defects."""
    return BenchmarkRunner.run_all_baselines()


# Static file serving for Frontend UI
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_frontend_index():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
