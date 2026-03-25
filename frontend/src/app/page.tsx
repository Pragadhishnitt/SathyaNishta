"use client";

import { useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { SidebarNav } from "@/components/SidebarNav";
import { ChatInput } from "@/components/ChatInput";
import { ChatMessage, Message } from "@/components/ChatMessage";
import { InvestigationPanel, AgentEvent, SynthesisResult } from "@/components/InvestigationPanel";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { AlertCircle, Lock } from "lucide-react";

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
    // Add user message
    setMessages(prev => [...prev, { role: "user", content: query }]);
    
    if (mode === "standard") {
      // Standard dummy response
      setIsLoading(true);
      setTimeout(() => {
        setMessages(prev => [...prev, { 
          role: "assistant", 
          content: "This is a standard chat response. Turn on Sathyanishta Mode to trigger a deep multi-agent forensic investigation." 
        }]);
        setIsLoading(false);
      }, 1000);
      return;
    }

    // Sathyanishta Mode - Trigger Investigation SSE stream
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
          content: "Investigation complete. Please review the detailed risk scorecard and evidence matrix in the panel above." 
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
    <div className="flex h-screen bg-[#0f0f0f] text-white">
      <SidebarNav />
      
      <main className="flex flex-col flex-1 overflow-hidden">
        {/* Top bar */}
        <header className="flex items-center gap-3 px-6 py-3 border-b border-white/10 mt-1">
          <span className="font-semibold px-2">Sathya Nishta</span>
          <span className="text-xs text-gray-400 bg-white/5 py-1 px-3 rounded-full">
            ET Markets · Market ChatGPT Next Gen
          </span>
        </header>

        {/* Chat area */}
        <div className="flex-1 overflow-y-auto px-6 pt-8 pb-32 max-w-4xl mx-auto w-full space-y-6">
          {messages.length === 0 && <WelcomeScreen mode={mode} />}
          
          {messages.map((m, i) => (
            <ChatMessage key={i} message={m} />
          ))}

          {/* Sathyanishta Mode Inline Investigation Panel */}
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

      {/* Login Required Modal */}
      {showLoginModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-gradient-to-br from-blue-900/95 to-purple-900/95 rounded-xl border border-white/20 p-8 max-w-md shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-red-500/20 p-3 rounded-lg">
                <AlertCircle className="w-6 h-6 text-red-400" />
              </div>
              <h2 className="text-xl font-bold text-white">Login Required</h2>
            </div>
            
            <p className="text-gray-300 mb-6">
              Sathyanishta Mode requires authentication to access advanced investigation features.
            </p>

            <div className="space-y-3">
              <button
                onClick={() => {
                  setShowLoginModal(false);
                  router.push("/auth/login");
                }}
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-medium py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition"
              >
                <Lock className="w-4 h-4" />
                Sign In
              </button>
              <button
                onClick={() => setShowLoginModal(false)}
                className="w-full bg-white/10 hover:bg-white/20 border border-white/20 text-white font-medium py-3 px-4 rounded-lg transition"
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
