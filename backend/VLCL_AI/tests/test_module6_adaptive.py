# test_module6_adaptive.py
import unittest
import numpy as np

from VLCL_AI.communication.subcarrier_grid import SubcarrierGrid
from VLCL_AI.adaptive.config import AdaptiveConfig
from VLCL_AI.adaptive.feedback import ChannelFeedback
from VLCL_AI.adaptive.snr_thresholds import SNRThresholdTable
from VLCL_AI.adaptive.resource_mask import ResourceMask, SubcarrierLockType
from VLCL_AI.adaptive.modulation_controller import AdaptiveModulationController
from VLCL_AI.adaptive.rate_evaluator import RateEvaluator
from VLCL_AI.adaptive.qos import QoSEvaluator, QoSStatus
from VLCL_AI.adaptive.allocation import TwoStageSubcarrierAllocator
from VLCL_AI.adaptive.decision import AllocationDecision
from VLCL_AI.adaptive.metrics import AdaptiveMetrics
from VLCL_AI.adaptive.validation import AllocationValidator
from VLCL_AI.adaptive.engine import AdaptiveTransmissionEngine

class TestModule6AdaptiveTransmission(unittest.TestCase):

    def setUp(self):
        self.grid = SubcarrierGrid(fft_size=256, total_bandwidth=20e6, sample_rate=50e6)
        self.config = AdaptiveConfig(ber_max=3.8e-3, supported_modulations=[2, 4, 16, 64, 256])
        self.threshold_table = SNRThresholdTable(ber_max=3.8e-3, supported_modulations=[2, 4, 16, 64, 256])
        self.controller = AdaptiveModulationController(ber_max=3.8e-3, threshold_table=self.threshold_table)
        self.engine = AdaptiveTransmissionEngine(self.config)

    # -------------------------------------------------------------------
    # AMC TESTS (T-M6-AMC-001 to 007)
    # -------------------------------------------------------------------
    def test_amc_thresholds_derivation(self):
        """Verify derived SNR thresholds are strictly increasing with M."""
        thresh_4 = self.threshold_table.get_threshold_linear(4)
        thresh_16 = self.threshold_table.get_threshold_linear(16)
        thresh_64 = self.threshold_table.get_threshold_linear(64)
        thresh_256 = self.threshold_table.get_threshold_linear(256)

        self.assertLess(thresh_4, thresh_16)
        self.assertLess(thresh_16, thresh_64)
        self.assertLess(thresh_64, thresh_256)

    def test_amc_monotonicity(self):
        """Verify increasing SNR never decreases selected modulation order."""
        snrs = np.linspace(0.1, 1000.0, 100)
        last_M = 0
        for snr in snrs:
            M, ber, feat = self.controller.select_modulation_order(snr)
            self.assertGreaterEqual(M, last_M, f"Monotonicity violated at SNR={snr}")
            last_M = M

    def test_amc_zero_snr_handling(self):
        """Verify zero or negative SNR yields M=0, BER=1.0, and is_feasible=False."""
        M, ber, feat = self.controller.select_modulation_order(0.0)
        self.assertEqual(M, 0)
        self.assertEqual(ber, 1.0)
        self.assertFalse(feat)

    def test_amc_threshold_boundary(self):
        """Verify SNR right above threshold selects M, and right below selects lower M."""
        thresh_16 = self.threshold_table.get_threshold_linear(16)
        
        # Slightly above threshold -> 16
        M_above, _, feat_above = self.controller.select_modulation_order(thresh_16 * 1.01)
        self.assertGreaterEqual(M_above, 16)
        self.assertTrue(feat_above)

        # Slightly below threshold -> < 16
        M_below, _, _ = self.controller.select_modulation_order(thresh_16 * 0.99)
        self.assertLess(M_below, 16)

    # -------------------------------------------------------------------
    # ALLOCATION & LOCK PROTECTION TESTS (T-M6-ALLOC-001, 002)
    # -------------------------------------------------------------------
    def test_resource_mask_localization_protection(self):
        """Verify localization subcarriers (SG_{K+1}) are locked and cannot be allocated."""
        resource_mask = ResourceMask(self.grid, localization_indices=[5, 6, 7, 8, 9])
        for sc in [5, 6, 7, 8, 9]:
            self.assertTrue(resource_mask.is_localization_locked(sc))
            self.assertFalse(resource_mask.is_allocatable(sc))

    def test_multi_device_exclusive_allocation(self):
        """Verify subcarrier allocation is strictly exclusive (sum_k rho[k,n] <= 1)."""
        K = 4
        N = self.grid.fft_size
        device_ids = [1, 2, 3, 4]
        
        snr_matrix = np.random.uniform(5.0, 50.0, size=(K, N))
        min_rates = {dev: 1.0e6 for dev in device_ids}

        decision = self.engine.allocate_from_snr_matrix(
            snr_matrix=snr_matrix,
            device_ids=device_ids,
            min_rates_bps=min_rates,
            grid=self.grid
        )

        col_sums = np.sum(decision.rho, axis=0)
        self.assertTrue(np.all(col_sums <= 1), "Subcarrier collision detected!")

    # -------------------------------------------------------------------
    # QOS & INFEASIBILITY TESTS (T-M6-QOS-001, 002)
    # -------------------------------------------------------------------
    def test_qos_feasible_scenario(self):
        """Verify achievable rates meet low QoS demands -> qos_status = FEASIBLE."""
        device_ids = [1, 2]
        snr_matrix = np.full((2, self.grid.fft_size), 50.0) # High SNR
        min_rates = {1: 1.0e6, 2: 1.0e6} # Low demand

        decision = self.engine.allocate_from_snr_matrix(
            snr_matrix=snr_matrix,
            device_ids=device_ids,
            min_rates_bps=min_rates,
            grid=self.grid
        )

        self.assertEqual(decision.qos_status, "FEASIBLE")
        self.assertTrue(all(decision.qos_satisfied.values()))

    def test_qos_infeasible_scenario(self):
        """Verify impossible QoS demand reports positive deficits and non-FEASIBLE status."""
        device_ids = [1, 2]
        snr_matrix = np.full((2, self.grid.fft_size), 2.0) # Low SNR
        min_rates = {1: 50.0e6, 2: 50.0e6} # Unreasonably high demand

        decision = self.engine.allocate_from_snr_matrix(
            snr_matrix=snr_matrix,
            device_ids=device_ids,
            min_rates_bps=min_rates,
            grid=self.grid
        )

        self.assertIn(decision.qos_status, ["PARTIALLY_FEASIBLE", "INFEASIBLE_QOS"])
        self.assertTrue(any(d > 0 for d in decision.qos_deficits_bps.values()))

    # -------------------------------------------------------------------
    # BENCHMARK COMPARISON TEST (T-M6-COMPARE-001)
    # -------------------------------------------------------------------
    def test_adaptive_vs_static_throughput_gain(self):
        """
        Verify adaptive mode achieves higher or equal sum rate compared to static mode
        under a frequency-selective SNR channel.
        """
        device_ids = [1, 2]
        N = self.grid.fft_size
        
        # Frequency selective channel: User 1 good on low carriers, User 2 good on high carriers
        snr_matrix = np.zeros((2, N))
        snr_matrix[0, :N//2] = 100.0  # High SNR for User 1
        snr_matrix[0, N//2:] = 1.0    # Low SNR for User 1
        snr_matrix[1, :N//2] = 1.0    # Low SNR for User 2
        snr_matrix[1, N//2:] = 100.0  # High SNR for User 2

        min_rates = {1: 0.0, 2: 0.0}

        # Adaptive engine
        adaptive_engine = AdaptiveTransmissionEngine(AdaptiveConfig(mode="ADAPTIVE"))
        decision_adapt = adaptive_engine.allocate_from_snr_matrix(
            snr_matrix=snr_matrix,
            device_ids=device_ids,
            min_rates_bps=min_rates,
            grid=self.grid
        )

        # Static engine
        static_engine = AdaptiveTransmissionEngine(AdaptiveConfig(mode="STATIC", default_static_modulation=16))
        decision_static = static_engine.allocate_from_snr_matrix(
            snr_matrix=snr_matrix,
            device_ids=device_ids,
            min_rates_bps=min_rates,
            grid=self.grid
        )

        self.assertGreaterEqual(
            decision_adapt.sum_rate_bps,
            decision_static.sum_rate_bps,
            "Adaptive mode should outperform or match static mode sum rate!"
        )

    # -------------------------------------------------------------------
    # INVARIANT & METRICS TESTS
    # -------------------------------------------------------------------
    def test_jains_fairness_index(self):
        """Verify Jain's fairness index computation."""
        rates_equal = {1: 10e6, 2: 10e6, 3: 10e6}
        self.assertAlmostEqual(AdaptiveMetrics.compute_jains_fairness_index(rates_equal), 1.0)

        rates_unequal = {1: 10e6, 2: 0.0}
        self.assertAlmostEqual(AdaptiveMetrics.compute_jains_fairness_index(rates_unequal), 0.5)

    def test_allocation_validator_invariants(self):
        """Verify AllocationValidator catches matrix size mismatch or non-binary values."""
        resource_mask = ResourceMask(self.grid)
        bad_rho = np.full((2, self.grid.fft_size), 2) # Non-binary
        
        with self.assertRaises(Exception):
            AllocationValidator.validate_allocation_decision(
                rho=bad_rho,
                resource_mask=resource_mask,
                device_ids=[1, 2]
            )

if __name__ == "__main__":
    unittest.main()
