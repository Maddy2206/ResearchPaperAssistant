"use client";

import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { cancelMessage, listMessages, postMessage, useChatStream } from "@/lib/api";
import type { Message } from "@/lib/types";
import { MessageList } from "./message-list";
import { MessageInput } from "./message-input";
import { ErrorBanner } from "./error-banner";
import type { DisplayMessage } from "./message-bubble";

// How long to wait for the automatic kickoff analysis (fired server-side as
// soon as ingestion finishes) before giving up and showing the normal
// "ask a question" empty state.
const KICKOFF_POLL_INTERVAL_MS = 2000;
const KICKOFF_POLL_MAX_ATTEMPTS = 30;

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
  const [awaitingKickoff, setAwaitingKickoff] = useState(false);
  const [bannerError, setBannerError] = useState<string | null>(null);

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

  // A conversation may exist with zero messages because its automatic
  // kickoff analysis (fired when ingestion finished) is still running.
  // Poll briefly for it instead of showing the "ask a question" empty state.
  const attemptsRef = useRef(0);
  useEffect(() => {
    attemptsRef.current = 0;
    if (loading || messages.length > 0 || activeRunId) {
      setAwaitingKickoff(false);
      return;
    }
    setAwaitingKickoff(true);
    let cancelled = false;
    const interval = setInterval(async () => {
      attemptsRef.current += 1;
      try {
        const msgs = await listMessages(conversationId);
        if (cancelled) return;
        if (msgs.length > 0) {
          setMessages(msgs.map(toDisplay));
          setAwaitingKickoff(false);
          clearInterval(interval);
        } else if (attemptsRef.current >= KICKOFF_POLL_MAX_ATTEMPTS) {
          setAwaitingKickoff(false);
          clearInterval(interval);
        }
      } catch {
        // transient error; keep polling until max attempts
      }
    }, KICKOFF_POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId, loading, messages.length, activeRunId]);

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
      if (stream.error || stream.agentError) {
        setBannerError(stream.error || stream.agentError);
      }
      setActiveRunId(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stream.done]);

  async function handleSend(content: string) {
    setBannerError(null);
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

  async function handleStop() {
    if (!activeRunId) return;
    try {
      await cancelMessage(conversationId, activeRunId);
    } catch {
      toast.error("Failed to stop generation");
    }
  }

  const displayMessages = messages.map((m) =>
    m.id === `streaming-${activeRunId}`
      ? { ...m, content: stream.content, streaming: true }
      : m
  );

  return (
    <div className="flex h-full flex-col">
      {bannerError && (
        <ErrorBanner message={bannerError} onDismiss={() => setBannerError(null)} />
      )}
      {loading ? (
        <div className="flex-1" />
      ) : (
        <MessageList
          messages={displayMessages}
          onCitationClick={onCitationClick}
          emptyState={
            awaitingKickoff ? (
              <div className="mt-10 flex flex-col items-center gap-2 text-center text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" />
                Generating initial analysis...
              </div>
            ) : undefined
          }
        />
      )}
      <MessageInput
        onSend={handleSend}
        disabled={!!activeRunId}
        streaming={!!activeRunId}
        onStop={handleStop}
      />
    </div>
  );
}
