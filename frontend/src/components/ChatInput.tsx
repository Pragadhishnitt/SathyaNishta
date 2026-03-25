import { ArrowUp, Sparkles, Loader2 } from "lucide-react";

interface ChatInputProps {
  mode: "standard" | "sathyanishta";
  onModeToggle: () => void;
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

export function ChatInput({ mode, onModeToggle, onSubmit, isLoading }: ChatInputProps) {
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    const query = data.get("query") as string;
    if (query && !isLoading) {
      onSubmit(query);
      e.currentTarget.reset();
    }
  };

  const isSathya = mode === "sathyanishta";

  return (
    <div className="w-full max-w-3xl mx-auto px-6 pb-5 pt-2 sticky bottom-0 z-10">
      {/* Gradient fade above */}
      <div className="absolute inset-x-0 -top-8 h-8 bg-gradient-to-t from-surface-0 to-transparent pointer-events-none" />

      <form
        onSubmit={handleSubmit}
        className={`relative flex flex-col w-full rounded-2xl glass-card overflow-hidden transition-all duration-300 ${
          isSathya
            ? "border-neon-indigo/50"
            : "border-white/[0.06] hover:border-white/10"
        }`}
      >
        <textarea
          name="query"
          placeholder={
            isSathya
              ? "Investigate a company — e.g., 'Investigate FraudCorp for circular trading'..."
              : "Ask a question or request an investigation..."
          }
          className="w-full resize-none bg-transparent p-4 pb-2 pr-12 outline-none text-white text-sm placeholder:text-gray-500"
          rows={1}
          autoFocus
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if (e.currentTarget.value.trim() && !isLoading) {
                onSubmit(e.currentTarget.value);
                e.currentTarget.value = "";
              }
            }
          }}
        />

        <div className="flex items-center justify-between p-3 pt-0">
          {/* Mode Toggle */}
          <button
            type="button"
            onClick={onModeToggle}
            className={`flex items-center gap-2 rounded-full px-3.5 py-1.5 text-[11px] font-semibold transition-all duration-300 ${
              isSathya
                ? "bg-neon-indigo/15 text-neon-indigo border border-neon-indigo/30"
                : "bg-white/[0.03] text-gray-500 border border-white/[0.06] hover:bg-white/[0.06] hover:text-gray-300"
            }`}
          >
            <Sparkles
              size={13}
              className={`transition-all duration-300 ${isSathya ? "text-neon-indigo" : ""}`}
            />
            {isSathya ? "SathyaNishta Mode" : "Market Insights"}
            {isSathya && (
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-neon-indigo" />
            )}
          </button>

          {/* Submit */}
          <button
            type="submit"
            disabled={isLoading}
            className={`flex h-8 w-8 items-center justify-center rounded-lg transition-all duration-200 ${
              isLoading
                ? "bg-neon-indigo/20 text-neon-indigo"
                : "bg-white text-black hover:bg-gray-200 hover:scale-105 active:scale-95"
            }`}
          >
            {isLoading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <ArrowUp size={16} />
            )}
          </button>
        </div>
      </form>

      {/* Subtle helper text */}
      <div className="text-center mt-2">
        <span className="text-[10px] text-gray-600">
          {isSathya ? "5 agents will analyze your query" : "Toggle Sathyanishta Mode for deep investigation"}
        </span>
      </div>
    </div>
  );
}
