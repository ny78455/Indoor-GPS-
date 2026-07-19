# demo_ofdm_spectrum.py
from VLCL_AI.communication.subcarrier_grid import SubcarrierGrid

def main():
    grid = SubcarrierGrid(fft_size=64, total_bandwidth=20e6)
    dict_payload = grid.to_dict()
    
    print("\n" + "="*60)
    print("           OFDM SUBCARRIER GRID SPECTRUM ALLOCATION")
    print("="*60)
    print(f"{'Index':<8}{'Frequency (MHz)':<20}{'Purpose':<20}{'Active'}")
    print("-"*60)
    
    # Print a representative sample of subcarrier allocations
    for i in range(len(dict_payload)):
        sc = dict_payload[i]
        if i < 8 or i > 56 or i in [16, 32, 48]:
            print(f"{sc['index']:<8}{sc['center_frequency']/1e6:<20.4f}{sc['purpose']:<20}{sc['active']}")
        elif i == 8:
            print("...")
            
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
