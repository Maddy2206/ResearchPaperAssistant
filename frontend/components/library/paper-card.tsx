import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Paper } from "@/lib/types";
import { FileText } from "lucide-react";

const STATUS_VARIANT: Record<Paper["status"], { label: string; className: string }> = {
  uploaded: { label: "Queued", className: "bg-muted text-muted-foreground" },
  processing: { label: "Processing", className: "bg-amber-500/15 text-amber-600 dark:text-amber-400" },
  ready: { label: "Ready", className: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400" },
  failed: { label: "Failed", className: "bg-destructive/15 text-destructive" },
};

export function PaperCard({ paper }: { paper: Paper }) {
  const status = STATUS_VARIANT[paper.status];

  return (
    <Link href={`/papers/${paper.id}`}>
      <Card className="h-full transition-colors hover:bg-muted/50">
        <CardHeader className="flex-row items-start gap-3 space-y-0">
          <FileText className="mt-0.5 size-5 shrink-0 text-muted-foreground" />
          <div className="min-w-0 flex-1">
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
      </Card>
    </Link>
  );
}
