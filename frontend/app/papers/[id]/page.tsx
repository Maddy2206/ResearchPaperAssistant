"use client";

import { use, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import {
  deletePaper,
  getOrCreateAgentConversation,
  getPaper,
  paperFileUrl,
  usePaperIngestStream,
  useAsync,
} from "@/lib/api";
import type { PdfViewerHandle } from "@/components/pdf/pdf-viewer";
import { AgentTabs } from "@/components/chat/agent-tabs";
import { ChatPanel } from "@/components/chat/chat-panel";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Loader2, ArrowLeft, Trash2 } from "lucide-react";
import type { AgentKey } from "@/lib/types";

// pdfjs-dist touches browser-only globals (DOMMatrix) at module-evaluation
// time, which breaks Next.js SSR — load it client-only.
const PdfViewer = dynamic(
  () => import("@/components/pdf/pdf-viewer").then((m) => m.PdfViewer),
  { ssr: false }
);

const DEFAULT_AGENT: AgentKey = "research_analysis";

export default function PaperWorkspacePage({ params }: { params: Promise<{ id: string }> }) {
  const { id: paperId } = use(params);
  const router = useRouter();
  const searchParams = useSearchParams();
  const selectedAgent = (searchParams.get("agent") as AgentKey | null) ?? DEFAULT_AGENT;

  const { data: paper, loading: paperLoading, reload: reloadPaper } = useAsync(
    () => getPaper(paperId),
    [paperId]
  );

  const notReady = paper && paper.status !== "ready" && paper.status !== "failed";
  const ingest = usePaperIngestStream(notReady ? paperId : null);

  useEffect(() => {
    if (ingest.done) reloadPaper();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ingest.done]);

  const { data: conversation } = useAsync(
    () =>
      paper?.status === "ready"
        ? getOrCreateAgentConversation(paperId, selectedAgent)
        : Promise.resolve(null),
    [paperId, paper?.status, selectedAgent]
  );

  const pdfViewerRef = useRef<PdfViewerHandle>(null);

  function handleSelectAgent(agent: AgentKey) {
    router.push(`/papers/${paperId}?agent=${agent}`);
  }

  async function handleDelete() {
    try {
      await deletePaper(paperId);
      router.push("/");
    } catch {
      toast.error("Failed to delete paper");
    }
  }

  if (paperLoading || !paper) {
    return (
      <div className="flex h-dvh items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (paper.status === "failed") {
    return (
      <div className="flex h-dvh items-center justify-center px-6 text-center">
        <p className="text-sm text-destructive">
          Failed to process this paper{paper.error_message ? `: ${paper.error_message}` : "."}
        </p>
      </div>
    );
  }

  if (notReady) {
    return (
      <div className="flex h-dvh flex-col items-center justify-center gap-3 px-6 text-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
        <p className="text-sm font-medium">Processing paper...</p>
        <p className="max-w-sm text-xs text-muted-foreground">
          {ingest.status?.event === "embedding_progress"
            ? `Embedding chunks: ${ingest.status.done}/${ingest.status.total}`
            : ingest.status?.event === "sections_extracted"
            ? `Extracted ${ingest.status.count} sections...`
            : "Parsing PDF and extracting structure..."}
        </p>
        <Skeleton className="h-2 w-64 rounded-full" />
      </div>
    );
  }

  return (
    <div className="flex h-dvh flex-col overflow-hidden">
      <header className="flex shrink-0 items-center gap-3 border-b px-4 py-2">
        <Link
          href="/"
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Library
        </Link>
        <span className="truncate text-sm font-medium">{paper.title || paper.original_filename}</span>

        <AlertDialog>
          <AlertDialogTrigger
            render={
              <Button
                variant="ghost"
                size="icon"
                className="ml-auto size-7 text-muted-foreground hover:text-destructive"
              >
                <Trash2 className="size-3.5" />
              </Button>
            }
          />
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete this paper?</AlertDialogTitle>
              <AlertDialogDescription>
                This permanently deletes &quot;{paper.title || paper.original_filename}&quot;,
                all its extracted chunks, and every conversation with it. This can&apos;t be
                undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                onClick={handleDelete}
              >
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </header>

      <div className="flex min-h-0 flex-1 overflow-hidden">
        <div className="min-h-0 w-1/2 border-r">
          <PdfViewer ref={pdfViewerRef} fileUrl={paperFileUrl(paperId)} />
        </div>

        <div className="flex min-h-0 flex-1 flex-col">
          <div className="shrink-0 border-b px-2 py-1.5">
            <AgentTabs value={selectedAgent} onValueChange={handleSelectAgent} />
          </div>

          <div className="min-h-0 flex-1">
            {conversation ? (
              <ChatPanel
                key={conversation.id}
                conversationId={conversation.id}
                onCitationClick={(page) => pdfViewerRef.current?.scrollToPage(page)}
              />
            ) : (
              <div className="flex h-full items-center justify-center">
                <Loader2 className="size-5 animate-spin text-muted-foreground" />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
