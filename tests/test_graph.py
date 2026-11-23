"""
Tests for Temporal Transaction Graph & Pattern Detectors
"""

import unittest
from backend.models.schemas import Transaction
from backend.graph.temporal_graph import TemporalTransactionGraph
from backend.graph.detectors import CandidatePatternDetector
from backend.data.sample_cases import get_case_mule_ring, get_case_payroll_false_positive


class TestTemporalGraph(unittest.TestCase):

    def setUp(self):
        self.mule_txs = get_case_mule_ring()
        self.graph = TemporalTransactionGraph(self.mule_txs)
        self.detector = CandidatePatternDetector(self.graph)

    def test_node_in_out_degree_and_volume(self):
        """Verify accounts receive correct in/out degree and balance aggregations."""
        origin_node = self.graph.nodes["ACC-ORIGIN-01"]
        self.assertEqual(origin_node["out_degree"], 1)
        self.assertEqual(origin_node["in_degree"], 1)
        self.assertEqual(origin_node["total_out"], 485000.0)
        self.assertEqual(origin_node["total_in"], 455000.0)

    def test_cycle_detection(self):
        """Verify that circular flow A -> B -> C -> D -> E -> A is correctly discovered."""
        cycles = self.graph.find_temporal_cycles(max_hops=6)
        self.assertTrue(len(cycles) >= 1)
        
        cycle = cycles[0]
        self.assertEqual(cycle["hop_count"], 5)
        self.assertEqual(cycle["accounts"][0], cycle["accounts"][-1])
        self.assertEqual(cycle["accounts"][0], "ACC-ORIGIN-01")

    def test_time_respecting_paths(self):
        """Verify that discovered paths strictly respect causality t_i <= t_{i+1}."""
        paths = self.graph.find_time_respecting_paths(max_hops=6, max_window_hours=48.0)
        self.assertTrue(len(paths) > 0)
        for p in paths:
            self.assertTrue(p.is_chronological)
            self.assertTrue(p.total_duration_hours >= 0)

    def test_rapid_pass_through_detection(self):
        """Verify that intermediary accounts with rapid fund forwarding are flagged."""
        patterns = self.detector.detect_rapid_pass_through()
        self.assertTrue(len(patterns) >= 1)
        p = patterns[0]
        self.assertEqual(p.pattern_type, "rapid_pass_through")
        self.assertIn("transit_delay_hours", p.metrics)
        self.assertTrue(p.metrics["transit_delay_hours"] <= 6.0)

    def test_fan_out_detection(self):
        """Verify corporate payroll fan-out detection."""
        payroll_txs = get_case_payroll_false_positive()
        p_graph = TemporalTransactionGraph(payroll_txs)
        p_detector = CandidatePatternDetector(p_graph)
        fan_outs = p_detector.detect_fan_out()
        self.assertTrue(len(fan_outs) >= 1)
        self.assertEqual(fan_outs[0].metrics["distributor_account"], "ACC-PAYROLL-DISBURSE")


if __name__ == "__main__":
    unittest.main()
