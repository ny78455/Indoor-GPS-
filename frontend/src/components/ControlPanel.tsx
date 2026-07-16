import React from "react";
import { Play, Pause, RotateCcw, Download, Terminal, Sliders, Layers, RefreshCw } from "lucide-react";
import { SimulationState } from "../types";

interface ControlPanelProps {
  state: SimulationState;
  setState: React.Dispatch<React.SetStateAction<SimulationState>>;
  onDownloadZip: () => void;
  onReset: () => void;
  runPythonSimulationOnServer: () => void;
  pythonRunSuccess: boolean | null;
  pythonLoading: boolean;
}

export default function ControlPanel({
  state,
  setState,
  onDownloadZip,
  onReset,
  runPythonSimulationOnServer,
  pythonRunSuccess,
  pythonLoading
}: ControlPanelProps) {
  
  const handleTogglePlay = () => {
    setState((prev) => ({ ...prev, isPlaying: !prev.isPlaying }));
  };

  const handleSpeedFactor = (val: number) => {
    setState((prev) => ({ ...prev, speedFactor: val }));
  };

  const handleTrajectoryChange = (type: any) => {
    setState((prev) => ({
      ...prev,
      mobility: { ...prev.mobility, type },
      trajectoryPoints: [] // Clear path on transition
    }));
  };

  // Generic state updates
  const updateLED = (id: number, field: string, val: any) => {
    setState((prev) => {
      const leds = prev.leds.map((led) => {
        if (led.id === id) {
          return { ...led, [field]: val };
        }
        return led;
      });
      return { ...prev, leds };
    });
  };

  const updateReceiver = (field: string, val: any) => {
    setState((prev) => ({
      ...prev,
      receiver: { ...prev.receiver, [field]: val }
    }));
  };

  const updateObstacle = (id: string, field: string, index: number, val: number) => {
    setState((prev) => {
      const obstacles = prev.obstacles.map((obs) => {
        if (obs.id === id) {
          if (field === "position" || field === "scale" || field === "rotation") {
            const arr = [...obs[field]] as [number, number, number];
            arr[index] = val;
            return { ...obs, [field]: arr };
          }
        }
        return obs;
      });
      return { ...prev, obstacles };
    });
  };

  const handleExportYaml = () => {
    // Generate YAML dynamically based on live React parameters
    const yamlContent = `room:
  width: ${state.room.width.toFixed(1)}
  length: ${state.room.length.toFixed(1)}
  height: ${state.room.height.toFixed(1)}
  wall_reflectivity: ${state.room.wallReflectivity.toFixed(2)}
  floor_reflectivity: ${state.room.floorReflectivity.toFixed(2)}
  ceiling_reflectivity: ${state.room.ceilingReflectivity.toFixed(2)}

leds:
${state.leds
  .map(
    (led) => `  - id: ${led.id}
    position: [${led.position.join(", ")}]
    orientation: [${led.orientation.join(", ")}]
    power: ${led.power.toFixed(1)}
    bias_current: ${led.biasCurrent.toFixed(1)}
    frequency: ${led.frequency.toFixed(1)}
    lambertian_order: ${led.lambertianOrder.toFixed(1)}
    beam_angle: ${led.beamAngle.toFixed(1)}
    fov: ${led.fov.toFixed(1)}
    communication_enabled: ${led.communicationEnabled}
    localization_enabled: ${led.localizationEnabled}`
  )
  .join("\n")}

receiver:
  position: [${state.receiver.position.map(n => n.toFixed(2)).join(", ")}]
  orientation: [${state.receiver.orientation.join(", ")}]
  velocity: [${state.receiver.velocity.join(", ")}]
  acceleration: [${state.receiver.acceleration.join(", ")}]
  fov: ${state.receiver.fov.toFixed(1)}
  apd_size: ${state.receiver.apdSize.toExponential(1)}
  noise: ${state.receiver.noise.toExponential(1)}
  gain: ${state.receiver.gain.toFixed(1)}
  roll: ${state.receiver.roll.toFixed(1)}
  pitch: ${state.receiver.pitch.toFixed(1)}
  yaw: ${state.receiver.yaw.toFixed(1)}

mobility:
  type: "${state.mobility.type}"
  speed: ${state.mobility.speed.toFixed(2)}
  radius: ${state.mobility.radius.toFixed(2)}
  center: [${state.mobility.center.join(", ")}]

obstacles:
${state.obstacles
  .map(
    (obs) => `  - id: "${obs.id}"
    type: "${obs.type}"
    position: [${obs.position.join(", ")}]
    rotation: [${obs.rotation.join(", ")}]
    scale: [${obs.scale.join(", ")}]
    reflectivity: ${obs.reflectivity.toFixed(1)}
    material: "${obs.material}"`
  )
  .join("\n")}
`;

    // Save as local YAML download file
    const blob = new Blob([yamlContent], { type: "text/yaml;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "default.yaml");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="w-full flex flex-col gap-5 bg-[#0f172a]/70 border border-slate-800 rounded-xl p-5 shadow-xl text-slate-300 backdrop-blur-md">
      
      {/* 1. Simulation Playback Controls */}
      <div className="flex flex-col gap-2 border-b border-slate-800 pb-4">
        <h3 className="font-semibold text-xs text-slate-100 flex items-center gap-1.5 uppercase tracking-wider">
          <Layers className="w-4 h-4 text-cyan-400" />
          Simulation Core
        </h3>
        
        <div className="flex flex-wrap items-center gap-2 mt-1">
          <button
            onClick={handleTogglePlay}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition ${
              state.isPlaying
                ? "bg-amber-500 hover:bg-amber-600 text-slate-950 shadow-md shadow-amber-500/10"
                : "bg-emerald-500 hover:bg-emerald-600 text-slate-950 shadow-md shadow-emerald-500/10"
            }`}
          >
            {state.isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {state.isPlaying ? "Pause Engine" : "Start Engine"}
          </button>
          
          <button
            onClick={onReset}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 transition"
          >
            <RotateCcw className="w-4 h-4 text-cyan-400" />
            Reset State
          </button>
          
          <div className="flex bg-slate-950 rounded-lg p-0.5 border border-slate-850">
            {["0.5", "1.0", "2.0"].map((s) => {
              const val = parseFloat(s);
              return (
                <button
                  key={s}
                  onClick={() => handleSpeedFactor(val)}
                  className={`px-3 py-1 text-[10px] font-bold rounded-md transition ${
                    state.speedFactor === val
                      ? "bg-cyan-500 text-slate-950 shadow-sm"
                      : "text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {s}x
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 2. Mobility Trajectories */}
      <div className="flex flex-col gap-2 border-b border-slate-800 pb-4">
        <h3 className="font-semibold text-xs text-slate-100 flex items-center gap-1.5 uppercase tracking-wider">
          <RefreshCw className="w-4 h-4 text-cyan-400 animate-spin-slow" />
          Mobility Kinetics
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-1">
          {["static", "linear", "circular", "random_walk", "waypoint"].map((type) => (
            <button
              key={type}
              onClick={() => handleTrajectoryChange(type as any)}
              className={`px-3 py-1.5 text-xs font-bold rounded-lg capitalize border transition-all ${
                state.mobility.type === type
                  ? "bg-cyan-500 hover:bg-cyan-600 text-slate-950 border-cyan-400 shadow-lg shadow-cyan-500/10"
                  : "bg-slate-900 hover:bg-slate-800 text-slate-400 border-slate-800"
              }`}
            >
              {type.replace("_", " ")}
            </button>
          ))}
        </div>
        
        {state.mobility.type !== "static" && (
          <div className="flex items-center justify-between gap-4 mt-2">
            <span className="text-xs text-slate-400">Kinetic Velocity Speed:</span>
            <div className="flex items-center gap-2 w-2/3">
              <input
                type="range"
                min="0.1"
                max="2.0"
                step="0.05"
                value={state.mobility.speed}
                onChange={(e) =>
                  setState((prev) => ({
                    ...prev,
                    mobility: { ...prev.mobility, speed: parseFloat(e.target.value) }
                  }))
                }
                className="w-full h-1 bg-slate-850 rounded appearance-none cursor-pointer accent-cyan-500"
              />
              <span className="text-xs font-mono text-cyan-400 w-12 text-right">
                {state.mobility.speed.toFixed(2)} m/s
              </span>
            </div>
          </div>
        )}
      </div>

      {/* 3. Parameters Sliders */}
      <div className="flex flex-col gap-3 border-b border-slate-800 pb-4">
        <h3 className="font-semibold text-xs text-slate-100 flex items-center gap-1.5 uppercase tracking-wider">
          <Sliders className="w-4 h-4 text-cyan-400" />
          Hardware & Geometry Sliders
        </h3>
        
        {/* LED 1 & 2 power sliders */}
        <div className="flex flex-col gap-2.5 bg-slate-950/40 p-3 rounded-lg border border-slate-850/60">
          <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-850/80 pb-1 flex items-center justify-between">
            <span>Transmit Powers (W)</span>
            <span className="text-cyan-400 text-[10px] font-mono font-semibold">Lambertian Order: 1.0</span>
          </h4>
          {state.leds.map((led) => (
            <div key={led.id} className="flex flex-col gap-1">
              <div className="flex justify-between items-center text-xs">
                <span>LED Emitter {led.id} Power:</span>
                <span className="font-mono text-cyan-400 font-semibold">{led.power.toFixed(0)} W</span>
              </div>
              <input
                type="range"
                min="5"
                max="50"
                step="1"
                value={led.power}
                onChange={(e) => updateLED(led.id, "power", parseInt(e.target.value))}
                className="w-full h-1 bg-slate-850 rounded accent-cyan-500"
              />
            </div>
          ))}
        </div>

        {/* Receiver properties */}
        <div className="flex flex-col gap-2.5 bg-slate-950/40 p-3 rounded-lg border border-slate-850/60 mt-1">
          <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-850/80 pb-1">
            Receiver Parameters
          </h4>
          
          {/* APD FOV */}
          <div className="flex flex-col gap-1">
            <div className="flex justify-between items-center text-xs">
              <span>APD Receiver FOV cone:</span>
              <span className="font-mono text-cyan-400 font-semibold">{state.receiver.fov.toFixed(0)}°</span>
            </div>
            <input
              type="range"
              min="30"
              max="90"
              step="2"
              value={state.receiver.fov}
              onChange={(e) => updateReceiver("fov", parseInt(e.target.value))}
              className="w-full h-1 bg-slate-850 rounded accent-cyan-500"
            />
          </div>

          {/* Roll / Pitch / Yaw rotation */}
          <div className="grid grid-cols-3 gap-2 mt-1">
            <div className="flex flex-col gap-0.5">
              <span className="text-[9px] text-slate-500 uppercase tracking-wider font-semibold">Roll (θx)</span>
              <input
                type="number"
                min="-45"
                max="45"
                value={state.receiver.roll}
                onChange={(e) => updateReceiver("roll", parseFloat(e.target.value) || 0)}
                className="bg-slate-950 border border-slate-850 rounded px-1.5 py-0.5 font-mono text-[11px] text-cyan-400 focus:outline-none focus:border-cyan-500 text-center"
              />
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-[9px] text-slate-500 uppercase tracking-wider font-semibold">Pitch (θy)</span>
              <input
                type="number"
                min="-45"
                max="45"
                value={state.receiver.pitch}
                onChange={(e) => updateReceiver("pitch", parseFloat(e.target.value) || 0)}
                className="bg-slate-950 border border-slate-850 rounded px-1.5 py-0.5 font-mono text-[11px] text-cyan-400 focus:outline-none focus:border-cyan-500 text-center"
              />
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-[9px] text-slate-500 uppercase tracking-wider font-semibold">Yaw (θz)</span>
              <input
                type="number"
                min="-180"
                max="180"
                value={state.receiver.yaw}
                onChange={(e) => updateReceiver("yaw", parseFloat(e.target.value) || 0)}
                className="bg-slate-950 border border-slate-850 rounded px-1.5 py-0.5 font-mono text-[11px] text-cyan-400 focus:outline-none focus:border-cyan-500 text-center"
              />
            </div>
          </div>
        </div>

        {/* Obstacles config */}
        <div className="flex flex-col gap-2.5 bg-slate-950/40 p-3 rounded-lg border border-slate-850/60 mt-1">
          <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest border-b border-slate-850/80 pb-1">
            Blocker Obstacle positions
          </h4>
          
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between text-xs text-slate-300">
              <span className="font-bold text-[10px] uppercase tracking-wider text-rose-400 bg-rose-950/40 border border-rose-900/30 px-1.5 py-0.5 rounded">
                Human X-Position:
              </span>
              <span className="font-mono text-rose-300">{state.obstacles[0].position[0].toFixed(2)} m</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="4.5"
              step="0.05"
              value={state.obstacles[0].position[0]}
              onChange={(e) => updateObstacle("obs_human", "position", 0, parseFloat(e.target.value))}
              className="w-full h-1 bg-slate-850 rounded accent-rose-500"
            />
          </div>

          <div className="flex flex-col gap-2 mt-1">
            <div className="flex items-center justify-between text-xs text-slate-300">
              <span className="font-bold text-[10px] uppercase tracking-wider text-rose-400 bg-rose-950/40 border border-rose-900/30 px-1.5 py-0.5 rounded">
                Human Y-Position:
              </span>
              <span className="font-mono text-rose-300">{state.obstacles[0].position[1].toFixed(2)} m</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="4.5"
              step="0.05"
              value={state.obstacles[0].position[1]}
              onChange={(e) => updateObstacle("obs_human", "position", 1, parseFloat(e.target.value))}
              className="w-full h-1 bg-slate-850 rounded accent-rose-500"
            />
          </div>
        </div>
      </div>

      {/* 4. Research Compilation & Export */}
      <div className="flex flex-col gap-3">
        <h3 className="font-semibold text-xs text-slate-100 flex items-center gap-1.5 uppercase tracking-wider">
          <Terminal className="w-4 h-4 text-cyan-400" />
          Compilation & Research Export
        </h3>
        
        <div className="flex flex-col gap-2">
          <div className="flex gap-2">
            <button
              onClick={handleExportYaml}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-bold bg-slate-850 hover:bg-slate-750 text-slate-200 border border-slate-700 transition"
            >
              <Download className="w-3.5 h-3.5 text-cyan-400" />
              YAML Export
            </button>
            
            <button
              onClick={onDownloadZip}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-bold bg-[#0f172a] hover:bg-slate-800 text-cyan-400 border border-cyan-500/30 hover:border-cyan-500/60 transition shadow-lg shadow-cyan-500/5"
            >
              <Download className="w-3.5 h-3.5 text-cyan-400" />
              ZIP Framework
            </button>
          </div>

          <button
            onClick={runPythonSimulationOnServer}
            disabled={pythonLoading}
            className={`w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg text-xs font-bold transition border ${
              pythonLoading
                ? "bg-slate-800 text-slate-500 border-slate-750 cursor-not-allowed"
                : pythonRunSuccess === true
                ? "bg-emerald-900/40 text-emerald-300 border-emerald-850 hover:bg-emerald-900/60 font-semibold"
                : pythonRunSuccess === false
                ? "bg-rose-950/40 text-rose-300 border-rose-850 hover:bg-rose-950/60 font-semibold"
                : "bg-cyan-500 hover:bg-cyan-600 text-slate-950 border-cyan-400 shadow-md shadow-cyan-500/10"
            }`}
          >
            <Terminal className="w-4 h-4 text-slate-950" />
            {pythonLoading
              ? "Running Python Telemetry Engine..."
              : pythonRunSuccess === true
              ? "Python Execution Success (Reload)"
              : pythonRunSuccess === false
              ? "Engine Error (Retry)"
              : "Execute Python Code on Server"}
          </button>
        </div>
      </div>

    </div>
  );
}
