import { User, ShieldAlert } from "lucide-react";

export function WelcomeScreen({ mode }: { mode: "standard" | "sathyanishta" }) {
  return (
    <div className="mt-20 flex flex-col items-center justify-center text-center">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-white/10 ring-1 ring-white/20">
        <ShieldAlert size={32} className="text-white" />
      </div>
      <h1 className="mb-2 text-2xl font-semibold">
        Sathya Nishta <span className="text-gray-400">Investigator</span>
      </h1>
      <p className="max-w-md text-sm text-gray-400 mb-8">
        Your AI-powered forensic assistant. Drop in financial statements, transcripts, or query companies directly.
      </p>

      {mode === "sathyanishta" && (
        <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-4 text-sm max-w-lg text-left">
          <div className="font-semibold text-indigo-400 mb-2 flex items-center gap-2">
            <ShieldAlert size={16} /> Sathyanishta Mode is ON
          </div>
          <p className="text-indigo-200/80">
            Queries will now trigger full multi-agent investigations across financial, compliance, graph, and audio vectors before synthesizing a final verdict.
          </p>
        </div>
      )}
    </div>
  );
}
