"use client";

import { useState, useEffect } from "react";
import { Shield, TrendingUp, Network, Mic, FileCheck, Newspaper, Activity, MessageSquare } from "lucide-react";

const FINANCE_QUOTES = [
  "The stock market is a device for transferring money from the impatient to the patient. — Warren Buffett",
  "Risk comes from not knowing what you're doing. — Warren Buffett",
  "Buy when there's blood in the streets, even if the blood is your own. — Baron Rothschild",
  "The market is a pendulum that forever swings between unsustainable optimism and unjustified pessimism.",
  "In investing, what is comfortable is rarely profitable. — Robert Arnott",
  "The greatest enemy of a good decision is the illusion of complete certainty. — Preet Banaji",
  "Do not put all your eggs in one basket unless that basket is very carefully examined. — J.P. Morgan",
  "Money is a terrible master but an excellent servant. — P.T. Barnum",
  "The four most expensive words in investing: 'This time is different.' — Sir John Templeton",
  "Compound interest is the eighth wonder of the world. He who understands it, earns it. — Albert Einstein",
];

const CAPABILITIES = [
  {
    icon: <TrendingUp size={18} />,
    title: "Financial Agent",
    desc: "Balance sheet anomalies, cash flow divergence, related-party flags",
    color: "text-neon-cyan",
    bg: "bg-neon-cyan/5",
    border: "border-cyan-500/10",
  },
  {
    icon: <Network size={18} />,
    title: "Graph Agent",
    desc: "Neo4j circular trading loops and shell company networks",
    color: "text-neon-indigo",
    bg: "bg-neon-indigo/5",
    border: "border-indigo-500/10",
  },
  {
    icon: <FileCheck size={18} />,
    title: "Compliance Agent",
    desc: "SEBI LODR violations and regulatory RAG analysis",
    color: "text-neon-amber",
    bg: "bg-neon-amber/5",
    border: "border-amber-500/10",
  },
  {
    icon: <Mic size={18} />,
    title: "Audio Agent",
    desc: "Earnings call tone analysis and deception marker detection",
    color: "text-neon-red",
    bg: "bg-neon-red/5",
    border: "border-red-500/10",
  },
  {
    icon: <Newspaper size={18} />,
    title: "News Agent",
    desc: "Real-time news sentiment and crisis detection via Tavily",
    color: "text-neon-emerald",
    bg: "bg-neon-emerald/5",
    border: "border-emerald-500/10",
  },
];

export function WelcomeScreen({ mode }: { mode: "standard" | "sathyanishta" }) {
  const [currentQuoteIndex, setCurrentQuoteIndex] = useState(0);
  const [nifty, setNifty] = useState({ value: 0, change: 0, changePercent: 0 });
  const [sensex, setSensex] = useState({ value: 0, change: 0, changePercent: 0 });

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentQuoteIndex((prev) => (prev + 1) % FINANCE_QUOTES.length);
    }, 10000); // Change every 10 seconds

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Fetch Nifty and Sensex data from backend
    const fetchMarketData = async () => {
      try {
        console.log('Fetching market data from backend...');
        const response = await fetch('http://localhost:8000/api/market/indices');
        
        if (!response.ok) {
          console.error('API response error:', response.status, response.statusText);
          const text = await response.text();
          console.error('Response body:', text);
          return;
        }
        
        const data = await response.json();
        console.log('Backend market data response:', data);

        if (data.nifty && data.nifty.price) {
          console.log('Setting NIFTY:', data.nifty);
          setNifty({
            value: parseFloat(data.nifty.price) || 0,
            change: parseFloat(data.nifty.change) || 0,
            changePercent: parseFloat(data.nifty.changePercent) || 0,
          });
        } else {
          console.warn('No NIFTY data received');
        }

        if (data.sensex && data.sensex.price) {
          console.log('Setting SENSEX:', data.sensex);
          setSensex({
            value: parseFloat(data.sensex.price) || 0,
            change: parseFloat(data.sensex.change) || 0,
            changePercent: parseFloat(data.sensex.changePercent) || 0,
          });
        } else {
          console.warn('No SENSEX data received');
        }
      } catch (error) {
        console.error('Error fetching market data:', error);
      }
    };

    // Fetch immediately
    console.log('Initial fetch started');
    fetchMarketData();

    // Set up interval for every 10 minutes (600000 ms) to avoid rate limiting
    const interval = setInterval(fetchMarketData, 600000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="mt-12 flex flex-col items-center justify-center text-center animate-fade-in">
      {/* Animated Logo */}
      <div className="relative mb-6">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500/20 to-indigo-600/20 flex items-center justify-center border border-blue-500/20 animate-pulse-glow">
          <Activity size={36} className="text-blue-400 animate-float" />
        </div>
        {/* Decorative rings */}
        <div className="absolute inset-0 -m-3 rounded-2xl border border-blue-500/10 animate-pulse-glow" style={{ animationDelay: '0.5s' }} />
      </div>

      {/* Title */}
      <h1 className="mb-2 text-2xl font-bold tracking-tight">
        <span className="gradient-text">MarketChatGPT</span>{" "}
        <span className="text-blue-400/60 font-medium text-sm">by ET</span>
      </h1>
      <p className="max-w-lg text-sm text-gray-500 mb-8 leading-relaxed">
        Next-generation AI financial intelligence. Chat naturally about markets, or 
        enable <span className="text-neon-indigo font-semibold">SathyaNishta Mode</span> for deep forensic audits.
      </p>

      {/* Sathyanishta Mode Active Banner */}
      {mode === "sathyanishta" && (
        <div className="rounded-xl neon-border-indigo bg-neon-indigo/5 p-4 text-sm max-w-lg text-left mb-8 animate-slide-up">
          <div className="font-semibold text-neon-indigo mb-1.5 flex items-center gap-2 text-xs uppercase tracking-wide">
            <div className="relative">
              <Shield size={14} />
              <div className="absolute inset-0 animate-radar-ping rounded-full border border-neon-indigo" />
            </div>
            Deep Investigation Mode Active
          </div>
          <p className="text-indigo-200/70 text-xs leading-relaxed">
            Queries trigger full multi-agent investigation across Financial, Graph, Compliance,
            Audio, and News vectors with cross-validation and final synthesis verdict.
          </p>
        </div>
      )}

      {/* Capability Cards - Only show prominently in SathyaNishta mode */}
      {mode === "sathyanishta" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-w-2xl w-full animate-fade-in">
          {CAPABILITIES.map((cap, idx) => (
            <div
              key={cap.title}
              className={`glass-card glass-card-hover p-3.5 text-left animate-slide-up stagger-${idx + 1} ${cap.bg} border ${cap.border}`}
            >
              <div className={`${cap.color} mb-2`}>{cap.icon}</div>
              <div className="text-xs font-semibold text-gray-200 mb-1">{cap.title}</div>
              <div className="text-[11px] text-gray-500 leading-relaxed">{cap.desc}</div>
            </div>
          ))}
        </div>
      )}

      {mode === "standard" && (
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="flex items-center gap-2 text-xs text-gray-500 font-medium px-3 py-1.5 rounded-full bg-white/[0.03] border border-white/[0.05]">
            <MessageSquare size={12} className="text-blue-400" />
            Standard Market Intelligence Active
          </div>
          
          {/* Real-time Quotes Section */}
          <div className="max-w-2xl w-full mt-2 p-3 rounded-lg border border-white/[0.05] bg-white/[0.02] backdrop-blur-sm">
            <div className="min-h-12 flex items-center">
              <p className="text-sm text-gray-300 leading-relaxed italic animate-fade-in transition-all duration-500">
                "{FINANCE_QUOTES[currentQuoteIndex]}"
              </p>
            </div>
            <div className="flex justify-center gap-1 mt-4">
              {FINANCE_QUOTES.map((_, idx) => (
                <div
                  key={idx}
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    idx === currentQuoteIndex ? "bg-blue-400 w-3" : "bg-gray-600/40 w-1.5"
                  }`}
                />
              ))}
            </div>
          </div>

          {/* Market Indices Section */}
          <div className="grid grid-cols-2 gap-4 max-w-2xl w-full mt-3">
            {/* NIFTY 50 */}
            <div className="p-3 rounded-lg border border-white/[0.05] bg-white/[0.02] backdrop-blur-sm">
              <div className="text-[10px] text-gray-400 uppercase tracking-widest font-semibold mb-2">NIFTY 50</div>
              <div className="text-lg font-bold text-gray-100 mb-1">{nifty.value.toFixed(2)}</div>
              <div className={`text-xs font-semibold flex items-center gap-1 ${nifty.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                <span>{nifty.change >= 0 ? '↑' : '↓'} {Math.abs(nifty.change).toFixed(2)}</span>
                <span>({nifty.changePercent >= 0 ? '+' : ''}{nifty.changePercent.toFixed(2)}%)</span>
              </div>
            </div>

            {/* SENSEX */}
            <div className="p-3 rounded-lg border border-white/[0.05] bg-white/[0.02] backdrop-blur-sm">
              <div className="text-[10px] text-gray-400 uppercase tracking-widest font-semibold mb-2">SENSEX</div>
              <div className="text-lg font-bold text-gray-100 mb-1">{sensex.value.toFixed(2)}</div>
              <div className={`text-xs font-semibold flex items-center gap-1 ${sensex.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                <span>{sensex.change >= 0 ? '↑' : '↓'} {Math.abs(sensex.change).toFixed(2)}</span>
                <span>({sensex.changePercent >= 0 ? '+' : ''}{sensex.changePercent.toFixed(2)}%)</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
