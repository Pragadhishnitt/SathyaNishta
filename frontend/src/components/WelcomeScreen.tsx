import { Shield, TrendingUp, Network, Mic, FileCheck, Newspaper, Activity, MessageSquare } from "lucide-react";

const CAPABILITIES = [
  {
    icon: <TrendingUp size={18} />,
    title: "Financial Agent",
    desc: "Balance sheet anomalies, cash flow divergence, related-party flags",
    color: "text-neon-cyan",
    bg: "bg-neon-cyan/5",
    border: "border-cyan-500/10",
  },
  {
    icon: <Network size={18} />,
    title: "Graph Agent",
    desc: "Neo4j circular trading loops and shell company networks",
    color: "text-neon-indigo",
    bg: "bg-neon-indigo/5",
    border: "border-indigo-500/10",
  },
  {
    icon: <FileCheck size={18} />,
    title: "Compliance Agent",
    desc: "SEBI LODR violations and regulatory RAG analysis",
    color: "text-neon-amber",
    bg: "bg-neon-amber/5",
    border: "border-amber-500/10",
  },
  {
    icon: <Mic size={18} />,
    title: "Audio Agent",
    desc: "Earnings call tone analysis and deception marker detection",
    color: "text-neon-red",
    bg: "bg-neon-red/5",
    border: "border-red-500/10",
  },
  {
    icon: <Newspaper size={18} />,
    title: "News Agent",
    desc: "Real-time news sentiment and crisis detection via Tavily",
    color: "text-neon-emerald",
    bg: "bg-neon-emerald/5",
    border: "border-emerald-500/10",
  },
];

export function WelcomeScreen({ mode }: { mode: "standard" | "sathyanishta" }) {
  return (
    <div className="mt-12 flex flex-col items-center justify-center text-center animate-fade-in">
      {/* Animated Logo */}
      <div className="relative mb-6">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500/20 to-indigo-600/20 flex items-center justify-center border border-blue-500/20 animate-pulse-glow">
          <Activity size={36} className="text-blue-400 animate-float" />
        </div>
        {/* Decorative rings */}
        <div className="absolute inset-0 -m-3 rounded-2xl border border-blue-500/10 animate-pulse-glow" style={{ animationDelay: '0.5s' }} />
      </div>

      {/* Title */}
      <h1 className="mb-2 text-2xl font-bold tracking-tight">
        <span className="gradient-text">MarketChatGPT</span>{" "}
        <span className="text-blue-400/60 font-medium text-sm">by ET</span>
      </h1>
      <p className="max-w-lg text-sm text-gray-500 mb-8 leading-relaxed">
        Next-generation AI financial intelligence. Chat naturally about markets, or 
        enable <span className="text-neon-indigo font-semibold">SathyaNishta Mode</span> for deep forensic audits.
      </p>

      {/* Sathyanishta Mode Active Banner */}
      {mode === "sathyanishta" && (
        <div className="rounded-xl neon-border-indigo bg-neon-indigo/5 p-4 text-sm max-w-lg text-left mb-8 animate-slide-up">
          <div className="font-semibold text-neon-indigo mb-1.5 flex items-center gap-2 text-xs uppercase tracking-wide">
            <div className="relative">
              <Shield size={14} />
              <div className="absolute inset-0 animate-radar-ping rounded-full border border-neon-indigo" />
            </div>
            Deep Investigation Mode Active
          </div>
          <p className="text-indigo-200/70 text-xs leading-relaxed">
            Queries trigger full multi-agent investigation across Financial, Graph, Compliance,
            Audio, and News vectors with cross-validation and final synthesis verdict.
          </p>
        </div>
      )}

      {/* Capability Cards - Only show prominently in SathyaNishta mode */}
      {mode === "sathyanishta" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-w-2xl w-full animate-fade-in">
          {CAPABILITIES.map((cap, idx) => (
            <div
              key={cap.title}
              className={`glass-card glass-card-hover p-3.5 text-left animate-slide-up stagger-${idx + 1} ${cap.bg} border ${cap.border}`}
            >
              <div className={`${cap.color} mb-2`}>{cap.icon}</div>
              <div className="text-xs font-semibold text-gray-200 mb-1">{cap.title}</div>
              <div className="text-[11px] text-gray-500 leading-relaxed">{cap.desc}</div>
            </div>
          ))}
        </div>
      )}

      {mode === "standard" && (
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="flex items-center gap-2 text-xs text-gray-500 font-medium px-3 py-1.5 rounded-full bg-white/[0.03] border border-white/[0.05]">
            <MessageSquare size={12} className="text-blue-400" />
            Standard Market Intelligence Active
          </div>
          <div className="grid grid-cols-2 gap-2 text-[10px] text-gray-600 uppercase tracking-widest mt-4">
             <div className="px-4 py-2 border border-white/[0.04] rounded-lg">Real-time Quotes</div>
             <div className="px-4 py-2 border border-white/[0.04] rounded-lg">Sentiment Analysis</div>
          </div>
        </div>
      )}
    </div>
  );
}
