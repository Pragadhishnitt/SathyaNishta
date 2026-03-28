"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { SidebarNav } from "@/components/SidebarNav";
import { ChatInput } from "@/components/ChatInput";
import { ChatMessage, Message } from "@/components/ChatMessage";
import { InvestigationPanel, AgentEvent, SynthesisResult } from "@/components/InvestigationPanel";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { AlertCircle, Lock, Shield, X, Loader2 } from "lucide-react";
import { Thread, Mode } from "@/context/ThreadContext";
import { usePremiumAuth } from "@/hooks/usePremiumAuth";
import { useChatPersistence } from "@/hooks/useChatPersistence";

export default function Home() {
  const router = useRouter();
  const { data: session } = useSession();
  const { threads, currentThreadId, setCurrentThreadId, createThread, addMessage, updateThread, isInitialized } = useChatPersistence();
  const { requireAuth, requirePremium, redirectToLogin, redirectToProfile } = usePremiumAuth();
  const [mode, setMode] = useState<Mode>("standard");
  const [isLoading, setIsLoading] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [investigationEvents, setInvestigationEvents] = useState<AgentEvent[]>([]);
  const [synthesisResult, setSynthesisResult] = useState<SynthesisResult | null>(null);
  const [investigationId, setInvestigationId] = useState<string>("");

  const loadingMessages = [
    "Thinking...",
    "Searching evidence...",
    "Analyzing market data...",
    "Correlating signals...",
    "Synthesizing response..."
  ];

  // Cycle loading messages
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isLoading) {
      interval = setInterval(() => {
        setLoadingStep(prev => (prev + 1) % loadingMessages.length);
      }, 2000);
    } else {
      setLoadingStep(0);
    }
    return () => clearInterval(interval);
  }, [isLoading]);

  // Get current thread from context
  const currentThread = threads.find(t => t.id === currentThreadId) || threads[0] || {
    id: "default",
    title: "New Chat",
    messages: [],
    mode: "standard"
  };

  const handleNewChat = () => {
    createThread(mode);
  };

  const handleSubmit = async (query: string) => {
    const userMsg: Message = { role: "user", content: query };
    const updatedMessages = [...(currentThread.messages || []), userMsg];

    // Add message to thread first
    await addMessage(currentThreadId, query, "user");

    // Update thread title if needed
    let title = currentThread.title;
    if (!currentThread.messages || currentThread.messages.length === 0) {
      if (mode === "sathyanishta") {
        // Try to extract company name (capitalized word after 'investigate' or just first capitalized)
        const companyMatch = query.match(/investigate\s+([A-Z][a-z]+)/i) || query.match(/([A-Z][a-z]+)/);
        const company = companyMatch ? companyMatch[1] : null;
        title = company ? `Forensic: ${company}` : `Investigation: ${query.substring(0, 15)}...`;
      } else {
        title = query.length > 25 ? query.substring(0, 25) + "..." : query;
      }
    }

    if (mode === "standard") {
      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ messages: updatedMessages }),
        });
        const data = await res.json();
        // Add assistant response to persistence
        await addMessage(currentThreadId, data.content, "assistant");
      } catch (error) {
        console.error("Standard chat error:", error);
      } finally {
        setIsLoading(false);
      }
      return;
    }

    // Sathyanishta Mode — SSE stream
    setIsLoading(true);
    try {
      const res = await fetch("/api/investigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, mode }),
      });

      if (!res.ok) {
        throw new Error(`Investigation failed: ${res.statusText}`);
      }

      const { stream_url, investigation_id } = await res.json();
      setInvestigationId(investigation_id);
      setInvestigationEvents([]); // Reset events for new investigation
      const es = new EventSource(stream_url);

      es.addEventListener("agent_start", (e) => {
        const d = JSON.parse(e.data);
        setInvestigationEvents(prev => [...prev, { ...d, status: "running" }]);
      });

      es.addEventListener("agent_done", (e) => {
        const d = JSON.parse(e.data);
        setInvestigationEvents(prev => prev.map(evt =>
          evt.agent === d.agent ? { ...evt, status: "complete" } : evt
        ));
      });

      es.addEventListener("synthesis", (e) => {
        const d = JSON.parse(e.data);
        setSynthesisResult(d);
      });

      es.addEventListener("complete", () => {
        setIsLoading(false);
        es.close();
      });

      es.onerror = () => {
        console.error("EventSource error");
        setIsLoading(false);
        es.close();
      };
    } catch (error) {
      console.error("Failed to start investigation:", error);
      setIsLoading(false);
    }
  };

  const handleModeToggle = () => {
    if (!requireAuth()) {
      setShowLoginModal(true);
      return;
    }

    const newMode = mode === "standard" ? "sathyanishta" : "standard";

    if (newMode === "sathyanishta" && !requirePremium()) {
      setShowLoginModal(true);
      return;
    }

    setMode(newMode);
    // Note: Thread mode update would need additional API call
  };

  return (
    <div className="flex flex-col h-screen bg-surface-0 text-white">
      <Navbar mode={mode} />
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
            {!session ? (
              <WelcomeScreen mode={mode} />
            ) : (
              <>
                {(currentThread.messages || []).length === 0 && <WelcomeScreen mode={mode} />}

                {(currentThread.messages || []).map((m, i) => (
                  <ChatMessage key={i} message={m} />
                ))}

                {/* Investigation Panel */}
                {mode === "sathyanishta" && (investigationEvents.length > 0 || synthesisResult) && (
                  <InvestigationPanel
                    agentEvents={investigationEvents}
                    synthesis={synthesisResult}
                    isLoading={isLoading}
                    investigationId={investigationId}
                    companyName={(synthesisResult as any)?.company_name || ""}
                    onInvestigateEntity={(entity) => handleSubmit(`Investigate ${entity}`)}
                  />
                )}

                {/* Standard Loading State */}
                {isLoading && mode === "standard" && (
                  <div className="flex items-start gap-4 animate-pulse">
                    <div className="w-8 h-8 rounded-lg bg-neon-indigo/10 flex items-center justify-center flex-shrink-0">
                      <Loader2 size={16} className="animate-spin text-neon-indigo" />
                    </div>
                    <div className="flex-1 space-y-2 py-1">
                      <div className="text-xs font-semibold text-neon-indigo animate-pulse">
                        {loadingMessages[loadingStep]}
                      </div>
                      <div className="h-2 bg-white/5 rounded w-3/4"></div>
                      <div className="h-2 bg-white/5 rounded w-1/2"></div>
                    </div>
                  </div>
                )}
              </>
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
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[60] animate-fade-in">
          <div className="glass-card neon-border-indigo p-6 max-w-sm w-full mx-4 animate-slide-up relative">
            <button
              onClick={() => setShowLoginModal(false)}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-300 transition-colors"
            >
              <X size={16} />
            </button>

            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-neon-indigo/10 flex items-center justify-center animate-pulse-glow">
                <Shield size={20} className="text-neon-indigo" />
              </div>
              <div>
                <h2 className="text-base font-bold text-white">MarketChatGPT Pro</h2>
                <p className="text-xs text-gray-500">SathyaNishta Mode access</p>
              </div>
            </div>

            <p className="text-sm text-gray-400 mb-5 leading-relaxed">
              Deep forensic investigation mode requires a Pro account to access advanced multi-agent analysis.
            </p>

            <div className="space-y-2.5">
              <button
                onClick={() => redirectToLogin()}
                className="btn-primary w-full flex items-center justify-center gap-2 py-2.5"
              >
                <Lock size={14} />
                Sign In to Unlock SathyaNishta
              </button>
              <button
                onClick={() => setShowLoginModal(false)}
                className="btn-ghost w-full py-2.5"
              >
                Stay in Standard Mode
              </button>
              <button
                onClick={() => redirectToProfile()}
                className="btn-ghost w-full py-2 text-neon-indigo hover:text-neon-indigo/80"
              >
                Upgrade to Premium
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function queryFromEvidence(thread: Thread): string | undefined {
  const finding = thread.synthesis?.evidence?.[0]?.finding;
  if (!finding) return undefined;
  const match = finding.match(/\b([A-Z][A-Za-z0-9&.\-\s]{2,40})\b/);
  return match ? match[1].trim() : undefined;
}
