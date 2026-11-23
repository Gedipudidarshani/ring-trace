"""
RingTrace: Prosecutor / Suspicious-Hypothesis Builder
Constructs testable suspicious-activity claims anchored to verified transaction IDs and computed metrics.
Enforces strict separation between objective factual observations and subjective typology interpretations.
"""

from typing import List, Dict, Any
from backend.models.schemas import EvidencePack, StructuredClaim, DetectedPattern


class ProsecutorAgent:
    """
    Formulates structured claims supporting the suspicious hypothesis.
    Cites specific transaction IDs and computed graph indicators.
    """

    def __init__(self, evidence_pack: EvidencePack):
        self.evidence_pack = evidence_pack

    def build_suspicious_claims(self) -> List[StructuredClaim]:
        claims: List[StructuredClaim] = []
        patterns = self.evidence_pack.patterns
        paths = self.evidence_pack.paths

        claim_idx = 0

        # Claim 1: High-level topology finding
        if patterns:
            top_p = patterns[0]
            claim_idx += 1
            claims.append(StructuredClaim(
                claim_id=f"CLM-PROS-{claim_idx:03d}",
                agent_role="prosecutor",
                claim_type="pattern_interpretation",
                statement=(
                    f"Flow network exhibits {top_p.title}. "
                    f"Involves accounts {top_p.involved_accounts[:3]} and {len(top_p.involved_transactions)} sequential transfers."
                ),
                transaction_ids=top_p.involved_transactions[:4],
                supporting_evidence_ids=[top_p.pattern_id],
                confidence_label="supported",
                unknowns=["customer_economic_purpose"],
                is_interpretation=True,
                validation_status="pending"
            ))

        # Claim 2: Temporal velocity / rapid pass-through observation
        rapid_patterns = [p for p in patterns if p.pattern_type == "rapid_pass_through"]
        if rapid_patterns:
            rp = rapid_patterns[0]
            claim_idx += 1
            claims.append(StructuredClaim(
                claim_id=f"CLM-PROS-{claim_idx:03d}",
                agent_role="prosecutor",
                claim_type="rapid_pass_through",
                statement=(
                    f"Intermediary account '{rp.metrics.get('intermediary_account')}' received inflow and forwarded "
                    f"funds within {rp.metrics.get('transit_delay_hours')} hours with {rp.metrics.get('flow_retention_ratio')*100:.0f}% pass-through ratio."
                ),
                transaction_ids=rp.involved_transactions,
                supporting_evidence_ids=[rp.pattern_id],
                confidence_label="verified",
                unknowns=["business_nature_of_intermediary"],
                is_interpretation=False,  # This is a measurable mathematical fact
                validation_status="pending"
            ))

        # Claim 3: Multi-hop layering chain
        if paths and len(paths[0].accounts) >= 3:
            p = paths[0]
            claim_idx += 1
            claims.append(StructuredClaim(
                claim_id=f"CLM-PROS-{claim_idx:03d}",
                agent_role="prosecutor",
                claim_type="temporal_observation",
                statement=(
                    f"Chronologically sequential flow traversed {len(p.accounts)} accounts over {p.total_duration_hours} hours. "
                    f"Total transacted volume across chain: {p.total_amount:.2f}."
                ),
                transaction_ids=p.transaction_ids[:4],
                supporting_evidence_ids=[p.path_id],
                confidence_label="verified",
                unknowns=["source_of_wealth"],
                is_interpretation=False,
                validation_status="pending"
            ))

        return claims
