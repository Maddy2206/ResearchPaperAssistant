"use client";

import { useAsync } from "@/lib/api";
import { listPapers } from "@/lib/api";
import { PaperCard } from "./paper-card";
import { Skeleton } from "@/components/ui/skeleton";

export function PaperGrid() {
  const { data: papers, loading, reload } = useAsync(listPapers, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-32 rounded-xl" />
        ))}
      </div>
    );
  }

  if (!papers || papers.length === 0) {
    return (
      <p className="py-10 text-center text-sm text-muted-foreground">
        No papers uploaded yet. Upload one above to get started.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {papers.map((paper) => (
        <PaperCard key={paper.id} paper={paper} onDeleted={reload} />
      ))}
    </div>
  );
}
