# visualization.py
import numpy as np
import json
from typing import List, Dict, Any, Tuple
from VLCL_AI.localization.state import LocalizationState

class LocalizationVisualizer:
    """Provides utilities for plotting and exporting localization trajectories and metrics."""
    
    def __init__(self, history: List[LocalizationState]):
        self.history = history

    def export_to_json(self, file_path: str):
        """Exports the entire run history to a JSON file."""
        serializable_history = [s.to_dict() for s in self.history]
        with open(file_path, 'w') as f:
            json.dump(serializable_history, f, indent=2)

    def plot_trajectory_comparison(self, output_path: str):
        """
        Plots a 2D/3D comparison of true vs. estimated trajectory and saves it.
        Uses matplotlib conditionally.
        """
        try:
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            
            true_pts = np.array([s.true_position_for_evaluation_only for s in self.history])
            est_pts = np.array([s.estimated_position for s in self.history])
            times = np.array([s.simulation_time for s in self.history])
            
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection='3d')
            
            # Ground truth line
            ax.plot(true_pts[:, 0], true_pts[:, 1], true_pts[:, 2], 'g-', label='Ground Truth Trajectory', linewidth=2)
            ax.scatter(true_pts[0, 0], true_pts[0, 1], true_pts[0, 2], color='green', marker='o', s=100, label='Start')
            
            # Estimate line
            ax.plot(est_pts[:, 0], est_pts[:, 1], est_pts[:, 2], 'b--', label='A-DPDOA Estimate', linewidth=1.5)
            ax.scatter(est_pts[0, 0], est_pts[0, 1], est_pts[0, 2], color='blue', marker='x', s=100)
            
            # Error vectors
            for i in range(0, len(self.history), max(1, len(self.history)//15)):
                ax.plot(
                    [true_pts[i, 0], est_pts[i, 0]],
                    [true_pts[i, 1], est_pts[i, 1]],
                    [true_pts[i, 2], est_pts[i, 2]],
                    'r:', alpha=0.6
                )
                
            ax.set_xlabel('X Position (m)')
            ax.set_ylabel('Y Position (m)')
            ax.set_zlabel('Z Position (m)')
            ax.set_title('A-DPDOA Localization 3D Trajectory Comparison')
            ax.legend()
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150)
            plt.close()
        except ImportError:
            # Fallback when matplotlib is not available
            pass

    def plot_error_vs_time(self, output_path: str):
        """Plots instantaneous and cumulative localization errors over time."""
        try:
            import matplotlib.pyplot as plt
            
            times = np.array([s.simulation_time for s in self.history])
            errs_3d = np.array([s.instantaneous_error_m * 100 for s in self.history]) # convert to cm
            errs_horiz = np.array([s.horizontal_error_m * 100 for s in self.history])
            errs_vert = np.array([s.vertical_error_m * 100 for s in self.history])
            
            plt.figure(figsize=(10, 5))
            plt.plot(times, errs_3d, 'r-', label='3D Euclidean Error', linewidth=2)
            plt.plot(times, errs_horiz, 'b--', label='Horizontal 2D Error', alpha=0.8)
            plt.plot(times, errs_vert, 'g:', label='Vertical Error', alpha=0.8)
            
            plt.xlabel('Simulation Time (s)')
            plt.ylabel('Localization Error (cm)')
            plt.title('A-DPDOA Error Evolution Over Time')
            plt.grid(True, linestyle='--', alpha=0.5)
            plt.legend()
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150)
            plt.close()
        except ImportError:
            pass

    def plot_error_cdf(self, output_path: str):
        """Plots the Cumulative Distribution Function (CDF) of the 3D positioning errors."""
        try:
            import matplotlib.pyplot as plt
            
            errs_3d = np.array([s.instantaneous_error_m * 100 for s in self.history]) # convert to cm
            sorted_errs = np.sort(errs_3d)
            cdf = np.arange(1, len(sorted_errs) + 1) / len(sorted_errs)
            
            plt.figure(figsize=(8, 5))
            plt.plot(sorted_errs, cdf, 'b-', linewidth=2)
            
            # Draw lines for 95th and 50th (median) percentile
            median_err = np.percentile(errs_3d, 50)
            p95_err = np.percentile(errs_3d, 95)
            
            plt.axvline(median_err, color='r', linestyle='--', alpha=0.7, label=f'Median: {median_err:.1f} cm')
            plt.axvline(p95_err, color='g', linestyle='-.', alpha=0.7, label=f'95th Percentile: {p95_err:.1f} cm')
            
            plt.xlabel('3D Positioning Error (cm)')
            plt.ylabel('Cumulative Probability')
            plt.title('A-DPDOA Error Cumulative Distribution Function (CDF)')
            plt.grid(True, linestyle='--', alpha=0.5)
            plt.legend()
            plt.xlim(left=0)
            plt.ylim(0, 1.05)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=150)
            plt.close()
        except ImportError:
            pass
