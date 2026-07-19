# test_ofdm.py
import unittest
import numpy as np
from VLCL_AI.communication.subcarrier_grid import SubcarrierGrid
from VLCL_AI.communication.ofdm import OFDMModulator, OFDMDemodulator

class TestOFDMModem(unittest.TestCase):
    
    def setUp(self):
        self.grid = SubcarrierGrid(fft_size=256, total_bandwidth=20e6)
        self.modulator = OFDMModulator(grid=self.grid, cyclic_prefix_ratio=0.125)
        self.demodulator = OFDMDemodulator(grid=self.grid, cyclic_prefix_ratio=0.125)

    def test_hermitian_symmetry_real_output(self):
        rng = np.random.default_rng(42)
        # 16-QAM active symbols mapping
        active_sc = self.grid.get_active_indices()
        pilot_sc = self.grid.get_pilot_indices()
        half_n = self.grid.fft_size // 2
        
        # Count positive-frequency writable elements
        writable_pos_count = sum(1 for idx in (active_sc + pilot_sc) if 0 < idx < half_n)
        
        # Generate random QAM symbols
        tx_symbols = rng.normal(size=writable_pos_count) + 1j * rng.normal(size=writable_pos_count)
        
        # Modulate
        time_waveform, freq_grid = self.modulator.modulate(tx_symbols)
        
        # Check that the time-waveform is strictly real (imaginary component is tiny)
        self.assertTrue(np.all(np.abs(np.imag(time_waveform)) < 1e-12))
        
        # Check that cyclic prefix is attached
        expected_len = (self.grid.fft_size + self.modulator.cp_length)
        self.assertEqual(len(time_waveform), expected_len)

    def test_loopback_ideal(self):
        rng = np.random.default_rng(42)
        active_sc = self.grid.get_active_indices()
        pilot_sc = self.grid.get_pilot_indices()
        half_n = self.grid.fft_size // 2
        
        writable_pos_count = sum(1 for idx in (active_sc + pilot_sc) if 0 < idx < half_n)
        
        # Send 5 frames worth of symbols
        tx_symbols = (rng.normal(size=5 * writable_pos_count) + 1j * rng.normal(size=5 * writable_pos_count))
        
        # Modulate
        time_waveform, freq_grid = self.modulator.modulate(tx_symbols)
        
        # Demodulate
        rx_symbols, rx_grid = self.demodulator.demodulate(time_waveform)
        
        # Compare transmitted and received symbols (they should match exactly in ideal condition)
        # Trim padding if any
        rx_symbols_trimmed = rx_symbols[:len(tx_symbols)]
        np.testing.assert_allclose(tx_symbols, rx_symbols_trimmed, rtol=1e-10, atol=1e-10)

if __name__ == '__main__':
    unittest.main()
