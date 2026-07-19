/**
 * FormulaPanel.tsx
 * 
 * Physics & Math reference panel — redesigned to be readable by newcomers.
 * Each formula includes:
 *   - Plain-English explanation
 *   - Visual variable legend
 *   - SVG diagram illustrating the concept
 */

import { BookOpen, HelpCircle, Lightbulb, Triangle } from "lucide-react";

// ─── Variable Badge ────────────────────────────────────────────────────────
function VarBadge({ symbol, meaning, color = "text-cyan-300" }: { symbol: string; meaning: string; color?: string }) {
  return (
    <span className="inline-flex items-baseline gap-1 mx-0.5">
      <code className={`font-mono font-bold text-sm ${color} bg-slate-900 px-1.5 py-0.5 rounded`}>{symbol}</code>
      <span className="text-slate-500 text-xs">= {meaning}</span>
    </span>
  );
}

// ─── SVG: Lambertian Emission Cone ────────────────────────────────────────
function LambertianDiagram() {
  return (
    <svg viewBox="0 0 200 160" className="w-full max-w-[200px] mx-auto" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="beamGrad" cx="50%" cy="0%" r="90%">
          <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.5" />
          <stop offset="100%" stopColor="#fbbf24" stopOpacity="0.03" />
        </radialGradient>
      </defs>

      {/* LED body */}
      <rect x="88" y="10" width="24" height="14" rx="4" fill="#0f172a" stroke="#fbbf24" strokeWidth="1.5" />
      <circle cx="100" cy="17" r="5" fill="#fbbf24" opacity="0.9" />

      {/* Beam cone */}
      <polygon points="100,24  55,145  145,145" fill="url(#beamGrad)" />
      {/* Cone boundary lines */}
      <line x1="100" y1="24" x2="55" y2="145" stroke="#fbbf24" strokeWidth="1" strokeDasharray="4,3" opacity="0.5" />
      <line x1="100" y1="24" x2="145" y2="145" stroke="#fbbf24" strokeWidth="1" strokeDasharray="4,3" opacity="0.5" />

      {/* Half-angle arc */}
      <path d="M 100 24 L 100 70" stroke="#94a3b8" strokeWidth="1" strokeDasharray="3,2" />
      <path d="M 100 50 A 26 26 0 0 1 124 63" fill="none" stroke="#22d3ee" strokeWidth="1.5" />
      <text x="113" y="58" fill="#22d3ee" fontSize="9" fontFamily="Inter" fontWeight="bold">θ_half</text>

      {/* Labels */}
      <text x="100" y="8" textAnchor="middle" fill="#fbbf24" fontSize="8" fontFamily="Inter" fontWeight="bold">LED</text>
      <text x="100" y="158" textAnchor="middle" fill="#94a3b8" fontSize="8" fontFamily="Inter">Light Beam Cone</text>

      {/* Intensity gradient dots */}
      <circle cx="100" cy="90" r="3" fill="#fbbf24" opacity="0.9" />
      <circle cx="78" cy="120" r="2.5" fill="#fbbf24" opacity="0.5" />
      <circle cx="122" cy="120" r="2.5" fill="#fbbf24" opacity="0.5" />
      <circle cx="62" cy="140" r="2" fill="#fbbf24" opacity="0.2" />
      <circle cx="138" cy="140" r="2" fill="#fbbf24" opacity="0.2" />
    </svg>
  );
}

// ─── SVG: Channel Gain Geometry ───────────────────────────────────────────
function ChannelGainDiagram() {
  return (
    <svg viewBox="0 0 220 160" className="w-full max-w-[220px] mx-auto" xmlns="http://www.w3.org/2000/svg">
      {/* LED on ceiling */}
      <rect x="94" y="8" width="32" height="12" rx="3" fill="#0f172a" stroke="#fbbf24" strokeWidth="1.5" />
      <circle cx="110" cy="14" r="5" fill="#fbbf24" opacity="0.9" />
      <text x="110" y="6" textAnchor="middle" fill="#fbbf24" fontSize="8" fontFamily="Inter" fontWeight="bold">LED</text>

      {/* Signal line */}
      <line x1="110" y1="20" x2="60" y2="130" stroke="#22d3ee" strokeWidth="2" strokeDasharray="5,3" />

      {/* Distance label */}
      <text x="72" y="82" fill="#22d3ee" fontSize="9" fontFamily="Inter" fontWeight="bold">d</text>

      {/* φ angle at LED */}
      <line x1="110" y1="20" x2="110" y2="70" stroke="#94a3b8" strokeWidth="1" strokeDasharray="3,2" />
      <path d="M110 45 A25 25 0 0 0 95 52" fill="none" stroke="#f59e0b" strokeWidth="1.5" />
      <text x="88" y="52" fill="#f59e0b" fontSize="9" fontFamily="Inter" fontWeight="bold">φ</text>
      <text x="125" y="50" fill="#f59e0b" fontSize="8" fontFamily="Inter">irradiance angle</text>

      {/* Receiver */}
      <polygon points="60,130  50,148  70,148" fill="#38bdf8" />
      <text x="60" y="158" textAnchor="middle" fill="#38bdf8" fontSize="8" fontFamily="Inter" fontWeight="bold">Receiver</text>

      {/* ψ angle at receiver */}
      <line x1="60" y1="130" x2="60" y2="100" stroke="#94a3b8" strokeWidth="1" strokeDasharray="3,2" />
      <path d="M60 112 A18 18 0 0 1 74 120" fill="none" stroke="#a78bfa" strokeWidth="1.5" />
      <text x="76" y="120" fill="#a78bfa" fontSize="9" fontFamily="Inter" fontWeight="bold">ψ</text>
      <text x="78" y="130" fill="#a78bfa" fontSize="8" fontFamily="Inter">incident angle</text>
    </svg>
  );
}

// ─── SVG: Rotation Axes ───────────────────────────────────────────────────
function RotationDiagram() {
  return (
    <svg viewBox="0 0 200 160" className="w-full max-w-[200px] mx-auto" xmlns="http://www.w3.org/2000/svg">
      {/* Body */}
      <polygon points="100,50  85,120  115,120" fill="#38bdf8" opacity="0.8" />
      <circle cx="100" cy="50" r="8" fill="#38bdf8" opacity="0.9" />

      {/* Normal arrow (Z up) */}
      <line x1="100" y1="50" x2="100" y2="20" stroke="#10b981" strokeWidth="2" markerEnd="url(#arrowG)" />
      <text x="107" y="18" fill="#10b981" fontSize="9" fontFamily="Inter" fontWeight="bold">n (normal)</text>

      {/* X axis */}
      <line x1="60" y1="130" x2="160" y2="130" stroke="#f43f5e" strokeWidth="1.5" markerEnd="url(#arrowR)" />
      <text x="162" y="134" fill="#f43f5e" fontSize="9" fontFamily="Inter">X</text>

      {/* Y axis */}
      <line x1="60" y1="130" x2="60" y2="30" stroke="#22d3ee" strokeWidth="1.5" markerEnd="url(#arrowC)" />
      <text x="54" y="26" fill="#22d3ee" fontSize="9" fontFamily="Inter">Z</text>

      {/* Roll arc */}
      <path d="M 80 90 A 20 20 0 0 1 110 85" fill="none" stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="4,2" />
      <text x="88" y="80" fill="#f59e0b" fontSize="8" fontFamily="Inter">Roll</text>

      {/* Pitch arc */}
      <path d="M 100 65 A 20 10 0 0 1 130 85" fill="none" stroke="#a78bfa" strokeWidth="1.5" strokeDasharray="4,2" />
      <text x="120" y="74" fill="#a78bfa" fontSize="8" fontFamily="Inter">Pitch</text>

      {/* Yaw arc */}
      <path d="M 80 128 A 20 8 0 0 1 120 128" fill="none" stroke="#34d399" strokeWidth="1.5" strokeDasharray="4,2" />
      <text x="90" y="144" fill="#34d399" fontSize="8" fontFamily="Inter">Yaw</text>

      <defs>
        <marker id="arrowG" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" fill="#10b981" />
        </marker>
        <marker id="arrowR" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" fill="#f43f5e" />
        </marker>
        <marker id="arrowC" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" fill="#22d3ee" />
        </marker>
      </defs>
    </svg>
  );
}

// ─── SVG: Signal vs Noise ─────────────────────────────────────────────────
function SnrDiagram() {
  return (
    <svg viewBox="0 0 200 160" className="w-full max-w-[200px] mx-auto" xmlns="http://www.w3.org/2000/svg">
      {/* Background axes */}
      <line x1="20" y1="140" x2="180" y2="140" stroke="#475569" strokeWidth="1" />
      <line x1="20" y1="20" x2="20" y2="140" stroke="#475569" strokeWidth="1" />
      
      {/* Noise Floor (Red jagged line) */}
      <path d="M 20 120 L 40 125 L 60 115 L 80 122 L 100 118 L 120 124 L 140 116 L 160 125 L 180 119" fill="none" stroke="#f43f5e" strokeWidth="2" opacity="0.6" />
      <polygon points="20,120 40,125 60,115 80,122 100,118 120,124 140,116 160,125 180,119 180,140 20,140" fill="#f43f5e" opacity="0.1" />
      
      {/* Signal (Green Sine Wave) */}
      <path d="M 20 80 Q 40 30, 60 80 T 100 80 T 140 80 T 180 80" fill="none" stroke="#10b981" strokeWidth="2" />
      
      {/* Annotations */}
      <text x="25" y="45" fill="#10b981" fontSize="10" fontFamily="Inter" fontWeight="bold">Signal Power</text>
      <text x="25" y="110" fill="#f43f5e" fontSize="10" fontFamily="Inter" fontWeight="bold">Noise Floor</text>
      
      {/* SNR Arrow */}
      <line x1="100" y1="80" x2="100" y2="118" stroke="#38bdf8" strokeWidth="1.5" strokeDasharray="3,2" markerEnd="url(#arrowS)" markerStart="url(#arrowS_rev)" />
      <text x="105" y="103" fill="#38bdf8" fontSize="10" fontFamily="Inter" fontWeight="bold">SNR</text>

      <defs>
        <marker id="arrowS" markerWidth="6" markerHeight="6" refX="4" refY="3" orient="auto">
          <path d="M0,0 L6,3 L0,6 Z" fill="#38bdf8" />
        </marker>
        <marker id="arrowS_rev" markerWidth="6" markerHeight="6" refX="2" refY="3" orient="auto-start-reverse">
          <path d="M0,0 L6,3 L0,6 Z" fill="#38bdf8" />
        </marker>
      </defs>
    </svg>
  );
}

// ─── Formula Card ─────────────────────────────────────────────────────────
interface FormulaCardProps {
  number: number;
  title: string;
  plainEnglish: string;
  formula: string;
  variables: { symbol: string; meaning: string; color?: string }[];
  diagram: React.ReactNode;
  extraNote?: string;
}

function FormulaCard({ number, title, plainEnglish, formula, variables, diagram, extraNote }: FormulaCardProps) {
  return (
    <div className="flex flex-col gap-5 bg-slate-900/40 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-colors">
      
      {/* Header */}
      <div className="flex items-start gap-3 border-b border-slate-800 pb-4">
        <div className="w-8 h-8 rounded-lg bg-cyan-950/60 border border-cyan-900/40 flex items-center justify-center flex-shrink-0">
          <span className="text-cyan-400 font-black text-sm">{number}</span>
        </div>
        <div>
          <h4 className="font-bold text-slate-100 text-sm">{title}</h4>
          <p className="text-slate-400 text-xs mt-0.5 leading-relaxed">{plainEnglish}</p>
        </div>
      </div>

      {/* Diagram + Formula side by side on larger screens */}
      <div className="flex flex-col md:flex-row gap-5 items-center">
        
        {/* Diagram */}
        <div className="flex-shrink-0 w-full md:w-48 flex items-center justify-center bg-slate-950/60 border border-slate-800 rounded-xl p-3">
          {diagram}
        </div>

        {/* Formula + variables */}
        <div className="flex flex-col gap-3 flex-1">
          <div className="bg-slate-950 border border-slate-700 rounded-xl px-4 py-3">
            <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-2 font-semibold">Mathematical Formula</p>
            <code className="text-cyan-300 font-mono text-sm font-bold leading-relaxed block">{formula}</code>
          </div>

          <div className="flex flex-col gap-2">
            <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold">Variable Key</p>
            <div className="flex flex-wrap gap-2">
              {variables.map((v, i) => (
                <div key={i} className="flex items-baseline gap-1.5 bg-slate-900 border border-slate-800 rounded-lg px-2 py-1">
                  <code className={`font-mono font-bold text-xs ${v.color || 'text-cyan-300'}`}>{v.symbol}</code>
                  <span className="text-slate-500 text-[11px]">= {v.meaning}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Extra note */}
      {extraNote && (
        <div className="flex items-start gap-2 bg-amber-950/20 border border-amber-900/30 rounded-xl px-3 py-2.5">
          <Lightbulb className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <p className="text-amber-200/80 text-xs leading-relaxed">{extraNote}</p>
        </div>
      )}
    </div>
  );
}

// ─── Main Export ───────────────────────────────────────────────────────────
export default function FormulaPanel() {
  return (
    <div className="w-full flex flex-col gap-5 animate-fade-in">

      {/* Header */}
      <div className="bg-gradient-to-r from-violet-950/50 to-slate-900/60 border border-violet-900/30 rounded-2xl p-5 flex items-center gap-4">
        <div className="w-10 h-10 bg-violet-500/20 border border-violet-500/30 rounded-xl flex items-center justify-center">
          <BookOpen className="w-5 h-5 text-violet-400" />
        </div>
        <div>
          <h3 className="text-base font-bold text-white">Physical & Geometric Formulations</h3>
          <p className="text-slate-400 text-sm">The core math that powers the VLCL positioning engine — explained simply.</p>
        </div>
      </div>

      {/* Formulas */}
      <div className="grid grid-cols-1 gap-5">

        <FormulaCard
          number={1}
          title="Lambertian Emission Order (m)"
          plainEnglish="This formula determines how focused or spread the LED's light beam is. A narrow beam concentrates more light in the center but covers a smaller area."
          formula={"m  =  −ln(2) / ln( cos(θ_half) )"}
          variables={[
            { symbol: "m", meaning: "beam focus strength (higher = more focused)", color: "text-cyan-300" },
            { symbol: "θ_half", meaning: "the beam's half-angle (60° by default)", color: "text-amber-300" },
            { symbol: "ln()", meaning: "natural logarithm function", color: "text-slate-400" },
          ]}
          diagram={<LambertianDiagram />}
          extraNote="At a default beam angle of 60°, m = 1.0 (even spread). Try smaller beam angles on the slider to see how m increases and the cone narrows!"
        />

        <FormulaCard
          number={2}
          title="Channel DC Path Gain — H(0)"
          plainEnglish="H(0) is the core metric: how much light power actually reaches the receiver from one LED. It depends on distance, angles, and sensor size. A higher H(0) = better signal and more accurate positioning."
          formula={"H(0) = [(m+1)·A_apd / (2π·d²)] · cosᵐ(φ) · g · cos(ψ)"}
          variables={[
            { symbol: "H(0)", meaning: "DC channel gain (signal strength)", color: "text-cyan-300" },
            { symbol: "m", meaning: "Lambertian order from formula 1", color: "text-amber-300" },
            { symbol: "A_apd", meaning: "sensor active area (m²)", color: "text-violet-300" },
            { symbol: "d", meaning: "distance from LED to receiver (m)", color: "text-emerald-300" },
            { symbol: "φ", meaning: "irradiance angle at LED (emission side)", color: "text-orange-300" },
            { symbol: "ψ", meaning: "incident angle at receiver (reception side)", color: "text-pink-300" },
            { symbol: "g", meaning: "optical concentrator gain", color: "text-slate-400" },
          ]}
          diagram={<ChannelGainDiagram />}
          extraNote="Both angles φ and ψ must be within their respective FOV limits, AND the path must be LOS (not blocked) for H(0) > 0. Move the receiver closer to an LED to watch H(0) rise!"
        />

        <FormulaCard
          number={3}
          title="3D Rotation — Receiver Orientation"
          plainEnglish="When the receiver device is tilted (like a phone held at an angle), its sensor no longer points straight up. This formula computes the new pointing direction after applying Roll, Pitch, and Yaw rotations."
          formula={"R = Rz(yaw) · Ry(pitch) · Rx(roll)\nn_rx = R · [0, 0, 1]ᵀ"}
          variables={[
            { symbol: "R", meaning: "combined 3×3 rotation matrix", color: "text-cyan-300" },
            { symbol: "Rx/Ry/Rz", meaning: "rotation matrices around each axis", color: "text-emerald-300" },
            { symbol: "roll", meaning: "tilt left/right (θx)", color: "text-amber-300" },
            { symbol: "pitch", meaning: "tilt forward/back (θy)", color: "text-violet-300" },
            { symbol: "yaw", meaning: "rotate horizontally (θz)", color: "text-pink-300" },
            { symbol: "n_rx", meaning: "resulting normal vector (where sensor points)", color: "text-slate-300" },
          ]}
          diagram={<RotationDiagram />}
          extraNote="Try changing Roll/Pitch/Yaw in the control panel to see the receiver orientation change in the 3D view. When tilted away from the LEDs, H(0) drops because cos(ψ) decreases."
        />

        <FormulaCard
          number={4}
          title="Signal-to-Noise Ratio (SNR)"
          plainEnglish="SNR measures how strong the received light signal is compared to background electronic and optical noise. Higher SNR means a cleaner signal for the communication engine."
          formula={"SNR_dB = 10 · log10( (R · Prx)² / (σ²_thermal + σ²_shot) )"}
          variables={[
            { symbol: "SNR_dB", meaning: "Signal-to-noise ratio in decibels", color: "text-cyan-300" },
            { symbol: "R", meaning: "Photodiode responsivity (A/W)", color: "text-emerald-300" },
            { symbol: "Prx", meaning: "Received optical power from LEDs", color: "text-amber-300" },
            { symbol: "σ²_thermal", meaning: "Thermal noise variance (circuit heat)", color: "text-rose-300" },
            { symbol: "σ²_shot", meaning: "Shot noise variance (background light)", color: "text-pink-300" },
          ]}
          diagram={<SnrDiagram />}
          extraNote="The physics engine calculates SNR, which the communication engine then uses to determine how much data can be successfully transmitted without errors!"
        />

        <FormulaCard
          number={5}
          title="Shannon Capacity (Max Data Rate)"
          plainEnglish="The Shannon-Hartley theorem calculates the absolute maximum data rate (in Mbps) that can be reliably transmitted over the optical channel, bounded by bandwidth and SNR."
          formula={"C = B · log2( 1 + SNR_linear )"}
          variables={[
            { symbol: "C", meaning: "Channel Capacity (bits per second)", color: "text-cyan-300" },
            { symbol: "B", meaning: "Bandwidth of the LED/Channel (Hz)", color: "text-violet-300" },
            { symbol: "SNR_linear", meaning: "Linear Signal-to-Noise Ratio (not dB!)", color: "text-emerald-300" },
            { symbol: "log2", meaning: "Base-2 logarithm (converting to bits)", color: "text-slate-400" },
          ]}
          diagram={<SnrDiagram />}
          extraNote="Module 3 uses this formula to calculate the Theoretical Maximum Rate shown in the Communication Panel. Notice how getting further from the LED drops the SNR, which immediately drops the Data Rate!"
        />

      </div>

      {/* Summary note */}
      <div className="flex items-start gap-3 bg-cyan-950/20 border border-cyan-900/30 rounded-2xl p-4 mt-2">
        <HelpCircle className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
        <div className="flex flex-col gap-1">
          <h4 className="text-sm font-bold text-cyan-300">How These Formulas Connect</h4>
          <p className="text-slate-400 text-xs leading-relaxed">
            Formula 1 gives you <code className="text-cyan-300 font-mono">m</code>. 
            That <code className="text-cyan-300 font-mono">m</code> feeds into Formula 2 to compute <code className="text-cyan-300 font-mono">H(0)</code>. 
            Formula 3 determines the receiver orientation which affects <code className="text-cyan-300 font-mono">ψ</code> in Formula 2.
            This gives the received power <code className="text-cyan-300 font-mono">Prx</code>, which Formula 4 uses to calculate the <code className="text-cyan-300 font-mono">SNR</code>.
            Finally, the Communication Engine plugs that <code className="text-cyan-300 font-mono">SNR</code> into Formula 5 to calculate your live <code className="text-cyan-300 font-mono">Data Rate</code>!
          </p>
        </div>
      </div>

    </div>
  );
}
