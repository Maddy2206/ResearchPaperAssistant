"use client";

import { useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
import { deletePaper } from "@/lib/api";
import type { Paper } from "@/lib/types";
import { FileText, Trash2, Loader2 } from "lucide-react";

const STATUS_VARIANT: Record<Paper["status"], { label: string; className: string }> = {
  uploaded: { label: "Queued", className: "bg-muted text-muted-foreground" },
  processing: { label: "Processing", className: "bg-amber-500/15 text-amber-600 dark:text-amber-400" },
  ready: { label: "Ready", className: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400" },
  failed: { label: "Failed", className: "bg-destructive/15 text-destructive" },
};

export function PaperCard({
  paper,
  onDeleted,
}: {
  paper: Paper;
  onDeleted?: () => void;
}) {
  const status = STATUS_VARIANT[paper.status];
  const [deleting, setDeleting] = useState(false);

  async function handleDelete() {
    setDeleting(true);
    try {
      await deletePaper(paper.id);
      onDeleted?.();
    } catch {
      toast.error("Failed to delete paper");
      setDeleting(false);
    }
  }

  return (
    <Card className="relative h-full transition-colors hover:bg-muted/50">
      <AlertDialog>
        <AlertDialogTrigger
          render={
            <Button
              variant="ghost"
              size="icon"
              className="absolute top-2 right-2 z-10 size-7 text-muted-foreground hover:text-destructive"
              onClick={(e) => e.preventDefault()}
            >
              {deleting ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : (
                <Trash2 className="size-3.5" />
              )}
            </Button>
          }
        />
        <AlertDialogContent onClick={(e) => e.preventDefault()}>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this paper?</AlertDialogTitle>
            <AlertDialogDescription>
              This permanently deletes &quot;{paper.title || paper.original_filename}&quot;,
              all its extracted chunks, and every conversation with it. This can&apos;t be undone.
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

      <Link href={`/papers/${paper.id}`}>
        <CardHeader className="flex-row items-start gap-3 space-y-0">
          <FileText className="mt-0.5 size-5 shrink-0 text-muted-foreground" />
          <div className="min-w-0 flex-1 pr-6">
            <CardTitle className="line-clamp-2 text-sm">
              {paper.title || paper.original_filename}
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <Badge variant="secondary" className={status.className}>
              {status.label}
            </Badge>
            {paper.num_pages && (
              <span className="text-xs text-muted-foreground">{paper.num_pages} pages</span>
            )}
          </div>
        </CardContent>
      </Link>
    </Card>
  );
}
