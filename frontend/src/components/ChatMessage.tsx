import { User, Shield } from "lucide-react";
import ReactMarkdown from "react-markdown";

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex w-full gap-3.5 p-5 animate-slide-up ${
      isUser ? "" : "glass-card"
    }`}>
      {/* Avatar */}
      <div className="flex-shrink-0 mt-0.5">
        {isUser ? (
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-neon-indigo/30 to-purple-600/30 border border-neon-indigo/20">
            <User size={14} className="text-neon-indigo" />
          </div>
        ) : (
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-neon-emerald/30 to-cyan-600/30 border border-neon-emerald/20">
            <Shield size={14} className="text-neon-emerald" />
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 space-y-1 overflow-hidden min-w-0">
        <div className="font-semibold text-xs text-gray-400 uppercase tracking-wide">
          {isUser ? "You" : "Sathya Nishta"}
        </div>
        <div className="text-sm leading-relaxed text-gray-200 prose prose-invert prose-sm max-w-none">
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
              ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-1">{children}</ol>,
              li: ({ children }) => <li>{children}</li>,
              strong: ({ children }) => <strong className="font-bold text-white">{children}</strong>,
              em: ({ children }) => <em className="italic text-gray-300">{children}</em>,
              div: ({ children }) => <div className="mb-2 last:mb-0">{children}</div>,
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
