"use client";

import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import type { Citation } from "@/lib/types";

export function CitationBadge({
  citation,
  onClick,
}: {
  citation: Citation;
  onClick?: (pageNumber: number) => void;
}) {
  const clickable = citation.page_number != null && !!onClick;

  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <Badge
            variant="secondary"
            className={clickable ? "cursor-pointer hover:bg-secondary/70" : "cursor-default"}
            onClick={() => {
              if (clickable) onClick!(citation.page_number!);
            }}
          >
            [{citation.index}] {citation.section_title ?? "Untitled"}
            {citation.page_number ? ` · p.${citation.page_number}` : ""}
          </Badge>
        }
      />
      <TooltipContent className="max-w-xs text-xs">{citation.snippet}</TooltipContent>
    </Tooltip>
  );
}
