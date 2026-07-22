/**
 * PowerPanel.tsx
 *
 * Module 7 — Power Allocation & LED Pre-Equalization Engine
 * Displays: power budget distribution, per-LED allocation, PAPR before/after
 * pre-equalization, predicted BER per device, and feasibility status.
 */

import {
  AlertCircle, CheckCircle2, Loader, Zap, Battery,
  TrendingDown, Activity, BarChart2, Cpu
} from "lucide-react";
import { PowerMetrics } from "../types";

interface PowerPanelProps {
  metrics: PowerMetrics | null;
  loading: boolean;
}

// ─── Power Mode Badge ─────────────────────────────────────────────────────────
function PowerModeBadge({ mode }: { mode: string }) {
  if (mode === "WATER_FILLING")
    return (
      <span className="px-2 py-0.5 rounded-lg text-[9px] font-black bg-blue-950/80 text-blue-300 border border-blue-900/40 uppercase tracking-wide">
        WATER-FILLING
      </span>
    );
  return (
    <span className="px-2 py-0.5 rounded-lg text-[9px] font-black bg-slate-800 text-slate-400 border border-slate-700 uppercase tracking-wide">
      EQUAL POWER
    </span>
  );
}

// ─── Pre-EQ Mode Badge ────────────────────────────────────────────────────────
function PreEqBadge({ mode }: { mode: string }) {
  const colorMap: Record<string, string> = {
    REGULARIZED: "bg-violet-950/80 text-violet-300 border-violet-900/40",
    ZERO_FORCING: "bg-sky-950/80 text-sky-300 border-sky-900/40",
    PAPER_WEIGHTED: "bg-amber-950/80 text-amber-300 border-amber-900/40",
    NONE: "bg-slate-800 text-slate-500 border-slate-700",
  };
  const cls = colorMap[mode] ?? colorMap["NONE"];
  return (
    <span className={`px-2 py-0.5 rounded-lg text-[9px] font-black border uppercase tracking-wide ${cls}`}>
      {mode.replace("_", "-")}
    </span>
  );
}

// ─── PAPR LED Row ─────────────────────────────────────────────────────────────
function PaprRow({ ledId, before, after }: { ledId: string; before: number; after: number }) {
  const reduction = before - after;
  const maxPapr = 15;
  const afterPct = Math.min(100, Math.max(0, (after / maxPapr) * 100));
  const beforePct = Math.min(100, Math.max(0, (before / maxPapr) * 100));

  return (
    <div className="flex flex-col gap-1.5 bg-slate-950/60 rounded-xl p-2.5 border border-slate-800">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded">LED {ledId}</span>
        <div className="flex items-center gap-1.5">
          {reduction > 0 && (
            <span className="text-[9px] font-bold text-emerald-400 flex items-center gap-0.5">
              <TrendingDown className="w-2.5 h-2.5" />
              -{reduction.toFixed(1)} dB
            </span>
          )}
        </div>
      </div>
      {/* Before bar */}
      <div className="flex items-center gap-2">
        <span className="text-[9px] text-slate-600 w-10 text-right shrink-0">Before</span>
        <div className="flex-1 bg-slate-800 h-1.5 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-amber-600 to-amber-400 transition-all duration-700"
            style={{ width: `${beforePct}%` }}
          />
        </div>
        <span className="text-[9px] font-mono text-amber-300 w-10 text-right shrink-0">{before.toFixed(1)} dB</span>
      </div>
      {/* After bar */}
      <div className="flex items-center gap-2">
        <span className="text-[9px] text-slate-600 w-10 text-right shrink-0">After</span>
        <div className="flex-1 bg-slate-800 h-1.5 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${
              after < 8
                ? "bg-gradient-to-r from-emerald-600 to-emerald-400"
                : after < 12
                ? "bg-gradient-to-r from-sky-600 to-sky-400"
                : "bg-gradient-to-r from-rose-600 to-rose-400"
            }`}
            style={{ width: `${afterPct}%` }}
          />
        </div>
        <span className={`text-[9px] font-mono w-10 text-right shrink-0 ${
          after < 8 ? "text-emerald-300" : after < 12 ? "text-sky-300" : "text-rose-300"
        }`}>{after.toFixed(1)} dB</span>
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export default function PowerPanel({ metrics, loading }: PowerPanelProps) {
  const pa = metrics?.power_allocation;
  const preEq = metrics?.pre_eq;

  const ledIds = pa ? Object.keys(pa.per_led_max_power_w).sort((a, b) => Number(a) - Number(b)) : [];
  const devIds = metrics ? Object.keys(metrics.predicted_ber).sort((a, b) => Number(a) - Number(b)) : [];

  const totalBudget = pa?.total_power_budget_w ?? 0;
  const totalUsed = pa
    ? Object.values(pa.per_device_power_w).reduce((a, b) => a + b, 0)
    : 0;
  const usedPct = totalBudget > 0 ? Math.min(100, (totalUsed / totalBudget) * 100) : 0;

  const nominalMbps = metrics ? (metrics.nominal_sum_rate_bps / 1e6) : 0;
  const feasibleMbps = metrics ? (metrics.feasible_sum_rate_bps / 1e6) : 0;
  const allFeasible = metrics ? Object.values(metrics.modulation_feasible).every(Boolean) : false;

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-4 flex flex-col gap-3">

      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Battery className="w-3.5 h-3.5 text-amber-400" />
          <h4 className="font-bold text-xs text-slate-200">Module 7: Power & Pre-EQ</h4>
        </div>
        {loading && (
          <span className="flex items-center gap-1 text-[10px] text-amber-400">
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
          <Battery className="w-6 h-6 text-slate-700 mx-auto mb-2" />
          <p className="text-[11px] text-slate-600 leading-relaxed">
            Power engine requires the Python venv.<br />
            Waiting for first Module 7 frame&hellip;
          </p>
        </div>
      )}

      {metrics && pa && preEq && (
        <>
          {/* Mode Badges */}
          <div className="flex items-center gap-2 flex-wrap">
            <PowerModeBadge mode={pa.mode} />
            <span className="text-slate-700 text-[10px]">·</span>
            <PreEqBadge mode={preEq.mode} />
          </div>

          {/* Power Budget Overview */}
          <div className="bg-slate-950/40 rounded-xl p-3 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Zap className="w-3 h-3 text-amber-400" />
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Power Budget</span>
              </div>
              <span className="font-mono font-black text-xs text-amber-300">
                {totalBudget.toFixed(1)} W
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[9px] text-slate-600 w-10 text-right shrink-0">Used</span>
              <div className="flex-1 bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${
                    usedPct < 70
                      ? "bg-gradient-to-r from-emerald-600 to-emerald-400"
                      : usedPct < 90
                      ? "bg-gradient-to-r from-amber-600 to-amber-400"
                      : "bg-gradient-to-r from-rose-600 to-rose-400"
                  }`}
                  style={{ width: `${usedPct}%` }}
                />
              </div>
              <span className="text-[9px] font-mono text-slate-300 w-14 text-right shrink-0">
                {totalUsed.toFixed(2)} W
              </span>
            </div>
          </div>

          {/* Per-LED Power Breakdown */}
          {ledIds.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Zap className="w-3 h-3 text-amber-400" />
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Per-LED Allocation</span>
              </div>
              <div className="flex flex-col gap-1.5">
                {ledIds.map((ledId) => {
                  const maxP = pa.per_led_max_power_w[ledId] ?? 1;
                  const locP = pa.localization_reserved_power_w[ledId] ?? 0;
                  const commP = pa.communication_available_power_w[ledId] ?? 0;
                  const locPct = Math.round((locP / maxP) * 100);
                  const commPct = Math.round((commP / maxP) * 100);
                  return (
                    <div key={ledId} className="bg-slate-950/60 rounded-xl p-2.5 border border-slate-800">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded">LED {ledId}</span>
                        <span className="text-[9px] font-mono text-slate-500">max {maxP.toFixed(2)} W</span>
                      </div>
                      <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden flex">
                        <div
                          className="h-full bg-gradient-to-r from-orange-600 to-orange-400 transition-all duration-700"
                          style={{ width: `${locPct}%` }}
                          title={`Loc reserve: ${locP.toFixed(3)} W`}
                        />
                        <div
                          className="h-full bg-gradient-to-r from-sky-600 to-sky-400 transition-all duration-700"
                          style={{ width: `${commPct}%` }}
                          title={`Comm power: ${commP.toFixed(3)} W`}
                        />
                      </div>
                      <div className="flex justify-between mt-1">
                        <span className="text-[9px] text-orange-500 font-mono flex items-center gap-0.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-orange-500 inline-block" />
                          Loc: {locP.toFixed(3)} W
                        </span>
                        <span className="text-[9px] text-sky-400 font-mono flex items-center gap-0.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-sky-500 inline-block" />
                          Comm: {commP.toFixed(3)} W
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* PAPR Before/After Pre-EQ */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Activity className="w-3 h-3 text-violet-400" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">PAPR Before / After Pre-EQ</span>
            </div>
            <div className="flex flex-col gap-2">
              {Object.keys(preEq.papr_before_db)
                .sort((a, b) => Number(a) - Number(b))
                .map((ledId) => (
                  <PaprRow
                    key={ledId}
                    ledId={ledId}
                    before={preEq.papr_before_db[ledId] ?? 0}
                    after={preEq.papr_after_db[ledId] ?? 0}
                  />
                ))}
            </div>
          </div>

          {/* Predicted BER per Device */}
          {devIds.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <BarChart2 className="w-3 h-3 text-sky-400" />
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Predicted BER</span>
              </div>
              <div className="flex flex-col gap-1.5">
                {devIds.map((devId) => {
                  const ber = metrics.predicted_ber[devId] ?? 1;
                  const feasible = metrics.modulation_feasible[devId] ?? false;
                  return (
                    <div key={devId} className="flex items-center justify-between bg-slate-950/60 rounded-xl px-3 py-2 border border-slate-800">
                      <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded w-8 text-center">
                        D{devId}
                      </span>
                      <span className={`font-mono font-bold text-xs ${
                        ber < 1e-4 ? "text-emerald-400"
                        : ber < 1e-3 ? "text-amber-400"
                        : "text-rose-400"
                      }`}>
                        {ber.toExponential(2)}
                      </span>
                      <span className={`text-[9px] font-black px-1.5 py-0.5 rounded border ${
                        feasible
                          ? "bg-emerald-950/80 text-emerald-400 border-emerald-900/40"
                          : "bg-rose-950/80 text-rose-400 border-rose-900/40"
                      }`}>
                        {feasible ? "✓ OK" : "✗ FAIL"}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Feasible vs Nominal Rate */}
          <div className="bg-slate-950/40 rounded-xl p-3 flex flex-col gap-1.5 border border-slate-800/60">
            <div className="flex items-center gap-1.5 mb-0.5">
              <Cpu className="w-3 h-3 text-teal-400" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Throughput Feasibility</span>
              <span className={`ml-auto text-[9px] font-black px-1.5 py-0.5 rounded border ${
                allFeasible
                  ? "bg-emerald-950/80 text-emerald-400 border-emerald-900/40"
                  : "bg-rose-950/80 text-rose-400 border-rose-900/40"
              }`}>
                {allFeasible ? "ALL FEASIBLE" : "PARTIAL FAIL"}
              </span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-500">Nominal</span>
              <span className="font-mono font-bold text-slate-300">
                {nominalMbps >= 1000 ? `${(nominalMbps / 1000).toFixed(2)} Gbps` : `${nominalMbps.toFixed(1)} Mbps`}
              </span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-slate-500">Feasible</span>
              <span className={`font-mono font-bold ${feasibleMbps >= nominalMbps * 0.9 ? "text-emerald-400" : "text-rose-400"}`}>
                {feasibleMbps >= 1000 ? `${(feasibleMbps / 1000).toFixed(2)} Gbps` : `${feasibleMbps.toFixed(1)} Mbps`}
              </span>
            </div>
          </div>

          {/* Warnings */}
          {metrics.warnings && metrics.warnings.length > 0 && (
            <div className="bg-amber-950/20 border border-amber-900/30 rounded-xl p-2.5">
              <div className="flex items-center gap-1.5 mb-1.5">
                <AlertCircle className="w-3 h-3 text-amber-400" />
                <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">Warnings</span>
              </div>
              {metrics.warnings.map((w, i) => (
                <p key={i} className="text-[10px] text-amber-300/80 leading-relaxed">{w}</p>
              ))}
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center gap-1.5 pt-1 border-t border-slate-800/60">
            <Battery className="w-3 h-3 text-slate-600" />
            <span className="text-[10px] text-slate-600">
              Pre-EQ: H<sup>-1</sup>(f) · max gain {preEq.max_gain_db.toFixed(1)} dB
            </span>
          </div>
        </>
      )}
    </div>
  );
}
