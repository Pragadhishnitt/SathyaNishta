"use client";

import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import { LogOut, LogIn, Activity, TrendingUp, Shield, User } from "lucide-react";
import { useThreads, Mode } from "@/context/ThreadContext";

export function Navbar({ mode }: { mode?: Mode }) {
  const { data: session } = useSession();
  const router = useRouter();
  const { threads, currentThreadId } = useThreads();
  
  const currentThread = threads.find(t => t.id === currentThreadId);
  const isForensicMode = mode === "sathyanishta" || currentThread?.mode === "sathyanishta";

  return (
    <nav className="glass-card border-0 border-b border-white/[0.06] sticky top-0 z-50">
      <div className="flex justify-between items-center h-14 px-5">
        {/* Logo */}
        <div
          className="flex items-center gap-2.5 cursor-pointer group"
          onClick={() => router.push("/")}
        >
          <div className="relative w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center animate-pulse-glow shadow-lg shadow-blue-500/20">
            <Activity size={16} className="text-white" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="text-white font-bold text-sm tracking-tight">
                MarketChatGPT
              </span>
              <span className="text-[9px] font-medium text-blue-400 bg-blue-500/10 border border-blue-500/20 rounded px-1.5 py-0">
                by ET
              </span>
            </div>
          </div>
        </div>
        {/* Center Section: SathyaNishta Indicator */}
        <div className="absolute left-1/2 -translate-x-1/2 flex items-center gap-2">
          {isForensicMode && (
            <div className="flex items-center gap-2 animate-fade-in">
              <Shield size={16} className="text-neon-indigo animate-pulse-glow" />
              <span className="text-white font-bold text-sm tracking-[0.2em] uppercase opacity-90">
                SathyaNishta
              </span>
              <div className="w-1.5 h-1.5 rounded-full bg-neon-indigo animate-pulse" />
            </div>
          )}
        </div>
        {/* Auth Section */}
        <div className="flex items-center gap-3">
          {session ? (
            <>
              <div className="flex items-center gap-2.5">
                {session.user?.image ? (
                  <img
                    src={session.user.image}
                    alt="Avatar"
                    className="w-7 h-7 rounded-full ring-2 ring-neon-indigo/30"
                  />
                ) : (
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-neon-indigo/30 to-purple-600/30 flex items-center justify-center text-xs font-bold text-neon-indigo">
                    {session.user?.name?.charAt(0) || "U"}
                  </div>
                )}
                <div className="hidden sm:block">
                  <p className="text-white text-xs font-medium leading-tight">
                    {session.user?.name}
                  </p>
                  <p className="text-gray-500 text-[10px] leading-tight">
                    {session.user?.email}
                  </p>
                </div>
              </div>
              <button
                onClick={() => router.push("/profile")}
                className="p-2 rounded-lg text-gray-400 hover:text-gray-300 hover:bg-white/[0.05] transition-all"
                title="Profile"
              >
                <User size={16} />
              </button>
              <button
                onClick={() => signOut({ callbackUrl: "/auth/login" })}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-red-400/80 hover:text-red-300 bg-red-500/5 hover:bg-red-500/10 border border-red-500/10 hover:border-red-500/20 transition-all"
              >
                <LogOut size={13} />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </>
          ) : (
            <button
              onClick={() => router.push("/auth/login")}
              className="btn-primary flex items-center gap-1.5 text-xs py-2 px-4"
            >
              <LogIn size={13} />
              Sign In
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}
