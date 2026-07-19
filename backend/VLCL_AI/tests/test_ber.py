# test_ber.py
import unittest
import numpy as np
from VLCL_AI.communication.ber import BERCalculator

class TestBER(unittest.TestCase):
    
    def test_empirical_ber(self):
        tx = np.array([0, 1, 1, 0, 1, 0])
        rx = np.array([0, 1, 0, 0, 1, 1])  # 2 errors
        
        ber, errors = BERCalculator.compute_empirical(tx, rx)
        self.assertEqual(errors, 2)
        self.assertAlmostEqual(ber, 2.0 / 6.0)

    def test_analytical_qam_ber(self):
        # Higher SNR should lead to lower analytical BER
        ber_low_snr = BERCalculator.compute_analytical_qam(2.0, 16)  # 3 dB approx
        ber_high_snr = BERCalculator.compute_analytical_qam(100.0, 16)  # 20 dB approx
        
        self.assertTrue(ber_high_snr < ber_low_snr)

if __name__ == '__main__':
    unittest.main()
