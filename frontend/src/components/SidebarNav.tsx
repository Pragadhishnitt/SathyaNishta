"use client";

import { useRouter, usePathname } from "next/navigation";
import { MessageSquare, Plus, Settings, User, GitCompare, Shield, Zap, Edit2, Trash2, Check, X } from "lucide-react";
import { useThreads, Thread } from "@/context/ThreadContext";
import { useState } from "react";

export function SidebarNav() {
  const router = useRouter();
  const pathname = usePathname();
  const { threads, currentThreadId, setCurrentThreadId, addThread, renameThread, deleteThread } = useThreads();

  return (
    <aside className="w-[240px] bg-surface-1 flex flex-col h-full border-r border-white/[0.04]">
      {/* New Chat Button */}
      <div className="p-3 pt-4">
        <button
          onClick={() => addThread("standard")}
          className="flex w-full items-center justify-center gap-2 rounded-xl p-2.5 text-sm font-medium transition-all bg-gradient-to-r from-blue-500/10 to-indigo-600/10 hover:from-blue-500/20 hover:to-indigo-600/20 border border-blue-500/20 hover:border-blue-500/30 text-blue-400 hover:shadow-blue-500/20 group"
        >
          <Plus size={15} className="group-hover:rotate-90 transition-transform duration-300" />
          New Chat
        </button>
      </div>

      {/* Navigation */}
      <div className="px-3 mt-2">
        <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2 px-2">
          Navigation
        </div>
        <NavItem
          icon={<MessageSquare size={15} />}
          label="Market Chat"
          active={pathname === "/"}
          onClick={() => router.push("/")}
        />
        <NavItem
          icon={<GitCompare size={15} />}
          label="Compare Mode"
          active={pathname === "/compare"}
          onClick={() => router.push("/compare")}
          badge="PRO"
        />
      </div>

      {/* Recent Chats */}
      <div className="flex-1 overflow-y-auto px-3 mt-4 custom-scrollbar">
        <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2 px-2 flex justify-between items-center">
          Recent Chats
          <span className="text-[8px] bg-white/[0.05] px-1.5 py-0.5 rounded opacity-50">{threads.length}</span>
        </div>
        <div className="space-y-0.5">
          {threads.map((thread) => (
            <HistoryItem 
              key={thread.id} 
              thread={thread}
              active={currentThreadId === thread.id}
              onClick={() => {
                setCurrentThreadId(thread.id);
                if (pathname !== "/") router.push("/");
              }}
              onRename={(title) => renameThread(thread.id, title)}
              onDelete={() => deleteThread(thread.id)}
            />
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-white/[0.04] p-3 space-y-0.5">
        <FooterItem icon={<Settings size={14} />} label="Settings" />
        <FooterItem icon={<User size={14} />} label="Profile" />
      </div>
    </aside>
  );
}

function NavItem({
  icon,
  label,
  active = false,
  onClick,
  badge,
}: {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
  onClick?: () => void;
  badge?: string;
}) {
  return (
    <div
      onClick={onClick}
      className={`flex cursor-pointer items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition-all mb-0.5 ${
        active
          ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
          : "text-gray-400 hover:text-gray-200 hover:bg-white/[0.03] border border-transparent"
      }`}
    >
      {icon}
      <span className="font-medium">{label}</span>
      {badge && (
        <span className={`ml-auto text-[9px] font-bold px-1.5 py-0.5 rounded-full ${
          badge === "PRO" ? "bg-neon-indigo/20 text-neon-indigo" : "bg-blue-500/20 text-blue-400"
        }`}>
          {badge}
        </span>
      )}
    </div>
  );
}

function HistoryItem({ 
  thread, 
  active = false, 
  onClick,
  onRename,
  onDelete
}: { 
  thread: Thread; 
  active?: boolean; 
  onClick: () => void;
  onRename: (title: string) => void;
  onDelete: () => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(thread.title);

  const handleRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (editValue.trim() && editValue !== thread.title) {
      onRename(editValue);
    }
    setIsEditing(false);
  };

  const handleCancel = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditValue(thread.title);
    setIsEditing(false);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm("Delete this chat?")) {
      onDelete();
    }
  };

  return (
    <div
      onClick={onClick}
      className={`flex cursor-pointer items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs transition-all relative group ${
        active
          ? "bg-white/[0.05] text-white font-medium shadow-sm"
          : "text-gray-500 hover:text-gray-300 hover:bg-white/[0.02]"
      }`}
    >
      <div className={`p-1 rounded-md shrink-0 ${thread.mode === 'sathyanishta' ? 'bg-neon-indigo/10' : 'bg-blue-500/10'}`}>
        {thread.mode === 'sathyanishta' ? (
          <Shield size={12} className="text-neon-indigo" />
        ) : (
          <MessageSquare size={12} className="text-blue-400" />
        )}
      </div>

      {isEditing ? (
        <div className="flex items-center gap-1 flex-1 min-w-0" onClick={e => e.stopPropagation()}>
          <input
            autoFocus
            className="bg-surface-1 border border-white/10 rounded px-1.5 py-0.5 w-full outline-none text-white text-[11px]"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleRename(e as any);
              if (e.key === 'Escape') handleCancel(e as any);
            }}
          />
          <button onClick={handleRename} className="text-emerald-400 hover:text-emerald-300"><Check size={12}/></button>
          <button onClick={handleCancel} className="text-gray-500 hover:text-gray-400"><X size={12}/></button>
        </div>
      ) : (
        <>
          <span className="truncate flex-1">{thread.title || "New Chat"}</span>
          <div className="hidden group-hover:flex items-center gap-1.5 transition-opacity">
            <button 
              onClick={(e) => { e.stopPropagation(); setIsEditing(true); setEditValue(thread.title); }}
              className="text-gray-500 hover:text-white transition-colors"
            >
              <Edit2 size={11} />
            </button>
            <button 
              onClick={handleDelete}
              className="text-gray-500 hover:text-red-400 transition-colors"
            >
              <Trash2 size={11} />
            </button>
          </div>
        </>
      )}

      {active && !isEditing && (
        <div className={`absolute left-0 w-0.5 h-4 rounded-full ${thread.mode === 'sathyanishta' ? 'bg-neon-indigo' : 'bg-blue-400'}`} />
      )}
    </div>
  );
}

function FooterItem({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex cursor-pointer items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs text-gray-500 hover:text-gray-300 hover:bg-white/[0.03] transition-all">
      {icon}
      {label}
    </div>
  );
}
