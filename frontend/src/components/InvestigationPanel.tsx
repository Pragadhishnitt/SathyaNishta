"use client";

import { useEffect, useRef, useState } from "react";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import {
  Loader2, CheckCircle2, AlertTriangle, FileText, Download,
  TrendingUp, Network, Mic, FileCheck, Newspaper, Shield, ChevronDown, ChevronUp,
  ExternalLink, Sparkles, Search, MessageSquare, Mail,
} from "lucide-react";
import { GraphVisualization } from "./GraphVisualization";
import { AudioTimeline } from "./AudioTimeline";
import { EvidenceViewer } from "./EvidenceViewer";
import { EvidenceChat } from "./EvidenceChat";
import { EmailReportModal } from "./EmailReportModal";

export interface AgentEvent {
  agent: string;
  status: "running" | "complete";
  timestamp?: string;
  risk_score?: number;
  findings?: string[];
  evidence_map?: Record<string, any>;
  passed?: boolean;
  graph_data?: { nodes: any[]; edges: any[] };
  deception_markers?: { start: number; end: number; label: string }[];
}

export interface SynthesisResult {
  fraud_risk_score: number;
  verdict: "SAFE" | "CAUTION" | "HIGH_RISK" | "CRITICAL";
  evidence: Array<{
    source: string;
    finding: string;
    severity: string;
  }>;
  financial_findings?: object;
  graph_findings?: object;
  compliance_findings?: object;
  audio_findings?: object;
  news_findings?: object;
  graph_payload?: { nodes: any[]; edges: any[] };
  audio_timeline?: any[];
  audio_timeline_total_duration_s?: number;
}

interface InvestigationPanelProps {
  agentEvents: AgentEvent[];
  synthesis: SynthesisResult | null;
  isLoading: boolean;
  investigationId?: string;
  companyName?: string;
  onInvestigateEntity?: (entity: string) => void;
}

const AGENT_META: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  financial: { icon: <TrendingUp size={14} />, color: "neon-cyan", label: "Financial Agent" },
  graph: { icon: <Network size={14} />, color: "neon-indigo", label: "Graph Agent" },
  compliance: { icon: <FileCheck size={14} />, color: "neon-amber", label: "Compliance Agent" },
  audio: { icon: <Mic size={14} />, color: "neon-red", label: "Audio Agent" },
  news: { icon: <Newspaper size={14} />, color: "neon-emerald", label: "News Agent" },
  reflection: { icon: <Shield size={14} />, color: "neon-indigo", label: "Reflection Gate" },
};

function getRiskColor(score: number): string {
  if (score >= 8) return "neon-red";
  if (score >= 6) return "neon-amber";
  if (score >= 4) return "neon-amber";
  return "neon-emerald";
}

function getVerdictStyle(verdict: string) {
  switch (verdict) {
    case "CRITICAL": return { bg: "bg-red-500/10", border: "border-red-500/30", text: "text-red-400", glow: "shadow-neon-red" };
    case "HIGH_RISK": return { bg: "bg-orange-500/10", border: "border-orange-500/30", text: "text-orange-400", glow: "" };
    case "CAUTION": return { bg: "bg-amber-500/10", border: "border-amber-500/30", text: "text-amber-400", glow: "" };
    default: return { bg: "bg-emerald-500/10", border: "border-emerald-500/30", text: "text-emerald-400", glow: "shadow-neon-emerald" };
  }
}

// Safe renderer for any value that might be a string or object
function safeRender(value: any): string {
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (value === null || value === undefined) return '';
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

export function InvestigationPanel({ agentEvents, synthesis, isLoading, investigationId, companyName, onInvestigateEntity }: InvestigationPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());
  const [selectedEvidence, setSelectedEvidence] = useState<{ source: string; finding: string } | null>(null);
  const [brief, setBrief] = useState("");
  const [generatingBrief, setGeneratingBrief] = useState(false);
  const [relatedEntities, setRelatedEntities] = useState<string[]>([]);
  const [extractingEntities, setExtractingEntities] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);

  const toggleAgent = (agent: string) => {
    setExpandedAgents(prev => {
      const next = new Set(prev);
      if (next.has(agent)) next.delete(agent);
      else next.add(agent);
      return next;
    });
  };

  const handleDownloadPDF = async () => {
    if (investigationId) {
      try {
        setIsDownloading(true);
        // Direct download from backend
        window.location.href = `/api/investigate/${investigationId}/report`;
        return;
      } catch (error) {
        console.error("Backend report failed, falling back to client-side", error);
      } finally {
        setTimeout(() => setIsDownloading(false), 2000);
      }
    }

    // Fallback to client-side screenshot if no ID or backend failed
    if (!panelRef.current) return;
    try {
      setIsDownloading(true);
      const canvas = await html2canvas(panelRef.current, {
        scale: 1.5, // Reduced from 2 for better size
        backgroundColor: "#0a0a0f", logging: false, useCORS: true,
      });
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF({ orientation: "portrait", unit: "px", format: [canvas.width, canvas.height] });
      pdf.addImage(imgData, "PNG", 0, 0, canvas.width, canvas.height);
      const pdfBlob = pdf.output("blob");
      const url = URL.createObjectURL(pdfBlob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `SathyaNishta_Investigation_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Failed to generate PDF", error);
    } finally {
      setIsDownloading(false);
    }
  };

  useEffect(() => {
    const run = async () => {
      if (!synthesis?.evidence?.length || !companyName) return;
      setExtractingEntities(true);
      try {
        const res = await fetch("/api/extract-entities", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ company_name: companyName, evidence: synthesis.evidence }),
        });
        const data = await res.json();
        setRelatedEntities(Array.isArray(data?.entities) ? data.entities : []);
      } catch {
        setRelatedEntities([]);
      } finally {
        setExtractingEntities(false);
      }
    };
    run();
  }, [synthesis, companyName]);

  const generateBrief = async () => {
    if (!synthesis) return;
    setGeneratingBrief(true);
    try {
      const res = await fetch("/api/generate-brief", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          investigation_state: {
            company_name: companyName,
            ...synthesis,
          },
        }),
      });
      const data = await res.json();
      setBrief(data?.brief || "");
    } catch {
      setBrief("Unable to generate FIR summary right now.");
    } finally {
      setGeneratingBrief(false);
    }
  };

  return (
    <>
      <div ref={panelRef} className="w-full rounded-2xl glass-card neon-border-indigo overflow-hidden my-4 animate-slide-up">
        {/* Header */}
        <div className="border-b border-white/[0.06] bg-neon-indigo/[0.03] p-4 flex items-center justify-between">
          <h3 className="flex items-center gap-2.5 font-semibold text-sm">
            {isLoading ? (
              <>
                <div className="relative">
                  <Loader2 size={16} className="animate-spin text-neon-indigo" />
                  <div className="absolute inset-0 rounded-full border border-neon-indigo animate-radar-ping" />
                </div>
                <span className="text-neon-indigo animate-text-glow">Running Deep Investigation...</span>
              </>
            ) : (
              <>
                <CheckCircle2 size={16} className="text-neon-emerald" />
                <span className="text-neon-emerald">Investigation Complete</span>
              </>
            )}
          </h3>
          {!isLoading && synthesis && (
            <div className="flex gap-2">
              <button
                onClick={() => setShowEmailModal(true)}
                className="btn-ghost flex items-center gap-2 text-xs py-2 px-3"
              >
                <Mail size={14} />
                Email
              </button>
              <button
                onClick={handleDownloadPDF}
                disabled={isDownloading}
                className="btn-primary flex items-center gap-2 text-xs py-2 px-3"
              >
                {isDownloading ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
                {isDownloading ? "Exporting..." : "Export PDF"}
              </button>
            </div>
          )}
        </div>

        {/* Agent Cards */}
        <div className="p-4 space-y-2.5">
          {agentEvents.map((e, idx) => {
            const meta = AGENT_META[e.agent] || { icon: <Shield size={14} />, color: "neon-indigo", label: e.agent };
            const isRunning = e.status === "running";
            const isExpanded = expandedAgents.has(e.agent);
            const riskColor = e.risk_score !== undefined ? getRiskColor(e.risk_score) : meta.color;

            return (
              <div
                key={e.agent}
                className={`rounded-xl glass-card overflow-hidden transition-all duration-300 animate-slide-up stagger-${idx + 1} ${
                  isRunning ? "neon-border-indigo animate-shimmer" : `border-${riskColor}/20`
                }`}
              >
                {/* Agent Header */}
                <div
                  onClick={() => !isRunning && toggleAgent(e.agent)}
                  className="flex items-center gap-3 p-3.5 cursor-pointer hover:bg-white/[0.02] transition-colors"
                >
                  {/* Status indicator */}
                  <div className="relative flex-shrink-0">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center bg-${meta.color}/10 text-${meta.color}`}>
                      {meta.icon}
                    </div>
                    {isRunning && (
                      <div className="absolute -top-0.5 -right-0.5">
                        <span className="flex h-2.5 w-2.5">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-neon-indigo opacity-75" />
                          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-neon-indigo" />
                        </span>
                      </div>
                    )}
                    {!isRunning && (
                      <div className="absolute -top-0.5 -right-0.5">
                        <CheckCircle2 size={10} className="text-neon-emerald bg-surface-1 rounded-full" />
                      </div>
                    )}
                  </div>

                  {/* Agent info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-gray-200">{meta.label}</span>
                      {e.timestamp && (
                        <span className="text-xs text-gray-600 font-mono">[{e.timestamp}]</span>
                      )}
                    </div>
                    {isRunning && (
                      <div className="text-xs text-gray-500 mt-0.5">Analyzing...</div>
                    )}
                  </div>

                  {/* Risk score badge */}
                  {e.status === "complete" && typeof e.risk_score === "number" && (
                    <div className={`text-sm font-bold font-mono text-${riskColor} bg-${riskColor}/10 px-2.5 py-1 rounded-lg border border-${riskColor}/20`}>
                      {e.risk_score.toFixed(1)}
                    </div>
                  )}

                  {/* Expand toggle */}
                  {!isRunning && ((e.findings && e.findings.length > 0) || (e.evidence_map && Object.keys(e.evidence_map).length > 0) || e.graph_data || e.deception_markers) && (
                    <div className="text-gray-500">
                      {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </div>
                  )}
                </div>

                {/* Expanded findings */}
                {isExpanded && e.status === "complete" && (
                  <div className="border-t border-white/[0.04] p-3.5 pt-3 animate-fade-in">
                    {e.findings && e.findings.length > 0 && (
                      <ul className="space-y-1.5 mb-2">
                        {e.findings.map((f, i) => (
                          <li key={i} className="flex items-start gap-2 text-xs text-gray-400 leading-relaxed">
                            <span className="text-gray-600 mt-0.5">•</span>
                            <span>{safeRender(f)}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                    
                    {e.evidence_map && Object.keys(e.evidence_map).length > 0 && (
                      <div className="space-y-2 mt-2">
                        {Object.entries(e.evidence_map).slice(0, 5).map(([k, v], i) => (
                          <div key={i} className="text-xs flex flex-col gap-1">
                            <span className="font-semibold text-gray-400 capitalize">{k.replace(/_/g, " ")}:</span>
                            <span className="text-gray-300 font-mono bg-white/[0.02] p-2 rounded max-h-32 overflow-y-auto custom-scrollbar break-words whitespace-pre-wrap">
                              {typeof v === 'object' ? JSON.stringify(v, null, 2) : String(v)}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Graph Visualization for graph agent */}
                    {e.agent === "graph" && e.graph_data && (
                      <div className="mt-3">
                        <GraphVisualization data={e.graph_data} />
                      </div>
                    )}

                    {/* Audio Timeline for audio agent */}
                    {e.agent === "audio" && e.deception_markers && (
                      <div className="mt-3">
                        <AudioTimeline markers={e.deception_markers} />
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}

          {/* ═══════════ Synthesis Scorecard ═══════════ */}
          {synthesis && (
            <div className="mt-4 animate-slide-up">
              {(() => {
                const vs = getVerdictStyle(synthesis.verdict);
                return (
                  <div className={`rounded-2xl ${vs.bg} border ${vs.border} ${vs.glow} p-5`}>
                    {/* Verdict Header */}
                    <div className="flex items-center justify-between mb-5">
                      <h4 className={`flex items-center gap-2.5 font-bold text-base ${vs.text}`}>
                        <AlertTriangle size={18} />
                        Final Verdict: {synthesis.verdict.replace("_", " ")}
                      </h4>
                    </div>

                    {/* Score + Gauge */}
                    <div className="flex items-center gap-6 mb-5">
                      {/* SVG Gauge */}
                      <div className="relative w-24 h-24 flex-shrink-0">
                        <svg className="w-full h-full" viewBox="0 0 100 100">
                          {/* Background circle */}
                          <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="6" />
                          {/* Score arc */}
                          <circle
                            cx="50" cy="50" r="45"
                            fill="none"
                            stroke={synthesis.fraud_risk_score >= 8 ? "#ef4444" : synthesis.fraud_risk_score >= 6 ? "#f59e0b" : synthesis.fraud_risk_score >= 4 ? "#f59e0b" : "#10b981"}
                            strokeWidth="6"
                            strokeLinecap="round"
                            strokeDasharray="283"
                            strokeDashoffset={283 - (283 * synthesis.fraud_risk_score / 10)}
                            className="risk-gauge-circle"
                            style={{ filter: `drop-shadow(0 0 6px ${synthesis.fraud_risk_score >= 8 ? 'rgba(239,68,68,0.5)' : synthesis.fraud_risk_score >= 6 ? 'rgba(245,158,11,0.5)' : 'rgba(16,185,129,0.5)'})` }}
                          />
                        </svg>
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                          <span className={`text-2xl font-bold font-mono ${vs.text}`}>
                            {synthesis.fraud_risk_score.toFixed(1)}
                          </span>
                          <span className="text-[9px] text-gray-500 uppercase tracking-wider">/ 10</span>
                        </div>
                      </div>

                      {/* Score breakdown */}
                      <div className="flex-1">
                        <div className="text-xs text-gray-400 mb-2 font-medium">Composite Fraud Risk</div>
                        <div className="w-full bg-white/[0.04] rounded-full h-2 overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-1000"
                            style={{
                              width: `${synthesis.fraud_risk_score * 10}%`,
                              background: synthesis.fraud_risk_score >= 8
                                ? 'linear-gradient(90deg, #ef4444, #dc2626)'
                                : synthesis.fraud_risk_score >= 6
                                  ? 'linear-gradient(90deg, #f59e0b, #d97706)'
                                  : 'linear-gradient(90deg, #10b981, #059669)'
                            }}
                          />
                        </div>
                        <div className="flex justify-between mt-1.5 text-[10px] text-gray-600">
                          <span>SAFE</span>
                          <span>CAUTION</span>
                          <span>CRITICAL</span>
                        </div>
                      </div>
                    </div>

                    {/* Evidence Matrix */}
                    <div>
                      <div className="font-semibold text-xs mb-3 text-gray-300 uppercase tracking-wide flex items-center gap-2">
                        <FileText size={13} />
                        Synthesized Evidence Matrix
                      </div>
                      <div className="space-y-1.5">
                        {synthesis.evidence.map((ev, idx) => {
                          const sevColor = ev.severity === "CRITICAL" ? "red" : ev.severity === "HIGH" ? "orange" : ev.severity === "MEDIUM" ? "amber" : "emerald";
                          return (
                            <div
                              key={idx}
                              className="flex items-start gap-2.5 glass-card p-3 rounded-lg cursor-pointer hover:bg-white/[0.03] transition-all group"
                              onClick={() => setSelectedEvidence({ source: safeRender(ev.source), finding: safeRender(ev.finding) })}
                            >
                              <FileText size={12} className="mt-0.5 text-gray-500 flex-shrink-0" />
                              <div className="flex-1 min-w-0 text-xs">
                                <span className={`font-semibold text-neon-indigo mr-1.5`}>[{safeRender(ev.source)}]</span>
                                <span className="text-gray-300">{safeRender(ev.finding)}</span>
                              </div>
                              <span className={`text-[9px] font-bold text-${sevColor}-400 bg-${sevColor}-500/10 px-1.5 py-0.5 rounded border border-${sevColor}-500/20 flex-shrink-0`}>
                                {ev.severity}
                              </span>
                              <ExternalLink size={11} className="text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 mt-0.5" />
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Download button */}
                    <div data-html2canvas-ignore="true" className="mt-5 flex justify-end">
                      <button
                        onClick={handleDownloadPDF}
                        disabled={isDownloading}
                        className="btn-primary flex items-center gap-2 text-xs"
                      >
                        {isDownloading ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
                        {isDownloading ? "Generating..." : "Download Official Report"}
                      </button>
                    </div>
                  </div>
                );
              })()}
            </div>
          )}

          {/* Related entities drill-down */}
          {!!synthesis && (
            <div className="mt-3 rounded-xl border border-white/[0.08] bg-surface-1 p-3">
              <div className="flex items-center gap-2 text-[11px] font-semibold text-gray-300 mb-2">
                <Search size={12} className="text-neon-indigo" />
                Related Entities for Drill-Down
              </div>
              {extractingEntities ? (
                <div className="text-[11px] text-gray-500 flex items-center gap-2">
                  <Loader2 size={12} className="animate-spin" />
                  Extracting entities...
                </div>
              ) : relatedEntities.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {relatedEntities.map((entity) => (
                    <button
                      key={entity}
                      onClick={() => onInvestigateEntity?.(entity)}
                      className="text-[11px] px-2.5 py-1 rounded-full border border-neon-indigo/30 text-neon-indigo hover:bg-neon-indigo/10"
                    >
                      🔍 {entity}
                    </button>
                  ))}
                </div>
              ) : (
                <div className="text-[11px] text-gray-500">No related entities extracted from current evidence.</div>
              )}
            </div>
          )}

          {/* FIR Summary */}
          {!!synthesis && (
            <div className="mt-3 rounded-xl border border-amber-500/20 bg-amber-500/[0.04] p-3">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-[11px] font-semibold text-amber-300">
                  <Sparkles size={12} />
                  Generate FIR Summary
                </div>
                <button
                  onClick={generateBrief}
                  disabled={generatingBrief}
                  className="px-3 py-1.5 rounded-lg bg-amber-500/80 hover:bg-amber-500 text-white text-[11px] disabled:opacity-50"
                >
                  {generatingBrief ? "Generating..." : "Generate"}
                </button>
              </div>
              {!!brief && (
                <pre className="mt-3 p-3 rounded-lg bg-surface-0 border border-white/[0.08] text-xs text-gray-300 whitespace-pre-wrap font-mono max-h-72 overflow-y-auto">
                  {brief}
                </pre>
              )}
            </div>
          )}

          {/* Evidence chat */}
          {!!synthesis && (
            <EvidenceChat
              investigationContext={{
                company_name: companyName,
                ...synthesis,
              }}
            />
          )}
        </div>
      </div>

      {/* Evidence Viewer Slide-Over */}
      {selectedEvidence && (
        <EvidenceViewer
          source={selectedEvidence.source}
          finding={selectedEvidence.finding}
          onClose={() => setSelectedEvidence(null)}
        />
      )}

      {/* Email Report Modal */}
      {showEmailModal && synthesis && (
        <EmailReportModal
          isOpen={showEmailModal}
          onClose={() => setShowEmailModal(false)}
          investigationData={synthesis}
          reportType="investigation"
          companyName={companyName}
        />
      )}
    </>
  );
}
