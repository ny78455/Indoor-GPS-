import unittest
import numpy as np

from VLCL_AI.environment.coordinate_system import CoordinateSystem
from VLCL_AI.environment.room import Room
from VLCL_AI.environment.led import LED, LEDArray
from VLCL_AI.environment.receiver import Receiver
from VLCL_AI.environment.geometry import GeometryEngine
from VLCL_AI.environment.mobility import MobilityEngine
from VLCL_AI.environment.obstacle import BoxObstacle
from VLCL_AI.environment.scene import Scene
from VLCL_AI.environment.config import ConfigurationManager

class TestVLCLSimulation(unittest.TestCase):

    def test_distance(self):
        p1 = np.array([0, 0, 0])
        p2 = np.array([3, 4, 12])
        dist = GeometryEngine.distance(p1, p2)
        self.assertEqual(dist, 13.0)

    def test_angles(self):
        # LED facing down
        p_tx = np.array([2.5, 2.5, 3.0])
        n_tx = np.array([0.0, 0.0, -1.0])
        
        # Rx directly below, facing straight up
        p_rx = np.array([2.5, 2.5, 1.0])
        n_rx = np.array([0.0, 0.0, 1.0])
        
        phi, psi = GeometryEngine.calculate_angles(p_tx, n_tx, p_rx, n_rx)
        self.assertAlmostEqual(phi, 0.0)
        self.assertAlmostEqual(psi, 0.0)

    def test_visibility_and_blockage(self):
        p_tx = np.array([2.5, 2.5, 3.0])
        p_rx = np.array([2.5, 2.5, 1.0])
        
        # Create obstacle directly in between (Z = 2.0)
        obs = BoxObstacle("blocker", np.array([2.5, 2.5, 2.0]), np.array([0.5, 0.5, 0.2]))
        
        # Test blockage
        is_visible, blocking_id = GeometryEngine.is_visible_los(p_tx, p_rx, [obs])
        self.assertFalse(is_visible)
        self.assertEqual(blocking_id, "blocker")

    def test_mobility_circular(self):
        mobility = MobilityEngine("circular", speed=1.0, radius=2.0, center=(0, 0, 0))
        pos0 = np.array([2.0, 0.0, 0.0])
        vel0 = np.array([0.0, 1.0, 0.0])
        
        # Advance clock by quarter period: T = 2*pi*R / speed = 2*pi*2 / 1 = 4*pi seconds
        # dt = pi seconds => 90 deg rotation
        dt = np.pi
        pos1, vel1 = mobility.update_position(pos0, vel0, dt)
        
        # Should be at (0, 2.0, 0.0)
        self.assertAlmostEqual(pos1[0], 0.0)
        self.assertAlmostEqual(pos1[1], 2.0)

    def test_scene_metrics(self):
        room = Room(5.0, 5.0, 3.0)
        receiver = Receiver([2.5, 2.5, 1.0], [0, 0, 1])
        led = LED(1, [2.5, 2.5, 3.0], [0, 0, -1], power=20.0)
        
        scene = Scene(room, receiver, [led])
        metrics = scene.get_geometric_metrics()
        
        self.assertEqual(metrics["distances"][1], 2.0)
        self.assertTrue(metrics["visibility_matrix"][1])
        self.assertTrue(metrics["los_matrix"][1])

if __name__ == '__main__':
    unittest.main()
