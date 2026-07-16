import { BookOpen, HelpCircle } from "lucide-react";

export default function FormulaPanel() {
  return (
    <div className="w-full flex flex-col gap-4 bg-[#0f172a]/70 border border-slate-800 rounded-xl p-5 shadow-xl text-xs text-slate-300 backdrop-blur-md">
      <h3 className="font-semibold text-xs text-slate-100 flex items-center gap-1.5 uppercase tracking-wider border-b border-slate-800 pb-2">
        <BookOpen className="w-4 h-4 text-cyan-400" />
        VLCL Physical & Geometric Formulations
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Formula 1 */}
        <div className="flex flex-col gap-2 bg-slate-950/40 p-4 rounded-lg border border-slate-850">
          <span className="font-bold text-[10px] text-cyan-400 uppercase tracking-widest border-b border-slate-850 pb-1 flex items-center gap-1">
            <HelpCircle className="w-3.5 h-3.5 text-cyan-400" />
            1. Lambertian Emission Order
          </span>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            The spatial radiation intensity profile of an LED is modeled using a Lambertian emission profile.
            The Lambertian order <span className="font-mono text-slate-200">m</span> depends on the LED semi-angle at half power <span className="font-mono text-slate-200">θ_half</span>:
          </p>
          <div className="flex justify-center py-2 bg-slate-900/60 rounded font-mono text-cyan-400 text-xs font-bold my-1 select-all">
            m = -ln(2) / ln(cos(θ_half))
          </div>
          <p className="text-slate-500 text-[10px]">
            For a default beam angle of 60°, <span className="font-mono">m = 1.0</span>. Narrower angles result in larger Lambertian order values, concentrating light power in a tighter cone.
          </p>
        </div>

        {/* Formula 2 */}
        <div className="flex flex-col gap-2 bg-slate-950/40 p-4 rounded-lg border border-slate-850">
          <span className="font-bold text-[10px] text-cyan-400 uppercase tracking-widest border-b border-slate-850 pb-1 flex items-center gap-1">
            <HelpCircle className="w-3.5 h-3.5 text-cyan-400" />
            2. Channel DC Path Loss G(0)
          </span>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            The line-of-sight (LOS) link channel optical DC gain between transmitter and receiver is given by:
          </p>
          <div className="flex flex-col gap-1 py-1 px-2 bg-slate-900/60 rounded font-mono text-cyan-400 text-[10.5px] font-bold my-1 select-all">
            H(0) = [(m+1)·A_apd / (2π·d²)] · cosᵐ(φ) · g_concentrator · cos(ψ)
          </div>
          <p className="text-slate-500 text-[10px] leading-relaxed">
            Where <span className="font-mono text-slate-300">d</span> is the distance, <span className="font-mono text-slate-300">φ</span> is the irradiance angle, <span className="font-mono text-slate-300">ψ</span> is the incident angle, <span className="font-mono text-slate-300">A_apd</span> is active sensor area, and <span className="font-mono text-slate-300">g_concentrator</span> is optical gain.
          </p>
        </div>

        {/* Formula 3 */}
        <div className="flex flex-col gap-2 bg-slate-950/40 p-4 rounded-lg border border-slate-850">
          <span className="font-bold text-[10px] text-cyan-400 uppercase tracking-widest border-b border-slate-850 pb-1 flex items-center gap-1">
            <HelpCircle className="w-3.5 h-3.5 text-cyan-400" />
            3. Rotational Coordinate Transforms
          </span>
          <p className="text-slate-400 text-[11px] leading-relaxed">
            Receiver normal pointing vector <span className="font-mono text-slate-200">n_rx</span> changes with Pitch, Roll, and Yaw angles:
          </p>
          <div className="flex flex-col gap-1 py-1.5 px-2 bg-slate-900/60 rounded font-mono text-cyan-400 text-[10px] font-bold my-1 leading-normal select-all">
            R = Rz(yaw) · Ry(pitch) · Rx(roll)<br />
            n_rx = R · [0, 0, 1]ᵀ
          </div>
          <p className="text-slate-500 text-[10px]">
            This models real-world mobile receiver tilting (e.g., inside drones, vehicles, hand-held smartphones) affecting VLC connectivity.
          </p>
        </div>
      </div>
    </div>
  );
}
