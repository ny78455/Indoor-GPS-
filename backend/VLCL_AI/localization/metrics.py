# metrics.py
import numpy as np
from typing import List, Dict, Any, Tuple

class LocalizationMetrics:
    """Computes and tracks historical localization performance and stats."""
    
    def __init__(self):
        self.reset()

    def reset(self):
        self.errors_3d = []
        self.errors_horizontal = []
        self.errors_vertical = []
        self.statuses = []
        self.confidence_scores = []
        self.timestamps = []

    def add_frame(
        self,
        timestamp: float,
        estimated_pos: np.ndarray,
        true_pos: np.ndarray,
        status: str,
        confidence: float
    ):
        """Adds performance results of a single localization frame."""
        self.timestamps.append(timestamp)
        self.statuses.append(status)
        self.confidence_scores.append(confidence)
        
        # Calculate errors
        diff = estimated_pos - true_pos
        err_3d = np.linalg.norm(diff)
        err_horiz = np.linalg.norm(diff[:2])
        err_vert = np.abs(diff[2])
        
        self.errors_3d.append(err_3d)
        self.errors_horizontal.append(err_horiz)
        self.errors_vertical.append(err_vert)

    def get_metrics(self) -> Dict[str, Any]:
        """Calculates running statistical performance indicators."""
        if not self.errors_3d:
            return {
                "count": 0,
                "mean_3d_error_m": 0.0,
                "median_3d_error_m": 0.0,
                "rmse_3d_error_m": 0.0,
                "std_3d_error_m": 0.0,
                "percentile_95_3d_error_m": 0.0,
                "max_3d_error_m": 0.0,
                "mean_horizontal_error_m": 0.0,
                "mean_vertical_error_m": 0.0,
                "success_rate": 0.0,
                "failure_rate": 0.0,
                "low_confidence_rate": 0.0
            }
            
        errs_3d = np.array(self.errors_3d)
        errs_horiz = np.array(self.errors_horizontal)
        errs_vert = np.array(self.errors_vertical)
        stats = np.array(self.statuses)
        
        total_frames = len(errs_3d)
        valid_count = np.sum(stats == "VALID")
        fail_count = np.sum(stats == "SOLVER_FAILED")
        low_conf_count = np.sum(stats == "LOW_CONFIDENCE")
        
        rmse = np.sqrt(np.mean(errs_3d ** 2))
        
        return {
            "count": total_frames,
            "mean_3d_error_m": float(np.mean(errs_3d)),
            "median_3d_error_m": float(np.median(errs_3d)),
            "rmse_3d_error_m": float(rmse),
            "std_3d_error_m": float(np.std(errs_3d)),
            "percentile_95_3d_error_m": float(np.percentile(errs_3d, 95)),
            "max_3d_error_m": float(np.max(errs_3d)),
            "mean_horizontal_error_m": float(np.mean(errs_horiz)),
            "mean_vertical_error_m": float(np.mean(errs_vert)),
            "success_rate": float(valid_count / total_frames),
            "failure_rate": float(fail_count / total_frames),
            "low_confidence_rate": float(low_conf_count / total_frames)
        }
