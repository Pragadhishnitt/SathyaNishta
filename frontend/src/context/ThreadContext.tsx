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
  addMessage: (threadId: string, content: string, role: "user" | "assistant") => Promise<void>;
  isInitialized: boolean;
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
    if (session && session.user) {
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

  // Fetch threads from backend
  const fetchBackendThreads = async (userId: string, token: string) => {
    try {
      const response = await fetch(`/api/persistence/chat/threads/${userId}`, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        // Backend returns messages in each thread directly
        if (Array.isArray(data) && data.length > 0) {
          const mappedThreads: Thread[] = data.map((t: any) => ({
            id: t.id,
            title: t.title,
            mode: t.mode as Mode,
            investigationId: t.investigation_id,
            createdAt: new Date(t.created_at).getTime(),
            messages: (t.messages || []).map((m: any) => ({
              role: m.role,
              content: m.content,
              createdAt: m.created_at
            }))
          }));
          setThreads(mappedThreads);
          if (!currentThreadId && mappedThreads.length > 0) {
            setCurrentThreadId(mappedThreads[0].id);
          }
          return true;
        }
      }
    } catch (e) {
      console.error("Failed to load backend threads", e);
    }
    return false;
  };

  // Sync with session
  useEffect(() => {
    if (status === "loading") return;

    const initData = async () => {
      if (!session) {
        setThreads([]);
        setCurrentThreadId("");
      } else if (session && session.user) {
        const userId = (session.user as any).id || session.user.email;
        const token = (session.user as any).accessToken;
        
        let loaded = false;
        if (token) {
           loaded = await fetchBackendThreads(userId, token);
        }
        
        if (!loaded) {
          // Create initial thread if none loaded
          const id = Math.random().toString(36).substring(7);
          setThreads([{ id, title: "New Market Chat", messages: [], mode: "standard", createdAt: Date.now() }]);
          setCurrentThreadId(id);
        }
      }
      setIsInitialized(true);
    };
    
    if (!isInitialized) {
      initData();
    }
  }, [session, status, isInitialized, currentThreadId]);

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
    
    // Create in backend if session
    if (session && session.user) {
      const userId = (session.user as any).id || session.user.email;
      const token = (session.user as any).accessToken;
      if (token) {
        fetch(`/api/persistence/chat/threads/${userId}`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: "New Chat", mode, investigation_id: mode === "sathyanishta" ? "auto-generated" : null })
        }).then(res => res.ok ? res.json() : null).then(data => {
          if (data && data.id) {
             // Link the generated local ID to the backend ID by replacing it
             setThreads(prev => prev.map(t => t.id === id ? { ...t, id: data.id } : t));
             setCurrentThreadId(data.id);
          }
        }).catch(e => console.error("Thread creation failed", e));
      }
    }
    return id;
  };

  const updateThread = (id: string, updatesOrUpdater: Partial<Thread> | ((prev: Thread) => Partial<Thread>)) => {
    let resolvedUpdates: Partial<Thread> = {};
    
    setThreads(prevThreads => prevThreads.map(t => {
      if (t.id === id) {
        resolvedUpdates = typeof updatesOrUpdater === "function" ? updatesOrUpdater(t) : updatesOrUpdater;
        return { ...t, ...resolvedUpdates };
      }
      return t;
    }));

    // Update backend title if changed
    if (session && session.user && (resolvedUpdates.title || resolvedUpdates.investigationId)) {
       const userId = (session.user as any).id || session.user.email;
       const token = (session.user as any).accessToken;
       if (token) {
         fetch(`/api/persistence/chat/threads/${userId}/${id}`, {
           method: 'PUT',
           headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
           body: JSON.stringify({ 
              title: resolvedUpdates.title, 
              investigation_id: resolvedUpdates.investigationId 
           })
         }).catch(e => console.error("Thread update failed", e));
       }
    }
  };

  const setInvestigationId = (threadId: string, invId: string) => {
    updateThread(threadId, { investigationId: invId });
  };

  const renameThread = (id: string, title: string) => {
    updateThread(id, { title });
  };

  const deleteThread = (id: string) => {
    setThreads(prev => {
      const filtered = prev.filter(t => t.id !== id);
      if (currentThreadId === id && filtered.length > 0) {
        setCurrentThreadId(filtered[0].id);
      } else if (filtered.length === 0) {
        // Automatically create a new thread if we deleted the last one
        const newId = Math.random().toString(36).substring(7);
        setTimeout(() => addThread("standard"), 0);
      }
      return filtered;
    });

    // Delete from backend
    if (session && session.user) {
       const userId = (session.user as any).id || session.user.email;
       const token = (session.user as any).accessToken;
       if (token) {
         fetch(`/api/persistence/chat/threads/${userId}/${id}`, {
           method: 'DELETE',
           headers: { 'Authorization': `Bearer ${token}` }
         }).catch(e => console.error("Thread deletion failed", e));
       }
    }
  };

  const addMessage = async (threadId: string, content: string, role: "user" | "assistant") => {
    // Optimistic UI
    setThreads(prev => prev.map(t => {
       if (t.id === threadId) {
          const newMsg: Message = { role, content };
          return { ...t, messages: [...(t.messages || []), newMsg] };
       }
       return t;
    }));

    if (session && session.user) {
       const userId = (session.user as any).id || session.user.email;
       const token = (session.user as any).accessToken;
       if (token) {
         try {
           await fetch(`/api/persistence/chat/threads/${userId}/${threadId}/messages`, {
             method: 'POST',
             headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
             body: JSON.stringify({ role, content })
           });
         } catch (e) {
           console.error("Failed to add message to backend", e);
         }
       }
    }
  };


  return (
    <ThreadContext.Provider value={{ threads, currentThreadId, setCurrentThreadId, addThread, updateThread, renameThread, deleteThread, addMessage, isInitialized }}>
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
