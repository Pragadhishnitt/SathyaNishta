import { User, ShieldAlert } from "lucide-react";

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex w-full gap-4 p-6 ${isUser ? "" : "bg-[#171717] rounded-xl"}`}>
      <div className="flex-shrink-0 mt-1">
        {isUser ? (
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600">
            <User size={16} className="text-white" />
          </div>
        ) : (
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-600">
            <ShieldAlert size={16} className="text-white" />
          </div>
        )}
      </div>
      <div className="flex-1 space-y-2 overflow-hidden">
        <div className="font-semibold text-sm text-gray-300">
          {isUser ? "You" : "Sathya Nishta"}
        </div>
        <div className="prose prose-invert max-w-none text-sm leading-relaxed">
          {message.content}
        </div>
      </div>
    </div>
  );
}
