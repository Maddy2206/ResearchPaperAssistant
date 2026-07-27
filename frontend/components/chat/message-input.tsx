"use client";

import { useState, type KeyboardEvent } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Send, Square } from "lucide-react";

export function MessageInput({
  onSend,
  disabled,
  streaming,
  onStop,
}: {
  onSend: (content: string) => void;
  disabled?: boolean;
  streaming?: boolean;
  onStop?: () => void;
}) {
  const [value, setValue] = useState("");

  function submit() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="flex items-end gap-2 border-t p-3">
      <Textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about this paper's methodology, math, results, or architecture..."
        className="min-h-[44px] flex-1 resize-none"
        rows={1}
        disabled={disabled}
      />
      {streaming ? (
        <Button onClick={onStop} size="icon" variant="secondary">
          <Square className="size-3.5 fill-current" />
        </Button>
      ) : (
        <Button onClick={submit} disabled={disabled || !value.trim()} size="icon">
          <Send className="size-4" />
        </Button>
      )}
    </div>
  );
}
