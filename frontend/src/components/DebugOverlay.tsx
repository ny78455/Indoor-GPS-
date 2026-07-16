import { Cpu, Wifi, ShieldAlert, Navigation, CircleAlert } from "lucide-react";
import { SimulationState } from "../types";

interface DebugOverlayProps {
  state: SimulationState;
}

export default function DebugOverlay({ state }: DebugOverlayProps) {
  return (
    <div className="w-full grid grid-cols-1 md:grid-cols-4 gap-4 bg-[#0f172a]/70 border border-slate-800 rounded-xl p-5 shadow-xl text-xs text-slate-300 backdrop-blur-md">
      
      {/* Panel 1: Simulation Clock */}
      <div className="flex flex-col gap-2 bg-slate-950/50 p-4 rounded-lg border border-slate-850 shadow-inner">
        <h4 className="font-bold text-[10px] text-slate-400 uppercase tracking-widest flex items-center gap-1.5 border-b border-slate-850 pb-1.5 mb-1 font-semibold">
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          Simulation Clock
        </h4>
        <div className="flex flex-col gap-1.5 font-mono">
          <div className="flex justify-between">
            <span className="text-slate-500">Sim Time:</span>
            <span className="text-cyan-400 font-bold">{state.currentTime.toFixed(2)} s</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Frame Index:</span>
            <span className="text-slate-300">{state.frameIndex}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Live Framerate:</span>
            <span className="text-emerald-400 font-bold">{state.fps.toFixed(1)} FPS</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Time Step (dt):</span>
            <span className="text-slate-300">0.05 s</span>
          </div>
        </div>
      </div>

      {/* Panel 2: Receiver Kinematics */}
      <div className="flex flex-col gap-2 bg-slate-950/50 p-4 rounded-lg border border-slate-850 shadow-inner">
        <h4 className="font-bold text-[10px] text-slate-400 uppercase tracking-widest flex items-center gap-1.5 border-b border-slate-850 pb-1.5 mb-1 font-semibold">
          <Navigation className="w-3.5 h-3.5 text-cyan-400" />
          Receiver Kinematics
        </h4>
        <div className="flex flex-col gap-1.5 font-mono">
          <div className="flex justify-between">
            <span className="text-slate-500">Position (X,Y,Z):</span>
            <span className="text-cyan-400 font-semibold">
              [{state.receiver.position.map((n) => n.toFixed(2)).join(", ")}] m
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Orientation Normal:</span>
            <span className="text-slate-300">
              [{state.receiver.orientation.map((n) => n.toFixed(2)).join(", ")}]
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Rotations (R,P,Y):</span>
            <span className="text-slate-300 text-[10px]">
              {state.receiver.roll.toFixed(1)}°, {state.receiver.pitch.toFixed(1)}°, {state.receiver.yaw.toFixed(1)}°
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Mobility Path:</span>
            <span className="text-cyan-400 font-bold capitalize">{state.mobility.type.replace("_", " ")}</span>
          </div>
        </div>
      </div>

      {/* Panel 3: LED Arrays & Optical Gain */}
      <div className="flex flex-col gap-2 bg-slate-950/50 p-4 rounded-lg border border-slate-850 shadow-inner md:col-span-2">
        <h4 className="font-bold text-[10px] text-slate-400 uppercase tracking-widest flex items-center gap-1.5 border-b border-slate-850 pb-1.5 mb-1 font-semibold">
          <Wifi className="w-3.5 h-3.5 text-cyan-400" />
          Active Emitters & Channel Gain H(0)
        </h4>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 font-mono">
          {state.leds.map((led) => {
            const dist = state.distances[led.id] || 0;
            const gain = state.dcGains[led.id] || 0;
            const isLos = state.losMatrix[led.id];
            const isFov = state.visibilityMatrix[led.id];
            const isBlockedBy = state.blockingObstacles[led.id];
            
            // Channel Gain logic mapping for real-time progress bar (nominal max dc gain ~1.2e-4)
            const gainPercent = Math.min(100, Math.max(0, Math.round((gain / 1.2e-4) * 100)));

            return (
              <div key={led.id} className="flex flex-col gap-0.5 border-b border-slate-850/50 pb-1 last:border-0 last:pb-0">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-slate-300 flex items-center gap-1 text-[10px]">
                    <span className={`w-1.5 h-1.5 rounded-full ${led.id % 2 === 0 ? 'bg-cyan-400' : 'bg-cyan-500'}`} />
                    LED {led.id} ({led.power}W):
                  </span>
                  {isLos ? (
                    isFov ? (
                      <span className="bg-emerald-950/80 text-emerald-400 border border-emerald-900/40 px-1 py-0.2 rounded text-[8px] font-bold">
                        LOS
                      </span>
                    ) : (
                      <span className="bg-slate-800 text-slate-400 border border-slate-700 px-1 py-0.2 rounded text-[8px] font-bold">
                        OUT OF FOV
                      </span>
                    )
                  ) : (
                    <span className="bg-rose-950/80 text-rose-400 border border-rose-900/40 px-1 py-0.2 rounded text-[8px] font-bold flex items-center gap-0.5" title={`Blocked by ${isBlockedBy}`}>
                      <ShieldAlert className="w-2.5 h-2.5" />
                      BLOCKED
                    </span>
                  )}
                </div>
                
                <div className="flex justify-between text-[10px] text-slate-400">
                  <span>Dist: {dist.toFixed(2)} m</span>
                  <span>
                    H(0): <span className="text-cyan-400 font-bold">{gain > 0 ? gain.toExponential(2) : "0.00"}</span>
                  </span>
                </div>

                {/* Sleek Theme Real-time Progress Bar */}
                <div className="w-full bg-slate-800/80 h-1 rounded-full overflow-hidden mt-1">
                  <div 
                    className={`h-full transition-all duration-300 ${
                      isLos && isFov ? 'bg-emerald-400' : 'bg-slate-600'
                    }`} 
                    style={{ width: `${isLos && isFov ? gainPercent : 0}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
}
