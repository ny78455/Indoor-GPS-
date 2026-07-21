import { 
  MapPin, AlertCircle, CheckCircle2, Loader, 
  Activity, Zap, Target, Wifi, Radio
} from "lucide-react";
import { IntegratedMetrics } from "../types";

interface IntegratedPanelProps {
  metrics: IntegratedMetrics | null;
  loading: boolean;
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
export default function IntegratedPanel({ metrics, loading }: IntegratedPanelProps) {
  const commEntries = metrics 
    ? Object.entries(metrics.communications).sort((a, b) => Number(a[0]) - Number(b[0]))
    : [];
    
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-4 flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Radio className="w-3.5 h-3.5 text-fuchsia-400" />
          <h4 className="font-bold text-xs text-slate-200">Module 5: Integrated Engine</h4>
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

      {/* Offline placeholder */}
      {!metrics && !loading && (
        <div className="text-center py-4">
          <Radio className="w-6 h-6 text-slate-700 mx-auto mb-2" />
          <p className="text-[11px] text-slate-600 leading-relaxed">
            Integrated metrics require the Python venv.<br />
            Waiting for first Integrated Engine frame&hellip;
          </p>
        </div>
      )}

      {metrics && (
        <>
          {/* Localization Results */}
          <div className="bg-orange-950/20 border border-orange-900/30 rounded-xl p-3 flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <MapPin className="w-3 h-3 text-orange-400" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Localization</span>
              <span className={`ml-auto text-[9px] font-bold px-1.5 py-0.5 rounded-md ${metrics.localization.success ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-900/40' : 'bg-rose-950/80 text-rose-400 border border-rose-900/40'}`}>
                {metrics.localization.success ? 'SUCCESS' : 'FAILED'}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-1">
              <MCell 
                label="3D Error" 
                value={metrics.localization.error_3d_m.toFixed(3)} 
                unit="m" 
                color="text-orange-300" 
              />
              <MCell 
                label="Estimated Pos" 
                value={`[${metrics.localization.estimated_position.map(v => v.toFixed(2)).join(',')}]`} 
                unit="m" 
                color="text-slate-300" 
              />
            </div>
          </div>

          {/* Communication Results */}
          {commEntries.length > 0 && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Wifi className="w-3 h-3 text-cyan-400" />
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Communications</span>
              </div>
              <div className="flex flex-col gap-2">
                {commEntries.map(([ledId, res]) => (
                  <div key={ledId} className="bg-slate-950/60 rounded-xl p-2.5 flex justify-between items-center border border-slate-800">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded">L{ledId}</span>
                      <div className="flex flex-col">
                        <span className="text-[10px] text-slate-500 leading-none">BER</span>
                        <span className={`font-mono font-bold text-xs ${res.empirical_ber < 1e-3 ? 'text-emerald-400' : 'text-amber-400'}`}>
                          {res.empirical_ber.toExponential(2)}
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-4">
                      <div className="flex flex-col items-end">
                        <span className="text-[9px] text-slate-500">Errors</span>
                        <span className="font-mono text-xs text-rose-300">{res.bit_errors}</span>
                      </div>
                      <div className="flex flex-col items-end">
                        <span className="text-[9px] text-slate-500">Symbols</span>
                        <span className="font-mono text-xs text-cyan-300">{res.num_recovered_symbols}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Transmitter Stats */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <Zap className="w-3 h-3 text-amber-400" />
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Transmitter (PAPR & Clipping)</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <MCell 
                label="Avg PAPR" 
                value={(Object.values(metrics.transmitter.papr_db).reduce((a, b) => a + b, 0) / (Object.keys(metrics.transmitter.papr_db).length || 1)).toFixed(1)} 
                unit="dB" 
                color="text-amber-300" 
              />
              <MCell 
                label="Avg Clipping" 
                value={(Object.values(metrics.transmitter.clipping_ratio_pct).reduce((a, b) => a + b, 0) / (Object.keys(metrics.transmitter.clipping_ratio_pct).length || 1)).toFixed(1)} 
                unit="%" 
                color="text-rose-300" 
              />
              <MCell 
                label="Avg Bias" 
                value={(Object.values(metrics.transmitter.dc_bias_volts).reduce((a, b) => a + b, 0) / (Object.keys(metrics.transmitter.dc_bias_volts).length || 1)).toFixed(2)} 
                unit="V" 
                color="text-cyan-300" 
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
