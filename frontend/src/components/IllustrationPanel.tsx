/**
 * IllustrationPanel.tsx
 * 
 * Newbie-friendly illustrated overview of how the Indoor VLC GPS system works.
 * Contains annotated SVG diagrams explaining system components visually.
 */

import { Lightbulb, Wifi, Eye, Users, Radio, ArrowRight, Info } from "lucide-react";

// ─── Concept Card ───────────────────────────────────────────────────────────
interface ConceptCardProps {
  icon: React.ReactNode;
  title: string;
  color: string;
  bgColor: string;
  borderColor: string;
  description: string;
  detail: string;
}

function ConceptCard({ icon, title, color, bgColor, borderColor, description, detail }: ConceptCardProps) {
  return (
    <div className={`flex flex-col gap-3 rounded-xl p-4 border ${borderColor} ${bgColor} transition-all duration-200 hover:scale-[1.01]`}>
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${bgColor} border ${borderColor} shadow-inner`}>
          <span className={color}>{icon}</span>
        </div>
        <h4 className={`font-bold text-sm ${color}`}>{title}</h4>
      </div>
      <p className="text-slate-300 text-sm leading-relaxed">{description}</p>
      <div className="bg-slate-900/60 rounded-lg px-3 py-2 border border-slate-700/50">
        <p className="text-slate-400 text-xs leading-relaxed italic">{detail}</p>
      </div>
    </div>
  );
}

// ─── SVG Room Diagram ──────────────────────────────────────────────────────
function RoomDiagram() {
  return (
    <div className="w-full flex flex-col items-center gap-3">
      <svg
        viewBox="0 0 500 320"
        className="w-full max-w-2xl"
        style={{ maxHeight: 300 }}
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* ── Room floor ── */}
        <defs>
          <linearGradient id="floorGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#0f172a" />
            <stop offset="100%" stopColor="#1e293b" />
          </linearGradient>
          <linearGradient id="ceilGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0c4a6e" />
            <stop offset="100%" stopColor="#0f172a" />
          </linearGradient>
          <radialGradient id="coneGrad1" cx="50%" cy="0%" r="80%">
            <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#fbbf24" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="coneGrad2" cx="50%" cy="0%" r="80%">
            <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#fbbf24" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="coneGrad3" cx="50%" cy="0%" r="80%">
            <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.20" />
            <stop offset="100%" stopColor="#fbbf24" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Room background */}
        <rect x="30" y="20" width="440" height="270" rx="12" fill="url(#floorGrad)" stroke="#1e293b" strokeWidth="1.5" />
        
        {/* Ceiling band */}
        <rect x="30" y="20" width="440" height="40" rx="12" fill="url(#ceilGrad)" />
        <text x="250" y="44" textAnchor="middle" fill="#94a3b8" fontSize="11" fontFamily="Inter">
          🏠  Room Ceiling — LEDs mounted here
        </text>

        {/* Floor label */}
        <text x="250" y="278" textAnchor="middle" fill="#475569" fontSize="10" fontFamily="Inter">
          Room Floor (5m × 5m)
        </text>

        {/* ─── LED Cones (light beams) ─── */}
        {/* LED 1 */}
        <polygon points="100,60  45,240  155,240" fill="url(#coneGrad1)" />
        {/* LED 2 */}
        <polygon points="200,60  145,240  255,240" fill="url(#coneGrad2)" />
        {/* LED 3 */}
        <polygon points="330,60  275,240  385,240" fill="url(#coneGrad2)" />
        {/* LED 4 */}
        <polygon points="430,60  375,240  470,240" fill="url(#coneGrad1)" />

        {/* ─── LEDs (ceiling) ─── */}
        {[100, 200, 330, 430].map((x, i) => (
          <g key={i}>
            <circle cx={x} cy={60} r={9} fill="#fbbf24" opacity="0.9" />
            <circle cx={x} cy={60} r={14} fill="#fbbf24" opacity="0.15" />
            <text x={x} y={48} textAnchor="middle" fill="#fbbf24" fontSize="9" fontFamily="Inter" fontWeight="bold">
              LED {i + 1}
            </text>
          </g>
        ))}

        {/* ─── Signal lines (LOS) ─── */}
        <line x1="100" y1="60" x2="240" y2="200" stroke="#22d3ee" strokeWidth="1.5" strokeDasharray="5,3" opacity="0.7" />
        <line x1="200" y1="60" x2="240" y2="200" stroke="#22d3ee" strokeWidth="1.5" strokeDasharray="5,3" opacity="0.7" />
        <line x1="330" y1="60" x2="240" y2="200" stroke="#22d3ee" strokeWidth="1.5" strokeDasharray="5,3" opacity="0.7" />

        {/* ─── NLOS line (blocked) ─── */}
        <line x1="430" y1="60" x2="320" y2="190" stroke="#f43f5e" strokeWidth="1.5" strokeDasharray="5,3" opacity="0.8" />
        <text x="388" y="138" fill="#f43f5e" fontSize="9" fontFamily="Inter" fontWeight="bold">BLOCKED</text>

        {/* ─── Obstacle (human) ─── */}
        <rect x="310" y="165" width="22" height="55" rx="4" fill="#dc2626" opacity="0.85" />
        <circle cx="321" cy="158" r="10" fill="#dc2626" opacity="0.85" />
        <text x="321" y="238" textAnchor="middle" fill="#fca5a5" fontSize="9" fontFamily="Inter" fontWeight="bold">Obstacle</text>
        <text x="321" y="248" textAnchor="middle" fill="#fca5a5" fontSize="8" fontFamily="Inter">(Human / Object)</text>

        {/* ─── Receiver (mobile device) ─── */}
        <polygon points="240,185  230,205  250,205" fill="#38bdf8" />
        <circle cx="240" cy="200" r="16" fill="#38bdf8" opacity="0.15" />
        <circle cx="240" cy="200" r="10" fill="none" stroke="#38bdf8" strokeWidth="1" strokeDasharray="3,2" opacity="0.6" />
        <text x="240" y="220" textAnchor="middle" fill="#38bdf8" fontSize="9" fontFamily="Inter" fontWeight="bold">Receiver</text>
        <text x="240" y="230" textAnchor="middle" fill="#7dd3fc" fontSize="8" fontFamily="Inter">(Mobile Device)</text>

        {/* ─── Legend ─── */}
        <g transform="translate(35, 250)">
          <line x1="0" y1="5" x2="20" y2="5" stroke="#22d3ee" strokeWidth="1.5" strokeDasharray="5,3" />
          <text x="25" y="9" fill="#94a3b8" fontSize="9" fontFamily="Inter">LOS Signal (clear path)</text>

          <line x1="0" y1="20" x2="20" y2="20" stroke="#f43f5e" strokeWidth="1.5" strokeDasharray="5,3" />
          <text x="25" y="24" fill="#94a3b8" fontSize="9" fontFamily="Inter">NLOS Signal (blocked)</text>
        </g>
      </svg>

      <p className="text-slate-500 text-xs text-center max-w-lg leading-relaxed">
        ↑ Each LED on the ceiling emits a cone of light. The mobile receiver on the floor picks up signals from visible LEDs. 
        When an obstacle blocks the path, it's called NLOS (Non-Line-of-Sight).
      </p>
    </div>
  );
}

// ─── How It Works — Step Flow ──────────────────────────────────────────────
function HowItWorksFlow() {
  const steps = [
    {
      num: "1",
      icon: <Lightbulb className="w-5 h-5" />,
      color: "text-amber-400",
      bg: "bg-amber-950/40",
      border: "border-amber-900/40",
      title: "LEDs Emit Light",
      desc: "4 LED lights on the ceiling each pulse at different frequencies (like a unique ID). Each has a cone-shaped coverage area."
    },
    {
      num: "2",
      icon: <Radio className="w-5 h-5" />,
      color: "text-cyan-400",
      bg: "bg-cyan-950/40",
      border: "border-cyan-900/40",
      title: "Signal Travels",
      desc: "Light travels from LED to the receiver. The system measures how long it takes and at what angle it arrives."
    },
    {
      num: "3",
      icon: <Eye className="w-5 h-5" />,
      color: "text-violet-400",
      bg: "bg-violet-950/40",
      border: "border-violet-900/40",
      title: "Receiver Detects",
      desc: "An APD (photodetector) sensor picks up the light. If a wall or person blocks the path, signal strength drops — this is NLOS."
    },
    {
      num: "4",
      icon: <Wifi className="w-5 h-5" />,
      color: "text-emerald-400",
      bg: "bg-emerald-950/40",
      border: "border-emerald-900/40",
      title: "Position Calculated",
      desc: "Using signal strengths from all visible LEDs and trilateration math, the receiver's exact X,Y,Z position is computed."
    }
  ];

  return (
    <div className="flex flex-col gap-3">
      <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2">
        <ArrowRight className="w-4 h-4 text-cyan-400" /> How It Works — Step by Step
      </h4>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {steps.map((step, idx) => (
          <div key={idx} className={`relative flex flex-col gap-2 rounded-xl p-4 border ${step.border} ${step.bg}`}>
            <div className="flex items-center gap-2">
              <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-black ${step.bg} border ${step.border} ${step.color}`}>
                {step.num}
              </span>
              <span className={step.color}>{step.icon}</span>
            </div>
            <h5 className={`font-bold text-sm ${step.color}`}>{step.title}</h5>
            <p className="text-slate-400 text-xs leading-relaxed">{step.desc}</p>
            {idx < steps.length - 1 && (
              <div className="hidden lg:flex absolute -right-2 top-1/2 -translate-y-1/2 z-10">
                <ArrowRight className="w-4 h-4 text-slate-600" />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Glossary ──────────────────────────────────────────────────────────────
function GlossarySection() {
  const terms = [
    { term: "LOS", full: "Line-of-Sight", color: "text-emerald-400", desc: "A direct, unobstructed path exists between the LED and the receiver. Best signal quality." },
    { term: "NLOS", full: "Non-Line-of-Sight", color: "text-rose-400", desc: "The light path is blocked by an obstacle (human, furniture). Signal may be zero or severely degraded." },
    { term: "H(0)", full: "DC Channel Gain", color: "text-cyan-400", desc: "A number representing how much light power reaches the receiver from one LED. Higher = stronger signal." },
    { term: "APD", full: "Avalanche Photodiode", color: "text-violet-400", desc: "The light sensor on the receiver. Converts light into electrical signal. Defined by its active area size (A_apd)." },
    { term: "FOV", full: "Field of View", color: "text-amber-400", desc: "The cone angle (in degrees) within which the receiver can detect light. Outside this cone, signal = 0." },
    { term: "Lambertian m", full: "Lambertian Emission Order", color: "text-pink-400", desc: "Describes how focused the LED beam is. m=1 means even spread. Higher m = narrower, more focused beam." },
  ];

  return (
    <div className="flex flex-col gap-3">
      <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2">
        <Info className="w-4 h-4 text-cyan-400" /> Key Terms Glossary
      </h4>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {terms.map((t, i) => (
          <div key={i} className="flex flex-col gap-1.5 bg-slate-900/50 border border-slate-800 rounded-xl p-3">
            <div className="flex items-baseline gap-2">
              <span className={`font-black text-base font-mono ${t.color}`}>{t.term}</span>
              <span className="text-slate-500 text-xs">{t.full}</span>
            </div>
            <p className="text-slate-400 text-xs leading-relaxed">{t.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Main Export ───────────────────────────────────────────────────────────
export default function IllustrationPanel() {
  return (
    <div className="w-full flex flex-col gap-6 animate-fade-in">
      
      {/* Header */}
      <div className="bg-gradient-to-r from-cyan-950/60 to-slate-900/60 border border-cyan-900/30 rounded-2xl p-5 flex flex-col gap-1">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-cyan-500/20 border border-cyan-500/30 rounded-xl flex items-center justify-center">
            <Lightbulb className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">What is Indoor VLC Positioning?</h3>
            <p className="text-slate-400 text-xs">Visible Light Communication (VLC) uses LED light to locate devices indoors — like GPS, but with light!</p>
          </div>
        </div>
      </div>

      {/* Room Diagram */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5 flex flex-col gap-4">
        <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <Users className="w-4 h-4 text-cyan-400" /> System Overview Diagram
        </h4>
        <RoomDiagram />
      </div>

      {/* How It Works */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5">
        <HowItWorksFlow />
      </div>

      {/* Component Cards */}
      <div className="flex flex-col gap-3">
        <h4 className="text-sm font-bold text-slate-200 flex items-center gap-2">
          <Info className="w-4 h-4 text-cyan-400" /> System Components Explained
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <ConceptCard
            icon={<Lightbulb className="w-5 h-5" />}
            title="LED Emitters (Transmitters)"
            color="text-amber-400"
            bgColor="bg-amber-950/30"
            borderColor="border-amber-900/40"
            description="4 LED lights are mounted on the ceiling, each pointing downward. They continuously broadcast light signals at unique frequencies."
            detail="In the 3D view: yellow spheres on the ceiling. Each emits a cone-shaped beam downward."
          />
          <ConceptCard
            icon={<Eye className="w-5 h-5" />}
            title="APD Receiver (Mobile Device)"
            color="text-cyan-400"
            bgColor="bg-cyan-950/30"
            borderColor="border-cyan-900/40"
            description="The mobile device (phone/drone) has a light sensor that receives signals from the LEDs above it. It moves around the room."
            detail="In the 3D view: the small blue cone/triangle that moves around the floor."
          />
          <ConceptCard
            icon={<Users className="w-5 h-5" />}
            title="Obstacles (Blockers)"
            color="text-rose-400"
            bgColor="bg-rose-950/30"
            borderColor="border-rose-900/40"
            description="People or furniture can block the light path between an LED and the receiver. This creates NLOS (Non-Line-of-Sight) conditions."
            detail="In the 3D view: the red cylinder (human) and red box (desk) that you can reposition with sliders."
          />
        </div>
      </div>

      {/* Glossary */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-5">
        <GlossarySection />
      </div>

    </div>
  );
}
