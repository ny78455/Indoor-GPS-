# loc_power_controller.py
import numpy as np
from typing import Dict, Any, Callable, Tuple, Optional

class LocalizationPowerController:
    """
    Step 03 Controller: Bounded Search for minimum localization tone power (P_loc)
    required to guarantee target 3D localization accuracy E_loc <= E_loc_max.
    """

    def __init__(
        self,
        target_error_m: float = 0.20,
        min_p_loc_w: float = 0.1,
        max_p_loc_w: float = 10.0,
        tolerance_m: float = 0.01,
        max_search_iterations: int = 6
    ):
        self.target_error_m = target_error_m
        self.min_p_loc_w = min_p_loc_w
        self.max_p_loc_w = max_p_loc_w
        self.tolerance_m = tolerance_m
        self.max_search_iterations = max_search_iterations

    def optimize_power(
        self,
        eval_fn: Callable[[float], Tuple[float, Dict[str, Any]]],
        initial_p_loc_w: float = 2.0
    ) -> Tuple[float, float, Dict[str, Any]]:
        """
        Performs a bounded bisection / secant search to find the minimal P_loc
        that achieves E_loc <= target_error_m.

        Args:
            eval_fn: Function mapping P_loc -> (3D_error_m, eval_metadata)
            initial_p_loc_w: Initial seed power in Watts.

        Returns:
            optimal_p_loc_w (float): Optimal localization power [Watts].
            achieved_error_m (float): Resulting 3D localization error [meters].
            meta (dict): Search metadata and convergence history.
        """
        history = []

        # Evaluate at initial guess
        curr_p = np.clip(initial_p_loc_w, self.min_p_loc_w, self.max_p_loc_w)
        err, meta = eval_fn(curr_p)
        history.append({"p_loc": curr_p, "error_m": err})

        if abs(err - self.target_error_m) <= self.tolerance_m or (err <= self.target_error_m and curr_p == self.min_p_loc_w):
            return curr_p, err, {"history": history, "search_iterations": 1, "satisfied": err <= self.target_error_m}

        low_p = self.min_p_loc_w
        high_p = self.max_p_loc_w

        # If initial P_loc passes target, try lower bound to see if we can save power
        if err <= self.target_error_m:
            high_p = curr_p
            low_err, _ = eval_fn(low_p)
            history.append({"p_loc": low_p, "error_m": low_err})
            if low_err <= self.target_error_m:
                return low_p, low_err, {"history": history, "search_iterations": 2, "satisfied": True}
        else:
            # Initial P_loc failed, evaluate upper bound
            low_p = curr_p
            high_err, _ = eval_fn(high_p)
            history.append({"p_loc": high_p, "error_m": high_err})
            if high_err > self.target_error_m:
                # Even maximum power fails to meet target error (e.g. extreme shadowing)
                return high_p, high_err, {"history": history, "search_iterations": 2, "satisfied": False}

        # Bisection loop
        best_p = high_p
        best_err = err
        
        for it in range(self.max_search_iterations):
            mid_p = 0.5 * (low_p + high_p)
            mid_err, mid_meta = eval_fn(mid_p)
            history.append({"p_loc": mid_p, "error_m": mid_err})

            if mid_err <= self.target_error_m:
                best_p = mid_p
                best_err = mid_err
                high_p = mid_p # Try finding even smaller power
            else:
                low_p = mid_p # Need more power

            if abs(high_p - low_p) < 0.05: # 50mW power resolution threshold
                break

        return best_p, best_err, {
            "history": history,
            "search_iterations": len(history),
            "satisfied": best_err <= self.target_error_m
        }
