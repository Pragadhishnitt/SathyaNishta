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
  const [currentUserId, setCurrentUserId] = useState<string>("");

  // Detect user change and clear data
  useEffect(() => {
    if (session) {
      const userId = (session.user as any).id || session.user.email;
      if (currentUserId && currentUserId !== userId) {
        // User has changed, clear all data and reset
        setThreads([]);
        setCurrentThreadId("");
        setIsInitialized(false);
      }
      setCurrentUserId(userId);
    } else {
      setCurrentUserId("");
    }
  }, [session, currentUserId]);

  // Sync with session
  useEffect(() => {
    if (status === "loading") return;

    if (!session) {
      // Clear state if not logged in
      setThreads([]);
      setCurrentThreadId("");
      setIsInitialized(true);
    } else if (!isInitialized) {
      // Clear any old generic localStorage key to prevent data leakage
      const oldGenericKey = "market-chat-threads";
      localStorage.removeItem(oldGenericKey);
      
      // Load from localStorage with user-specific key if logged in and not yet initialized
      const userId = (session.user as any).id || session.user.email;
      const userSpecificKey = `market-chat-threads-${userId}`;
      const saved = localStorage.getItem(userSpecificKey);
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

  // Save to localStorage on change - ONLY if logged in with user-specific key
  useEffect(() => {
    if (isInitialized && session && threads.length > 0) {
      const userId = (session.user as any).id || session.user.email;
      const userSpecificKey = `market-chat-threads-${userId}`;
      localStorage.setItem(userSpecificKey, JSON.stringify(threads));
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
