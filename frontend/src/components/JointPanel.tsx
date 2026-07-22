import React from "react";
import { Zap, Activity, CheckCircle2, AlertCircle, Loader } from "lucide-react";
import { JointMetrics } from "../types";

interface JointPanelProps {
  metrics: JointMetrics | null;
  isLoading: boolean;
}

export const JointPanel: React.FC<JointPanelProps> = ({ metrics, isLoading }) => {
  if (isLoading && !metrics) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-4 flex-shrink-0 flex flex-col gap-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <div className="flex items-center gap-2">
            <Zap className="w-3.5 h-3.5 text-pink-400" />
            <h4 className="font-bold text-xs text-slate-200">Module 8: Joint Adaptive</h4>
          </div>
          <span className="flex items-center gap-1 text-[10px] text-amber-400">
            <Loader className="w-3 h-3 animate-spin" /> Optimizing...
          </span>
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
    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-4 text-sm relative overflow-hidden flex-shrink-0 flex flex-col gap-3">
      {isLoading && (
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-pink-500 to-transparent animate-[shimmer_1.5s_infinite]"></div>
      )}
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Zap className="w-3.5 h-3.5 text-pink-400" />
          <h4 className="font-bold text-xs text-slate-200">Module 8: Joint Adaptive Engine</h4>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-mono text-[10px]">Iter: {iteration_count}</span>
          <span className={`px-2 py-0.5 rounded-lg text-[9px] font-black uppercase tracking-wide border ${converged ? 'bg-emerald-950/80 text-emerald-400 border-emerald-900/40' : 'bg-rose-950/80 text-rose-400 border-rose-900/40'}`}>
            {converged ? 'CONVERGED' : 'NOT CONVERGED'}
          </span>
        </div>
      </div>

      <div className="text-slate-500 text-[10px] italic">
        {convergence_reason}
      </div>

      {/* Constraints Grid */}
      <div className="grid grid-cols-5 gap-2">
        <ConstraintBadge label="Overall" satisfied={constraint_status.overall_feasible} />
        <ConstraintBadge label="QoS" satisfied={constraint_status.qos_satisfied} />
        <ConstraintBadge label="BER" satisfied={constraint_status.ber_satisfied} />
        <ConstraintBadge label="Loc" satisfied={constraint_status.localization_satisfied} />
        <ConstraintBadge label="Power" satisfied={constraint_status.power_satisfied} />
      </div>

      {/* Main Metrics */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-slate-950/40 border border-slate-800/60 rounded-xl p-3">
          <div className="text-slate-500 text-[10px] font-bold uppercase tracking-wider mb-1">Total Sum Rate</div>
          <div className="text-lg font-bold text-pink-400">
            {(sum_rate_bps / 1e6).toFixed(1)} Mbps
          </div>
          <div className="text-slate-600 text-[9px] mt-1">Active Subcarriers: {active_subcarriers_count}</div>
        </div>
        <div className="bg-slate-950/40 border border-slate-800/60 rounded-xl p-3">
          <div className="text-slate-500 text-[10px] font-bold uppercase tracking-wider mb-1">Loc Error (3D)</div>
          <div className={`text-lg font-bold ${constraint_status.localization_satisfied ? 'text-emerald-400' : 'text-rose-400'}`}>
            {(localization_error_m * 100).toFixed(1)} cm
          </div>
          <div className="text-slate-600 text-[9px] mt-1">Target: {(constraint_status.localization_target_m * 100).toFixed(1)} cm</div>
        </div>
      </div>

      {/* Power Split */}
      <div className="bg-slate-950/40 border border-slate-800/60 rounded-xl p-3 flex flex-col gap-2">
        <div className="flex justify-between items-center text-[10px] font-bold text-slate-400 uppercase tracking-wider">
          <div className="flex items-center gap-1.5"><Activity className="w-3 h-3 text-pink-400" /> Power Split ({total_power_w.toFixed(2)} W)</div>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden flex">
          <div 
            className="bg-gradient-to-r from-sky-600 to-sky-400 flex items-center justify-center text-[10px] font-bold"
            style={{ width: `${(comm_power_w / total_power_w) * 100}%` }}
          />
          <div 
            className="bg-gradient-to-r from-orange-600 to-orange-400 flex items-center justify-center text-[10px] font-bold text-white"
            style={{ width: `${(loc_power_w / total_power_w) * 100}%` }}
          />
        </div>
        <div className="flex justify-between mt-1">
           <span className="text-[9px] text-sky-400 font-mono flex items-center gap-0.5">
             <span className="w-1.5 h-1.5 rounded-full bg-sky-500 inline-block" />
             Comm: {comm_power_w.toFixed(2)} W
           </span>
           <span className="text-[9px] text-orange-500 font-mono flex items-center gap-0.5">
             <span className="w-1.5 h-1.5 rounded-full bg-orange-500 inline-block" />
             Loc: {loc_power_w.toFixed(2)} W
           </span>
        </div>
      </div>

      {/* Convergence Trajectory */}
      {history_summary && history_summary.length > 0 && (
        <div className="flex flex-col gap-2">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Optimization Trajectory</div>
          <div className="max-h-40 overflow-y-auto custom-scrollbar pr-1 bg-slate-950/60 border border-slate-800 rounded-xl">
            <table className="w-full text-left border-collapse text-[10px]">
              <thead className="bg-slate-900 sticky top-0">
                <tr className="border-b border-slate-800 text-slate-500">
                  <th className="py-2 px-2 font-semibold">Iter</th>
                  <th className="py-2 px-2 font-semibold">Sum Rate</th>
                  <th className="py-2 px-2 font-semibold">Loc Err</th>
                  <th className="py-2 px-2 font-semibold">Loc Pwr</th>
                  <th className="py-2 px-2 font-semibold">Feasible</th>
                </tr>
              </thead>
              <tbody>
                {history_summary.map((h, i) => (
                  <tr key={i} className="border-b border-slate-800/60 text-slate-300 hover:bg-slate-900/50 transition-colors">
                    <td className="py-2 px-2">#{h.iteration}</td>
                    <td className="py-2 px-2 font-mono">{(h.sum_rate_bps / 1e6).toFixed(1)} M</td>
                    <td className="py-2 px-2 font-mono">{(h.localization_error_m * 100).toFixed(1)} cm</td>
                    <td className="py-2 px-2 font-mono">{h.loc_power_w.toFixed(2)} W</td>
                    <td className="py-2 px-2">
                      {h.feasible ? <CheckCircle2 className="w-3 h-3 text-emerald-400" /> : <AlertCircle className="w-3 h-3 text-rose-400" />}
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
  <div className={`flex flex-col items-center justify-center p-2 rounded-xl text-center border ${satisfied ? 'bg-emerald-950/40 border-emerald-900/30' : 'bg-rose-950/40 border-rose-900/30'}`}>
    <div className={`text-sm font-bold ${satisfied ? 'text-emerald-400' : 'text-rose-400'}`}>
      {satisfied ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
    </div>
    <div className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mt-1">
      {label}
    </div>
  </div>
);
