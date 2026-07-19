# test_module2_integration.py
import unittest
import numpy as np

from VLCL_AI.environment.room import Room
from VLCL_AI.environment.led import LED
from VLCL_AI.environment.receiver import Receiver
from VLCL_AI.environment.scene import Scene
from VLCL_AI.environment.simulator import VLCLSimulator, MobilityEngine
from VLCL_AI.physics.physics_engine import PhysicsEngine
from VLCL_AI.communication.engine import CommunicationEngine

class TestModule2Integration(unittest.TestCase):
    
    def setUp(self):
        # Initialize Scene (Module 1)
        self.room = Room(5.0, 5.0, 3.0)
        self.receiver = Receiver([2.5, 2.5, 1.0], [0.0, 0.0, 1.0])
        self.led = LED(1, [2.5, 2.5, 3.0], [0.0, 0.0, -1.0], power=20.0)
        self.scene = Scene(self.room, self.receiver, [self.led])
        
        self.mobility = MobilityEngine("circular", speed=1.0, radius=1.0, center=(2.5, 2.5, 1.0))
        self.simulator = VLCLSimulator(self.scene, self.mobility)
        
        self.physics = PhysicsEngine()
        self.engine = CommunicationEngine()

    def test_receiver_mobility_effects(self):
        # Position 1: Directly under the LED (high gain, high SNR)
        self.receiver.position = np.array([2.5, 2.5, 1.0])
        env_1 = self.simulator.get_state()
        phys_1 = self.physics.step(env_1)
        comm_1 = self.engine.step(env_1, phys_1)
        
        # Position 2: Far corner of the room (low gain, high attenuation)
        self.receiver.position = np.array([0.1, 0.1, 1.0])
        env_2 = self.simulator.get_state()
        phys_2 = self.physics.step(env_2)
        comm_2 = self.engine.step(env_2, phys_2)
        
        # Average SNR in position 1 should be significantly higher than position 2
        snr_1 = np.mean(comm_1.snr_per_subcarrier)
        snr_2 = np.mean(comm_2.snr_per_subcarrier)
        
        self.assertTrue(snr_1 > snr_2)

if __name__ == '__main__':
    unittest.main()
