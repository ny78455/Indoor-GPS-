# test_equalization.py
import unittest
import numpy as np
from VLCL_AI.communication.channel_equalizer import ChannelEqualizer

class TestChannelEqualizer(unittest.TestCase):
    
    def test_zf_equalization(self):
        eq = ChannelEqualizer(mode="ZF")
        
        # Test synthetic distortion: H = 0.5 + 0.2j
        h = np.array([0.5 + 0.2j, 0.8 - 0.1j])
        tx_symbols = np.array([1.0 + 1.0j, -1.0 + 0.5j])
        
        # Distort
        rx_symbols = tx_symbols * h
        
        # Equalize
        recovered = eq.equalize(rx_symbols, h)
        
        np.testing.assert_allclose(tx_symbols, recovered, rtol=1e-10, atol=1e-10)

    def test_mmse_equalization(self):
        eq = ChannelEqualizer(mode="MMSE")
        h = np.array([0.5 + 0.2j, 0.8 - 0.1j])
        tx_symbols = np.array([1.0 + 1.0j, -1.0 + 0.5j])
        
        # Under 0 noise, MMSE should approach ZF
        rx_symbols = tx_symbols * h
        recovered = eq.equalize(rx_symbols, h, noise_variance=0.0)
        
        np.testing.assert_allclose(tx_symbols, recovered, rtol=1e-10, atol=1e-10)

if __name__ == '__main__':
    unittest.main()
