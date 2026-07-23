import numpy as np
from VLCL_AI.physics.constants import ELECTRON_CHARGE, BOLTZMANN_CONSTANT, DEFAULT_RESPONSIVITY, DEFAULT_TRANSIMPEDANCE_GAIN
from VLCL_AI.physics.noise import total_noise_variance
from VLCL_AI.communication.snr import compute_communication_snr
from VLCL_AI.communication.ber import BERCalculator

def trace_single_subcarrier():
    print("==================================================")
    print("PHASE 3: SINGLE SUBCARRIER END-TO-END TRACE")
    print("==================================================")
    
    # 1. Physical Parameters
    bandwidth = 125000.0  # 125 kHz per subcarrier
    temperature = 298.15
    I_bg = 100e-6
    mu = DEFAULT_RESPONSIVITY
    R_tia = DEFAULT_TRANSIMPEDANCE_GAIN
    eta = 1.0
    
    # 2. Transmit side (2 LEDs for simplicity)
    # Electrical power allocated to this subcarrier on each LED
    p_alloc = np.array([4.0, 9.0])
    
    # 3. Channel
    # Optical channel gains (dimensionless)
    h_channel = np.array([0.1, 0.2])
    
    print(f"[TX] Subcarrier allocated electrical power P_i: {p_alloc} W")
    print(f"[CH] Subcarrier optical channel gains H_i: {h_channel}")
    
    # 4. Propagation and Optical Sum
    # Optical amplitude is proportional to sqrt(P)
    optical_amp_tx = np.sqrt(p_alloc)
    print(f"[TX] Subcarrier optical amplitudes (sqrt(P_i)): {optical_amp_tx}")
    
    # The optical signal arriving at the PD is the sum of (sqrt(P) * H)
    received_optical = np.sum(optical_amp_tx * h_channel)
    print(f"[RX] Combined received optical amplitude: {received_optical:.4f}")
    
    # 5. Photodiode conversion
    signal_current = received_optical * mu * eta
    print(f"[RX] PD Responsivity (mu): {mu} A/W")
    print(f"[RX] Signal photocurrent amplitude: {signal_current:.4f} A")
    
    signal_power_electrical = signal_current ** 2
    print(f"[RX] Signal electrical power (I^2): {signal_power_electrical:.4e} A^2")
    
    # 6. Noise variance calculation
    noise = total_noise_variance(
        signal_current=signal_current, # usually use average current, but using peak for trace
        tia_gain=R_tia,
        bandwidth=bandwidth,
        temperature=temperature,
        background_current=I_bg
    )
    
    print(f"[NOISE] Shot noise variance: {noise['shot_variance']:.4e} A^2")
    print(f"[NOISE] Thermal noise variance: {noise['thermal_variance']:.4e} A^2")
    print(f"[NOISE] Total noise variance (delta^2): {noise['total_variance']:.4e} A^2")
    
    # 7. SNR Calculation (Pre-equalization)
    snr_linear_direct = signal_power_electrical / noise['total_variance']
    snr_db = 10 * np.log10(snr_linear_direct)
    print(f"[SNR] Pre-equalization SNR (Linear): {snr_linear_direct:.4f}")
    print(f"[SNR] Pre-equalization SNR (dB): {snr_db:.4f} dB")
    
    # Verify via library function
    P_matrix = np.array([p_alloc])
    H_matrix = np.array([h_channel]).T
    snr_lib = compute_communication_snr(mu, P_matrix, H_matrix, noise['total_variance'], eta)[0]
    print(f"[SNR] Library compute_communication_snr: {snr_lib:.4f}")
    assert np.isclose(snr_linear_direct, snr_lib)
    
    # 8. Post-Equalization
    # Zero-Forcing Equalizer scales Y by 1/H_eq
    # The effective channel for this composite signal is H_eq = received_optical / sqrt(p_alloc_ref)
    # But equalization is done per LED independently in OFDMA.
    # If LED 1 transmits its own bits on this subcarrier:
    h_eff_led1 = h_channel[0] * mu * eta
    print(f"[EQ] Effective electrical channel for LED 1: {h_eff_led1:.4f}")
    
    # Signal power after ZF equalization: P_tx
    # Noise power after ZF equalization: N / |h_eff|^2
    eq_signal_power = optical_amp_tx[0] ** 2
    eq_noise_power = noise['total_variance'] / (h_eff_led1 ** 2)
    snr_post_eq = eq_signal_power / eq_noise_power
    print(f"[EQ] Equalized signal power (LED 1): {eq_signal_power:.4f}")
    print(f"[EQ] Post-equalization noise power (LED 1): {eq_noise_power:.4e}")
    print(f"[EQ] Post-equalization SNR (Linear, LED 1): {snr_post_eq:.4f}")
    
    # Note: If LED 1 is the ONLY one transmitting on this subcarrier, snr_post_eq == snr_linear_direct.
    # Since we added interference from LED 2 in this trace, snr_post_eq will be different from the combined SNR.
    # But for an isolated LED (OFDMA), they match perfectly.
    
    # 9. BER Calculation
    M = 16
    ber = BERCalculator.compute_analytical_qam(snr_post_eq, M)
    print(f"[BER] Modulation order: {M}-QAM")
    print(f"[BER] Analytical BER (M=16): {ber:.4e}")

if __name__ == '__main__':
    trace_single_subcarrier()
