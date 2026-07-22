import React from "react";
import { JointMetrics } from "../types";

interface JointPanelProps {
  metrics: JointMetrics | null;
  isLoading: boolean;
}

export const JointPanel: React.FC<JointPanelProps> = ({ metrics, isLoading }) => {
  if (isLoading && !metrics) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-4 shadow-xl">
        <h3 className="text-xl font-bold text-gray-200 mb-2 border-b border-gray-700 pb-2 flex items-center gap-2">
          <span className="text-pink-400">⚡</span> Module 8: Joint Adaptive Engine
        </h3>
        <div className="flex items-center justify-center p-4">
          <div className="w-6 h-6 border-2 border-pink-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="ml-3 text-gray-400 font-mono text-sm">Optimizing Joint State...</span>
        </div>
      </div>
    );
  }

  if (!metrics) return null;

  const {
    iteration_count,
    converged,
    convergence_reason,
    total_power_w,
    loc_power_w,
    comm_power_w,
    sum_rate_bps,
    localization_error_m,
    constraint_status,
    active_subcarriers_count,
    history_summary
  } = metrics;

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-4 shadow-xl text-sm relative overflow-hidden">
      {isLoading && (
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-pink-500 to-transparent animate-[shimmer_1.5s_infinite]"></div>
      )}
      
      <div className="flex items-center justify-between mb-4 border-b border-gray-700 pb-2">
        <h3 className="text-lg font-bold text-gray-200 flex items-center gap-2">
          <span className="text-pink-400">⚡</span> Module 8: Joint Adaptive Engine
        </h3>
        <div className="flex items-center gap-2">
          <span className="text-gray-400 font-mono text-xs">Iter: {iteration_count}</span>
          <span className={`px-2 py-1 rounded text-xs font-bold ${converged ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
            {converged ? 'CONVERGED' : 'DID NOT CONVERGE'}
          </span>
        </div>
      </div>

      <div className="text-gray-400 text-xs italic mb-4">
        {convergence_reason}
      </div>

      {/* Constraints Grid */}
      <div className="grid grid-cols-5 gap-2 mb-4">
        <ConstraintBadge label="Overall" satisfied={constraint_status.overall_feasible} />
        <ConstraintBadge label="QoS" satisfied={constraint_status.qos_satisfied} />
        <ConstraintBadge label="BER" satisfied={constraint_status.ber_satisfied} />
        <ConstraintBadge label="Localization" satisfied={constraint_status.localization_satisfied} />
        <ConstraintBadge label="Power" satisfied={constraint_status.power_satisfied} />
      </div>

      {/* Main Metrics */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-gray-900 rounded p-3">
          <div className="text-gray-400 text-xs mb-1">Total Sum Rate</div>
          <div className="text-xl font-bold text-pink-400">
            {(sum_rate_bps / 1e6).toFixed(1)} Mbps
          </div>
          <div className="text-gray-500 text-xs mt-1">Active Subcarriers: {active_subcarriers_count}</div>
        </div>
        <div className="bg-gray-900 rounded p-3">
          <div className="text-gray-400 text-xs mb-1">Loc Error (3D)</div>
          <div className={`text-xl font-bold ${constraint_status.localization_satisfied ? 'text-green-400' : 'text-red-400'}`}>
            {(localization_error_m * 100).toFixed(1)} cm
          </div>
          <div className="text-gray-500 text-xs mt-1">Target: {(constraint_status.localization_target_m * 100).toFixed(1)} cm</div>
        </div>
      </div>

      {/* Power Split */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Power Distribution ({total_power_w.toFixed(2)} W)</span>
        </div>
        <div className="h-4 bg-gray-700 rounded-full overflow-hidden flex">
          <div 
            className="bg-purple-500 flex items-center justify-center text-[10px] font-bold"
            style={{ width: `${(comm_power_w / total_power_w) * 100}%` }}
          >
            {comm_power_w > 0 && `Comm ${comm_power_w.toFixed(2)}W`}
          </div>
          <div 
            className="bg-orange-500 flex items-center justify-center text-[10px] font-bold text-white"
            style={{ width: `${(loc_power_w / total_power_w) * 100}%` }}
          >
            {loc_power_w > 0 && `Loc ${loc_power_w.toFixed(2)}W`}
          </div>
        </div>
      </div>

      {/* Convergence Trajectory */}
      {history_summary && history_summary.length > 0 && (
        <div className="mt-4">
          <div className="text-gray-400 text-xs mb-2">Optimization Trajectory</div>
          <div className="max-h-40 overflow-y-auto custom-scrollbar pr-1 border border-gray-700 rounded-lg">
            <table className="w-full text-left border-collapse text-xs">
              <thead className="bg-gray-800 sticky top-0">
                <tr className="border-b border-gray-700 text-gray-500">
                  <th className="py-2 px-2">Iter</th>
                  <th className="py-2 px-2">Sum Rate (Mbps)</th>
                  <th className="py-2 px-2">Loc Err (cm)</th>
                  <th className="py-2 px-2">Loc Pwr (W)</th>
                  <th className="py-2 px-2">Feasible</th>
                </tr>
              </thead>
              <tbody>
                {history_summary.map((h, i) => (
                  <tr key={i} className="border-b border-gray-800 text-gray-300 hover:bg-gray-750 transition-colors">
                    <td className="py-2 px-2">#{h.iteration}</td>
                    <td className="py-2 px-2 font-mono">{(h.sum_rate_bps / 1e6).toFixed(1)}</td>
                    <td className="py-2 px-2 font-mono">{(h.localization_error_m * 100).toFixed(1)}</td>
                    <td className="py-2 px-2 font-mono">{h.loc_power_w.toFixed(2)}</td>
                    <td className="py-2 px-2">
                      {h.feasible ? <span className="text-green-400">✓</span> : <span className="text-red-400">✗</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

const ConstraintBadge = ({ label, satisfied }: { label: string; satisfied: boolean }) => (
  <div className={`flex flex-col items-center justify-center p-2 rounded text-center border ${satisfied ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
    <div className={`text-sm font-bold ${satisfied ? 'text-green-400' : 'text-red-400'}`}>
      {satisfied ? '✓' : '✗'}
    </div>
    <div className="text-[10px] text-gray-400 uppercase tracking-wide mt-1">
      {label}
    </div>
  </div>
);
