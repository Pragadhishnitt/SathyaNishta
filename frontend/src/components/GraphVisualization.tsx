"use client";

import { useEffect, useRef, useState } from "react";
import { Network, AlertTriangle, Maximize2, Minimize2 } from "lucide-react";

interface GraphData {
  nodes: Array<{ id: string; label: string; type?: string }>;
  edges: Array<{ from: string; to: string; amount?: number; suspicious?: boolean; label?: string }>;
}

interface GraphVisualizationProps {
  data: GraphData;
}

export function GraphVisualization({ data }: GraphVisualizationProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (!containerRef.current || !data.nodes.length) return;

    // Dynamic import of vis-network (it's a browser-only library)
    import("vis-network/standalone").then(({ Network: VisNetwork, DataSet }) => {
      const nodes = new DataSet(
        data.nodes.map((n) => ({
          id: n.id,
          label: n.label || n.id,
          color: {
            background: n.type === "suspicious" ? "rgba(239, 68, 68, 0.3)" : "rgba(99, 102, 241, 0.3)",
            border: n.type === "suspicious" ? "#ef4444" : "#6366f1",
            highlight: { background: "rgba(139, 92, 246, 0.5)", border: "#8b5cf6" },
          },
          font: { color: "#e2e8f0", size: 12, face: "Inter" },
          shape: "dot",
          size: 18,
          borderWidth: 2,
          shadow: {
            enabled: true,
            color: n.type === "suspicious" ? "rgba(239, 68, 68, 0.3)" : "rgba(99, 102, 241, 0.2)",
            size: 10,
          },
        }))
      );

      const edges = new DataSet(
        data.edges.map((e, i) => ({
          id: `edge-${i}`,
          from: e.from,
          to: e.to,
          label: e.label || (e.amount ? `₹${e.amount} Cr` : ""),
          color: {
            color: e.suspicious ? "#ef4444" : "rgba(99, 102, 241, 0.5)",
            highlight: "#8b5cf6",
          },
          font: { color: "#94a3b8", size: 10, strokeWidth: 0, face: "JetBrains Mono" },
          arrows: "to",
          width: e.suspicious ? 3 : 1.5,
          smooth: { enabled: true, type: "curvedCW", roundness: 0.2 },
          dashes: !e.suspicious,
          shadow: e.suspicious ? { enabled: true, color: "rgba(239, 68, 68, 0.4)", size: 8 } : false,
        }))
      );

      const network = new VisNetwork(
        containerRef.current!,
        { nodes: nodes as any, edges: edges as any },
        {
          physics: {
            forceAtlas2Based: { gravitationalConstant: -30, centralGravity: 0.005, springLength: 120 },
            solver: "forceAtlas2Based",
            stabilization: { iterations: 100 },
          },
          interaction: { hover: true, tooltipDelay: 200, zoomView: true, dragView: true },
          layout: { improvedLayout: true },
        }
      );

      // Fit after stabilization
      network.once("stabilizationIterationsDone", () => {
        network.fit({ animation: { duration: 500, easingFunction: "easeInOutQuad" } });
      });
    }).catch(() => {
      // vis-network not available — silently fail to fallback view
    });
  }, [data]);

  if (!data.nodes.length) return null;

  const suspiciousEdges = data.edges.filter(e => e.suspicious);

  return (
    <div className="rounded-xl overflow-hidden border border-neon-indigo/10 bg-surface-1 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-white/[0.04] bg-neon-indigo/[0.03]">
        <div className="flex items-center gap-2 text-[11px] font-semibold text-neon-indigo">
          <Network size={13} />
          Transaction Network Graph
        </div>
        <div className="flex items-center gap-2">
          {suspiciousEdges.length > 0 && (
            <span className="flex items-center gap-1 text-[10px] text-red-400 bg-red-500/10 px-2 py-0.5 rounded-full border border-red-500/15">
              <AlertTriangle size={10} />
              {suspiciousEdges.length} suspicious
            </span>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-500 hover:text-gray-300 transition-colors"
          >
            {isExpanded ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
          </button>
        </div>
      </div>

      {/* Graph Canvas */}
      <div
        ref={containerRef}
        className="transition-all duration-300"
        style={{ height: isExpanded ? "400px" : "220px" }}
      />

      {/* Legend */}
      <div className="flex items-center gap-4 px-3 py-2 border-t border-white/[0.04] text-[10px] text-gray-500">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-neon-indigo" />
          Entity
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-neon-red" />
          Suspicious
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-neon-indigo/50" />
          Normal flow
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-neon-red" />
          Suspicious flow
        </div>
      </div>
    </div>
  );
}
