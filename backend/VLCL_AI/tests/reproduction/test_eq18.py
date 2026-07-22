import unittest
import numpy as np

from VLCL_AI.communication.pre_equalizer import PreEqualizer
from VLCL_AI.reproduction.equations import eq18_pre_equalized


class TestPaperEquationEighteen(unittest.TestCase):
    def test_sqrt_power_and_inverse_are_applied_once(self):
        symbols = np.array([1 + 1j, -1 + 1j])
        response = np.array([.8 + 0j, .5 + 0j])
        expected = eq18_pre_equalized(symbols, response, 4.0)
        actual = PreEqualizer(mode="zero_forcing", max_gain_db=100).apply_eq18(symbols, response, 4.0)
        np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)
