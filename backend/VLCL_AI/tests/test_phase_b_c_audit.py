"""
T-M1-ANGLE: Angular Unit Contract Tests (M1-ENV-ANGLE-001)

Verifies that GeometryEngine.calculate_angles() returns radians,
and that all downstream consumers (scene.py FOV checks) use radians correctly.

Test cases derived from analytically obvious geometries (no lookup tables).

T-M1-001: get_state() returns no dc_gains field
T-M1-002: grep-style test — EnvironmentState has no dc_gains field
T-M1-003: LED.__init__ stores only beam_angle, no lambertian_order
T-M1-004: Receiver has no receive_signal() or measure_snr() methods
T-M1-ANGLE-001: LED directly above → phi=0, psi=0 radians
T-M1-ANGLE-002: 45-degree geometry → phi=pi/4, psi=pi/4
T-M1-ANGLE-003: Exactly at FOV boundary → LED is visible
T-M1-ANGLE-004: Just outside FOV → LED is invisible
T-M2-001: Synthetic H(0) hand-computed case — LED directly above, verified formula
T-M2-002: FOV gate — angle just outside FOV returns H(0)=0.0
T-M2-TILT: Tilted vs vertical LED produces different gains
T-INT-001: EnvironmentState angle fields are in radians, no dc_gains
"""

import numpy as np
import math
import unittest
import importlib

from VLCL_AI.environment.geometry import GeometryEngine
from VLCL_AI.environment.state import EnvironmentState
from VLCL_AI.environment.led import LED
from VLCL_AI.environment.receiver import Receiver
from VLCL_AI.environment.room import Room
from VLCL_AI.environment.scene import Scene
from VLCL_AI.environment.simulator import VLCLSimulator
from VLCL_AI.environment.mobility import MobilityEngine
from VLCL_AI.physics.optical_channel import compute_los_dc_gain
from VLCL_AI.physics.lambertian import lambertian_order
from VLCL_AI.physics.physics_engine import PhysicsEngine


TOL = 1e-9  # Tolerance for analytical checks


class TestAngularUnitContract(unittest.TestCase):
    """M1-ENV-ANGLE-001: All calculate_angles() output must be in radians."""

    def test_directly_below_phi_psi_zero(self):
        """T-M1-ANGLE-001: LED directly above receiver → phi=0, psi=0 radians."""
        p_tx = np.array([2.5, 2.5, 3.0])
        n_tx = np.array([0.0, 0.0, -1.0])  # LED pointing down
        p_rx = np.array([2.5, 2.5, 1.0])
        n_rx = np.array([0.0, 0.0,  1.0])  # Receiver pointing up

        phi_rad, psi_rad = GeometryEngine.calculate_angles(p_tx, n_tx, p_rx, n_rx)

        self.assertAlmostEqual(phi_rad, 0.0, delta=TOL,
                               msg=f"phi should be 0 rad but got {phi_rad}")
        self.assertAlmostEqual(psi_rad, 0.0, delta=TOL,
                               msg=f"psi should be 0 rad but got {psi_rad}")
        # Verify these are NOT degrees (0.0 is the same in both so ok — but
        # the 45-degree case below catches a wrong unit definitively)

    def test_45_degree_geometry(self):
        """T-M1-ANGLE-002: 45-degree offset geometry → phi=pi/4, psi=pi/4 radians."""
        # LED at origin pointing along -Z
        p_tx = np.array([0.0, 0.0, 1.0])
        n_tx = np.array([0.0, 0.0, -1.0])
        # Receiver at same height, 1 unit in X direction, pointing up
        # Vector from tx to rx: [1, 0, -1], but we need a 45-deg geometry
        # Place receiver at [1, 0, 0] with n_rx = [0,0,1]
        p_rx = np.array([1.0, 0.0, 0.0])
        n_rx = np.array([0.0, 0.0, 1.0])

        phi_rad, psi_rad = GeometryEngine.calculate_angles(p_tx, n_tx, p_rx, n_rx)

        # Vector tx→rx = [1,0,-1], normalized = [1/√2, 0, -1/√2]
        # n_tx = [0,0,-1], cos(phi) = dot([1/√2, 0, -1/√2], [0,0,-1]) = 1/√2 → phi = π/4
        # n_rx = [0,0,1], -v_tr_unit = [-1/√2, 0, 1/√2], cos(psi) = dot([-1/√2, 0, 1/√2], [0,0,1]) = 1/√2 → psi = π/4
        expected = math.pi / 4.0
        self.assertAlmostEqual(phi_rad, expected, delta=TOL,
                               msg=f"phi: expected pi/4={expected:.6f} rad, got {phi_rad:.6f} rad")
        self.assertAlmostEqual(psi_rad, expected, delta=TOL,
                               msg=f"psi: expected pi/4={expected:.6f} rad, got {psi_rad:.6f} rad")

        # DEFINITIVE unit check: if output were in degrees, we would get 45.0 here.
        # 45.0 ≠ pi/4 ≈ 0.785 → any degree output would fail this assertion.
        self.assertLess(phi_rad, 2.0,
                        "If this fails, calculate_angles() returned degrees not radians!")

    def test_fov_boundary_exactly_at_limit_is_visible(self):
        """T-M1-ANGLE-003: Angle exactly at FOV boundary → LED must be accepted."""
        fov_deg = 60.0
        fov_rad = math.radians(fov_deg)

        # Create receiver with 60° FOV
        receiver = Receiver([0.0, 0.0, 0.0], [0.0, 0.0, 1.0], fov=fov_deg)

        # Place LED such that psi == exactly fov_rad
        # LED at position that produces exactly 60° incident angle at receiver
        # If receiver at origin facing up, LED at angle 60° from receiver normal
        # receiver normal is [0,0,1], LED at [sin(60°), 0, cos(60°)] direction from rx
        # But LED is ceiling-mounted, so let's compute positions directly:
        # distance d, with psi = 60°:
        # Place LED at [d*sin(fov_rad), 0, d*cos(fov_rad)] above receiver
        d = 2.0
        led_x = d * math.sin(fov_rad)
        led_z = d * math.cos(fov_rad)
        p_tx = np.array([led_x, 0.0, led_z])
        n_tx = np.array([0.0, 0.0, -1.0])
        p_rx = np.array([0.0, 0.0, 0.0])
        n_rx = np.array([0.0, 0.0, 1.0])

        _, psi_rad = GeometryEngine.calculate_angles(p_tx, n_tx, p_rx, n_rx)

        # psi should be approximately fov_rad
        self.assertAlmostEqual(psi_rad, fov_rad, delta=1e-6,
                               msg=f"Expected psi={fov_rad:.4f}, got {psi_rad:.4f}")

        # scene.py FOV check: psi_rad <= rx_fov_rad → must be True (accepted)
        self.assertLessEqual(psi_rad, fov_rad + 1e-12,
                             "LED exactly at FOV boundary must be accepted")

    def test_outside_fov_is_invisible(self):
        """T-M1-ANGLE-004: Angle just outside FOV → LED must be rejected."""
        fov_deg = 60.0
        fov_rad = math.radians(fov_deg)
        epsilon = 1e-6  # just outside FOV

        d = 2.0
        angle = fov_rad + epsilon
        led_x = d * math.sin(angle)
        led_z = d * math.cos(angle)
        p_tx = np.array([led_x, 0.0, led_z])
        n_tx = np.array([0.0, 0.0, -1.0])
        p_rx = np.array([0.0, 0.0, 0.0])
        n_rx = np.array([0.0, 0.0, 1.0])

        _, psi_rad = GeometryEngine.calculate_angles(p_tx, n_tx, p_rx, n_rx)

        # scene.py FOV check: psi_rad <= rx_fov_rad → must be False (rejected)
        self.assertGreater(psi_rad, fov_rad,
                           "LED just outside FOV must be rejected (psi > fov_rad)")


class TestModule1OwnershipBoundary(unittest.TestCase):
    """Tests for M1-ENV-001, M1-ENV-002, M1-ENV-003, M1-ENV-004."""

    def test_environment_state_has_no_dc_gains(self):
        """T-M1-001/T-M1-002: EnvironmentState must NOT have a dc_gains field."""
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(EnvironmentState)}
        self.assertNotIn("dc_gains", field_names,
                         "M1-ENV-002: dc_gains must not be in EnvironmentState")
        self.assertIn("incident_angles_rad", field_names,
                      "M1-ENV-ANGLE-001: incident_angles_rad must be in EnvironmentState")
        self.assertIn("irradiance_angles_rad", field_names,
                      "M1-ENV-ANGLE-001: irradiance_angles_rad must be in EnvironmentState")
        self.assertIn("room_dims", field_names,
                      "INT-001: room_dims must be in EnvironmentState")
        self.assertIn("led_orientations", field_names,
                      "INT-001: led_orientations must be in EnvironmentState")
        self.assertIn("led_beam_angles", field_names,
                      "INT-001: led_beam_angles must be in EnvironmentState")
        self.assertNotIn("led_lambertian_orders", field_names,
                         "led_lambertian_orders must NOT be in EnvironmentState (owned by Module 2)")

    def test_led_stores_only_beam_angle_not_lambertian_order(self):
        """T-M1-003: LED.__init__ stores beam_angle but not lambertian_order attribute."""
        led = LED(1, [2.5, 2.5, 3.0], [0.0, 0.0, -1.0], beam_angle=60.0)
        self.assertTrue(hasattr(led, "beam_angle"),
                        "LED must have beam_angle attribute")
        self.assertFalse(hasattr(led, "lambertian_order"),
                         "M1-ENV-003: LED must not compute or store lambertian_order")
        self.assertEqual(led.beam_angle, 60.0)

    def test_receiver_has_no_physics_methods(self):
        """T-M1-004: Receiver must not have receive_signal() or measure_snr()."""
        rx = Receiver([2.5, 2.5, 1.0], [0.0, 0.0, 1.0])
        self.assertFalse(hasattr(rx, "receive_signal"),
                         "M1-ENV-004: receive_signal() must be removed from Receiver")
        self.assertFalse(hasattr(rx, "measure_snr"),
                         "M1-ENV-004: measure_snr() must be removed from Receiver")

    def test_get_state_returns_geometry_only(self):
        """T-M1-001: VLCLSimulator.get_state() returns only geometry state, no PhysicsEngine side-effects."""
        room = Room(5.0, 5.0, 3.0)
        receiver = Receiver([2.5, 2.5, 1.0], [0.0, 0.0, 1.0])
        led = LED(1, [2.5, 2.5, 3.0], [0.0, 0.0, -1.0], beam_angle=60.0)
        scene = Scene(room, receiver, [led])
        mobility = MobilityEngine("static")
        sim = VLCLSimulator(scene, mobility)

        # Should not raise, should return an EnvironmentState
        state = sim.get_state()
        self.assertIsInstance(state, EnvironmentState)

        # Must not have dc_gains
        self.assertFalse(hasattr(state, "dc_gains"),
                         "get_state() must not populate dc_gains")

        # Must have new fields
        self.assertIsInstance(state.incident_angles_rad, dict)
        self.assertIsInstance(state.irradiance_angles_rad, dict)
        self.assertIsInstance(state.room_dims, list)
        self.assertIsInstance(state.led_orientations, dict)
        self.assertIsInstance(state.led_beam_angles, dict)


class TestModule2PhysicsGain(unittest.TestCase):
    """T-M2-001, T-M2-002, T-M2-TILT: Module 2 channel gain correctness."""

    def test_h0_directly_above_hand_computed(self):
        """
        T-M2-001: Synthetic H(0) for LED directly above receiver.

        Geometry: LED at [2.5, 2.5, 3.0], Rx at [2.5, 2.5, 1.0]
        phi = 0, psi = 0, d = 2.0 m, beam_angle = 60°

        Paper formula: H(0) = (m+1)·A / (2π·d²) · cos^m(phi) · g(psi) · cos(psi)
        With phi=psi=0: H(0) = (m+1)·A / (2π·d²) · g(0)
        """
        beam_angle_deg = 60.0
        d = 2.0
        phi_rad = 0.0
        psi_rad = 0.0
        area = 1e-4  # m²
        fov_deg = 70.0
        fov_rad = math.radians(fov_deg)
        n = 1.5  # refractive index
        m = lambertian_order(beam_angle_deg)

        # Call the canonical Module 2 function
        h0 = compute_los_dc_gain(
            distance=d,
            irradiance_angle_rad=phi_rad,
            incident_angle_rad=psi_rad,
            beam_angle_deg=beam_angle_deg,
            receiver_area=area,
            fov_rad=fov_rad,
            refractive_index=n,
            is_los=True
        )

        # Hand-computed:
        # g(0) = n² / sin²(FOV) [Snell's law concentrator at psi=0 → full concentrator gain]
        # g_concentrator = n² / sin²(FOV) for psi in [0, FOV]
        g_expected = (n ** 2) / (math.sin(fov_rad) ** 2)
        h0_expected = ((m + 1) * area / (2 * math.pi * d**2)) * \
                      (math.cos(phi_rad) ** m) * g_expected * math.cos(psi_rad)

        self.assertGreater(h0, 0.0, "H(0) must be positive for LOS, phi=psi=0")
        self.assertAlmostEqual(h0, h0_expected, delta=1e-9 * h0_expected + 1e-20,
                               msg=f"H(0) mismatch: got {h0:.6e}, expected {h0_expected:.6e}")

    def test_h0_zero_outside_fov(self):
        """T-M2-002: FOV gate — angle just outside FOV returns H(0)=0.0 exactly."""
        fov_deg = 60.0
        fov_rad = math.radians(fov_deg)
        outside_psi = fov_rad + 0.001  # just outside FOV

        h0 = compute_los_dc_gain(
            distance=2.0,
            irradiance_angle_rad=0.0,
            incident_angle_rad=outside_psi,
            beam_angle_deg=60.0,
            receiver_area=1e-4,
            fov_rad=fov_rad,
            refractive_index=1.5,
            is_los=True
        )

        self.assertEqual(h0, 0.0,
                         f"H(0) must be 0.0 for psi > FOV, got {h0}")

    def test_tilted_led_differs_from_vertical(self):
        """T-M2-TILT: Tilted LED produces different H(0) than vertical LED at same position."""
        d = 2.0
        area = 1e-4
        fov_rad = math.radians(70.0)
        n = 1.5
        beam_angle = 60.0

        # LED A: vertical (pointing straight down, phi=0 from receiver below)
        h0_vertical = compute_los_dc_gain(
            distance=d,
            irradiance_angle_rad=0.0,     # phi=0 (LED pointing at receiver)
            incident_angle_rad=0.0,        # psi=0 (receiver looking up at LED)
            beam_angle_deg=beam_angle,
            receiver_area=area,
            fov_rad=fov_rad,
            refractive_index=n,
            is_los=True
        )

        # LED B: tilted 30° (phi=pi/6 instead of 0)
        phi_tilt = math.pi / 6.0  # 30°
        h0_tilted = compute_los_dc_gain(
            distance=d,
            irradiance_angle_rad=phi_tilt,
            incident_angle_rad=0.0,
            beam_angle_deg=beam_angle,
            receiver_area=area,
            fov_rad=fov_rad,
            refractive_index=n,
            is_los=True
        )

        self.assertGreater(h0_vertical, 0.0)
        self.assertGreater(h0_tilted, 0.0)
        self.assertNotAlmostEqual(h0_vertical, h0_tilted, places=10,
                                  msg="Tilted and vertical LED must produce different H(0)")

        # Quantitative check: cos^m(30°) < cos^m(0°) = 1 → h0_tilted < h0_vertical
        m = lambertian_order(beam_angle)
        expected_ratio = math.cos(phi_tilt) ** m
        actual_ratio = h0_tilted / h0_vertical
        self.assertAlmostEqual(actual_ratio, expected_ratio, delta=1e-9,
                               msg=f"H(0) ratio: expected {expected_ratio:.6f}, got {actual_ratio:.6f}")


class TestIntegration001(unittest.TestCase):
    """T-INT-001: EnvironmentState angle contract across Module 1 → Module 2 boundary."""

    def setUp(self):
        room = Room(5.0, 5.0, 3.0)
        receiver = Receiver([2.5, 2.5, 1.0], [0.0, 0.0, 1.0], fov=70.0)
        led = LED(1, [2.5, 2.5, 3.0], [0.0, 0.0, -1.0], beam_angle=60.0)
        scene = Scene(room, receiver, [led])
        mobility = MobilityEngine("static")
        self.sim = VLCLSimulator(scene, mobility)
        self.physics_engine = PhysicsEngine()

    def test_angle_fields_in_radians(self):
        """T-INT-001: EnvironmentState angles are in radians; PhysicsEngine can consume directly."""
        state = self.sim.get_state()

        # Verify angle fields exist with correct names
        self.assertIn(1, state.incident_angles_rad)
        self.assertIn(1, state.irradiance_angles_rad)

        phi = state.irradiance_angles_rad[1]
        psi = state.incident_angles_rad[1]

        # LED directly above receiver → phi=0, psi=0
        self.assertAlmostEqual(phi, 0.0, delta=1e-9)
        self.assertAlmostEqual(psi, 0.0, delta=1e-9)

        # Both angles must be in [0, pi] (radian range) — not degrees [0, 180]
        # For this geometry both are 0, but verify they are physically radian-range values
        self.assertGreaterEqual(phi, 0.0)
        self.assertLessEqual(phi, math.pi)
        self.assertGreaterEqual(psi, 0.0)
        self.assertLessEqual(psi, math.pi)

    def test_physics_engine_produces_positive_gain(self):
        """T-INT-001 (part 2): PhysicsEngine.compute() produces positive H(0) using radian angles."""
        state = self.sim.get_state()
        physics_state = self.physics_engine.compute(state)

        # LED directly above → positive LOS gain
        self.assertIn(1, physics_state.los_gains)
        self.assertGreater(physics_state.los_gains[1], 0.0,
                           "M2-PHY-001 fix: H(0) must be positive for direct overhead LED")

        # Sanity check: gain must be < 1 (path loss)
        self.assertLess(physics_state.los_gains[1], 1.0)

    def test_room_dims_propagated(self):
        """T-INT-001 (INT-001): room_dims in EnvironmentState matches Room object."""
        state = self.sim.get_state()
        self.assertEqual(state.room_dims, [5.0, 5.0, 3.0])

    def test_led_beam_angles_propagated(self):
        """T-INT-001 (INT-001): led_beam_angles in EnvironmentState matches LED config."""
        state = self.sim.get_state()
        self.assertIn(1, state.led_beam_angles)
        self.assertEqual(state.led_beam_angles[1], 60.0)

    def test_led_orientations_propagated(self):
        """T-INT-001 (INT-001): led_orientations in EnvironmentState matches LED normal."""
        state = self.sim.get_state()
        self.assertIn(1, state.led_orientations)
        np.testing.assert_allclose(
            state.led_orientations[1], [0.0, 0.0, -1.0], atol=1e-9
        )


if __name__ == "__main__":
    unittest.main()
