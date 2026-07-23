import unittest
import numpy as np
from scipy.special import erfc
from VLCL_AI.communication.snr import compute_communication_snr
from VLCL_AI.physics.noise import total_noise_variance
from VLCL_AI.communication.ber import BERCalculator

class TestPhase3SNR(unittest.TestCase):
    
    def test_eq1_golden_numerical(self):
        """
        Validate Paper Eq. (1):
        γ_{k,n}^co = μ² · (Σ_i √P_{n,i} · H_{i,n,k})² / δ²
        We will use a deterministic case.
        """
        responsivity = 0.5  # μ
        # 3 subcarriers, 2 LEDs
        # P_{n,i}
        powers = np.array([
            [4.0, 9.0],
            [16.0, 0.0],
            [1.0, 1.0]
        ])
        
        # H_{i,n,k} shape: (N_leds, N_subcarriers)
        gains = np.array([
            [0.1, 0.2, 0.5],
            [0.3, 0.1, 0.5]
        ])
        
        noise_var = 1e-6 # δ²
        
        # Calculate manually
        # sqrt(P)
        sqrt_P = np.sqrt(powers) # [[2, 3], [4, 0], [1, 1]]
        
        # Subcarrier 0:
        # Σ √P_{0,i} H_{i,0} = 2 * 0.1 + 3 * 0.3 = 0.2 + 0.9 = 1.1
        # SNR_0 = (0.5)^2 * (1.1)^2 / 1e-6 = 0.25 * 1.21 / 1e-6 = 0.3025e6 = 302500
        
        # Subcarrier 1:
        # Σ √P_{1,i} H_{i,1} = 4 * 0.2 + 0 * 0.1 = 0.8
        # SNR_1 = (0.5)^2 * (0.8)^2 / 1e-6 = 0.25 * 0.64 / 1e-6 = 0.16e6 = 160000
        
        # Subcarrier 2:
        # Σ √P_{2,i} H_{i,2} = 1 * 0.5 + 1 * 0.5 = 1.0
        # SNR_2 = (0.5)^2 * (1.0)^2 / 1e-6 = 0.25 * 1.0 / 1e-6 = 0.25e6 = 250000
        
        expected_snr_linear = np.array([302500.0, 160000.0, 250000.0])
        
        actual_snr_linear = compute_communication_snr(
            responsivity=responsivity,
            subcarrier_powers=powers,
            channel_gains=gains,
            noise_variance=noise_var,
            eta_scaling=1.0
        )
        
        np.testing.assert_array_almost_equal(actual_snr_linear, expected_snr_linear)

    def test_power_increases_snr(self):
        p1 = np.array([[1.0, 1.0]])
        p2 = np.array([[4.0, 4.0]])
        h = np.array([[0.5], [0.5]])
        
        snr1 = compute_communication_snr(1.0, p1, h, 1e-6)[0]
        snr2 = compute_communication_snr(1.0, p2, h, 1e-6)[0]
        
        self.assertTrue(snr2 > snr1)
        self.assertAlmostEqual(snr2, 4.0 * snr1) # P * 4 -> sqrt(P) * 2 -> SNR * 4
        
    def test_gain_increases_snr(self):
        p = np.array([[1.0, 1.0]])
        h1 = np.array([[0.5], [0.5]])
        h2 = np.array([[1.0], [1.0]])
        
        snr1 = compute_communication_snr(1.0, p, h1, 1e-6)[0]
        snr2 = compute_communication_snr(1.0, p, h2, 1e-6)[0]
        
        self.assertTrue(snr2 > snr1)
        self.assertAlmostEqual(snr2, 4.0 * snr1) # H * 2 -> SNR * 4
        
    def test_noise_decreases_snr(self):
        p = np.array([[1.0, 1.0]])
        h = np.array([[0.5], [0.5]])
        
        snr1 = compute_communication_snr(1.0, p, h, 1e-6)[0]
        snr2 = compute_communication_snr(1.0, p, h, 2e-6)[0]
        
        self.assertTrue(snr1 > snr2)
        self.assertAlmostEqual(snr1, 2.0 * snr2) # Noise * 2 -> SNR / 2

    def test_zero_channel_gives_zero_snr(self):
        p = np.array([[100.0, 100.0]])
        h = np.array([[0.0], [0.0]])
        
        snr = compute_communication_snr(1.0, p, h, 1e-6)[0]
        self.assertEqual(snr, 0.0)

    def test_es_n0_vs_eb_n0_analytical(self):
        """
        Verify that compute_analytical_qam expects Es/N0 (symbol SNR) and evaluates correctly.
        """
        # For M=4 (4-QAM / QPSK), log2(M) = 2.
        # Eb/N0 = 10 dB -> Eb/N0_linear = 10
        # Es/N0 = log2(M) * Eb/N0 = 2 * 10 = 20
        # Analytical QPSK BER is Q(sqrt(2 * Eb/N0)) = 0.5 * erfc(sqrt(Eb/N0))
        eb_n0_linear = 10.0
        es_n0_linear = 2.0 * eb_n0_linear
        
        expected_ber = 0.5 * erfc(np.sqrt(eb_n0_linear))
        
        # Function takes Es/N0
        actual_ber = BERCalculator.compute_analytical_qam(comm_subcarrier_snr_linear=es_n0_linear, M=4)
        
        self.assertAlmostEqual(actual_ber, expected_ber)
        
        # Test 16-QAM
        M = 16
        es_n0_linear = 50.0
        expected_16qam = 0.5 * (4/4) * (1 - 1/4) * erfc(np.sqrt(3.0 * es_n0_linear / (2.0 * 15.0)))
        actual_16qam = BERCalculator.compute_analytical_qam(es_n0_linear, M)
        self.assertAlmostEqual(actual_16qam, expected_16qam)

    def test_noise_model_equations(self):
        """
        Verify that noise calculations match established physics models.
        """
        from VLCL_AI.physics.constants import ELECTRON_CHARGE, BOLTZMANN_CONSTANT
        
        B = 1e6 # 1 MHz
        I = 100e-6 # 100 uA
        R_tia = 1000 # 1 kOhm
        T = 300 # 300 K
        
        # Expected shot variance: 2 * q * I * B
        exp_shot = 2.0 * ELECTRON_CHARGE * I * B
        
        # Expected thermal variance: 4 * k_B * T * B / R_tia
        exp_thermal = 4.0 * BOLTZMANN_CONSTANT * T * B / R_tia
        
        res = total_noise_variance(signal_current=I, tia_gain=R_tia, bandwidth=B, temperature=T, background_current=0.0, config={"shot": True, "thermal": True, "background": False, "electronic": False})
        
        self.assertAlmostEqual(res["shot_variance"], exp_shot)
        self.assertAlmostEqual(res["thermal_variance"], exp_thermal)
        self.assertAlmostEqual(res["total_variance"], exp_shot + exp_thermal)

if __name__ == '__main__':
    unittest.main()
