"use client";

import { useState } from "react";
import { Mic, AlertTriangle, Info } from "lucide-react";

interface DeceptionMarker {
  start: number;  // percentage 0-100
  end: number;    // percentage 0-100
  label: string;
}

interface AudioTimelineProps {
  markers: DeceptionMarker[];
}

export function AudioTimeline({ markers }: AudioTimelineProps) {
  const [hoveredMarker, setHoveredMarker] = useState<DeceptionMarker | null>(null);

  if (!markers.length) return null;

  return (
    <div className="rounded-xl overflow-hidden border border-neon-red/10 bg-surface-1 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-white/[0.04] bg-neon-red/[0.03]">
        <div className="flex items-center gap-2 text-[11px] font-semibold text-neon-red">
          <Mic size={13} />
          Earnings Call Deception Heatmap
        </div>
        <div className="flex items-center gap-1 text-[10px] text-red-400 bg-red-500/10 px-2 py-0.5 rounded-full border border-red-500/15">
          <AlertTriangle size={10} />
          {markers.length} markers detected
        </div>
      </div>

      {/* Timeline */}
      <div className="p-3">
        <div className="relative">
          {/* Timeline bar background */}
          <div className="w-full h-3 bg-white/[0.04] rounded-full relative overflow-hidden">
            {/* Safe regions (green) */}
            <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/20 via-emerald-500/15 to-emerald-500/20 rounded-full" />

            {/* Deception marker regions (red) */}
            {markers.map((marker, idx) => (
              <div
                key={idx}
                className="absolute top-0 bottom-0 rounded-sm cursor-pointer transition-all hover:brightness-125"
                style={{
                  left: `${marker.start}%`,
                  width: `${marker.end - marker.start}%`,
                  background: 'linear-gradient(90deg, rgba(239, 68, 68, 0.7), rgba(239, 68, 68, 0.9))',
                  boxShadow: '0 0 8px rgba(239, 68, 68, 0.4)',
                }}
                onMouseEnter={() => setHoveredMarker(marker)}
                onMouseLeave={() => setHoveredMarker(null)}
              />
            ))}
          </div>

          {/* Tick marks */}
          <div className="flex justify-between mt-1.5 text-[9px] text-gray-600 font-mono">
            <span>0:00</span>
            <span>15:00</span>
            <span>30:00</span>
            <span>45:00</span>
            <span>60:00</span>
          </div>
        </div>

        {/* Tooltip / hover detail */}
        {hoveredMarker && (
          <div className="mt-2 p-2 rounded-lg bg-red-500/10 border border-red-500/20 text-[11px] text-red-300 flex items-start gap-2 animate-fade-in">
            <Info size={12} className="mt-0.5 flex-shrink-0" />
            <span>{hoveredMarker.label}</span>
          </div>
        )}
      </div>

      {/* Marker list */}
      <div className="border-t border-white/[0.04] px-3 py-2 space-y-1">
        {markers.map((m, idx) => (
          <div key={idx} className="flex items-center gap-2 text-[10px]">
            <span className="w-2 h-2 rounded-full bg-neon-red flex-shrink-0 shadow-neon-red" />
            <span className="text-gray-500 font-mono w-16 flex-shrink-0">
              {Math.floor(m.start * 0.6)}:00 - {Math.floor(m.end * 0.6)}:00
            </span>
            <span className="text-gray-400 truncate">{m.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
