"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { SidebarNav } from "@/components/SidebarNav";
import { InvestigationPanel, AgentEvent, SynthesisResult } from "@/components/InvestigationPanel";
import { GitCompare, ArrowRight, Loader2, Shield, AlertTriangle, CheckCircle2 } from "lucide-react";

interface CompanyInvestigation {
  name: string;
  agentEvents: AgentEvent[];
  synthesis: SynthesisResult | null;
  isLoading: boolean;
}

const INITIAL_STATE: CompanyInvestigation = {
  name: "",
  agentEvents: [],
  synthesis: null,
  isLoading: false,
};

export default function ComparePage() {
  const router = useRouter();
  const { data: session } = useSession();
  const [query, setQuery] = useState("");
  const [companyA, setCompanyA] = useState<CompanyInvestigation>({ ...INITIAL_STATE });
  const [companyB, setCompanyB] = useState<CompanyInvestigation>({ ...INITIAL_STATE });
  const [isRunning, setIsRunning] = useState(false);

  const parseCompanies = (input: string): [string, string] | null => {
    // Parse "CompanyA vs CompanyB" or "Compare CompanyA and CompanyB"
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

      const { stream_url } = await res.json();
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

    // Fire both investigations in parallel
    await Promise.all([
      startInvestigation(parsed[0], setCompanyA),
      startInvestigation(parsed[1], setCompanyB),
    ]);

    setIsRunning(false);
  };

  const hasResults = companyA.agentEvents.length > 0 || companyB.agentEvents.length > 0;

  return (
    <div className="flex flex-col h-screen bg-surface-0 text-white">
      <Navbar />
      <div className="flex flex-1 overflow-hidden">
        <SidebarNav />

        <main className="flex flex-col flex-1 overflow-hidden">
          {/* Header */}
          <div className="border-b border-white/[0.04] p-5 flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-neon-indigo/10 flex items-center justify-center">
              <GitCompare size={18} className="text-neon-indigo" />
            </div>
            <div>
              <h1 className="text-base font-bold">Compare Mode</h1>
              <p className="text-xs text-gray-500">Side-by-side forensic investigation of two companies</p>
            </div>
          </div>

          {/* Compare Input */}
          <div className="p-5 border-b border-white/[0.04]">
            <form onSubmit={handleSubmit} className="max-w-2xl mx-auto">
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="e.g., FraudCorp vs Wipro"
                    className="w-full px-4 py-3 glass-card rounded-xl text-sm text-white placeholder-gray-600 focus:outline-none focus:border-neon-indigo/30 focus:shadow-neon-indigo transition-all border border-white/[0.06]"
                    disabled={isRunning}
                  />
                </div>
                <button
                  type="submit"
                  disabled={isRunning || !parseCompanies(query)}
                  className="btn-primary flex items-center gap-2 px-5 disabled:opacity-50"
                >
                  {isRunning ? (
                    <Loader2 size={15} className="animate-spin" />
                  ) : (
                    <>
                      <GitCompare size={15} />
                      Compare
                    </>
                  )}
                </button>
              </div>
              <p className="text-[10px] text-gray-600 mt-2">
                Use "vs" or "compared to" — e.g., "Adani vs Reliance" or "Compare TCS and Infosys"
              </p>
            </form>
          </div>

          {/* Split Screen Results */}
          <div className="flex-1 overflow-y-auto">
            {hasResults ? (
              <div className="grid grid-cols-2 gap-0 h-full">
                {/* Company A */}
                <div className="border-r border-white/[0.04] p-4 overflow-y-auto">
                  <CompanyHeader name={companyA.name} synthesis={companyA.synthesis} isLoading={companyA.isLoading} />
                  <InvestigationPanel
                    agentEvents={companyA.agentEvents}
                    synthesis={companyA.synthesis}
                    isLoading={companyA.isLoading}
                  />
                </div>

                {/* Company B */}
                <div className="p-4 overflow-y-auto">
                  <CompanyHeader name={companyB.name} synthesis={companyB.synthesis} isLoading={companyB.isLoading} />
                  <InvestigationPanel
                    agentEvents={companyB.agentEvents}
                    synthesis={companyB.synthesis}
                    isLoading={companyB.isLoading}
                  />
                </div>
              </div>
            ) : (
              /* Empty state */
              <div className="flex flex-col items-center justify-center h-full text-center animate-fade-in">
                <div className="w-16 h-16 rounded-2xl bg-neon-indigo/10 flex items-center justify-center border border-neon-indigo/20 mb-4 animate-float">
                  <GitCompare size={28} className="text-neon-indigo" />
                </div>
                <h2 className="text-lg font-bold mb-1">Comparative Analysis</h2>
                <p className="text-sm text-gray-500 max-w-md">
                  Enter two company names to run parallel forensic investigations and compare risk profiles side by side.
                </p>
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
