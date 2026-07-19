# test_qam.py
import unittest
import numpy as np
from VLCL_AI.communication.qam import QAMModem

class TestQAMModem(unittest.TestCase):
    
    def setUp(self):
        self.modem = QAMModem()

    def test_bits_per_symbol(self):
        self.assertEqual(self.modem.bits_per_symbol(2), 1)
        self.assertEqual(self.modem.bits_per_symbol(4), 2)
        self.assertEqual(self.modem.bits_per_symbol(16), 4)
        self.assertEqual(self.modem.bits_per_symbol(64), 6)
        self.assertEqual(self.modem.bits_per_symbol(256), 8)

    def test_constellation_normalization(self):
        for M in [2, 4, 16, 64, 256]:
            constellation = self.modem.get_constellation(M)
            avg_energy = np.mean(np.abs(constellation) ** 2)
            # Energy should be normalized to exactly 1.0
            self.assertAlmostEqual(avg_energy, 1.0, places=5)

    def test_loopback_no_noise(self):
        rng = np.random.default_rng(12345)
        for M in [2, 4, 16, 64, 256]:
            k = self.modem.bits_per_symbol(M)
            # Generate 4000 random bits
            tx_bits = rng.integers(0, 2, size=4000 * k, dtype=np.uint8)
            
            # Modulate
            symbols = self.modem.modulate(tx_bits, M)
            self.assertEqual(len(symbols), 4000)
            
            # Demodulate (no noise)
            rx_bits = self.modem.demodulate(symbols, M)
            
            # Verify reconstructed bits match original
            np.testing.assert_array_equal(tx_bits, rx_bits)

if __name__ == '__main__':
    unittest.main()
