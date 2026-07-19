# test_subcarriers.py
import unittest
from VLCL_AI.communication.subcarrier_grid import SubcarrierGrid
from VLCL_AI.communication.subcarrier import SubcarrierPurpose

class TestSubcarriers(unittest.TestCase):
    
    def test_grid_initialization(self):
        grid = SubcarrierGrid(fft_size=256, guard_low=4, guard_high=4, pilot_spacing=16)
        
        # Guard bands
        guards = grid.get_subcarriers_by_purpose(SubcarrierPurpose.GUARD)
        self.assertTrue(len(guards) > 0)
        
        # DC Carrier
        dc_carriers = grid.get_subcarriers_by_purpose(SubcarrierPurpose.DC)
        self.assertEqual(len(dc_carriers), 1)
        self.assertEqual(dc_carriers[0].index, 0)
        
        # Active indices list
        active_indices = grid.get_active_indices()
        self.assertTrue(0 not in active_indices)
        self.assertTrue(255 not in active_indices)

if __name__ == '__main__':
    unittest.main()
