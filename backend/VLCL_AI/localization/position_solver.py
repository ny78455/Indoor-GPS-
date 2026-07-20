import numpy as np
from scipy.optimize import least_squares
from typing import List, Dict, Any, Tuple, Optional
from VLCL_AI.localization.exceptions import SolverError
from VLCL_AI.localization.frequency_plan import LocalizationFrequencyPlan
from VLCL_AI.physics.constants import SPEED_OF_LIGHT  # M2-PHY-005: no re-literaling of physical constants

class DistanceDifferenceSolver:
    """Solves the linear system relating DPD phases to LED distance differences."""
    
    def __init__(self, frequency_plan: LocalizationFrequencyPlan, tone_to_led_map: Dict[int, List[int]]):
        self.plan = frequency_plan
        self.tone_to_led_map = tone_to_led_map
        
        # Determine unique mapped LEDs and build matrix
        self.unique_led_ids = sorted(list(set(sum(tone_to_led_map.values(), []))))
        self.N = len(self.unique_led_ids)
        
        if self.N < 3:
            raise SolverError(f"A-DPDOA requires at least 3 unique LEDs for 2D/3D trilateration, found {self.N}.")
            
        self.led_to_var_idx = {led_id: i for i, led_id in enumerate(self.unique_led_ids)}
        self._build_coefficient_matrix()

    def _build_coefficient_matrix(self):
        """
        Constructs the 3 x (N-1) coefficient matrix A programmatically.
        The system of equations is: A * delta_d = theta
        where delta_d = [d_21, d_31, ..., d_N1]^T is the vector of distance differences.

        SIGN CONVENTION (cross-ref: localization/channel_interface.py::apply_channel)
        -----------------------------------------------------------------------
        channel_interface.py applies delay as: received_phase = -omega * tau
        (standard physics convention: s(t-tau) <=> e^{-j*omega*tau})

        Paper Eq.(5)/(6) writes phase as +omega*tau — a notation difference,
        NOT a physics error. The paper's hardware is agnostic to sign convention
        as long as it is applied consistently.

        Consequence:
          theta_measured = -theta_paper  (our phases are negated relative to paper)
          A_code = -A_paper * (2*pi/c)   (this explicit negation below)

        Net effect:
          A_code * delta_d = theta_measured
          (-A_paper)*(2pi/c) * delta_d = -theta_paper
          => A_paper*(2pi/c) * delta_d = theta_paper  [CORRECT — matches paper Eq.16]

        !!! WARNING !!!
        Do NOT "fix" the sign in only ONE of the two files.
        If channel_interface.py sign changes, A_code sign must also change.
        This invariant is enforced by regression test T-M4-004 / T-M4-006.
        -----------------------------------------------------------------------
        """
        # A shape is (3, N - 1)
        self.A = np.zeros((3, self.N - 1), dtype=np.float64)
        # Req: M2-PHY-005 — use canonical constant, not literal
        c = SPEED_OF_LIGHT
        
        # Differential equations multipliers
        # Eq 1: Tone 1 (+f1), Tone 2 (-2f2), Tone 3 (+f3)
        # Eq 2: Tone 2 (+f2), Tone 3 (-2f3), Tone 4 (+f4)
        # Eq 3: Tone 3 (+f3), Tone 4 (-2f4), Tone 5 (+f5)
        eq_coeffs = [
            {1: 1.0, 2: -2.0, 3: 1.0}, # eq 1
            {2: 1.0, 3: -2.0, 4: 1.0}, # eq 2
            {3: 1.0, 4: -2.0, 5: 1.0}  # eq 3
        ]
        
        for eq_idx in range(3):
            coeffs = eq_coeffs[eq_idx]
            for tone_id, multiplier in coeffs.items():
                leds = self.tone_to_led_map[tone_id]
                freq = self.plan.frequencies[tone_id - 1]
                
                # Use primary LED for the tone
                primary_led = leds[0]
                var_idx = self.led_to_var_idx[primary_led]
                
                if var_idx > 0: # var_idx == 0 is the reference LED (cancels out)
                    self.A[eq_idx, var_idx - 1] += multiplier * freq
                    
        # Apply phase factor (2 * pi / c) with negative sign for physical negative delay propagation
        self.A = -self.A * (2.0 * np.pi / c)
        
        # Calculate condition number
        self.cond_number = np.linalg.cond(self.A)

    def solve(self, theta: np.ndarray) -> Dict[str, float]:
        """
        Solves A * delta_d = theta using least-squares or direct solve.
        Returns a dictionary mapping (led_id_j, led_id_1) to distance difference delta_d_j1.
        """
        # Solve the system
        # If square system, solve exactly
        if self.A.shape[0] == self.A.shape[1]:
            try:
                delta_d = np.linalg.solve(self.A, theta)
            except np.linalg.LinAlgError:
                delta_d = np.linalg.lstsq(self.A, theta, rcond=None)[0]
        else:
            delta_d = np.linalg.lstsq(self.A, theta, rcond=None)[0]
            
        # Reconstruct mapping of distance differences
        ref_led = self.unique_led_ids[0]
        differences = {}
        
        for i in range(1, self.N):
            led_j = self.unique_led_ids[i]
            # delta_d_j1 = d_j - d_1
            differences[(led_j, ref_led)] = float(delta_d[i - 1])
            
        return differences


class PositionSolver:
    """Non-linear position solver to estimate (x, y, z) coordinates using distance differences."""
    
    def __init__(
        self,
        led_positions: Dict[int, List[float]],
        room_bounds: Tuple[float, float, float], # width, length, height
        dimensions: str = "3D",
        fixed_height_m: float = 0.85,
        solver_method: str = "trust_region",
        robust_loss: str = "soft_l1",
        max_iterations: int = 200,
        tolerance: float = 1.0e-9
    ):
        self.led_positions = {k: np.array(v, dtype=np.float64) for k, v in led_positions.items()}
        self.room_bounds = room_bounds
        self.dimensions = dimensions
        self.fixed_height = fixed_height_m
        self.solver_method = "trf" if solver_method == "trust_region" else "lm"
        self.robust_loss = robust_loss
        self.max_iterations = max_iterations
        self.tolerance = tolerance

    def _residual_func(self, p_opt: np.ndarray, diff_meas: Dict[Tuple[int, int], float]) -> np.ndarray:
        """Calculates residual error vector between modeled and measured distance differences."""
        if self.dimensions == "2D_fixed_height":
            p = np.array([p_opt[0], p_opt[1], self.fixed_height])
        else:
            p = p_opt
            
        residuals = []
        for (led_j, led_ref), diff_val in diff_meas.items():
            pos_j = self.led_positions[led_j]
            pos_ref = self.led_positions[led_ref]
            
            dist_j = np.linalg.norm(p - pos_j)
            dist_ref = np.linalg.norm(p - pos_ref)
            
            modeled_diff = dist_j - dist_ref
            residuals.append(modeled_diff - diff_val)
            
        return np.array(residuals, dtype=np.float64)

    def solve(
        self,
        distance_differences: Dict[Tuple[int, int], float],
        initial_guess: Optional[np.ndarray] = None,
        strategy: str = "previous_or_room_center"
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Solves for receiver position.
        Supports grid search, room-center, centroid of LEDs, and warm-starting.
        """
        # Determine bounds
        W, L, H = self.room_bounds
        
        # Step 1: Establish initial guess
        x0 = None
        if initial_guess is not None:
            x0 = np.copy(initial_guess)
            # Clip initial guess inside room bounds to be safe
            x0[0] = np.clip(x0[0], 0.0, W)
            x0[1] = np.clip(x0[1], 0.0, L)
            if self.dimensions == "3D":
                x0[2] = np.clip(x0[2], 0.0, H)
        
        if x0 is None or strategy == "room_center" or np.any(np.isnan(x0)):
            if self.dimensions == "2D_fixed_height":
                x0 = np.array([W / 2.0, L / 2.0])
            else:
                x0 = np.array([W / 2.0, L / 2.0, H / 2.0])
                
        if strategy == "grid_search":
            # Coarse grid search to bypass local minima
            best_cost = float('inf')
            best_p = None
            grid_x = np.linspace(0.1, W - 0.1, 5)
            grid_y = np.linspace(0.1, L - 0.1, 5)
            
            if self.dimensions == "2D_fixed_height":
                for gx in grid_x:
                    for gy in grid_y:
                        p_test = np.array([gx, gy])
                        res = self._residual_func(p_test, distance_differences)
                        cost = np.sum(res ** 2)
                        if cost < best_cost:
                            best_cost = cost
                            best_p = p_test
            else:
                grid_z = np.linspace(0.1, H - 0.1, 4)
                for gx in grid_x:
                    for gy in grid_y:
                        for gz in grid_z:
                            p_test = np.array([gx, gy, gz])
                            res = self._residual_func(p_test, distance_differences)
                            cost = np.sum(res ** 2)
                            if cost < best_cost:
                                best_cost = cost
                                best_p = p_test
            x0 = best_p
            
        elif strategy == "centroid_visible":
            # Average coordinates of mapped LEDs
            centroid = np.mean(list(self.led_positions.values()), axis=0)
            if self.dimensions == "2D_fixed_height":
                x0 = centroid[:2]
            else:
                x0 = centroid

        # Step 2: Establish boundaries for Levenberg-Marquardt vs Trust Region
        if self.dimensions == "2D_fixed_height":
            bounds = ([0.0, 0.0], [W, L])
            x0 = x0[:2]
        else:
            bounds = ([0.0, 0.0, 0.0], [W, L, H])
            x0 = x0[:3]
            
        # Step 3: Run optimization
        # Levenberg-Marquardt doesn't support box bounds or robust loss directly in least_squares.
        # So we use 'trf' (Trust Region Reflective) which fully supports bounds and robust loss functions.
        method = self.solver_method
        loss = self.robust_loss
        
        if method == "lm":
            # LM ignores bounds and robust loss
            res = least_squares(
                self._residual_func,
                x0,
                args=(distance_differences,),
                method="lm",
                max_nfev=self.max_iterations,
                ftol=self.tolerance,
                xtol=self.tolerance
            )
        else:
            res = least_squares(
                self._residual_func,
                x0,
                args=(distance_differences,),
                bounds=bounds,
                method="trf",
                loss=loss,
                max_nfev=self.max_iterations,
                ftol=self.tolerance,
                xtol=self.tolerance
            )
            
        # Reconstruct full 3D position
        if self.dimensions == "2D_fixed_height":
            p_estimated = np.array([res.x[0], res.x[1], self.fixed_height])
        else:
            p_estimated = res.x
            
        solver_metadata = {
            "success": res.success,
            "cost": res.cost,
            "iterations": res.nfev,
            "residual": res.fun.tolist(),
            "status_code": res.status,
            "optimality": res.optimality
        }
        
        return p_estimated, solver_metadata
