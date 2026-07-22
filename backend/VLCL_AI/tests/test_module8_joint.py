# test_module8_joint.py
import unittest
import numpy as np

from VLCL_AI.environment.room import Room
from VLCL_AI.environment.led import LED
from VLCL_AI.environment.receiver import Receiver
from VLCL_AI.environment.scene import Scene
from VLCL_AI.environment.simulator import VLCLSimulator, MobilityEngine
from VLCL_AI.physics.physics_engine import PhysicsEngine

from VLCL_AI.integrated_vlcl.engine import IntegratedVLCLEngine
from VLCL_AI.adaptive.joint_state import JointDecisionState, ConstraintStatus
from VLCL_AI.adaptive.constraint_evaluator import ConstraintEvaluator
from VLCL_AI.adaptive.loc_power_controller import LocalizationPowerController
from VLCL_AI.adaptive.joint_optimizer import JointAdaptiveOptimizer
from VLCL_AI.adaptive.baselines import BaselineComparators

class TestModule8JointOptimization(unittest.TestCase):

    def setUp(self):
        # Room geometry setup
        self.room = Room(5.0, 5.0, 3.0)
        self.receiver = Receiver([0.0, 0.0, 0.85], [0.0, 0.0, 1.0])
        self.leds = [
            LED(1, [-0.4,  0.4, 1.35], [0.0, 0.0, -1.0], power=10.0),
            LED(2, [ 0.4,  0.4, 1.35], [0.0, 0.0, -1.0], power=10.0),
            LED(3, [-0.4, -0.4, 1.35], [0.0, 0.0, -1.0], power=10.0),
            LED(4, [ 0.4, -0.4, 1.35], [0.0, 0.0, -1.0], power=10.0)
        ]
        self.scene = Scene(self.room, self.receiver, self.leds)
        self.mobility = MobilityEngine("static")
        self.simulator = VLCLSimulator(self.scene, self.mobility)
        self.physics = PhysicsEngine()

        self.env_state = self.simulator.get_state()
        self.physics_state = self.physics.step(self.env_state)

        self.vlcl_engine = IntegratedVLCLEngine()

    def test_constraint_evaluator(self):
        """Validates ConstraintEvaluator logic across feasible and infeasible conditions."""
        evaluator = ConstraintEvaluator(
            target_localization_error_m=0.20,
            ber_max=3.8e-3,
            per_led_max_power_w=10.0,
            total_max_power_w=40.0
        )

        rho = np.zeros((4, 256), dtype=int)
        rho[0, 10] = 1
        rho[1, 20] = 1

        status = evaluator.evaluate(
            localization_error_m=0.10,
            achieved_rates_bps={1: 2.0e6, 2: 2.0e6},
            min_rates_bps={1: 1.0e6, 2: 1.0e6},
            per_device_ber={1: 1.0e-4, 2: 1.0e-4},
            per_led_power_w={1: 5.0, 2: 5.0, 3: 5.0, 4: 5.0},
            rho=rho,
            loc_indices=[40, 42, 44, 46, 48]
        )

        self.assertTrue(status.overall_feasible)
        self.assertTrue(status.localization_satisfied)
        self.assertTrue(status.qos_satisfied)
        self.assertTrue(status.ber_satisfied)
        self.assertTrue(status.power_satisfied)

        # Test failure when localization error exceeds target
        status_infeasible = evaluator.evaluate(
            localization_error_m=0.35, # Exceeds 0.20m
            achieved_rates_bps={1: 2.0e6, 2: 2.0e6},
            min_rates_bps={1: 1.0e6, 2: 1.0e6},
            per_device_ber={1: 1.0e-4, 2: 1.0e-4},
            per_led_power_w={1: 5.0, 2: 5.0, 3: 5.0, 4: 5.0},
            rho=rho,
            loc_indices=[40, 42, 44, 46, 48]
        )
        self.assertFalse(status_infeasible.overall_feasible)
        self.assertFalse(status_infeasible.localization_satisfied)

    def test_loc_power_controller(self):
        """Validates LocalizationPowerController bisection search."""
        controller = LocalizationPowerController(
            target_error_m=0.20,
            min_p_loc_w=0.1,
            max_p_loc_w=10.0
        )

        # Mock function: E_loc = 1.0 / sqrt(P_loc)
        def mock_eval(p_loc):
            err = 0.30 / np.sqrt(p_loc)
            return err, {}

        opt_p, err, meta = controller.optimize_power(eval_fn=mock_eval, initial_p_loc_w=1.0)
        self.assertLessEqual(err, 0.20 + 0.02)
        self.assertTrue(meta["satisfied"])

    def test_joint_optimizer_execution(self):
        """Validates complete 8-step JointAdaptiveOptimizer execution loop."""
        optimizer = JointAdaptiveOptimizer(
            vlcl_engine=self.vlcl_engine,
            target_localization_error_m=0.20,
            max_iterations=5
        )

        np.random.seed(42)
        bits_dict = {
            1: np.random.randint(0, 2, 100),
            2: np.random.randint(0, 2, 100),
            3: np.random.randint(0, 2, 100),
            4: np.random.randint(0, 2, 100)
        }

        result_state = optimizer.optimize(
            env_state=self.env_state,
            physics_state=self.physics_state,
            min_rates_bps={1: 5.0e5, 2: 5.0e5, 3: 5.0e5, 4: 5.0e5},
            bits_dict=bits_dict
        )

        self.assertIsInstance(result_state, JointDecisionState)
        self.assertGreater(result_state.sum_rate_bps, 0.0)
        self.assertLessEqual(result_state.localization_error_m, 0.25)
        self.assertTrue(len(result_state.history) > 0)

    def test_baseline_comparators(self):
        """Validates all 4 baseline operational modes."""
        comparators = BaselineComparators(vlcl_engine=self.vlcl_engine)

        min_rates = {1: 5.0e5, 2: 5.0e5, 3: 5.0e5, 4: 5.0e5}

        state_a = comparators.run_baseline_a(self.env_state, self.physics_state, min_rates)
        state_b = comparators.run_baseline_b(self.env_state, self.physics_state, min_rates)
        state_c = comparators.run_baseline_c(self.env_state, self.physics_state, min_rates)
        state_proposed = comparators.run_proposed(self.env_state, self.physics_state, min_rates)

        self.assertIsInstance(state_a, JointDecisionState)
        self.assertIsInstance(state_b, JointDecisionState)
        self.assertIsInstance(state_c, JointDecisionState)
        self.assertIsInstance(state_proposed, JointDecisionState)

        # Proposed should achieve at least equal or higher sum rate than baseline A
        self.assertGreaterEqual(state_proposed.sum_rate_bps, state_a.sum_rate_bps)

if __name__ == "__main__":
    unittest.main()
