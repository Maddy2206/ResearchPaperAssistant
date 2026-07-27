import { Button } from "@/components/ui/button";
import { AlertTriangle, X } from "lucide-react";

export function ErrorBanner({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss: () => void;
}) {
  return (
    <div className="flex items-start gap-2 border-b border-destructive/30 bg-destructive/10 px-4 py-2.5 text-sm text-destructive">
      <AlertTriangle className="mt-0.5 size-4 shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="font-medium">The agent couldn&apos;t respond</p>
        <p className="mt-0.5 text-xs text-destructive/80">
          {message || "Unknown error"} — check that your LLM provider is configured correctly
          (API key, rate limits) and try again.
        </p>
      </div>
      <Button
        variant="ghost"
        size="icon"
        className="size-6 shrink-0 text-destructive hover:bg-destructive/10 hover:text-destructive"
        onClick={onDismiss}
      >
        <X className="size-3.5" />
      </Button>
    </div>
  );
}
