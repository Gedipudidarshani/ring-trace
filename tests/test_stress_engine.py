"""
Tests for Stress Test Engine & Pivotal Evidence Sensitivity
"""

import unittest
from backend.evidence.evidence_pack import EvidencePackBuilder
from backend.stress_tests.engine import StressTestEngine
from backend.agents.prosecutor import ProsecutorAgent
from backend.agents.defender import DefenderAgent
from backend.data.sample_cases import get_case_mule_ring, get_case_planted_defects


class TestStressTestEngine(unittest.TestCase):

    def test_mule_ring_pivotal_sensitivity(self):
        """
        Verify that in the circular ring case RT-1042, the diagnostic sensitivity test
        identifies the pivotal transaction and discloses that removing it breaks the cycle.
        """
        txs = get_case_mule_ring()
        evidence_pack = EvidencePackBuilder.build_evidence_pack("RT-1042", txs)
        
        pros = ProsecutorAgent(evidence_pack).build_suspicious_claims()
        def_claims, _ = DefenderAgent(evidence_pack).execute_read_only_tools()

        engine = StressTestEngine(evidence_pack)
        results = engine.run_all_stress_tests(pros, def_claims)
        
        # Test 5: Pivotal Sensitivity
        sens_test = next(t for t in results if t.test_name == "pivotal_evidence_sensitivity")
        self.assertEqual(sens_test.status, "SENSITIVE")
        self.assertIsNotNone(sens_test.pivotal_transaction_id)
        self.assertTrue(sens_test.sensitivity_impact["cycle_broken_on_removal"])
        self.assertTrue(sens_test.sensitivity_impact["is_case_fragile"])

    def test_planted_defects_detection(self):
        """
        Verify that planted defects (time travel timestamp and negative amount)
        are successfully caught by Stress Tests 1 & 2.
        """
        defect_txs = get_case_planted_defects()
        evidence_pack = EvidencePackBuilder.build_evidence_pack("RT-4088", defect_txs)
        
        pros = ProsecutorAgent(evidence_pack).build_suspicious_claims()
        def_claims, _ = DefenderAgent(evidence_pack).execute_read_only_tools()

        engine = StressTestEngine(evidence_pack)
        results = engine.run_all_stress_tests(pros, def_claims)
        
        prov_test = next(t for t in results if t.test_name == "provenance_integrity")
        self.assertEqual(prov_test.status, "FAILED")
        self.assertTrue(any(v["type"] == "non_positive_amount" for v in prov_test.violations))


if __name__ == "__main__":
    unittest.main()
