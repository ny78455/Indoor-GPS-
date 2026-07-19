# demo_constellation.py
from VLCL_AI.communication.qam import QAMModem

def main():
    modem = QAMModem()
    print("\n" + "="*50)
    print("      VLC CONSTELLATION MAPPER (NORMALIZED ENERGY)")
    print("="*50)
    
    for M in [4, 16]:
        constellation = modem.get_constellation(M)
        print(f"\n{M}-QAM Constellation Points (First 4 symbols):")
        print("-" * 45)
        for idx in range(min(4, len(constellation))):
            sym = constellation[idx]
            print(f"Symbol {idx:02d}: Real (I) = {sym.real:+.4f}, Imag (Q) = {sym.imag:+.4f}")
            
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
