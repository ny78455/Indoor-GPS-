import unittest

from VLCL_AI.reproduction.metrics import comparison_metrics, monte_carlo_summary, zero_error_ber_upper_bound


class TestReproductionMetrics(unittest.TestCase):
    def test_comparison_metrics_identical_series(self):
        metrics = comparison_metrics([1, 2, 3], [1, 2, 3])
        self.assertEqual(metrics["mae"], 0.0)
        self.assertEqual(metrics["rmse"], 0.0)

    def test_zero_error_bound_is_not_zero(self):
        self.assertGreater(zero_error_ber_upper_bound(10000), 0.0)

    def test_monte_carlo_summary_has_interval(self):
        result = monte_carlo_summary([1.0, 2.0, 3.0])
        self.assertLess(result["ci95_lower"], result["mean"])
        self.assertGreater(result["ci95_upper"], result["mean"])
