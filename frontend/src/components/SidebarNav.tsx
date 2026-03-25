"use client";

import { useRouter, usePathname } from "next/navigation";
import { MessageSquare, Plus, Settings, User, GitCompare, Shield, Zap } from "lucide-react";

export function SidebarNav() {
  const router = useRouter();
  const pathname = usePathname();

  return (
    <aside className="w-[240px] bg-surface-1 flex flex-col h-full border-r border-white/[0.04]">
      {/* New Investigation Button */}
      <div className="p-3 pt-4">
        <button
          onClick={() => router.push("/")}
          className="flex w-full items-center justify-center gap-2 rounded-xl p-2.5 text-sm font-medium transition-all bg-gradient-to-r from-neon-indigo/10 to-purple-600/10 hover:from-neon-indigo/20 hover:to-purple-600/20 border border-neon-indigo/20 hover:border-neon-indigo/30 text-neon-indigo hover:shadow-neon-indigo group"
        >
          <Plus size={15} className="group-hover:rotate-90 transition-transform duration-300" />
          New Investigation
        </button>
      </div>

      {/* Navigation */}
      <div className="px-3 mt-2">
        <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2 px-2">
          Navigation
        </div>
        <NavItem
          icon={<Shield size={15} />}
          label="Investigate"
          active={pathname === "/"}
          onClick={() => router.push("/")}
        />
        <NavItem
          icon={<GitCompare size={15} />}
          label="Compare Mode"
          active={pathname === "/compare"}
          onClick={() => router.push("/compare")}
          badge="NEW"
        />
      </div>

      {/* Recent Investigations */}
      <div className="flex-1 overflow-y-auto px-3 mt-4">
        <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2 px-2">
          Recent
        </div>
        <div className="space-y-0.5">
          <HistoryItem title="GVK Power & Infra Loop" active />
          <HistoryItem title="Adani Cash Flow Analysis" />
          <HistoryItem title="Q3 Revenue Anomalies" />
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
          ? "bg-neon-indigo/10 text-neon-indigo border border-neon-indigo/20"
          : "text-gray-400 hover:text-gray-200 hover:bg-white/[0.03] border border-transparent"
      }`}
    >
      {icon}
      <span className="font-medium">{label}</span>
      {badge && (
        <span className="ml-auto text-[9px] font-bold bg-neon-indigo/20 text-neon-indigo px-1.5 py-0.5 rounded-full">
          {badge}
        </span>
      )}
    </div>
  );
}

function HistoryItem({ title, active = false }: { title: string; active?: boolean }) {
  return (
    <div
      className={`flex cursor-pointer items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs transition-all ${
        active
          ? "bg-white/[0.04] text-gray-200"
          : "text-gray-500 hover:text-gray-300 hover:bg-white/[0.02]"
      }`}
    >
      <MessageSquare size={13} className="text-gray-500 flex-shrink-0" />
      <span className="truncate">{title}</span>
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
