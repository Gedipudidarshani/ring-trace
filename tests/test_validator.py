"""
Tests for Deterministic Claim Validator
"""

import unittest
from backend.models.schemas import Transaction, StructuredClaim
from backend.evidence.evidence_pack import EvidencePackBuilder
from backend.stress_tests.validator import DeterministicClaimValidator
from backend.data.sample_cases import get_case_mule_ring


class TestClaimValidator(unittest.TestCase):

    def setUp(self):
        self.txs = get_case_mule_ring()
        self.evidence_pack = EvidencePackBuilder.build_evidence_pack("RT-1042", self.txs)
        self.validator = DeterministicClaimValidator(self.evidence_pack)

    def test_valid_claim_acceptance(self):
        """A claim referencing valid transaction IDs and factual chronology is accepted."""
        claim = StructuredClaim(
            claim_id="TEST-CLM-001",
            agent_role="prosecutor",
            claim_type="temporal_observation",
            statement="Funds moved sequentially from ACC-ORIGIN-01 to ACC-LAYER-02 and then to ACC-LAYER-03.",
            transaction_ids=["TX-RING-001", "TX-RING-002"],
            supporting_evidence_ids=["PATH-001"],
            is_interpretation=False
        )
        is_valid, reason = self.validator.validate_claim(claim)
        self.assertTrue(is_valid)
        self.assertIn("VERIFIED", reason)

    def test_fabricated_transaction_id_rejection(self):
        """A claim citing a non-existent/hallucinated transaction ID must be rejected immediately."""
        claim = StructuredClaim(
            claim_id="TEST-CLM-002",
            agent_role="prosecutor",
            claim_type="temporal_observation",
            statement="Account A sent 500,000 to Account X.",
            transaction_ids=["TX-NONEXISTENT-9999"],  # Hallucinated ID
            supporting_evidence_ids=[],
            is_interpretation=False
        )
        is_valid, reason = self.validator.validate_claim(claim)
        self.assertFalse(is_valid)
        self.assertIn("REJECTED", reason)
        self.assertIn("does not exist", reason)

    def test_chronological_violation_rejection(self):
        """A claim presenting transactions in reverse chronological order must be rejected."""
        claim = StructuredClaim(
            claim_id="TEST-CLM-003",
            agent_role="prosecutor",
            claim_type="rapid_pass_through",
            statement="Funds flowed from TX-RING-002 backwards to TX-RING-001.",
            transaction_ids=["TX-RING-002", "TX-RING-001"],  # 002 is 11:15, 001 is 08:00
            supporting_evidence_ids=[],
            is_interpretation=False
        )
        is_valid, reason = self.validator.validate_claim(claim)
        self.assertFalse(is_valid)
        self.assertIn("Chronological violation", reason)

    def test_subjective_intent_word_must_be_interpretation(self):
        """Claims asserting criminal guilt or 'mule' intent cannot be classified as objective facts."""
        claim = StructuredClaim(
            claim_id="TEST-CLM-004",
            agent_role="prosecutor",
            claim_type="pattern_interpretation",
            statement="This is a fraudulent money mule ring engaging in illicit money laundering.",
            transaction_ids=["TX-RING-001"],
            supporting_evidence_ids=[],
            is_interpretation=False  # Incorrectly labeled as objective fact!
        )
        is_valid, reason = self.validator.validate_claim(claim)
        self.assertFalse(is_valid)
        self.assertIn("Must be flagged as an interpretation", reason)


if __name__ == "__main__":
    unittest.main()
