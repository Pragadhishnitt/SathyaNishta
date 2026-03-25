import { useRef, useState } from "react";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import { CircleDashed, CheckCircle2, AlertTriangle, FileText, Download, Loader2 } from "lucide-react";

export interface AgentEvent {
  agent: string;
  status: "running" | "complete";
  timestamp?: string;
  risk_score?: number;
  findings?: string[];
  passed?: boolean;
}

export interface SynthesisResult {
  fraud_risk_score: number;
  verdict: "SAFE" | "CAUTION" | "HIGH_RISK" | "CRITICAL";
  evidence: Array<{
    source: string;
    finding: string;
    severity: string;
  }>;
}

interface InvestigationPanelProps {
  agentEvents: AgentEvent[];
  synthesis: SynthesisResult | null;
  isLoading: boolean;
}

export function InvestigationPanel({ agentEvents, synthesis, isLoading }: InvestigationPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownloadPDF = async () => {
    if (!panelRef.current) return;
    try {
      setIsDownloading(true);
      const canvas = await html2canvas(panelRef.current, {
        scale: 2,
        backgroundColor: "#12121E",
        logging: false,
        useCORS: true
      });
      
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF({
        orientation: "portrait",
        unit: "px",
        format: [canvas.width, canvas.height]
      });
      
      pdf.addImage(imgData, "PNG", 0, 0, canvas.width, canvas.height);
      
      // Create blob and trigger download
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

  return (
    <div ref={panelRef} className="w-full rounded-xl border border-indigo-500/20 bg-[#12121e] overflow-hidden my-4 shadow-xl shadow-indigo-500/5">
      
      {/* Header */}
      <div className="border-b border-indigo-500/20 bg-indigo-500/10 p-4 flex items-center justify-between">
        <h3 className="flex items-center gap-2 font-medium text-indigo-300">
          {isLoading ? (
            <CircleDashed size={16} className="animate-spin" />
          ) : (
            <CheckCircle2 size={16} />
          )}
          {isLoading ? "Running Deep Investigation..." : "Investigation Complete"}
        </h3>
        {!isLoading && synthesis && (
          <button
            onClick={handleDownloadPDF}
            disabled={isDownloading}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 transition-colors text-sm font-medium text-white"
          >
            {isDownloading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Download size={16} />
            )}
            {isDownloading ? "Exporting..." : "Export PDF"}
          </button>
        )}
      </div>

      {/* Agents Timeline */}
      <div className="p-4 space-y-4">
        {agentEvents.map((e, idx) => (
          <div key={idx} className="flex gap-4 p-3 rounded-lg bg-[#1a1a2e] border border-white/5">
            <div className="pt-1">
              {e.status === "running" ? (
                <CircleDashed size={16} className="animate-spin text-indigo-400" />
              ) : (
                <CheckCircle2 size={16} className="text-emerald-500" />
              )}
            </div>
            <div>
              <div className="font-semibold text-sm capitalize flex items-center gap-2">
                {e.agent} Node
                {e.timestamp && <span className="text-xs font-normal text-gray-500">[{e.timestamp}]</span>}
              </div>
              
              {/* Completed finding payload */}
              {e.status === "complete" && e.findings && (
                <div className="mt-2 text-xs text-gray-400 space-y-1">
                  <div className="text-white/80">Risk Index: {e.risk_score}/10</div>
                  <ul className="list-disc pl-4 space-y-1 mt-1">
                    {e.findings.map((f, i) => <li key={i}>{f}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Synthesis Scorecard */}
        {synthesis && (
          <div className="mt-6 rounded-lg border-2 border-red-500/30 bg-red-500/10 p-5">
            <h4 className="flex items-center gap-2 font-bold text-red-400 text-lg mb-4">
              <AlertTriangle size={20} />
              Final Verdict: {synthesis.verdict}
            </h4>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-[#171717] p-3 rounded border border-white/5">
                <div className="text-xs text-gray-400 mb-1">Composite Fraud Risk</div>
                <div className="text-2xl font-bold font-mono text-red-500">
                  {synthesis.fraud_risk_score.toFixed(1)} <span className="text-sm">/ 10</span>
                </div>
              </div>
            </div>

            <div>
              <div className="font-semibold text-sm mb-2 mt-4 text-gray-300">Synthesized Evidence Matrix</div>
              <div className="space-y-2">
                {synthesis.evidence.map((ev, idx) => (
                  <div key={idx} className="flex items-start gap-3 bg-[#171717] p-3 rounded border border-white/5">
                    <FileText size={14} className="mt-0.5 text-gray-400" />
                    <div className="text-sm">
                      <span className="font-semibold text-indigo-300 mr-2">[{ev.source}]</span>
                      <span className="text-gray-300">{ev.finding}</span>
                      <span className="ml-2 text-xs font-bold text-red-400">({ev.severity})</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Report Download Action */}
            <div data-html2canvas-ignore="true" className="mt-6 flex justify-end">
              <button
                onClick={handleDownloadPDF}
                disabled={isDownloading}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-600/50 text-white rounded-md text-sm font-medium transition-colors"
              >
                {isDownloading ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
                {isDownloading ? "Generating PDF..." : "Download Official Report"}
              </button>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
