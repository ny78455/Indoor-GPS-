# test_physics.py
import unittest
import numpy as np

from VLCL_AI.physics.lambertian import lambertian_order, radiation_pattern, irradiance
from VLCL_AI.physics.optical_channel import compute_los_dc_gain
from VLCL_AI.physics.reflection import compute_nlos_reflection
from VLCL_AI.physics.noise import total_noise_variance
from VLCL_AI.physics.snr import compute_snr
from VLCL_AI.physics.photodiode import Photodiode
from VLCL_AI.physics.raytracer import RayTracer

class TestVLCLPhysics(unittest.TestCase):

    def test_lambertian_order(self):
        # Semi-angle 60 degrees should give m = 1.0
        m = lambertian_order(60.0)
        self.assertAlmostEqual(m, 1.0, places=4)
        
        # Semi-angle 30 degrees
        m_30 = lambertian_order(30.0)
        self.assertTrue(m_30 > 1.0)

    def test_irradiance(self):
        m = 1.0
        power = 20.0
        dist = 2.0
        phi = 0.0  # directly below
        irr = irradiance(m, power, dist, phi)
        # E = P * (m + 1) / (2 * pi * d^2) * cos^m(phi)
        # E = 20 * 2 / (2 * pi * 4) * 1 = 40 / (8 * pi) = 5 / pi
        self.assertAlmostEqual(irr, 5.0 / np.pi)

    def test_los_dc_gain(self):
        # Directly below, LOS
        gain = compute_los_dc_gain(
            distance=2.0,
            irradiance_angle_rad=0.0,
            incident_angle_rad=0.0,
            beam_angle_deg=60.0,
            receiver_area=1e-4,
            fov_rad=np.radians(70.0)
        )
        expected = (2.0 * 1e-4 / (2 * np.pi * 4.0)) * 1.5  # includes default lens gain of 1.5 in concentrator
        self.assertAlmostEqual(gain, expected)

    def test_noise_and_snr(self):
        # Test default photodiode and noise
        pd = Photodiode()
        current = pd.convert_power_to_current(1e-3)  # 1 mW received optical power
        self.assertAlmostEqual(current, 1e-3 * 0.54)
        
        noise_res = total_noise_variance(
            signal_current=current,
            tia_gain=1e4,
            bandwidth=20e6
        )
        self.assertTrue(noise_res["total_variance"] > 0)
        
        snr_res = compute_snr(current, noise_res["total_variance"])
        self.assertTrue(snr_res["electrical_snr_db"] > 0)

    def test_ray_tracer_cylinder_blockage(self):
        rt = RayTracer(room_dims=[5.0, 5.0, 3.0], ray_count=10)
        # Cylinder at center
        origin = np.array([1.5, 2.5, 1.0])
        direction = np.array([1.0, 0.0, 0.0]) # shooting straight positive x
        
        cyl_center = np.array([2.5, 2.5, 0.0])
        cyl_radius = 0.5
        cyl_height = 1.8
        
        t, normal = rt.intersect_cylinder_obstacle(origin, direction, cyl_center, cyl_radius, cyl_height)
        # Intersects at x = 2.0 (distance of 0.5m)
        self.assertAlmostEqual(t, 0.5)
        self.assertAlmostEqual(normal[0], -1.0)
        self.assertAlmostEqual(normal[1], 0.0)

if __name__ == '__main__':
    unittest.main()
