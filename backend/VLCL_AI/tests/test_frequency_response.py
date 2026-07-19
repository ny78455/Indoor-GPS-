# test_frequency_response.py
import unittest
import numpy as np
from VLCL_AI.communication.led_frequency_response import LEDFrequencyResponse

class TestLEDFrequencyResponse(unittest.TestCase):
    
    def test_low_pass_cutoff(self):
        fc = 20e6  # 20 MHz
        response = LEDFrequencyResponse(model_type="first_order", cutoff_frequency_hz=fc)
        
        # At DC (f=0), response should be 1.0
        h_dc = response.complex_response(0.0)
        self.assertAlmostEqual(np.abs(h_dc), 1.0)
        
        # At cutoff (f=fc), response magnitude should be 1/sqrt(2) ≈ 0.7071
        h_cutoff = response.complex_response(fc)
        self.assertAlmostEqual(np.abs(h_cutoff), 1.0 / np.sqrt(2.0), places=5)
        
        # Far above cutoff (f=100*fc), magnitude should be small
        h_high = response.complex_response(100.0 * fc)
        self.assertTrue(np.abs(h_high) < 0.05)

if __name__ == '__main__':
    unittest.main()
