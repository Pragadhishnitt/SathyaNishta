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

import { useThreads, Thread, Mode } from "@/context/ThreadContext";

export default function Home() {
  const router = useRouter();
  const { data: session } = useSession();
  const { threads, currentThreadId, setCurrentThreadId, addThread, updateThread } = useThreads();
  const [mode, setMode] = useState<Mode>("standard");
  const [isLoading, setIsLoading] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);

  // Get current thread from context
  const currentThread = threads.find(t => t.id === currentThreadId) || threads[0] || {
    id: "default",
    title: "New Chat",
    messages: [],
    mode: "standard"
  };

  const handleNewChat = () => {
    addThread(mode);
  };

  const handleSubmit = async (query: string) => {
    const userMsg: Message = { role: "user", content: query };
    const updatedMessages = [...(currentThread.messages || []), userMsg];
    
    // Automatic better naming
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

    updateThread(currentThreadId, { messages: updatedMessages, title });
    setIsLoading(true);

    if (mode === "standard") {
      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ messages: updatedMessages }),
        });
        const data = await res.json();
        updateThread(currentThreadId, { 
          messages: [...updatedMessages, { role: "assistant", content: data.content }] 
        });
      } catch (error) {
        console.error("Standard chat error:", error);
      } finally {
        setIsLoading(false);
      }
      return;
    }

    // Sathyanishta Mode — SSE stream
    updateThread(currentThreadId, { agentEvents: [], synthesis: null });

    try {
      const res = await fetch("/api/investigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, mode }),
      });

      const { stream_url, investigation_id } = await res.json();
      if (investigation_id) {
        updateThread(currentThreadId, { investigationId: investigation_id });
      }
      const es = new EventSource(stream_url);

      es.addEventListener("agent_start", (e) => {
        const d = JSON.parse(e.data);
        updateThread(currentThreadId, (prev: Thread) => ({ 
          agentEvents: [...(prev.agentEvents || []), { ...d, status: "running" }] 
        }));
      });

      es.addEventListener("agent_done", (e) => {
        const d = JSON.parse(e.data);
        updateThread(currentThreadId, (prev: Thread) => ({
          agentEvents: (prev.agentEvents || []).map(a => 
            a.agent === d.agent ? { ...a, ...d, status: "complete" } : a
          )
        }));
      });

      es.addEventListener("synthesis", (e) => {
        const d = JSON.parse(e.data);
        updateThread(currentThreadId, { synthesis: d });
      });

      es.addEventListener("complete", () => {
        setIsLoading(false);
        updateThread(currentThreadId, (prev: Thread) => ({
          messages: [...(prev.messages || []), {
            role: "assistant",
            content: "Investigation complete. Review the detailed risk scorecard and evidence matrix in the panel above."
          }]
        }));
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
    const newMode = mode === "standard" ? "sathyanishta" : "standard";
    setMode(newMode);
    updateThread(currentThreadId, { mode: newMode });
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
                {currentThread.mode === "sathyanishta" && (currentThread.agentEvents?.length || currentThread.synthesis) && (
                  <InvestigationPanel
                    agentEvents={currentThread.agentEvents || []}
                    synthesis={currentThread.synthesis || null}
                    isLoading={isLoading}
                    investigationId={currentThread.investigationId}
                    companyName={(currentThread.synthesis as any)?.company_name || queryFromEvidence(currentThread)}
                    onInvestigateEntity={(entity) => handleSubmit(`Investigate ${entity}`)}
                  />
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
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
          <div className="glass-card neon-border-indigo p-6 max-w-sm w-full mx-4 animate-slide-up">
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
                <h2 className="text-base font-bold text-white">MarketChatGPT Pro</h2>
                <p className="text-xs text-gray-500">SathyaNishta Mode access</p>
              </div>
            </div>

            <p className="text-sm text-gray-400 mb-5 leading-relaxed">
              Deep forensic investigation mode requires a Pro account to access advanced multi-agent analysis.
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
                Sign In to Unlock SathyaNishta
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

function queryFromEvidence(thread: Thread): string | undefined {
  const finding = thread.synthesis?.evidence?.[0]?.finding;
  if (!finding) return undefined;
  const match = finding.match(/\b([A-Z][A-Za-z0-9&.\-\s]{2,40})\b/);
  return match ? match[1].trim() : undefined;
}
