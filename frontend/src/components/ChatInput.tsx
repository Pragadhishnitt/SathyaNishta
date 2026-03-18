import { ArrowUp, Sparkles } from "lucide-react";

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

  return (
    <div className="w-full max-w-3xl mx-auto px-6 pb-6 pt-2 bg-gradient-to-t from-[#0f0f0f] to-transparent sticky bottom-0">
      <form
        onSubmit={handleSubmit}
        className="relative flex flex-col w-full rounded-2xl border border-gray-700 bg-[#2f2f2f] shadow-xl overflow-hidden focus-within:ring-1 focus-within:ring-gray-500 transition-all"
      >
        <textarea
          name="query"
          placeholder="Ask a question or request an investigation..."
          className="w-full resize-none bg-transparent p-4 pr-12 outline-none text-white text-sm"
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
          <button
            type="button"
            onClick={onModeToggle}
            className={`flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold transition-colors ${
              mode === "sathyanishta"
                ? "bg-indigo-600/20 text-indigo-400 border border-indigo-600/40"
                : "bg-gray-800 text-gray-400 border border-gray-700 hover:bg-gray-700"
            }`}
          >
            <Sparkles size={14} className={mode === "sathyanishta" ? "text-indigo-400" : ""} />
            Sathyanishta Mode
          </button>

          <button
            type="submit"
            disabled={isLoading}
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-black transition-colors hover:bg-gray-200 disabled:opacity-50"
          >
            <ArrowUp size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}
