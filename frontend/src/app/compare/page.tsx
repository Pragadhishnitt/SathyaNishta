"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { SidebarNav } from "@/components/SidebarNav";
import { InvestigationPanel, AgentEvent, SynthesisResult } from "@/components/InvestigationPanel";
import { GitCompare, ArrowRight, Loader2, Shield, AlertTriangle, CheckCircle2, Zap } from "lucide-react";

interface CompanyInvestigation {
  name: string;
  agentEvents: AgentEvent[];
  synthesis: SynthesisResult | null;
  isLoading: boolean;
  investigationId?: string;
}

const INITIAL_STATE: CompanyInvestigation = {
  name: "",
  agentEvents: [],
  synthesis: null,
  isLoading: false,
};

import { useThreads } from "@/context/ThreadContext";

export default function ComparePage() {
  const router = useRouter();
  const { data: session } = useSession();
  const { threads, currentThreadId, setCurrentThreadId, addThread, updateThread } = useThreads();
  const [query, setQuery] = useState("");
  const [companyA, setCompanyA] = useState<CompanyInvestigation>({ ...INITIAL_STATE });
  const [companyB, setCompanyB] = useState<CompanyInvestigation>({ ...INITIAL_STATE });
  const [isRunning, setIsRunning] = useState(false);

  // Redirect if not logged in
  if (!session) {
    if (typeof window !== "undefined") router.push("/auth/login?callbackUrl=/compare");
    return <div className="h-screen bg-surface-0 flex items-center justify-center">Redirecting...</div>;
  }

  const parseCompanies = (input: string): [string, string] | null => {
    const vsMatch = input.match(/(.+?)\s+(?:vs\.?|versus|compared?\s+(?:to|with))\s+(.+)/i);
    if (vsMatch) return [vsMatch[1].trim(), vsMatch[2].trim()];
    const andMatch = input.match(/compare\s+(.+?)\s+(?:and|&)\s+(.+)/i);
    if (andMatch) return [andMatch[1].trim(), andMatch[2].trim()];
    return null;
  };

  const startInvestigation = async (
    companyName: string,
    setter: React.Dispatch<React.SetStateAction<CompanyInvestigation>>
  ) => {
    setter(prev => ({ ...prev, name: companyName, isLoading: true, agentEvents: [], synthesis: null }));

    try {
      const res = await fetch("/api/investigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: `Investigate ${companyName}`, mode: "sathyanishta" }),
      });

      const { stream_url, investigation_id } = await res.json();
      if (investigation_id) {
        setter(prev => ({ ...prev, investigationId: investigation_id }));
      }
      const es = new EventSource(stream_url);

      es.addEventListener("agent_start", (e) => {
        const d = JSON.parse(e.data);
        setter(prev => ({ ...prev, agentEvents: [...prev.agentEvents, { ...d, status: "running" }] }));
      });

      es.addEventListener("agent_done", (e) => {
        const d = JSON.parse(e.data);
        setter(prev => ({
          ...prev,
          agentEvents: prev.agentEvents.map(a => a.agent === d.agent ? { ...a, ...d, status: "complete" } : a),
        }));
      });

      es.addEventListener("synthesis", (e) => {
        setter(prev => ({ ...prev, synthesis: JSON.parse(e.data) }));
      });

      es.addEventListener("complete", () => {
        setter(prev => ({ ...prev, isLoading: false }));
        es.close();
      });

      es.onerror = () => {
        setter(prev => ({ ...prev, isLoading: false }));
        es.close();
      };
    } catch (error) {
      console.error("Investigation failed:", error);
      setter(prev => ({ ...prev, isLoading: false }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isRunning) return;

    const parsed = parseCompanies(query);
    if (!parsed) return;

    setIsRunning(true);
    await Promise.all([
      startInvestigation(parsed[0], setCompanyA),
      startInvestigation(parsed[1], setCompanyB),
    ]);
    setIsRunning(false);
  };

  const hasResults = companyA.agentEvents.length > 0 || companyB.agentEvents.length > 0;

  return (
    <div className="flex flex-col h-screen bg-surface-0 text-white">
      <Navbar mode="sathyanishta" />
      <div className="flex flex-1 overflow-hidden">
        <SidebarNav />

        <main className="flex flex-col flex-1 overflow-hidden">
          {/* Header */}
          <div className="border-b border-white/[0.04] p-5 flex items-center gap-3 bg-surface-1/50 backdrop-blur-md sticky top-0 z-20">
            <div className="w-10 h-10 rounded-xl bg-neon-indigo/10 flex items-center justify-center border border-neon-indigo/20 shadow-neon-indigo/5">
              <GitCompare size={20} className="text-neon-indigo" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-tight">Comparative Forensics <span className="text-[10px] bg-neon-indigo/20 text-neon-indigo px-1.5 py-0.5 rounded ml-2 align-middle">PRO</span></h1>
              <p className="text-[11px] text-gray-500">Dual-stream multi-agent analysis for market-side peer comparison</p>
            </div>
          </div>

          {/* Compare Input */}
          <div className="p-6 border-b border-white/[0.04] bg-surface-1/30">
            <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
              <div className="flex gap-3">
                <div className="flex-1 relative group">
                  <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none text-gray-500 group-focus-within:text-neon-indigo transition-colors">
                    <Shield size={16} />
                  </div>
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Compare FraudCorp vs Wipro..."
                    className="w-full pl-11 pr-4 py-3.5 glass-card rounded-2xl text-sm text-white placeholder-gray-600 focus:outline-none focus:border-neon-indigo/40 focus:ring-1 focus:ring-neon-indigo/40 hover:border-white/10 transition-all border border-white/[0.08] shadow-inner"
                    disabled={isRunning}
                  />
                </div>
                <button
                  type="submit"
                  disabled={isRunning || !parseCompanies(query)}
                  className="btn-primary flex items-center gap-2 px-8 rounded-2xl disabled:opacity-50 whitespace-nowrap shadow-neon-indigo/20"
                >
                  {isRunning ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <>
                      <GitCompare size={16} />
                      Analyze Matchup
                    </>
                  )}
                </button>
              </div>
              <div className="flex items-center gap-4 mt-3 ml-1">
                <p className="text-[10px] text-gray-500 flex items-center gap-1">
                  <span className="w-1 h-1 rounded-full bg-neon-indigo shadow-neon-indigo animate-pulse" />
                  Try "Adani vs Reliance"
                </p>
                <p className="text-[10px] text-gray-400 font-medium">
                  SSE Streams Active
                </p>
              </div>
            </form>
          </div>

          {/* Split Screen Results */}
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            {hasResults ? (
              <div className="grid grid-cols-2 gap-px bg-white/[0.04] h-full min-h-[600px]">
                {/* Company A */}
                <div className="bg-surface-0 p-5 overflow-y-auto">
                  <CompanyHeader name={companyA.name} synthesis={companyA.synthesis} isLoading={companyA.isLoading} />
                  <div className="mt-4">
                    <InvestigationPanel
                      agentEvents={companyA.agentEvents}
                      synthesis={companyA.synthesis}
                      isLoading={companyA.isLoading}
                      investigationId={companyA.investigationId}
                    />
                  </div>
                </div>

                {/* Company B */}
                <div className="bg-surface-0 p-5 overflow-y-auto">
                  <CompanyHeader name={companyB.name} synthesis={companyB.synthesis} isLoading={companyB.isLoading} />
                  <div className="mt-4">
                    <InvestigationPanel
                      agentEvents={companyB.agentEvents}
                      synthesis={companyB.synthesis}
                      isLoading={companyB.isLoading}
                      investigationId={companyB.investigationId}
                    />
                  </div>
                </div>
              </div>
            ) : (
              /* Empty state */
              <div className="flex flex-col items-center justify-center h-full text-center animate-fade-in p-8">
                <div className="relative mb-8">
                  <div className="absolute inset-0 bg-neon-indigo/20 blur-2xl rounded-full scale-150 animate-pulse-glow" />
                  <div className="relative w-24 h-24 rounded-3xl bg-surface-1 flex items-center justify-center border border-neon-indigo/30 shadow-2xl animate-float">
                    <GitCompare size={40} className="text-neon-indigo" />
                  </div>
                </div>
                <h2 className="text-2xl font-bold mb-3 tracking-tight">Competitive Intelligence</h2>
                <p className="text-gray-400 max-w-md leading-relaxed mb-8">
                  Execute parallel multi-agent forensic investigations to compare risk benchmarks and financial anomalies across market peers.
                </p>
                <div className="grid grid-cols-3 gap-4 w-full max-w-xl">
                  <div className="glass-card p-4 rounded-2xl border-white/[0.04]">
                    <div className="text-neon-indigo mb-2 flex justify-center"><Shield size={18} /></div>
                    <div className="text-[10px] font-bold text-gray-300 uppercase mb-1">Risk Benchmarking</div>
                    <div className="text-[10px] text-gray-500">Side-by-side fraud score comparison</div>
                  </div>
                  <div className="glass-card p-4 rounded-2xl border-white/[0.04]">
                    <div className="text-purple-400 mb-2 flex justify-center"><Zap size={18} /></div>
                    <div className="text-[10px] font-bold text-gray-300 uppercase mb-1">Dual Agent SSE</div>
                    <div className="text-[10px] text-gray-500">Real-time parallel event tracking</div>
                  </div>
                  <div className="glass-card p-4 rounded-2xl border-white/[0.04]">
                    <div className="text-blue-400 mb-2 flex justify-center"><GitCompare size={18} /></div>
                    <div className="text-[10px] font-bold text-gray-300 uppercase mb-1">Peer Analysis</div>
                    <div className="text-[10px] text-gray-500">Cross-company anomaly detection</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

function CompanyHeader({
  name,
  synthesis,
  isLoading,
}: {
  name: string;
  synthesis: SynthesisResult | null;
  isLoading: boolean;
}) {
  if (!name) return null;

  return (
    <div className="flex items-center justify-between mb-3 glass-card p-3 rounded-xl">
      <div className="flex items-center gap-2">
        <Shield size={15} className="text-neon-indigo" />
        <span className="font-bold text-sm">{name}</span>
        {isLoading && (
          <span className="flex items-center gap-1 text-[10px] text-neon-indigo">
            <Loader2 size={10} className="animate-spin" />
            Investigating...
          </span>
        )}
      </div>
      {synthesis && (
        <span className={`text-xs font-bold px-2.5 py-1 rounded-lg ${
          synthesis.verdict === "CRITICAL" || synthesis.verdict === "HIGH_RISK"
            ? "bg-red-500/10 text-red-400 border border-red-500/20"
            : synthesis.verdict === "CAUTION"
              ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
              : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
        }`}>
          {synthesis.fraud_risk_score.toFixed(1)} — {synthesis.verdict.replace("_", " ")}
        </span>
      )}
    </div>
  );
}
