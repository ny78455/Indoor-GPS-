import unittest
import numpy as np

from VLCL_AI.communication.ber import BERCalculator
from VLCL_AI.communication.rate import RateCalculator
from VLCL_AI.communication.snr import compute_communication_snr
from VLCL_AI.reproduction.equations import eq01_snr, eq02_square_qam_ber, eq03_rate


class TestPaperEquationsOneToThree(unittest.TestCase):
    def test_eq01_coherent_sqrt_power_sum(self):
        powers = np.array([[1.0, 4.0]])
        gains = np.array([[0.5], [0.25]])
        expected = eq01_snr(0.5, powers, gains, 0.25)
        actual = compute_communication_snr(0.5, powers, gains, 0.25)
        np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)

    def test_eq02_paper_square_qam_expression(self):
        expected = eq02_square_qam_ber(11.0, 16)
        actual = BERCalculator.compute_analytical_qam(11.0, 16)
        self.assertAlmostEqual(float(actual), expected, places=14)

    def test_eq03_unallocated_carrier_contributes_nothing(self):
        rho = np.array([1, 0, 1])
        orders = np.array([4, 64, 16])
        expected = eq03_rate(125000.0, rho, orders)
        actual = RateCalculator.compute_user_rates([0, 2], np.full(3, 125000.0), orders, cp_ratio=0.0)["raw_rate_bps"]
        self.assertEqual(actual, expected)
