"use client";

import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble, type DisplayMessage } from "./message-bubble";

export function MessageList({
  messages,
  onCitationClick,
}: {
  messages: DisplayMessage[];
  onCitationClick?: (pageNumber: number) => void;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    // min-h-0 is required here: ScrollArea's Root has no overflow of its own
    // (the scrolling viewport is a child), so without it the flex item's
    // automatic min-height would stay content-based and it would refuse to
    // shrink, growing to fit all messages instead of scrolling internally.
    <ScrollArea className="min-h-0 flex-1 px-4">
      <div className="flex flex-col gap-5 py-4">
        {messages.length === 0 && (
          <p className="mt-10 text-center text-sm text-muted-foreground">
            Ask a question about this paper to get started.
          </p>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} onCitationClick={onCitationClick} />
        ))}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
