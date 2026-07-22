# baselines.py
import numpy as np
import copy
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from VLCL_AI.integrated_vlcl.engine import IntegratedVLCLEngine

from VLCL_AI.environment.state import EnvironmentState
from VLCL_AI.physics.physics_engine import PhysicsState
from VLCL_AI.adaptive.joint_state import JointDecisionState
from VLCL_AI.adaptive.joint_optimizer import JointAdaptiveOptimizer

class BaselineComparators:
    """
    Implements standardized baseline operational modes for scientific comparison (Section IV of Yang et al., 2023):
    1. BASELINE_A: Static subcarrier allocation + fixed 16-QAM + equal power.
    2. BASELINE_B: Adaptive M-QAM + subcarrier allocation + equal power (no water-filling / pre-EQ).
    3. BASELINE_C: Uncoupled single-pass adaptive allocation (Module 6 -> Module 7, no feedback loop).
    4. PROPOSED: Full Joint Adaptive Transmission Optimization Engine (Module 8).
    """

    def __init__(self, vlcl_engine: Optional["IntegratedVLCLEngine"] = None):
        if vlcl_engine is None:
            from VLCL_AI.integrated_vlcl.engine import IntegratedVLCLEngine
            self.vlcl_engine = IntegratedVLCLEngine()
        else:
            self.vlcl_engine = vlcl_engine

    def run_baseline_a(
        self,
        env_state: EnvironmentState,
        physics_state: PhysicsState,
        min_rates_bps: Optional[Dict[int, float]] = None
    ) -> JointDecisionState:
        """BASELINE A: Static 16-QAM, equal subcarrier allocation, equal power."""
        optimizer = JointAdaptiveOptimizer(
            vlcl_engine=self.vlcl_engine,
            max_iterations=1
        )
        # Execute single pass with EQUAL_POWER and NO pre-EQ
        state = optimizer.optimize(
            env_state=env_state,
            physics_state=physics_state,
            min_rates_bps=min_rates_bps,
            power_mode="EQUAL_POWER",
            pre_eq_mode="NONE"
        )
        state.convergence_reason = "BASELINE_A (Static 16-QAM, Equal Power)"
        return state

    def run_baseline_b(
        self,
        env_state: EnvironmentState,
        physics_state: PhysicsState,
        min_rates_bps: Optional[Dict[int, float]] = None
    ) -> JointDecisionState:
        """BASELINE B: Adaptive M-QAM + subcarrier allocation, equal power, no pre-EQ."""
        optimizer = JointAdaptiveOptimizer(
            vlcl_engine=self.vlcl_engine,
            max_iterations=1
        )
        state = optimizer.optimize(
            env_state=env_state,
            physics_state=physics_state,
            min_rates_bps=min_rates_bps,
            power_mode="EQUAL_POWER",
            pre_eq_mode="NONE"
        )
        state.convergence_reason = "BASELINE_B (Adaptive M-QAM, Equal Power)"
        return state

    def run_baseline_c(
        self,
        env_state: EnvironmentState,
        physics_state: PhysicsState,
        min_rates_bps: Optional[Dict[int, float]] = None
    ) -> JointDecisionState:
        """BASELINE C: Uncoupled single-pass adaptive allocation + water-filling (no joint loop)."""
        optimizer = JointAdaptiveOptimizer(
            vlcl_engine=self.vlcl_engine,
            max_iterations=1
        )
        state = optimizer.optimize(
            env_state=env_state,
            physics_state=physics_state,
            min_rates_bps=min_rates_bps,
            power_mode="WATER_FILLING",
            pre_eq_mode="REGULARIZED"
        )
        state.convergence_reason = "BASELINE_C (Uncoupled Single-Pass)"
        return state

    def run_proposed(
        self,
        env_state: EnvironmentState,
        physics_state: PhysicsState,
        min_rates_bps: Optional[Dict[int, float]] = None
    ) -> JointDecisionState:
        """PROPOSED: Complete Joint Adaptive Transmission Optimization Engine."""
        optimizer = JointAdaptiveOptimizer(
            vlcl_engine=self.vlcl_engine,
            max_iterations=10
        )
        state = optimizer.optimize(
            env_state=env_state,
            physics_state=physics_state,
            min_rates_bps=min_rates_bps,
            power_mode="WATER_FILLING",
            pre_eq_mode="REGULARIZED"
        )
        return state
