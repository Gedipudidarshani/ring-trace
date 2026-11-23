"""
Tests for Comparative Benchmark Runner
"""

import unittest
from backend.evaluation.benchmark import BenchmarkRunner


class TestBenchmarkRunner(unittest.TestCase):

    def test_benchmark_execution(self):
        """Runs the 3-arm benchmark evaluation and verifies comparative metric calculations."""
        benchmark_results = BenchmarkRunner.run_all_baselines()
        
        self.assertEqual(benchmark_results["cases_evaluated"], 4)
        self.assertIn("results_by_case", benchmark_results)
        self.assertIn("comparative_metrics_table", benchmark_results)

        table = benchmark_results["comparative_metrics_table"]
        self.assertTrue(len(table) >= 4)
        
        # Check planted defect row
        defect_row = next(r for r in table if "Planted Defect" in r["metric"])
        self.assertIn("100%", defect_row["ringtrace"])
        self.assertIn("0%", defect_row["detector_only"])


if __name__ == "__main__":
    unittest.main()
