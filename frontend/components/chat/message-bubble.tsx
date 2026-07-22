import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import type { AgentKey, Citation } from "@/lib/types";
import { MarkdownRenderer } from "./markdown-renderer";
import { AgentBadge } from "./agent-badge";
import { CitationBadge } from "./citation-badge";
import { StreamingCursor } from "./streaming-cursor";

export interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agentsUsed?: AgentKey[];
  citations?: Citation[];
  streaming?: boolean;
}

export function MessageBubble({
  message,
  onCitationClick,
}: {
  message: DisplayMessage;
  onCitationClick?: (pageNumber: number) => void;
}) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      <Avatar className="size-8 shrink-0">
        <AvatarFallback className={isUser ? "bg-primary text-primary-foreground" : "bg-muted"}>
          {isUser ? "You" : "AI"}
        </AvatarFallback>
      </Avatar>

      <div className={cn("flex max-w-[85%] flex-col gap-2", isUser && "items-end")}>
        {message.agentsUsed && message.agentsUsed.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {message.agentsUsed.map((agent) => (
              <AgentBadge key={agent} agent={agent} />
            ))}
          </div>
        )}

        <div
          className={cn(
            "rounded-2xl px-4 py-2.5",
            isUser ? "bg-primary text-primary-foreground" : "bg-muted"
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap text-sm">{message.content}</p>
          ) : (
            <>
              <MarkdownRenderer content={message.content} />
              {message.streaming && <StreamingCursor />}
            </>
          )}
        </div>

        {message.citations && message.citations.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {message.citations.map((c) => (
              <CitationBadge key={c.index} citation={c} onClick={onCitationClick} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
