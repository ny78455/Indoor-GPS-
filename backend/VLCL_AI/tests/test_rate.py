# test_rate.py
import unittest
import numpy as np
from VLCL_AI.communication.rate import RateCalculator

class TestRateCalculator(unittest.TestCase):
    
    def test_rates(self):
        # 10 active subcarriers, each of 100 kHz bandwidth, 16-QAM (4 bits/symbol)
        sc_indices = list(range(10))
        bw = np.full(10, 100e3)
        mod_orders = np.full(10, 16)
        
        rate_data = RateCalculator.compute_user_rates(
            allocated_subcarriers_indices=sc_indices,
            subcarrier_bandwidths=bw,
            modulation_orders=mod_orders,
            cp_ratio=0.0,  # 0 CP
            pilot_indices=[],
            ber=0.0,
            total_system_bandwidth=1e6
        )
        
        # Expected raw rate = 10 * 100 kHz * 4 = 4 Mbps
        self.assertEqual(rate_data["raw_rate_bps"], 4.0 * 1e6)
        self.assertEqual(rate_data["effective_throughput_bps"], 4.0 * 1e6)

if __name__ == '__main__':
    unittest.main()
