"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, MessageSquare } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export function EvidenceChat({ investigationContext }: { investigationContext: any }) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: `Investigation complete for ${investigationContext?.company_name || "this entity"}. Ask follow-up questions grounded in the evidence.`,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState("Analyzing evidence...");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (loading) {
      const loadingStates = [
        "Thinking...",
        "Searching evidence...",
        "Compiling info...",
        "Evaluating risk...",
        "Synthesizing response..."
      ];
      let i = 0;
      interval = setInterval(() => {
        setLoadingMessage(loadingStates[i % loadingStates.length]);
        i++;
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [loading]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const userMsg: Message = { role: "user", content: input.trim() };
    const outgoing = [...messages, userMsg];
    setMessages(outgoing);
    setInput("");
    setLoading(true);

    try {
      console.log("Sending chat request...", { outgoing, investigationContext });
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: outgoing,
          investigation_context: investigationContext,
        }),
      });
      
      if (!res.ok) throw new Error(`Status ${res.status}`);
      
      const data = await res.json();
      console.log("Chat response data:", data);
      const assistantContent =
        data?.content || data?.detail || "Unable to fetch an evidence-grounded answer right now.";
      setMessages((prev) => [...prev, { role: "assistant", content: assistantContent }]);
    } catch (e) {
      console.error("EvidenceChat error:", e);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error while contacting chat service." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-4 rounded-xl border border-neon-indigo/15 bg-surface-1 overflow-hidden">
      <div className="px-3 py-2 border-b border-white/[0.05] bg-neon-indigo/[0.03] text-[11px] font-semibold text-neon-indigo flex items-center gap-2">
        <MessageSquare size={13} />
        Chat with Evidence
      </div>
      <div className="h-64 overflow-y-auto p-3 space-y-2">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 text-xs leading-relaxed ${
                m.role === "user"
                  ? "bg-neon-indigo/30 text-indigo-100 border border-neon-indigo/30"
                  : "bg-white/[0.03] text-gray-300 border border-white/[0.08]"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-lg px-3 py-2 text-xs bg-white/[0.03] border border-white/[0.08] text-gray-400 flex items-center gap-2">
              <Loader2 size={12} className="animate-spin text-neon-indigo" />
              <span className="animate-pulse">{loadingMessage}</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="p-3 border-t border-white/[0.05] flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          disabled={loading}
          placeholder="Ask about anomalies, loops, compliance, or evidence..."
          className="flex-1 rounded-lg bg-surface-0 border border-white/[0.08] px-3 py-2 text-xs text-gray-200 outline-none focus:border-neon-indigo/50"
        />
        <button
          onClick={send}
          disabled={loading}
          className="px-3 py-2 rounded-lg bg-neon-indigo/80 hover:bg-neon-indigo text-white text-xs disabled:opacity-40"
        >
          Send
        </button>
      </div>
    </div>
  );
}
