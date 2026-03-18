import { MessageSquare, Clock, Plus, Settings, User } from "lucide-react";

export function SidebarNav() {
  return (
    <aside className="w-[260px] bg-[#171717] flex col-span-1 flex-col h-full border-r border-[#2d2d2d]">
      <div className="p-4">
        <button className="flex w-full items-center gap-2 rounded-lg p-3 text-sm transition-colors hover:bg-[#202123] bg-[#202123]">
          <Plus size={16} />
          New Investigation
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4">
        <div className="mb-2 text-xs font-semibold text-gray-400 mt-4">Recent</div>
        <div className="space-y-1">
          <HistoryItem title="GVK Power & Infra Loop" active />
          <HistoryItem title="Adani Cash Flow Analysis" />
          <HistoryItem title="Q3 Revenue Anomalies" />
        </div>
      </div>

      <div className="border-t border-[#2d2d2d] p-4 text-sm font-medium">
        <div className="flex cursor-pointer items-center gap-3 rounded-lg p-3 transition-colors hover:bg-[#202123]">
          <Settings size={16} />
          Settings
        </div>
        <div className="flex cursor-pointer items-center gap-3 rounded-lg p-3 transition-colors hover:bg-[#202123]">
          <User size={16} />
          Investigator Profile
        </div>
      </div>
    </aside>
  );
}

function HistoryItem({ title, active = false }: { title: string; active?: boolean }) {
  return (
    <div
      className={`flex cursor-pointer items-center gap-3 rounded-lg p-3 text-sm transition-colors ${
        active ? "bg-[#2d2d2d]" : "hover:bg-[#202123]"
      }`}
    >
      <MessageSquare size={16} className="text-gray-400" />
      <span className="truncate">{title}</span>
    </div>
  );
}
