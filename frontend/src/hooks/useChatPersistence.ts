import { useSession } from "next-auth/react";
import { useState, useEffect, useCallback } from "react";

interface ChatThread {
  id: string;
  title: string;
  mode: "standard" | "sathyanishta";
  investigation_id?: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

interface ChatMessage {
  id: number;
  content: string;
  role: "user" | "assistant";
  extra_data?: string;
  created_at: string;
  thread_id: string;
  user_id: number;
}

export function useChatPersistence() {
  const { data: session } = useSession();
  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [currentThreadId, setCurrentThreadId] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  // Fetch threads from backend
  const fetchThreads = useCallback(async () => {
    if (!session?.user) return;

    try {
      const userId = (session.user as any).id;
      const response = await fetch(`/api/persistence/chat/threads/${userId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${(session.user as any).accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setThreads(data);
        if (data.length > 0) {
          setCurrentThreadId(data[0].id);
        }
      }
    } catch (error) {
      console.error('Failed to fetch threads:', error);
    }
    setIsInitialized(true);
  }, [session]);

  // Create new thread
  const createThread = useCallback(async (mode: "standard" | "sathyanishta", title?: string) => {
    if (!session?.user) return;

    try {
      const userId = (session.user as any).id;
      const response = await fetch(`/api/persistence/chat/threads/${userId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${(session.user as any).accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: title || "New Chat",
          mode,
          investigation_id: mode === "sathyanishta" ? "auto-generated" : null,
        }),
      });

      if (response.ok) {
        const newThread = await response.json();
        setThreads(prev => [newThread, ...prev]);
        setCurrentThreadId(newThread.id);
      }
    } catch (error) {
      console.error('Failed to create thread:', error);
    }
  }, [session]);

  // Fetch thread with messages
  const fetchThread = useCallback(async (threadId: string) => {
    if (!session?.user) return;

    try {
      const userId = (session.user as any).id;
      const response = await fetch(`/api/persistence/chat/threads/${userId}/${threadId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${(session.user as any).accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const threadData = await response.json();
        setThreads(prev => prev.map(t => t.id === threadId ? threadData : t));
      }
    } catch (error) {
      console.error('Failed to fetch thread:', error);
    }
  }, [session]);

  // Add message to thread
  const addMessage = useCallback(async (threadId: string, content: string, role: "user" | "assistant") => {
    if (!session?.user) return;

    try {
      const userId = (session.user as any).id;
      const response = await fetch(`/api/persistence/chat/threads/${userId}/${threadId}/messages`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${(session.user as any).accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          role,
        }),
      });

      if (response.ok) {
        await fetchThread(threadId); // Refresh thread to get new message
      }
    } catch (error) {
      console.error('Failed to add message:', error);
    }
  }, [session, fetchThread]);

  // Update thread (local state for UI optimism)
  const updateThread = useCallback((threadId: string, updates: Partial<ChatThread>) => {
    setThreads(prev => prev.map(t => t.id === threadId ? { ...t, ...updates } : t));
  }, []);

  // Initialize on session change
  useEffect(() => {
    if (session && !isInitialized) {
      fetchThreads();
    } else if (!session) {
      setThreads([]);
      setCurrentThreadId("");
      setIsInitialized(false);
    }
  }, [session, fetchThreads, isInitialized]);

  return {
    threads,
    currentThreadId,
    setCurrentThreadId,
    createThread,
    fetchThread,
    addMessage,
    updateThread,
    isLoading,
    isInitialized,
  };
}
