# demo_vlc_communication.py
import numpy as np
from loguru import logger
from VLCL_AI.environment.room import Room
from VLCL_AI.environment.led import LED
from VLCL_AI.environment.receiver import Receiver
from VLCL_AI.environment.scene import Scene
from VLCL_AI.environment.simulator import VLCLSimulator, MobilityEngine
from VLCL_AI.physics.physics_engine import PhysicsEngine
from VLCL_AI.communication.engine import CommunicationEngine

def main():
    logger.info("Starting Visible Light Communication (VLC) End-to-End Demo...")
    
    # 1. Initialize Scene (Module 1)
    room = Room(5.0, 5.0, 3.0)
    receiver = Receiver([2.5, 2.5, 1.0], [0.0, 0.0, 1.0])
    led = LED(1, [2.5, 2.5, 3.0], [0.0, 0.0, -1.0], power=20.0)
    scene = Scene(room, receiver, [led])
    
    # Simple circular receiver path around center [2.5, 2.5]
    mobility = MobilityEngine("circular", speed=1.0, radius=1.0, center=(2.5, 2.5, 1.0))
    simulator = VLCLSimulator(scene, mobility)
    
    env_state = simulator.step()
    logger.info("Scene initialized. Ceiling LEDs and receiver placed.")
    
    # 2. Initialize Optical Physics Channel (Module 2)
    physics = PhysicsEngine()
    physics_state = physics.step(env_state)
    logger.info("Physics calculations completed. Optical gains and noise variances computed.")
    
    # 3. Initialize VLC & OFDM Communication Engine (Module 3)
    comm_engine = CommunicationEngine()
    
    # Run loopback transmission with 100,000 bits
    tx_bits = comm_engine.bit_generator.generate(100000)
    
    # Propagate through channel
    comm_state = comm_engine.transmit_receive(
        bits=tx_bits,
        environment_state=env_state,
        physics_state=physics_state
    )
    
    # Print results
    print("\n" + "="*50)
    print("           VLC END-TO-END SIMULATION SUMMARY")
    print("="*50)
    print(f"Receiver Position:       {env_state.receiver_position}")
    print(f"Active Transmitter LED:  LED {comm_state.metadata['active_led_id']}")
    print(f"Modulation Format:       16-QAM")
    print(f"FFT size / CP ratio:     {comm_engine.grid.fft_size} / {comm_engine.config.get('cyclic_prefix_ratio')}")
    print("-"*50)
    print(f"Transmitted bits:        {len(comm_state.transmitted_bits)}")
    print(f"Bit Errors Detected:     {comm_state.metadata['bit_errors']}")
    print(f"Empirical BER:           {comm_state.ber_per_user[1]:.2e}")
    print(f"Analytical BER:          {comm_state.metadata['average_analytical_ber']:.2e}")
    print(f"Receiver EVM (%):        {comm_state.evm_per_user[1] * 100.0:.2f}%")
    print(f"Achievable Data Rate:    {comm_state.sum_rate / 1e6:.2f} Mbps")
    print(f"Effective Throughput:    {comm_state.effective_throughput / 1e6:.2f} Mbps")
    print(f"Spectral Efficiency:     {comm_state.spectral_efficiency:.2f} bits/s/Hz")
    print(f"Signal PAPR:             {comm_state.papr:.2f} dB")
    print(f"LED Clipping Ratio:      {comm_state.clipping_ratio:.2f}%")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
