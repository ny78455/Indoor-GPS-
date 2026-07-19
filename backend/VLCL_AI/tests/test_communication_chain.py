# test_communication_chain.py
import unittest
import numpy as np

from VLCL_AI.environment.room import Room
from VLCL_AI.environment.led import LED
from VLCL_AI.environment.receiver import Receiver
from VLCL_AI.environment.scene import Scene
from VLCL_AI.environment.simulator import VLCLSimulator, MobilityEngine
from VLCL_AI.physics.physics_engine import PhysicsEngine
from VLCL_AI.communication.engine import CommunicationEngine

class TestCommunicationChain(unittest.TestCase):
    
    def setUp(self):
        # Initialize Scene (Module 1)
        self.room = Room(5.0, 5.0, 3.0)
        self.receiver = Receiver([2.5, 2.5, 1.0], [0.0, 0.0, 1.0])
        self.led = LED(1, [2.5, 2.5, 3.0], [0.0, 0.0, -1.0], power=20.0)
        self.scene = Scene(self.room, self.receiver, [self.led])
        
        # Mobility engine
        self.mobility = MobilityEngine("circular", speed=1.0, radius=1.0, center=(2.5, 2.5, 1.0))
        self.simulator = VLCLSimulator(self.scene, self.mobility)
        
        # Physics Engine (Module 2)
        self.physics = PhysicsEngine()
        
        # Communication Engine (Module 3)
        self.engine = CommunicationEngine()

    def test_end_to_end_loopback(self):
        # 1. Advance simulator step
        env_state = self.simulator.step()
        
        # 2. Compute physics
        physics_state = self.physics.step(env_state)
        
        # 3. Process communication
        comm_state = self.engine.step(env_state, physics_state)
        
        # Confirm we successfully generated, transmitted, and decoded bits
        self.assertEqual(len(comm_state.transmitted_bits), len(comm_state.received_bits))
        self.assertTrue(comm_state.sum_rate > 0)
        self.assertTrue(comm_state.effective_throughput > 0)
        self.assertIn(1, comm_state.ber_per_user)

if __name__ == '__main__':
    unittest.main()
