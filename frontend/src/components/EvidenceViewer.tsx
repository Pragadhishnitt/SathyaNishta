"use client";

import { X, FileText, Shield, ExternalLink } from "lucide-react";

interface EvidenceViewerProps {
  source: string;
  finding: string;
  onClose: () => void;
}

export function EvidenceViewer({ source, finding, onClose }: EvidenceViewerProps) {
  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Panel (slide from right) */}
      <div className="absolute right-0 top-0 bottom-0 w-full max-w-lg glass-card border-l border-neon-indigo/20 shadow-glass animate-slide-right overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between p-4 border-b border-white/[0.06] bg-surface-2/90 backdrop-blur-xl">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-neon-indigo/10 flex items-center justify-center">
              <FileText size={15} className="text-neon-indigo" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-200">Evidence Source</h3>
              <p className="text-[11px] text-neon-indigo">{source}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg hover:bg-white/[0.05] flex items-center justify-center text-gray-500 hover:text-gray-300 transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Finding */}
          <div>
            <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2">Finding Detail</div>
            <div className="glass-card p-4 rounded-xl text-sm text-gray-300 leading-relaxed">
              {finding}
            </div>
          </div>

          {/* Source reference */}
          <div>
            <div className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-2">Source Metadata</div>
            <div className="glass-card p-4 rounded-xl space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Agent</span>
                <span className="text-gray-300 font-medium flex items-center gap-1.5">
                  <Shield size={11} className="text-neon-indigo" />
                  {source} Agent
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Confidence</span>
                <span className="text-neon-emerald font-medium">High (RAG-verified)</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">Data Source</span>
                <span className="text-gray-300 font-medium">
                  {source === "Financial" && "Supabase — financial_filings"}
                  {source === "Graph" && "Neo4j — transaction_graph"}
                  {source === "Compliance" && "SEBI LODR Regulations (RAG)"}
                  {source === "Audio" && "Earnings Call Transcript"}
                  {source === "News" && "Tavily Real-Time Search"}
                  {!["Financial", "Graph", "Compliance", "Audio", "News"].includes(source) && "Investigation Database"}
                </span>
              </div>
            </div>
          </div>

          {/* Audit trail note */}
          <div className="glass-card p-3 rounded-xl flex items-start gap-2 text-[11px] text-gray-400 bg-neon-indigo/[0.03] border border-neon-indigo/10">
            <ExternalLink size={12} className="mt-0.5 text-neon-indigo flex-shrink-0" />
            <span>
              This finding is sourced from the {source} analysis vector and has been cross-validated by the Reflection Agent before synthesis. Full audit trail is stored in the investigation database.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
