/**
 * LocalizationPanel.tsx
 *
 * Module 4 — A-DPDOA Indoor Localization Engine KPI Dashboard.
 * Displays live positioning metrics from the Python LocalizationEngine:
 *   - Estimated vs. true 3D position
 *   - Instantaneous / horizontal / vertical / RMSE errors
 *   - Solver stats (method, iterations, residual cost)
 *   - Per-LED localization SNR bars
 *   - Distance differences between LED pairs
 *   - Running historical performance stats
 */

import {
  MapPin, AlertCircle, CheckCircle2, Loader,
  Navigation2, Activity, Target, Crosshair,
  BarChart3, ArrowUpDown, Zap,
} from "lucide-react";
import { LocalizationMetrics } from "../types";

interface LocalizationPanelProps {
  metrics: LocalizationMetrics | null;
  loading: boolean;
}

// ─── Status Badge ─────────────────────────────────────────────────────────────
function StatusBadge({ status }: { status: string }) {
  if (status === "VALID")
    return (
      <span className="px-1.5 py-0.5 text-[9px] font-bold rounded-md bg-emerald-950/80 text-emerald-400 border border-emerald-900/40">
        VALID
      </span>
    );
  if (status === "LOW_CONFIDENCE")
    return (
      <span className="px-1.5 py-0.5 text-[9px] font-bold rounded-md bg-amber-950/80 text-amber-400 border border-amber-900/40">
        LOW CONF
      </span>
    );
  if (status === "INSUFFICIENT_GEOMETRY")
    return (
      <span className="px-1.5 py-0.5 text-[9px] font-bold rounded-md bg-rose-950/80 text-rose-400 border border-rose-900/40">
        NO GEOM
      </span>
    );
  return (
    <span className="px-1.5 py-0.5 text-[9px] font-bold rounded-md bg-slate-800 text-slate-400 border border-slate-700">
      FAILED
    </span>
  );
}

// ─── Confidence Gauge ─────────────────────────────────────────────────────────
function ConfidenceGauge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 60 ? "from-emerald-600 to-emerald-400"
    : pct >= 30 ? "from-amber-600 to-amber-400"
    : "from-rose-600 to-rose-400";
  const textColor =
    pct >= 60 ? "text-emerald-400" : pct >= 30 ? "text-amber-400" : "text-rose-400";

  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between items-center">
        <span className="text-[10px] text-slate-500">Confidence Score</span>
        <span className={`text-[13px] font-mono font-black ${textColor}`}>
          {pct}%
        </span>
      </div>
      <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${color} transition-all duration-700`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ─── Error Bar ────────────────────────────────────────────────────────────────
function ErrorBar({ label, value, maxVal, unit, color }: {
  label: string; value: number; maxVal: number; unit: string; color: string;
}) {
  const pct = Math.min(100, Math.max(0, (value / maxVal) * 100));
  const gradClass =
    color === "emerald" ? "from-emerald-600 to-emerald-400"
    : color === "amber" ? "from-amber-600 to-amber-400"
    : "from-cyan-600 to-cyan-400";
  const textClass =
    color === "emerald" ? "text-emerald-300"
    : color === "amber" ? "text-amber-300"
    : "text-cyan-300";

  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between items-center">
        <span className="text-[10px] text-slate-500">{label}</span>
        <span className={`text-[11px] font-mono font-bold ${textClass}`}>
          {value.toFixed(3)} {unit}
        </span>
      </div>
      <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${gradClass} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ─── SNR Mini Bar ─────────────────────────────────────────────────────────────
function SnrRow({ ledId, snr }: { ledId: string; snr: number }) {
  const pct = Math.min(100, Math.max(0, Math.round(((snr + 10) / 50) * 100)));
  const color =
    snr > 25 ? "from-emerald-600 to-emerald-400"
    : snr > 10 ? "from-amber-600 to-amber-400"
    : "from-rose-600 to-rose-400";
  const textColor =
    snr > 25 ? "text-emerald-300" : snr > 10 ? "text-amber-300" : "text-rose-300";

  return (
    <div className="flex items-center gap-2">
      <span className="text-[9px] font-mono text-slate-500 w-8 shrink-0">L{ledId}</span>
      <div className="flex-1 bg-slate-800 h-1.5 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${color} transition-all duration-700`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`text-[10px] font-mono font-bold w-16 text-right ${textColor}`}>
        {snr.toFixed(1)} dB
      </span>
    </div>
  );
}

// ─── Metric Cell ─────────────────────────────────────────────────────────────
function MCell({ label, value, unit, color = "text-slate-300" }: {
  label: string; value: string; unit: string; color?: string;
}) {
  return (
    <div className="bg-slate-950/60 rounded-xl p-3 flex flex-col gap-0.5">
      <span className="text-[10px] text-slate-500 leading-none">{label}</span>
      <div className="flex items-baseline gap-1 mt-1">
        <span className={`font-mono font-black text-sm leading-none ${color}`}>{value}</span>
        <span className="text-[10px] text-slate-600">{unit}</span>
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function LocalizationPanel({ metrics, loading }: LocalizationPanelProps) {
  const snrEntries = metrics
    ? Object.entries(metrics.signals.localization_snr).sort((a, b) => Number(a[0]) - Number(b[0]))
    : [];

  const ddEntries = metrics
    ? Object.entries(metrics.geometry.distance_differences)
    : [];

  const runStats = metrics?.metadata?.running_stats as Record<string, number> | undefined;

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-4 flex flex-col gap-3">

      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <MapPin className="w-3.5 h-3.5 text-orange-400" />
          <h4 className="font-bold text-xs text-slate-200">A-DPDOA Localization</h4>
        </div>
        {loading && (
          <span className="flex items-center gap-1 text-[10px] text-orange-400">
            <Loader className="w-3 h-3 animate-spin" /> Computing...
          </span>
        )}
        {!loading && !metrics && (
          <span className="flex items-center gap-1 text-[10px] text-slate-600">
            <AlertCircle className="w-3 h-3" /> Python offline
          </span>
        )}
        {!loading && metrics && (
          <span className="flex items-center gap-1 text-[10px] text-emerald-400">
            <CheckCircle2 className="w-3 h-3" /> Live
          </span>
        )}
      </div>

      {/* Offline placeholder */}
      {!metrics && !loading && (
        <div className="text-center py-4">
          <MapPin className="w-6 h-6 text-slate-700 mx-auto mb-2" />
          <p className="text-[11px] text-slate-600 leading-relaxed">
            Localization metrics require the Python venv.<br />
            Waiting for first A-DPDOA frame&hellip;
          </p>
        </div>
      )}

      {metrics && (
        <>
          {/* Status + Confidence */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-slate-500">Frame #{metrics.frame_id}</span>
                <span className="text-[10px] text-slate-600">·</span>
                <span className="text-[10px] text-slate-500">{metrics.solver.method}</span>
              </div>
              <StatusBadge status={metrics.quality.status} />
            </div>
            <ConfidenceGauge value={metrics.quality.confidence} />
          </div>

          {/* Estimated Position */}
          <div className="bg-orange-950/20 border border-orange-900/30 rounded-xl p-3 flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <Crosshair className="w-3 h-3 text-orange-400" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Estimated Position</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {["X", "Y", "Z"].map((axis, i) => (
                <div key={axis} className="bg-slate-950/60 rounded-lg p-2 text-center">
                  <span className="text-[9px] text-slate-600 block">{axis}</span>
                  <span className="font-mono font-black text-sm text-orange-300">
                    {metrics.estimated_position[i].toFixed(2)}
                  </span>
                  <span className="text-[9px] text-slate-600 block">m</span>
                </div>
              ))}
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <Navigation2 className="w-3 h-3 text-slate-600" />
              <span className="text-[10px] text-slate-600">
                True:{" "}
                <span className="text-slate-400 font-mono">
                  [{metrics.true_position.map((v) => v.toFixed(2)).join(", ")}]
                </span>
              </span>
            </div>
          </div>

          {/* Error Metrics */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Target className="w-3 h-3 text-rose-400" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Positioning Error</span>
            </div>
            <div className="flex flex-col gap-2">
              <ErrorBar
                label="3D Error (instantaneous)"
                value={metrics.errors.instantaneous_m}
                maxVal={2.0}
                unit="m"
                color="amber"
              />
              <ErrorBar
                label="Horizontal Error (XY)"
                value={metrics.errors.horizontal_m}
                maxVal={2.0}
                unit="m"
                color="cyan"
              />
              <ErrorBar
                label="Vertical Error (Z)"
                value={metrics.errors.vertical_m}
                maxVal={1.0}
                unit="m"
                color="emerald"
              />
              <div className="flex justify-between items-center pt-0.5 border-t border-slate-800">
                <span className="text-[10px] text-slate-500">Running RMSE</span>
                <span className="font-mono font-black text-base text-orange-400">
                  {metrics.errors.rmse_m.toFixed(4)}
                  <span className="text-[10px] text-slate-600 font-normal ml-0.5">m</span>
                </span>
              </div>
            </div>
          </div>

          {/* Solver Stats */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Activity className="w-3 h-3 text-violet-400" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Solver</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <MCell
                label="Method"
                value={metrics.solver.method.replace(/_/g, "-")}
                unit=""
                color="text-violet-300"
              />
              <MCell
                label="Iterations"
                value={metrics.solver.iterations.toString()}
                unit="iters"
                color="text-indigo-300"
              />
              <MCell
                label="Solver Cost"
                value={metrics.solver.cost.toExponential(2)}
                unit=""
                color={metrics.solver.cost < 0.01 ? "text-emerald-300" : "text-amber-300"}
              />
              <MCell
                label="Calibrated"
                value={metrics.quality.calibration_applied ? "YES" : "NO"}
                unit=""
                color={metrics.quality.calibration_applied ? "text-emerald-300" : "text-slate-500"}
              />
            </div>
          </div>

          {/* Localization SNR per LED */}
          {snrEntries.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Zap className="w-3 h-3 text-amber-400" />
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Loc. SNR per LED</span>
              </div>
              <div className="flex flex-col gap-1.5">
                {snrEntries.map(([id, snr]) => (
                  <SnrRow key={id} ledId={id} snr={snr as number} />
                ))}
              </div>
            </div>
          )}

          {/* Distance Differences */}
          {ddEntries.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <ArrowUpDown className="w-3 h-3 text-teal-400" />
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Distance Differences</span>
              </div>
              <div className="flex flex-col gap-1">
                {ddEntries.map(([pair, val]) => (
                  <div key={pair} className="flex justify-between items-center text-[10px]">
                    <span className="text-slate-600 font-mono">{pair}</span>
                    <span className="font-mono font-bold text-teal-300">
                      {(val as number).toFixed(4)} m
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Running Stats */}
          {runStats && runStats.count > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <BarChart3 className="w-3 h-3 text-cyan-400" />
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  Session Stats ({runStats.count} frames)
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <MCell
                  label="Mean 3D Error"
                  value={runStats.mean_3d_error_m?.toFixed(4) ?? "—"}
                  unit="m"
                  color="text-orange-300"
                />
                <MCell
                  label="Median Error"
                  value={runStats.median_3d_error_m?.toFixed(4) ?? "—"}
                  unit="m"
                  color="text-amber-300"
                />
                <MCell
                  label="95th Percentile"
                  value={runStats.percentile_95_3d_error_m?.toFixed(3) ?? "—"}
                  unit="m"
                  color="text-rose-300"
                />
                <MCell
                  label="Success Rate"
                  value={
                    runStats.success_rate !== undefined
                      ? `${(runStats.success_rate * 100).toFixed(1)}`
                      : "—"
                  }
                  unit="%"
                  color={
                    (runStats.success_rate ?? 0) > 0.8
                      ? "text-emerald-300"
                      : (runStats.success_rate ?? 0) > 0.5
                      ? "text-amber-300"
                      : "text-rose-300"
                  }
                />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
