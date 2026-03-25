"use client";

import { useSession, signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import { LogOut, LogIn, Shield, Activity } from "lucide-react";

export function Navbar() {
  const { data: session } = useSession();
  const router = useRouter();

  return (
    <nav className="glass-card border-0 border-b border-white/[0.06] sticky top-0 z-50">
      <div className="flex justify-between items-center h-14 px-5">
        {/* Logo */}
        <div
          className="flex items-center gap-2.5 cursor-pointer group"
          onClick={() => router.push("/")}
        >
          <div className="relative w-8 h-8 rounded-lg bg-gradient-to-br from-neon-indigo to-purple-600 flex items-center justify-center animate-pulse-glow">
            <Shield size={16} className="text-white" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-white font-bold text-sm tracking-tight">
              Sathya Nishta
            </span>
            <span className="hidden sm:flex items-center gap-1.5 text-[10px] font-medium text-neon-indigo/80 bg-neon-indigo/10 border border-neon-indigo/20 rounded-full px-2.5 py-0.5">
              <Activity size={10} />
              COMMAND CENTER
            </span>
          </div>
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
