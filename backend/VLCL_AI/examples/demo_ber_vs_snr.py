# demo_ber_vs_snr.py
import numpy as np
from VLCL_AI.communication.ber import BERCalculator

def main():
    print("\n" + "="*60)
    print("      VLC OFDM SIMULATOR - ANALYTICAL BER VS SNR CHARACTERISTICS")
    print("="*60)
    print(f"{'SNR (dB)':<12}{'4-QAM BER':<16}{'16-QAM BER':<16}{'64-QAM BER':<16}")
    print("-"*60)
    
    snr_db_range = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    ber_calc = BERCalculator()
    
    for snr_db in snr_db_range:
        snr_linear = 10 ** (snr_db / 10.0)
        
        ber_4qam = ber_calc.compute_analytical_qam(snr_linear, 4)
        ber_16qam = ber_calc.compute_analytical_qam(snr_linear, 16)
        ber_64qam = ber_calc.compute_analytical_qam(snr_linear, 64)
        
        print(f"{snr_db:<12.1f}{ber_4qam:<16.2e}{ber_16qam:<16.2e}{ber_64qam:<16.2e}")
        
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
