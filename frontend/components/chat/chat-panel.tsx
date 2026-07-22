"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { listMessages, postMessage, useChatStream } from "@/lib/api";
import type { Message } from "@/lib/types";
import { MessageList } from "./message-list";
import { MessageInput } from "./message-input";
import type { DisplayMessage } from "./message-bubble";

function toDisplay(m: Message): DisplayMessage {
  return {
    id: m.id,
    role: m.role,
    content: m.content,
    agentsUsed: m.agent_used ?? undefined,
    citations: m.citations ?? undefined,
  };
}

export function ChatPanel({
  conversationId,
  onCitationClick,
}: {
  conversationId: string;
  onCitationClick?: (pageNumber: number) => void;
}) {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const stream = useChatStream(conversationId, activeRunId);

  useEffect(() => {
    // Reset loading state when switching conversations, before fetching.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true);
    listMessages(conversationId)
      .then((msgs) => setMessages(msgs.map(toDisplay)))
      .catch(() => toast.error("Failed to load conversation history"))
      .finally(() => setLoading(false));
  }, [conversationId]);

  useEffect(() => {
    if (stream.done && activeRunId) {
      // Commit the finished stream into persisted message state.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setMessages((prev) => {
        const withoutPlaceholder = prev.filter((m) => m.id !== `streaming-${activeRunId}`);
        if (stream.error) {
          toast.error(`Agent error: ${stream.error}`);
          return withoutPlaceholder;
        }
        return [
          ...withoutPlaceholder,
          {
            id: `assistant-${activeRunId}`,
            role: "assistant",
            content: stream.content,
            agentsUsed: stream.agentsUsed,
            citations: stream.citations,
          },
        ];
      });
      setActiveRunId(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stream.done]);

  async function handleSend(content: string) {
    const userMsg: DisplayMessage = { id: `user-${Date.now()}`, role: "user", content };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const { run_id } = await postMessage(conversationId, content);
      setMessages((prev) => [
        ...prev,
        {
          id: `streaming-${run_id}`,
          role: "assistant",
          content: "",
          streaming: true,
        },
      ]);
      setActiveRunId(run_id);
    } catch {
      toast.error("Failed to send message");
    }
  }

  const displayMessages = messages.map((m) =>
    m.id === `streaming-${activeRunId}`
      ? { ...m, content: stream.content, streaming: true }
      : m
  );

  return (
    <div className="flex h-full flex-col">
      {loading ? (
        <div className="flex-1" />
      ) : (
        <MessageList messages={displayMessages} onCitationClick={onCitationClick} />
      )}
      <MessageInput onSend={handleSend} disabled={!!activeRunId} />
    </div>
  );
}
