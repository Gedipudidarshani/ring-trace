"""
RingTrace: Bounded Investigation Orchestrator
Coordinates the post-alert investigation sequence:
Planner -> Prosecutor -> Defender (Read-only Tools) -> Validator -> Stress Tests -> Reconciler -> CERP.
Maintains an immutable append-only audit trail of every agent action and validation decision.
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
import uuid

from backend.models.schemas import (
    Transaction,
    EvidencePack,
    StructuredClaim,
    ToolCallRecord,
    StressTestResult,
    CERPReport,
    AuditEvent,
    InvestigationRunResult
)
from backend.evidence.evidence_pack import EvidencePackBuilder
from backend.agents.planner import InvestigationPlanner
from backend.agents.prosecutor import ProsecutorAgent
from backend.agents.defender import DefenderAgent
from backend.agents.reconciler import ReconciliationAgent
from backend.stress_tests.validator import DeterministicClaimValidator
from backend.stress_tests.engine import StressTestEngine


class InvestigationOrchestrator:
    """
    Executes a bounded, fully reproducible investigation run.
    Guarantees deterministic stopping, budget enforcement, and transparent auditing.
    """

    def __init__(self, case_id: str, transactions: List[Transaction]):
        self.case_id = case_id
        self.transactions = transactions
        self.audit_events: List[AuditEvent] = []

    def _log_audit(self, actor: str, action: str, details: Dict[str, Any]):
        event = AuditEvent(
            event_id=f"AUDIT-{uuid.uuid4().hex[:8].upper()}",
            case_id=self.case_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            actor=actor,
            action=action,
            details=details
        )
        self.audit_events.append(event)

    def run_investigation(self) -> InvestigationRunResult:
        """Executes the complete end-to-end investigation workflow."""
        self._log_audit("system", "INGESTION_STARTED", {"transaction_count": len(self.transactions)})

        # 1. Build immutable Evidence Pack
        evidence_pack = EvidencePackBuilder.build_evidence_pack(self.case_id, self.transactions)
        self._log_audit("system", "EVIDENCE_PACK_FROZEN", {
            "provenance_hash": evidence_pack.provenance_hash,
            "patterns_detected": len(evidence_pack.patterns),
            "paths_discovered": len(evidence_pack.paths)
        })

        # 2. Investigation Planner
        planner = InvestigationPlanner(evidence_pack, tool_budget=4)
        plan = planner.create_investigation_plan()
        self._log_audit("planner", "INVESTIGATION_PLAN_CREATED", plan)

        # 3. Prosecutor: Formulate suspicious claims
        prosecutor = ProsecutorAgent(evidence_pack)
        raw_prosecutor_claims = prosecutor.build_suspicious_claims()
        self._log_audit("prosecutor", "SUSPICIOUS_CLAIMS_FORMULATED", {
            "claim_count": len(raw_prosecutor_claims)
        })

        # 4. Defender: Execute read-only tools and formulate alternative claims
        defender = DefenderAgent(evidence_pack)
        raw_defender_claims, tool_calls = defender.execute_read_only_tools()
        for tc in tool_calls:
            self._log_audit("defender", f"TOOL_CALL::{tc.tool_name}", {
                "params": tc.query_params,
                "matches": len(tc.matched_record_ids),
                "duration_ms": tc.execution_time_ms
            })
        self._log_audit("defender", "ALTERNATIVE_CLAIMS_FORMULATED", {
            "claim_count": len(raw_defender_claims)
        })

        # 5. Deterministic Claim Validator: Filter unverified or hallucinated claims
        validator = DeterministicClaimValidator(evidence_pack)
        all_raw_claims = raw_prosecutor_claims + raw_defender_claims
        verified_claims, rejected_claims = validator.validate_all_claims(all_raw_claims)
        
        self._log_audit("validator", "DETERMINISTIC_VALIDATION_COMPLETED", {
            "verified_count": len(verified_claims),
            "rejected_count": len(rejected_claims),
            "rejections": [
                {"claim_id": c.claim_id, "reason": c.rejection_reason} 
                for c in rejected_claims
            ]
        })

        verified_pros = [c for c in verified_claims if c.agent_role == "prosecutor"]
        verified_def = [c for c in verified_claims if c.agent_role == "defender"]

        # 6. Stress Test Engine: Run 5 case-level stress tests
        stress_engine = StressTestEngine(evidence_pack)
        stress_results = stress_engine.run_all_stress_tests(verified_pros, verified_def)
        for st in stress_results:
            self._log_audit("stress_engine", f"STRESS_TEST::{st.test_name}", {
                "status": st.status,
                "checked": st.checked_count,
                "failed": st.failed_count,
                "pivotal_tx": st.pivotal_transaction_id
            })

        # 7. Reconciler: Synthesize findings and formulate CERP recommendation
        reconciler = ReconciliationAgent(
            evidence_pack=evidence_pack,
            verified_prosecutor_claims=verified_pros,
            verified_defender_claims=verified_def,
            stress_tests=stress_results
        )
        summary = reconciler.reconcile()
        self._log_audit("reconciler", "EVIDENCE_RECONCILED", {
            "workflow_status": summary["suggested_workflow_status"],
            "pivotal_dependency": summary["pivotal_dependency"]
        })

        # 8. Assemble CERP Report
        cerp = CERPReport(
            case_id=self.case_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            provenance_status=summary["provenance_status"],
            chronology_status=summary["chronology_status"],
            graph_path_status=summary["graph_path_status"],
            suspicious_hypothesis=summary["suspicious_hypothesis"],
            suspicious_hypothesis_status=summary["suspicious_hypothesis_status"],
            supporting_records=summary["supporting_records"],
            alternative_hypothesis=summary["alternative_hypothesis"],
            alternative_hypothesis_status=summary["alternative_hypothesis_status"],
            counter_records=summary["counter_records"],
            contradictions=summary["contradictions"],
            missing_context_unknowns=summary["missing_context_unknowns"],
            pivotal_dependency=summary["pivotal_dependency"],
            sensitivity_result=summary["sensitivity_result"],
            suggested_workflow_status=summary["suggested_workflow_status"],
            workflow_explanation=summary["workflow_explanation"]
        )

        self._log_audit("system", "INVESTIGATION_COMPLETED", {
            "final_workflow_status": cerp.suggested_workflow_status
        })

        return InvestigationRunResult(
            case_id=self.case_id,
            evidence_pack=evidence_pack,
            planner_plan=plan,
            prosecutor_claims=verified_pros,
            defender_claims=verified_def,
            defender_tool_calls=tool_calls,
            stress_test_results=stress_results,
            rejected_claims=rejected_claims,
            reconciler_summary=summary,
            cerp=cerp,
            audit_events=self.audit_events
        )
