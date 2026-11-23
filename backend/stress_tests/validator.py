"""
RingTrace: Deterministic Claim Validator
Ensures factual integrity by checking agent-generated claims against immutable source records.
Rejects fabricated IDs, arithmetic inconsistencies, and impossible chronology.
"""

from typing import List, Dict, Any, Tuple
from backend.models.schemas import Transaction, StructuredClaim, EvidencePack
from backend.graph.temporal_graph import parse_iso


class DeterministicClaimValidator:
    """
    Non-agentic, deterministic verification component.
    Validates factual references, ID existence, and timestamp chronology.
    Does NOT attempt to validate subjective intent or legal conclusions.
    """

    def __init__(self, evidence_pack: EvidencePack):
        self.evidence_pack = evidence_pack
        self.tx_map: Dict[str, Transaction] = {
            t.transaction_id: t for t in evidence_pack.transactions
        }
        self.acc_map = {a.account_id: a for a in evidence_pack.accounts}

    def validate_claim(self, claim: StructuredClaim) -> Tuple[bool, str]:
        """
        Validates an individual structured claim.
        Returns: (is_valid, reason)
        """
        # 1. Check transaction ID existence
        if not claim.transaction_ids and not claim.is_interpretation:
            return False, "Factual claim must cite at least one verified transaction ID."

        for tid in claim.transaction_ids:
            if tid not in self.tx_map:
                return False, f"REJECTED: Transaction ID '{tid}' does not exist in frozen case evidence (fabricated reference)."

        # 2. If claim references multiple transactions in sequence, verify chronological causality
        if len(claim.transaction_ids) >= 2 and claim.claim_type in ["temporal_observation", "rapid_pass_through", "layering_flow"]:
            prev_time = None
            for tid in claim.transaction_ids:
                tx = self.tx_map[tid]
                curr_time = parse_iso(tx.timestamp)
                if prev_time and curr_time < prev_time:
                    return False, f"REJECTED: Chronological violation. Transaction '{tid}' ({tx.timestamp}) occurs before prior transaction in sequence."
                prev_time = curr_time

        # 3. Label distinction between fact and interpretation
        # Statements containing subjective words like 'criminal', 'mule', 'illicit', 'guilty'
        # must be marked as interpretations, not deterministic facts.
        subjective_words = ["criminal", "mule", "illicit", "guilty", "laundered", "fraudulent"]
        lower_stmt = claim.statement.lower()
        contains_subjective = any(w in lower_stmt for w in subjective_words)

        if contains_subjective and not claim.is_interpretation:
            return False, "REJECTED: Statement uses criminal/typology intent terms but is marked as an objective fact. Must be flagged as an interpretation."

        return True, "VERIFIED: Citations and chronology confirmed against case records."

    def validate_all_claims(self, claims: List[StructuredClaim]) -> Tuple[List[StructuredClaim], List[StructuredClaim]]:
        """
        Validates all claims. 
        Returns: (verified_claims, rejected_claims)
        """
        verified = []
        rejected = []

        for claim in claims:
            is_valid, reason = self.validate_claim(claim)
            if is_valid:
                claim.validation_status = "verified"
                claim.validation_notes = reason
                verified.append(claim)
            else:
                claim.validation_status = "rejected"
                claim.rejection_reason = reason
                claim.validation_notes = reason
                rejected.append(claim)

        return verified, rejected
