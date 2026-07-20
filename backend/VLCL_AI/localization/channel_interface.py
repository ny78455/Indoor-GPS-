# channel_interface.py
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from VLCL_AI.environment.state import EnvironmentState
from VLCL_AI.physics.physics_engine import PhysicsState
from VLCL_AI.localization.signal_generator import LocalizationFrame

@dataclass
class ReceivedLocalizationSignal:
    """Represents the received localization signals at a simulation frame."""
    frame_id: int
    timestamp: float
    signal_mode: str
    
    # Received signals
    # For full_waveform: 1D array representing the composite received analog waveform (all tones + noise)
    # For phase_equivalent: 1D complex array representing the received complex phasors per tone
    received_signals: np.ndarray
    
    # Link quality metadata
    tone_powers_tx: np.ndarray
    received_powers_rx: Dict[int, float]  # tone_id to received power
    effective_gains: Dict[int, float]      # tone_id to effective channel gain
    propagation_delays: Dict[int, float]   # tone_id to propagation delay (s)
    los_statuses: Dict[int, bool]          # tone_id to LOS status
    noise_variance_wide: float
    noise_variance_inband: float
    snrs_db: Dict[int, float]              # tone_id to SNR (dB)
    metadata: Dict[str, Any]
    time_vector: Optional[np.ndarray] = None


class LocalizationChannelInterface:
    """Interfaces between Module 2 (Physics Engine) and Module 4 (Localization)."""

    def __init__(self, enable_noise: bool = True, channel_mode: str = "los_only",
                 rx_bandwidth: float = 50.0e6):
        self.enable_noise = enable_noise
        self.channel_mode = channel_mode  # "los_only" or "multipath"
        # M4-LOC-006: configurable bandwidth; was hardcoded in apply_channel()
        # Default 50 MHz retained for backward compatibility
        self.rx_bandwidth = rx_bandwidth

    def apply_channel(
        self,
        env_state: EnvironmentState,
        physics_state: PhysicsState,
        frame: LocalizationFrame,
        bp_bandwidth_hz: float = 20000.0
    ) -> ReceivedLocalizationSignal:
        """
        Applies physical propagation channel to the transmitted frame.
        """
        signal_mode = frame.signal_mode
        num_tones = len(frame.frequency_plan.frequencies)
        
        # Extract physical metrics from physics_state
        # Use total gains or los gains depending on channel_mode
        gains_source = physics_state.los_gains if self.channel_mode == "los_only" else physics_state.total_gains
        
        # Find default receiver bandwidth and noise
        # Default receiver noise variance is from the physics engine
        # In physics_state.noise_variances we have variance per LED signal, let's take average or max
        noise_var_wide = float(np.mean(list(physics_state.noise_variances.values())))
        
        # If noise is disabled, set to zero
        if not self.enable_noise:
            noise_var_wide = 0.0
            
        # Get photodiode parameters from env_state or physics_state
        # M4-LOC-006: rx_bandwidth sourced from config; was hardcoded 50.0e6
        # Default retained as 50 MHz until caller passes explicit config
        rx_bandwidth = self.rx_bandwidth
        noise_var_inband = noise_var_wide * (bp_bandwidth_hz / rx_bandwidth) if noise_var_wide > 0 else 0.0
        
        received_powers = {}
        effective_gains = {}
        propagation_delays = {}
        los_statuses = {}
        snrs_db = {}
        
        if signal_mode == "full_waveform":
            t = frame.time_vector
            num_samples = len(t)
            composite_received = np.zeros(num_samples, dtype=np.float64)
            
            for i in range(num_tones):
                tone_id = i + 1
                freq = frame.frequency_plan.frequencies[i]
                omega = frame.frequency_plan.angular_frequencies[i]
                pwr_tx = frame.powers[i]
                
                # Get the mapped LEDs for this tone
                led_ids = frame.tone_to_led_map.get(tone_id, [1])
                
                # Calculate superposed signal from all mapped LEDs
                tone_rx = np.zeros(num_samples, dtype=np.float64)
                eff_gain = 0.0
                delay_sum = 0.0
                is_los_all = True
                
                for led_id in led_ids:
                    gain = gains_source.get(led_id, 0.0)
                    delay = physics_state.propagation_times.get(led_id, 0.0)
                    is_los = env_state.los_matrix.get(led_id, True)

                    # SIGN CONVENTION (M4-LOC-008)
                    # -----------------------------------------------------------------
                    # We apply propagation delay as s(t - tau), giving phase: -omega*tau
                    # This is standard physics convention: s(t-tau) <=> e^{-j*omega*tau}
                    #
                    # Paper Eq.(5)/(6) writes received phase as +omega*tau.
                    # This is a notation difference, NOT a physics difference.
                    # The paper's hardware naturally inverts the sign depending on
                    # which side of the measurement is called "reference."
                    #
                    # Consequence for position_solver.py:
                    #   theta_measured = -theta_paper
                    #   A_code = -A_paper * (2*pi/c)  [see position_solver._build_coefficient_matrix]
                    #   Net: A_code * delta_d = theta_measured is CORRECT
                    #
                    # !!! WARNING !!!
                    # Do NOT "fix" this sign to match the paper literal notation
                    # without simultaneously changing position_solver.py.
                    # The two files form a compensating pair.
                    # Protected by regression test T-M4-004 / T-M4-006.
                    # -----------------------------------------------------------------
                    tone_rx += np.sqrt(pwr_tx) * gain * np.sin(omega * (t - delay) + frame.initial_phase)
                    eff_gain += gain
                    delay_sum += delay
                    is_los_all = is_los_all and is_los
                    
                composite_received += tone_rx
                
                # Metadata computations
                avg_delay = delay_sum / len(led_ids)
                effective_gains[tone_id] = eff_gain
                propagation_delays[tone_id] = avg_delay
                los_statuses[tone_id] = is_los_all
                
                rx_pwr = pwr_tx * (eff_gain ** 2) # Electrical power proportional to (H * sqrt(P))^2
                received_powers[tone_id] = rx_pwr
                
                # SNR
                responsivity = 0.54
                s_power = (responsivity * rx_pwr) ** 2
                if noise_var_inband > 0:
                    snr_linear = s_power / noise_var_inband
                    snrs_db[tone_id] = float(10 * np.log10(max(1e-24, snr_linear)))
                else:
                    snrs_db[tone_id] = 100.0
                
            # Add wideband noise to composite signal
            if self.enable_noise and noise_var_wide > 0:
                # Add white Gaussian noise with wideband variance
                noise = np.random.normal(0, np.sqrt(noise_var_wide), num_samples)
                composite_received += noise
                
            return ReceivedLocalizationSignal(
                frame_id=frame.frame_id,
                timestamp=frame.timestamp,
                signal_mode=signal_mode,
                received_signals=composite_received,
                time_vector=t,
                tone_powers_tx=frame.powers,
                received_powers_rx=received_powers,
                effective_gains=effective_gains,
                propagation_delays=propagation_delays,
                los_statuses=los_statuses,
                noise_variance_wide=noise_var_wide,
                noise_variance_inband=noise_var_inband,
                snrs_db=snrs_db,
                metadata={}
            )
            
        else:
            # Phase-equivalent mode
            # We construct a 1D complex array of received phasors
            received_phasors = np.zeros(num_tones, dtype=np.complex128)
            
            for i in range(num_tones):
                tone_id = i + 1
                freq = frame.frequency_plan.frequencies[i]
                omega = frame.frequency_plan.angular_frequencies[i]
                pwr_tx = frame.powers[i]
                
                led_ids = frame.tone_to_led_map.get(tone_id, [1])
                
                # Superposition of complex phasors
                # Y_i = sum_led sqrt(P_tx) * gain * e^{j * (-omega * delay + initial_phase)}
                val_complex = 0.0 + 0.0j
                eff_gain = 0.0
                delay_sum = 0.0
                is_los_all = True
                
                for led_id in led_ids:
                    gain = gains_source.get(led_id, 0.0)
                    delay = physics_state.propagation_times.get(led_id, 0.0)
                    is_los = env_state.los_matrix.get(led_id, True)
                    
                    val_complex += np.sqrt(pwr_tx) * gain * np.exp(1j * (-omega * delay + frame.initial_phase))
                    eff_gain += gain
                    delay_sum += delay
                    is_los_all = is_los_all and is_los
                    
                # Add complex in-band noise to each tone phasor individually
                if self.enable_noise and noise_var_inband > 0:
                    # complex noise with total variance = noise_var_inband
                    # standard deviation per real/imag component is sqrt(noise_var_inband / 2)
                    noise_std = np.sqrt(noise_var_inband / 2.0)
                    noise_complex = np.random.normal(0, noise_std) + 1j * np.random.normal(0, noise_std)
                    val_complex += noise_complex
                    
                received_phasors[i] = val_complex
                
                # Metadata
                avg_delay = delay_sum / len(led_ids)
                effective_gains[tone_id] = eff_gain
                propagation_delays[tone_id] = avg_delay
                los_statuses[tone_id] = is_los_all
                
                rx_pwr = pwr_tx * (eff_gain ** 2)
                received_powers[tone_id] = rx_pwr
                
                # SNR
                responsivity = 0.54
                s_power = (responsivity * rx_pwr) ** 2
                if noise_var_inband > 0:
                    snr_linear = s_power / noise_var_inband
                    snrs_db[tone_id] = float(10 * np.log10(max(1e-24, snr_linear)))
                else:
                    snrs_db[tone_id] = 100.0
                
            return ReceivedLocalizationSignal(
                frame_id=frame.frame_id,
                timestamp=frame.timestamp,
                signal_mode=signal_mode,
                received_signals=received_phasors,
                time_vector=None,
                tone_powers_tx=frame.powers,
                received_powers_rx=received_powers,
                effective_gains=effective_gains,
                propagation_delays=propagation_delays,
                los_statuses=los_statuses,
                noise_variance_wide=noise_var_wide,
                noise_variance_inband=noise_var_inband,
                snrs_db=snrs_db,
                metadata={}
            )
