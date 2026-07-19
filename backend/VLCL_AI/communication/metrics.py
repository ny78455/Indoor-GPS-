# metrics.py
import numpy as np
from typing import Dict, Any, List
from VLCL_AI.communication.snr import compute_communication_snr
from VLCL_AI.communication.ber import BERCalculator
from VLCL_AI.communication.evm import compute_evm
from VLCL_AI.communication.rate import RateCalculator
from VLCL_AI.physics.physics_engine import PhysicsState

class CommunicationMetrics:
    """Orchestrates high-level physical layer and digital communications KPI calculations."""
    
    def __init__(self, rate_calc: RateCalculator, ber_calc: BERCalculator):
        self.rate_calc = rate_calc
        self.ber_calc = ber_calc

    def calculate_all(
        self,
        tx_bits: np.ndarray,
        rx_bits: np.ndarray,
        tx_symbols: np.ndarray,
        rx_symbols: np.ndarray,
        subcarrier_bandwidths: np.ndarray,
        modulation_orders: np.ndarray,
        active_subcarriers: List[int],
        pilot_indices: List[int],
        cp_ratio: float,
        physics_state: PhysicsState,
        responsivity: float,
        subcarrier_powers: np.ndarray,  # N_subcarriers x N_leds
        channel_gains: np.ndarray,      # N_leds x N_subcarriers
        noise_variance: float,
        user_id: int = 1
    ) -> Dict[str, Any]:
        """Calculates and aggregates all communication-specific metrics."""
        # 1. Empirical BER
        empirical_ber, bit_errors = self.ber_calc.compute_empirical(tx_bits, rx_bits)
        
        # 2. EVM
        evm_data = compute_evm(tx_symbols, rx_symbols)
        
        # 3. SNR per subcarrier
        snr_per_sc = compute_communication_snr(
            responsivity=responsivity,
            subcarrier_powers=subcarrier_powers,
            channel_gains=channel_gains,
            noise_variance=noise_variance
        )
        
        # 4. Analytical BER per subcarrier
        # Map M_n modulation orders
        ber_per_sc = np.zeros_like(snr_per_sc)
        for idx in active_subcarriers:
            m_n = modulation_orders[idx]
            if m_n > 1:
                ber_per_sc[idx] = self.ber_calc.compute_analytical_qam(snr_per_sc[idx], m_n)
                
        # Average analytical BER across active subcarriers
        average_analytical_ber = float(np.mean([ber_per_sc[i] for i in active_subcarriers])) if active_subcarriers else 0.0
        
        # 5. Data Rates and Effective Throughput
        rate_data = self.rate_calc.compute_user_rates(
            allocated_subcarriers_indices=active_subcarriers,
            subcarrier_bandwidths=subcarrier_bandwidths,
            modulation_orders=modulation_orders,
            cp_ratio=cp_ratio,
            pilot_indices=pilot_indices,
            ber=empirical_ber,
            total_system_bandwidth=float(np.sum(subcarrier_bandwidths))
        )
        
        return {
            "empirical_ber": empirical_ber,
            "bit_errors": bit_errors,
            "average_analytical_ber": average_analytical_ber,
            "evm": evm_data,
            "snr_per_subcarrier": snr_per_sc,
            "ber_per_subcarrier": ber_per_sc,
            "raw_rate_bps": rate_data["raw_rate_bps"],
            "effective_throughput_bps": rate_data["effective_throughput_bps"],
            "spectral_efficiency": rate_data["spectral_efficiency"]
        }
