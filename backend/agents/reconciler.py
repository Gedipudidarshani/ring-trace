"""
RingTrace: Reconciliation Agent
Synthesizes verified Prosecutor claims, Defender counter-claims, stress test outcomes,
and explicit unknowns into a balanced, transparent case assessment.
Does NOT force a guilty/innocent binary or compute an artificial "guilt score".
"""

from typing import List, Dict, Any
from backend.models.schemas import (
    EvidencePack, 
    StructuredClaim, 
    StressTestResult, 
    CERPReport
)


class ReconciliationAgent:
    """
    Reconciles evidence and diagnostic stress tests.
    Determines actionable post-alert workflow recommendations for compliance teams.
    """

    def __init__(
        self,
        evidence_pack: EvidencePack,
        verified_prosecutor_claims: List[StructuredClaim],
        verified_defender_claims: List[StructuredClaim],
        stress_tests: List[StressTestResult]
    ):
        self.evidence_pack = evidence_pack
        self.prosecutor_claims = verified_prosecutor_claims
        self.defender_claims = verified_defender_claims
        self.stress_tests = stress_tests

    def reconcile(self) -> Dict[str, Any]:
        """Synthesizes the case findings into the CERP recommendation."""
        # Find test results
        prov_test = next((t for t in self.stress_tests if t.test_name == "provenance_integrity"), None)
        chrono_test = next((t for t in self.stress_tests if t.test_name == "temporal_consistency"), None)
        comp_test = next((t for t in self.stress_tests if t.test_name == "competing_hypotheses"), None)
        contra_test = next((t for t in self.stress_tests if t.test_name == "contradictions_and_gaps"), None)
        sens_test = next((t for t in self.stress_tests if t.test_name == "pivotal_evidence_sensitivity"), None)

        provenance_ok = (prov_test.status == "PASSED") if prov_test else False
        chrono_ok = (chrono_test.status == "PASSED") if chrono_test else False
        is_sensitive = (sens_test.status == "SENSITIVE") if sens_test else False

        # Check contradictions
        contradictions = []
        if contra_test and contra_test.violations:
            for v in contra_test.violations:
                contradictions.append(v.get("contradiction", "Unspecified contradiction"))

        # Check alternative claims
        has_substantive_alternative = any(
            c.claim_type in ["recurring_flow", "commercial_context"] 
            for c in self.defender_claims
        )

        # Formulate workflow status according to bounded business rules:
        if not provenance_ok or not chrono_ok:
            workflow_status = "INSUFFICIENT_EVIDENCE"
            explanation = (
                "Case contains corrupted provenance or chronological impossibilities. "
                "Investigation halted before alert escalation. System data audit required."
            )
        elif is_sensitive and has_substantive_alternative:
            workflow_status = "REQUEST_MORE_INFORMATION"
            explanation = (
                "Case is sensitive to a single pivotal transaction, and Defender identified plausible "
                "recurring/commercial indicators. Request invoice documentation and customer KYC profile before escalations."
            )
        elif has_substantive_alternative and not self.evidence_pack.patterns:
            workflow_status = "CLOSURE_REVIEW"
            explanation = (
                "Observed activity is fully explained by documented recurring commercial patterns with no "
                "high-severity flow anomalies. Recommend closing alert subject to routine sampling review."
            )
        else:
            workflow_status = "ESCALATE_FOR_HUMAN_REVIEW"
            explanation = (
                "Verified multi-hop or circular transaction pattern detected with high velocity. "
                "No conclusive commercial justification found in available records. Escalated for human analyst determination."
            )

        # Supporting and counter record references
        supporting_records = []
        for c in self.prosecutor_claims:
            supporting_records.extend(c.transaction_ids)
        supporting_records = list(set(supporting_records))

        counter_records = []
        for c in self.defender_claims:
            counter_records.extend(c.transaction_ids)
        counter_records = list(set(counter_records))

        # Pivotal transaction ID
        pivotal_tx_id = sens_test.pivotal_transaction_id if sens_test else None

        reconciliation_summary = {
            "suggested_workflow_status": workflow_status,
            "workflow_explanation": explanation,
            "provenance_status": "VERIFIED" if provenance_ok else "COMPROMISED",
            "chronology_status": "VERIFIED" if chrono_ok else "VIOLATED",
            "graph_path_status": "VALID" if (self.evidence_pack.paths and chrono_ok) else "BROKEN_OR_EMPTY",
            "suspicious_hypothesis": (
                self.prosecutor_claims[0].statement 
                if self.prosecutor_claims 
                else "No suspicious hypothesis formulated."
            ),
            "suspicious_hypothesis_status": "SUPPORTED" if self.prosecutor_claims else "UNVERIFIED",
            "supporting_records": supporting_records,
            "alternative_hypothesis": (
                self.defender_claims[0].statement 
                if self.defender_claims 
                else "No alternative hypothesis formulated."
            ),
            "alternative_hypothesis_status": "PLAUSIBLE" if has_substantive_alternative else "NO_SUPPORT_FOUND",
            "counter_records": counter_records,
            "contradictions": contradictions,
            "missing_context_unknowns": self.evidence_pack.missing_fields,
            "pivotal_dependency": pivotal_tx_id,
            "sensitivity_result": (
                f"SENSITIVE: Case narrative depends heavily on pivotal transaction '{pivotal_tx_id}'." 
                if is_sensitive 
                else "ROBUST: Narrative does not rely solely on a single isolated transaction."
            )
        }

        return reconciliation_summary
