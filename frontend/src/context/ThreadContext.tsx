"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { Message } from "@/components/ChatMessage";
import { AgentEvent, SynthesisResult } from "@/components/InvestigationPanel";
import { useSession } from "next-auth/react";

export type Mode = "standard" | "sathyanishta";

export interface Thread {
  id: string;
  title: string;
  messages: Message[];
  mode: Mode;
  agentEvents?: AgentEvent[];
  synthesis?: SynthesisResult | null;
  investigationId?: string;
  createdAt: number;
}

interface ThreadContextType {
  threads: Thread[];
  currentThreadId: string;
  setCurrentThreadId: (id: string) => void;
  addThread: (mode: Mode) => string;
  updateThread: (id: string, updates: Partial<Thread> | ((prev: Thread) => Partial<Thread>)) => void;
  renameThread: (id: string, title: string) => void;
  deleteThread: (id: string) => void;
}

const ThreadContext = createContext<ThreadContextType | undefined>(undefined);

export function ThreadProvider({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();
  const [threads, setThreads] = useState<Thread[]>([]);
  const [currentThreadId, setCurrentThreadId] = useState<string>("");
  const [isInitialized, setIsInitialized] = useState(false);

  // Sync with session
  useEffect(() => {
    if (status === "loading") return;

    if (!session) {
      // Clear state if not logged in
      setThreads([]);
      setCurrentThreadId("");
      setIsInitialized(true);
    } else if (!isInitialized) {
      // Load from localStorage if logged in and not yet initialized
      const saved = localStorage.getItem("market-chat-threads");
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          setThreads(parsed);
          if (parsed.length > 0) {
            setCurrentThreadId(parsed[0].id);
          } else {
            // Create default thread if empty
            const id = Math.random().toString(36).substring(7);
            const defaultThread: Thread = { id, title: "New Market Chat", messages: [], mode: "standard", createdAt: Date.now() };
            setThreads([defaultThread]);
            setCurrentThreadId(id);
          }
        } catch (e) {
          console.error("Failed to load threads", e);
        }
      } else {
        // Create initial thread
        const id = Math.random().toString(36).substring(7);
        setThreads([{ id, title: "New Market Chat", messages: [], mode: "standard", createdAt: Date.now() }]);
        setCurrentThreadId(id);
      }
      setIsInitialized(true);
    }
  }, [session, status, isInitialized]);

  // Save to localStorage on change - ONLY if logged in
  useEffect(() => {
    if (isInitialized && session && threads.length > 0) {
      localStorage.setItem("market-chat-threads", JSON.stringify(threads));
    }
  }, [threads, isInitialized, session]);

  const addThread = (mode: Mode) => {
    const id = Math.random().toString(36).substring(7);
    const newThread: Thread = {
      id,
      title: "New Chat",
      messages: [],
      mode,
      createdAt: Date.now(),
    };
    setThreads(prev => [newThread, ...prev]);
    setCurrentThreadId(id);
    return id;
  };

  const updateThread = (id: string, updatesOrUpdater: Partial<Thread> | ((prev: Thread) => Partial<Thread>)) => {
    setThreads(prevThreads => prevThreads.map(t => {
      if (t.id === id) {
        const u = typeof updatesOrUpdater === "function" ? updatesOrUpdater(t) : updatesOrUpdater;
        return { ...t, ...u };
      }
      return t;
    }));
  };

  const setInvestigationId = (threadId: string, invId: string) => {
    updateThread(threadId, { investigationId: invId });
  };

  const renameThread = (id: string, title: string) => {
    setThreads(prev => prev.map(t => t.id === id ? { ...t, title } : t));
  };

  const deleteThread = (id: string) => {
    setThreads(prev => {
      const filtered = prev.filter(t => t.id !== id);
      if (currentThreadId === id && filtered.length > 0) {
        setCurrentThreadId(filtered[0].id);
      }
      return filtered;
    });
  };


  return (
    <ThreadContext.Provider value={{ threads, currentThreadId, setCurrentThreadId, addThread, updateThread, renameThread, deleteThread }}>
      {children}
    </ThreadContext.Provider>
  );
}

export function useThreads() {
  const context = useContext(ThreadContext);
  if (context === undefined) {
    throw new Error("useThreads must be used within a ThreadProvider");
  }
  return context;
}
