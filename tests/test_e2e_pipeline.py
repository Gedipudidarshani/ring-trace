"""
End-to-End Pipeline Integration Test
"""

import unittest
from backend.agents.orchestrator import InvestigationOrchestrator
from backend.data.sample_cases import get_case_mule_ring, get_case_payroll_false_positive


class TestE2EPipeline(unittest.TestCase):

    def test_full_pipeline_mule_ring(self):
        """Runs the entire pipeline on RT-1042 and verifies CERP generation and audit log."""
        txs = get_case_mule_ring()
        orchestrator = InvestigationOrchestrator("RT-1042", txs)
        res = orchestrator.run_investigation()

        # Check evidence pack
        self.assertEqual(res.evidence_pack.case_id, "RT-1042")
        self.assertTrue(len(res.evidence_pack.transactions) == 5)
        self.assertTrue(len(res.evidence_pack.patterns) >= 1)

        # Check claims
        self.assertTrue(len(res.prosecutor_claims) >= 1)
        self.assertTrue(len(res.defender_claims) >= 1)

        # Check CERP
        cerp = res.cerp
        self.assertEqual(cerp.case_id, "RT-1042")
        self.assertEqual(cerp.provenance_status, "VERIFIED")
        self.assertEqual(cerp.chronology_status, "VERIFIED")
        self.assertIn(cerp.suggested_workflow_status, ["ESCALATE_FOR_HUMAN_REVIEW", "REQUEST_MORE_INFORMATION"])
        self.assertIsNotNone(cerp.pivotal_dependency)

        # Check audit trail
        self.assertTrue(len(res.audit_events) >= 8)
        actions = [e.action for e in res.audit_events]
        self.assertIn("INGESTION_STARTED", actions)
        self.assertIn("EVIDENCE_PACK_FROZEN", actions)
        self.assertIn("INVESTIGATION_PLAN_CREATED", actions)
        self.assertIn("DETERMINISTIC_VALIDATION_COMPLETED", actions)
        self.assertIn("INVESTIGATION_COMPLETED", actions)

    def test_full_pipeline_payroll_reconciliation(self):
        """Runs the pipeline on the payroll scenario RT-2091 and verifies Defender tool discoveries."""
        txs = get_case_payroll_false_positive()
        orchestrator = InvestigationOrchestrator("RT-2091", txs)
        res = orchestrator.run_investigation()

        # Defender should have found recurring payments of 45,000 and salary memos
        def_types = [c.claim_type for c in res.defender_claims]
        self.assertIn("recurring_flow", def_types)
        self.assertIn("commercial_context", def_types)

        # Reconciler should recognize commercial pretexts and request info or review closure
        cerp = res.cerp
        self.assertEqual(cerp.alternative_hypothesis_status, "PLAUSIBLE")
        self.assertTrue(len(cerp.contradictions) >= 1)


if __name__ == "__main__":
    unittest.main()
