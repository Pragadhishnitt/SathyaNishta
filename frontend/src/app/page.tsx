"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { SidebarNav } from "@/components/SidebarNav";
import { ChatInput } from "@/components/ChatInput";
import { ChatMessage, Message } from "@/components/ChatMessage";
import { InvestigationPanel, AgentEvent, SynthesisResult } from "@/components/InvestigationPanel";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { AlertCircle, Lock, Shield, X } from "lucide-react";

type Mode = "standard" | "sathyanishta";

export default function Home() {
  const router = useRouter();
  const { data: session } = useSession();
  const [mode, setMode] = useState<Mode>("standard");
  const [messages, setMessages] = useState<Message[]>([]);
  const [agentEvents, setAgentEvents] = useState<AgentEvent[]>([]);
  const [synthesis, setSynthesis] = useState<SynthesisResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);

  const handleSubmit = async (query: string) => {
    setMessages(prev => [...prev, { role: "user", content: query }]);

    if (mode === "standard") {
      setIsLoading(true);
      setTimeout(() => {
        setMessages(prev => [...prev, {
          role: "assistant",
          content: "This is a standard chat response. Toggle Sathyanishta Mode to trigger a deep multi-agent forensic investigation."
        }]);
        setIsLoading(false);
      }, 1000);
      return;
    }

    // Sathyanishta Mode — SSE stream
    setAgentEvents([]);
    setSynthesis(null);
    setIsLoading(true);

    try {
      const res = await fetch("/api/investigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, mode }),
      });

      const { stream_url } = await res.json();
      const es = new EventSource(stream_url);

      es.addEventListener("agent_start", (e) => {
        const d = JSON.parse(e.data);
        setAgentEvents(prev => [...prev, { ...d, status: "running" }]);
      });

      es.addEventListener("agent_done", (e) => {
        const d = JSON.parse(e.data);
        setAgentEvents(prev => prev.map(a =>
          a.agent === d.agent ? { ...a, ...d, status: "complete" } : a
        ));
      });

      es.addEventListener("synthesis", (e) => {
        setSynthesis(JSON.parse(e.data));
      });

      es.addEventListener("complete", () => {
        setIsLoading(false);
        setMessages(prev => [...prev, {
          role: "assistant",
          content: "Investigation complete. Review the detailed risk scorecard and evidence matrix in the panel above."
        }]);
        es.close();
      });

      es.onerror = () => {
        setIsLoading(false);
        es.close();
      };
    } catch (error) {
      console.error("Failed to start investigation:", error);
      setIsLoading(false);
    }
  };

  const handleModeToggle = () => {
    if (!session) {
      setShowLoginModal(true);
      return;
    }
    setMode(m => m === "standard" ? "sathyanishta" : "standard");
  };

  return (
    <div className="flex flex-col h-screen bg-surface-0 text-white">
      <Navbar />
      <div className="flex flex-1 overflow-hidden">
        <SidebarNav />

        <main className="flex flex-col flex-1 overflow-hidden relative">
          {/* Subtle background gradient */}
          <div className="absolute inset-0 pointer-events-none opacity-30">
            <div className="absolute top-0 left-1/4 w-96 h-96 bg-neon-indigo/5 rounded-full blur-3xl" />
            <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-600/5 rounded-full blur-3xl" />
          </div>

          {/* Chat area */}
          <div className="flex-1 overflow-y-auto px-6 pt-6 pb-32 max-w-4xl mx-auto w-full space-y-4 relative z-10">
            {messages.length === 0 && <WelcomeScreen mode={mode} />}

            {messages.map((m, i) => (
              <ChatMessage key={i} message={m} />
            ))}

            {/* Investigation Panel */}
            {mode === "sathyanishta" && (agentEvents.length > 0 || synthesis) && (
              <InvestigationPanel
                agentEvents={agentEvents}
                synthesis={synthesis}
                isLoading={isLoading}
              />
            )}
          </div>

          <ChatInput
            mode={mode}
            onModeToggle={handleModeToggle}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
        </main>
      </div>

      {/* Login Required Modal */}
      {showLoginModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
          <div className="glass-card neon-border-indigo p-6 max-w-sm w-full mx-4 animate-slide-up">
            {/* Close */}
            <button
              onClick={() => setShowLoginModal(false)}
              className="absolute top-3 right-3 text-gray-500 hover:text-gray-300 transition-colors"
            >
              <X size={16} />
            </button>

            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-neon-indigo/10 flex items-center justify-center animate-pulse-glow">
                <Shield size={20} className="text-neon-indigo" />
              </div>
              <div>
                <h2 className="text-base font-bold text-white">Authentication Required</h2>
                <p className="text-xs text-gray-500">Sathyanishta Mode access</p>
              </div>
            </div>

            <p className="text-sm text-gray-400 mb-5 leading-relaxed">
              Deep investigation mode requires authentication to access advanced multi-agent forensic analysis.
            </p>

            <div className="space-y-2.5">
              <button
                onClick={() => {
                  setShowLoginModal(false);
                  router.push("/auth/login");
                }}
                className="btn-primary w-full flex items-center justify-center gap-2 py-2.5"
              >
                <Lock size={14} />
                Sign In to Continue
              </button>
              <button
                onClick={() => setShowLoginModal(false)}
                className="btn-ghost w-full py-2.5"
              >
                Stay in Standard Mode
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
