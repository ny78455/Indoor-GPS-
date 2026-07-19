/**
 * CommunicationPanel.tsx
 *
 * Module 3 — VLC Communication Engine KPI Dashboard.
 * Displays live OFDM waveform metrics from the Python CommunicationEngine:
 *   - Data rates (sum rate, effective throughput, per-user)
 *   - Channel quality (spectral efficiency, active LED)
 *   - Error metrics (BER, EVM, bit errors)
 *   - Waveform integrity (PAPR, clipping ratio, electrical power)
 */

import {
  Radio, TrendingUp, AlertTriangle, CheckCircle2, AlertCircle,
  Loader, Zap, BarChart3, Waves, Cpu
} from "lucide-react";
import { CommunicationMetrics } from "../types";

interface CommunicationPanelProps {
  metrics: CommunicationMetrics | null;
  loading: boolean;
}

function BerBadge({ ber }: { ber: number }) {
  if (ber < 1e-5)
    return <span className="px-1.5 py-0.5 text-[9px] font-bold rounded-md bg-emerald-950/80 text-emerald-400 border border-emerald-900/40">EXCELLENT</span>;
  if (ber < 1e-3)
    return <span className="px-1.5 py-0.5 text-[9px] font-bold rounded-md bg-amber-950/80 text-amber-400 border border-amber-900/40">MODERATE</span>;
  return <span className="px-1.5 py-0.5 text-[9px] font-bold rounded-md bg-rose-950/80 text-rose-400 border border-rose-900/40">HIGH BER</span>;
}

function MetricCell({ label, value, unit, color = "text-slate-300" }: {
  label: string; value: string; unit: string; color?: string;
}) {
  return (
    <div className="bg-slate-950/60 rounded-xl p-3 flex flex-col gap-0.5">
      <span className="text-[10px] text-slate-500 leading-none">{label}</span>
      <div className="flex items-baseline gap-1 mt-1">
        <span className={`font-mono font-black text-lg leading-none ${color}`}>{value}</span>
        <span className="text-[10px] text-slate-600">{unit}</span>
      </div>
    </div>
  );
}

function ProgressRow({ label, value, max, valueLabel, barColor }: {
  label: string; value: number; max: number; valueLabel: string; barColor: string;
}) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const fromColor = barColor === "text-emerald-400" ? "from-emerald-600 to-emerald-400"
    : barColor === "text-amber-400" ? "from-amber-600 to-amber-400"
    : "from-rose-600 to-rose-400";
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between items-center">
        <span className="text-[10px] text-slate-500">{label}</span>
        <span className={`text-[11px] font-mono font-bold ${barColor}`}>{valueLabel}</span>
      </div>
      <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${fromColor} transition-all duration-700`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function CommunicationPanel({ metrics, loading }: CommunicationPanelProps) {
  const userId = metrics ? (Object.keys(metrics.ber_per_user)[0] ?? "1") : "1";
  const ber  = metrics?.ber_per_user[userId]      ?? 0;
  const evm  = metrics?.evm_per_user_pct[userId]  ?? 0;
  const rate = metrics?.rate_per_user_mbps[userId] ?? 0;

  const berColor =
    ber < 1e-5 ? "text-emerald-400" :
    ber < 1e-3 ? "text-amber-400"   :
                 "text-rose-400";

  const formatBer = (b: number) => b === 0 ? "0.000" : b.toExponential(2);

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-4 flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Radio className="w-3.5 h-3.5 text-fuchsia-400" />
          <h4 className="font-bold text-xs text-slate-200">VLC Communication (OFDM)</h4>
        </div>
        {loading && (
          <span className="flex items-center gap-1 text-[10px] text-fuchsia-400">
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

      {!metrics && !loading && (
        <div className="text-center py-4">
          <Radio className="w-6 h-6 text-slate-700 mx-auto mb-2" />
          <p className="text-[11px] text-slate-600 leading-relaxed">
            Communication metrics require the Python venv.<br />
            Waiting for first OFDM frame...
          </p>
        </div>
      )}

      {metrics && (
        <>
          {/* Active LED */}
          <div className="flex items-center gap-2 bg-fuchsia-950/30 border border-fuchsia-900/30 rounded-xl p-2.5">
            <Zap className="w-3.5 h-3.5 text-fuchsia-400 flex-shrink-0" />
            <span className="text-[11px] text-slate-400">
              Primary Transmitter:{" "}
              <span className="font-bold text-fuchsia-300">LED {metrics.metadata.active_led_id}</span>
              <span className="text-slate-600 ml-1">(highest optical power)</span>
            </span>
          </div>

          {/* Data Rate */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <TrendingUp className="w-3 h-3 text-cyan-400" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Data Rate</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <MetricCell label="Sum Rate"      value={metrics.sum_rate_mbps.toFixed(1)}          unit="Mbps"   color="text-cyan-400" />
              <MetricCell label="Throughput"    value={metrics.effective_throughput_mbps.toFixed(1)} unit="Mbps" color="text-teal-400" />
              <MetricCell label="Spectral Eff." value={metrics.spectral_efficiency.toFixed(2)}    unit="bps/Hz" color="text-blue-400" />
              <MetricCell label="User Rate"     value={rate.toFixed(1)}                           unit="Mbps"   color="text-indigo-400" />
            </div>
          </div>

          {/* Error Metrics */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <BarChart3 className="w-3 h-3 text-amber-400" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Error Metrics</span>
            </div>
            <div className="flex flex-col gap-2.5">
              <div className="bg-slate-950/60 rounded-xl p-3 flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-500">Bit Error Rate (BER)</span>
                  <BerBadge ber={ber} />
                </div>
                <span className={`font-mono font-black text-xl ${berColor}`}>{formatBer(ber)}</span>
                <div className="flex justify-between text-[10px]">
                  <span className="text-slate-600">Bit errors: <span className="text-slate-400 font-mono">{metrics.metadata.bit_errors}</span></span>
                  <span className="text-slate-600">Analytical: <span className="text-slate-400 font-mono">{formatBer(metrics.metadata.average_analytical_ber)}</span></span>
                </div>
              </div>
              <ProgressRow
                label="Error Vector Magnitude (EVM)"
                value={evm} max={30}
                valueLabel={`${evm.toFixed(2)}%`}
                barColor={evm < 5 ? "text-emerald-400" : evm < 15 ? "text-amber-400" : "text-rose-400"}
              />
            </div>
          </div>

          {/* Waveform Integrity */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Waves className="w-3 h-3 text-violet-400" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Waveform (OFDM)</span>
            </div>
            <div className="flex flex-col gap-2.5">
              <ProgressRow
                label="PAPR (Peak-to-Average Power Ratio)"
                value={metrics.papr_db} max={20}
                valueLabel={`${metrics.papr_db.toFixed(1)} dB`}
                barColor={metrics.papr_db < 8 ? "text-emerald-400" : metrics.papr_db < 12 ? "text-amber-400" : "text-rose-400"}
              />
              <ProgressRow
                label="Clipping Ratio"
                value={metrics.clipping_ratio_pct} max={25}
                valueLabel={`${metrics.clipping_ratio_pct.toFixed(2)}%`}
                barColor={metrics.clipping_ratio_pct < 5 ? "text-emerald-400" : metrics.clipping_ratio_pct < 15 ? "text-amber-400" : "text-rose-400"}
              />
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-1.5">
                  <Cpu className="w-3 h-3 text-violet-400" />
                  <span className="text-[10px] text-slate-500">Drive Power</span>
                </div>
                <span className="font-mono text-[11px] font-bold text-violet-300">
                  {(metrics.metadata.electrical_power * 1000).toFixed(2)} mW
                </span>
              </div>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-1.5">
                  <AlertTriangle className="w-3 h-3 text-slate-500" />
                  <span className="text-[10px] text-slate-500">Clipping Distortion</span>
                </div>
                <span className="font-mono text-[11px] font-bold text-slate-400">
                  {metrics.metadata.clipping_distortion.toExponential(2)}
                </span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
