/**
 * AdaptivePanel.tsx
 *
 * Module 6 — Adaptive Modulation & Dynamic Subcarrier Allocation Engine
 * Displays: QoS status, sum rate, spectral efficiency, Jain's fairness,
 * subcarrier utilization, per-device rates, and modulation depth.
 */

import {
  AlertCircle, CheckCircle2, Loader, Activity, Sliders,
  BarChart2, Users, TrendingUp, Wifi
} from "lucide-react";
import { AdaptiveMetrics } from "../types";

interface AdaptivePanelProps {
  metrics: AdaptiveMetrics | null;
  loading: boolean;
}

// ─── QoS Status Badge ─────────────────────────────────────────────────────────
function QoSBadge({ status }: { status: string }) {
  if (status === "FEASIBLE")
    return (
      <span className="flex items-center gap-1 px-2 py-0.5 rounded-lg text-[9px] font-black bg-emerald-950/80 text-emerald-400 border border-emerald-900/40 uppercase tracking-wide">
        <CheckCircle2 className="w-2.5 h-2.5" /> FEASIBLE
      </span>
    );
  if (status === "PARTIALLY_FEASIBLE")
    return (
      <span className="flex items-center gap-1 px-2 py-0.5 rounded-lg text-[9px] font-black bg-amber-950/80 text-amber-400 border border-amber-900/40 uppercase tracking-wide">
        <Activity className="w-2.5 h-2.5" /> PARTIAL
      </span>
    );
  return (
    <span className="flex items-center gap-1 px-2 py-0.5 rounded-lg text-[9px] font-black bg-rose-950/80 text-rose-400 border border-rose-900/40 uppercase tracking-wide">
      <AlertCircle className="w-2.5 h-2.5" /> INFEASIBLE
    </span>
  );
}

// ─── Gauge Bar ────────────────────────────────────────────────────────────────
function GaugeBar({ value, label, colorClass = "from-cyan-500 to-cyan-400" }: {
  value: number; // 0..1
  label: string;
  colorClass?: string;
}) {
  const pct = Math.min(100, Math.max(0, Math.round(value * 100)));
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between items-center">
        <span className="text-[10px] text-slate-500">{label}</span>
        <span className="text-[11px] font-mono font-bold text-slate-300">{pct}%</span>
      </div>
      <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${colorClass} transition-all duration-700`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ─── Metric Cell ──────────────────────────────────────────────────────────────
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
export default function AdaptivePanel({ metrics, loading }: AdaptivePanelProps) {
  const deviceEntries = metrics
    ? Object.entries(metrics.achievable_rates_bps).sort((a, b) => Number(a[0]) - Number(b[0]))
    : [];

  const diag = metrics?.diagnostics;
  const sumRateMbps = metrics ? (metrics.sum_rate_bps / 1e6) : 0;
  const spectralEff = diag ? diag.spectral_efficiency_bps_hz : 0;
  const fairness = diag ? diag.jains_fairness_index : 0;
  const utilization = diag ? diag.subcarrier_utilization_ratio : 0;
  const avgBpS = diag ? diag.average_bits_per_symbol : 0;

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-4 flex flex-col gap-3">

      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Sliders className="w-3.5 h-3.5 text-sky-400" />
          <h4 className="font-bold text-xs text-slate-200">Module 6: Adaptive Modulation</h4>
        </div>
        {loading && (
          <span className="flex items-center gap-1 text-[10px] text-sky-400">
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
          <Sliders className="w-6 h-6 text-slate-700 mx-auto mb-2" />
          <p className="text-[11px] text-slate-600 leading-relaxed">
            Adaptive engine requires the Python venv.<br />
            Waiting for first Module 6 frame&hellip;
          </p>
        </div>
      )}

      {metrics && (
        <>
          {/* QoS Status + Sum Rate */}
          <div className="flex items-center justify-between bg-slate-950/40 rounded-xl p-3">
            <div className="flex flex-col gap-0.5">
              <span className="text-[10px] text-slate-500">Sum Rate</span>
              <div className="flex items-baseline gap-1">
                <span className={`font-mono font-black text-xl ${sumRateMbps > 100 ? "text-emerald-400" : sumRateMbps > 10 ? "text-amber-400" : "text-rose-400"}`}>
                  {sumRateMbps >= 1000
                    ? (sumRateMbps / 1000).toFixed(2)
                    : sumRateMbps.toFixed(1)}
                </span>
                <span className="text-[11px] text-slate-500">
                  {sumRateMbps >= 1000 ? "Gbps" : "Mbps"}
                </span>
              </div>
            </div>
            <QoSBadge status={metrics.qos_status} />
          </div>

          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 gap-2">
            <MCell
              label="Spectral Eff."
              value={spectralEff.toFixed(2)}
              unit="bps/Hz"
              color="text-sky-400"
            />
            <MCell
              label="Avg Bits/Symbol"
              value={avgBpS.toFixed(2)}
              unit="bits"
              color="text-violet-400"
            />
            <MCell
              label="Allocated SCs"
              value={diag ? diag.allocated_subcarrier_count.toString() : "—"}
              unit={`/ ${diag?.total_comm_subcarrier_count ?? "—"}`}
              color="text-teal-400"
            />
            <MCell
              label="Unused SCs"
              value={metrics.unused_subcarriers_count.toString()}
              unit="sub."
              color={metrics.unused_subcarriers_count > 20 ? "text-amber-400" : "text-slate-400"}
            />
          </div>

          {/* Jain's Fairness Index */}
          <div className="bg-slate-950/40 rounded-xl p-3 flex flex-col gap-2">
            <div className="flex items-center gap-1.5 mb-0.5">
              <Users className="w-3 h-3 text-violet-400" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Jain's Fairness Index</span>
              <span className="ml-auto font-mono font-black text-sm text-violet-300">{fairness.toFixed(4)}</span>
            </div>
            <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${
                  fairness > 0.9
                    ? "bg-gradient-to-r from-emerald-500 to-emerald-400"
                    : fairness > 0.7
                    ? "bg-gradient-to-r from-amber-500 to-amber-400"
                    : "bg-gradient-to-r from-rose-500 to-rose-400"
                }`}
                style={{ width: `${Math.min(100, fairness * 100)}%` }}
              />
            </div>
            <div className="flex justify-between text-[9px] text-slate-700">
              <span>0.0 — Unfair</span>
              <span>1.0 — Perfect</span>
            </div>
          </div>

          {/* Subcarrier Utilization */}
          <GaugeBar
            value={utilization}
            label="Subcarrier Utilization"
            colorClass={
              utilization > 0.8
                ? "from-emerald-600 to-emerald-400"
                : utilization > 0.5
                ? "from-sky-600 to-sky-400"
                : "from-amber-600 to-amber-400"
            }
          />

          {/* Per-Device Rates */}
          {deviceEntries.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <BarChart2 className="w-3 h-3 text-sky-400" />
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Per-Device Rates</span>
              </div>
              <div className="flex flex-col gap-1.5">
                {deviceEntries.map(([devId, rateBps]) => {
                  const rateMbps = rateBps / 1e6;
                  const satisfied = metrics.qos_satisfied[devId] ?? false;
                  const deficit = metrics.qos_deficits_bps[devId] ?? 0;
                  return (
                    <div key={devId} className="flex items-center gap-2 bg-slate-950/60 rounded-xl px-3 py-2 border border-slate-800">
                      <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded w-8 text-center">
                        D{devId}
                      </span>
                      <div className="flex-1">
                        <div className="flex justify-between items-center mb-0.5">
                          <span className="font-mono font-bold text-xs text-slate-200">
                            {rateMbps >= 1000
                              ? `${(rateMbps / 1000).toFixed(2)} Gbps`
                              : `${rateMbps.toFixed(1)} Mbps`}
                          </span>
                          <span className={`text-[9px] font-black px-1.5 py-0.5 rounded ${
                            satisfied
                              ? "bg-emerald-950/80 text-emerald-400 border border-emerald-900/40"
                              : "bg-rose-950/80 text-rose-400 border border-rose-900/40"
                          }`}>
                            {satisfied ? "QoS ✓" : "QoS ✗"}
                          </span>
                        </div>
                        {!satisfied && deficit > 0 && (
                          <span className="text-[9px] text-rose-500 font-mono">
                            deficit: {(deficit / 1e6).toFixed(1)} Mbps
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Subcarrier Mode Footer */}
          <div className="flex items-center gap-1.5 pt-1 border-t border-slate-800/60">
            <Wifi className="w-3 h-3 text-slate-600" />
            <span className="text-[10px] text-slate-600">
              OFDM · FFT-256 · BER-constrained adaptive allocation
            </span>
          </div>
        </>
      )}
    </div>
  );
}
