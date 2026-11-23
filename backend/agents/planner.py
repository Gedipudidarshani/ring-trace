"""
RingTrace: Bounded Investigation Planner
Plans the post-alert case inquiry with strict call budgets, fixed stopping conditions,
and authorized tool permissions. Prevents unconstrained agentic looping.
"""

from typing import Dict, Any
from backend.models.schemas import EvidencePack


class InvestigationPlanner:
    """
    Formulates a bounded investigation plan for the post-alert case.
    Sets explicit tool budgets and hypothesis goals.
    """

    def __init__(self, evidence_pack: EvidencePack, tool_budget: int = 4):
        self.evidence_pack = evidence_pack
        self.tool_budget = tool_budget

    def create_investigation_plan(self) -> Dict[str, Any]:
        """Generates the structured plan for the Prosecutor and Defender."""
        top_pattern = (
            self.evidence_pack.patterns[0] 
            if self.evidence_pack.patterns 
            else None
        )
        
        target_typology = top_pattern.pattern_type if top_pattern else "unspecified_anomaly"
        target_accounts = top_pattern.involved_accounts if top_pattern else []

        plan = {
            "case_id": self.evidence_pack.case_id,
            "target_typology": target_typology,
            "primary_pattern_id": top_pattern.pattern_id if top_pattern else None,
            "focus_accounts": target_accounts,
            "investigation_budget": {
                "max_prosecutor_claims": 5,
                "max_defender_tool_calls": self.tool_budget,
                "max_defender_claims": 5,
                "allow_external_web": False,
                "read_only_case_evidence": True
            },
            "stopping_criteria": [
                "Single sequential pass completed",
                "Deterministic claim validation executed",
                "All 5 evidence stress tests computed"
            ],
            "hypotheses_to_test": [
                f"Suspicious Hypothesis: Directed funds movement exhibits structured {target_typology}.",
                "Alternative Hypothesis: Transactions represent legitimate commercial settlement, batch payroll, or routine recurring transfers."
            ]
        }
        return plan
