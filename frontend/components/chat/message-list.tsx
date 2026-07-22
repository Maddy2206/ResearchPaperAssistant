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
    <ScrollArea className="flex-1 px-4">
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
