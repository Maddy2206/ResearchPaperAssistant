"use client";

import { use, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import {
  createConversation,
  getPaper,
  listConversations,
  paperFileUrl,
  usePaperIngestStream,
  useAsync,
} from "@/lib/api";
import type { PdfViewerHandle } from "@/components/pdf/pdf-viewer";
import { ConversationSidebar } from "@/components/history/conversation-sidebar";
import { ChatPanel } from "@/components/chat/chat-panel";
import { Skeleton } from "@/components/ui/skeleton";
import { Loader2 } from "lucide-react";

// pdfjs-dist touches browser-only globals (DOMMatrix) at module-evaluation
// time, which breaks Next.js SSR — load it client-only.
const PdfViewer = dynamic(
  () => import("@/components/pdf/pdf-viewer").then((m) => m.PdfViewer),
  { ssr: false }
);

export default function PaperWorkspacePage({ params }: { params: Promise<{ id: string }> }) {
  const { id: paperId } = use(params);
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeConversationId = searchParams.get("c");

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

  const { data: conversations, reload: reloadConversations } = useAsync(
    () => (paper?.status === "ready" ? listConversations(paperId) : Promise.resolve([])),
    [paperId, paper?.status]
  );

  useEffect(() => {
    if (paper?.status === "ready" && conversations && conversations.length === 0) {
      createConversation(paperId).then((c) => {
        reloadConversations();
        router.replace(`/papers/${paperId}?c=${c.id}`);
      });
    }
  }, [paper?.status, conversations, paperId, reloadConversations, router]);

  useEffect(() => {
    if (paper?.status === "ready" && conversations && conversations.length > 0 && !activeConversationId) {
      router.replace(`/papers/${paperId}?c=${conversations[0].id}`);
    }
  }, [paper?.status, conversations, activeConversationId, paperId, router]);

  const pdfViewerRef = useRef<PdfViewerHandle>(null);

  async function handleCreateConversation() {
    try {
      const c = await createConversation(paperId);
      await reloadConversations();
      router.push(`/papers/${paperId}?c=${c.id}`);
    } catch {
      toast.error("Failed to create conversation");
    }
  }

  if (paperLoading || !paper) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (paper.status === "failed") {
    return (
      <div className="flex flex-1 items-center justify-center px-6 text-center">
        <p className="text-sm text-destructive">
          Failed to process this paper{paper.error_message ? `: ${paper.error_message}` : "."}
        </p>
      </div>
    );
  }

  if (notReady) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
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
    <div className="flex flex-1 overflow-hidden">
      <div className="w-1/2 border-r">
        <PdfViewer ref={pdfViewerRef} fileUrl={paperFileUrl(paperId)} />
      </div>

      <ConversationSidebar
        conversations={conversations ?? []}
        activeId={activeConversationId}
        onSelect={(id) => router.push(`/papers/${paperId}?c=${id}`)}
        onCreate={handleCreateConversation}
      />

      <div className="flex-1">
        {activeConversationId ? (
          <ChatPanel
            key={activeConversationId}
            conversationId={activeConversationId}
            onCitationClick={(page) => pdfViewerRef.current?.scrollToPage(page)}
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <Loader2 className="size-5 animate-spin text-muted-foreground" />
          </div>
        )}
      </div>
    </div>
  );
}
