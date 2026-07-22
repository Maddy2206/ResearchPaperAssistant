import { Badge } from "@/components/ui/badge";
import { AGENT_LABELS, type AgentKey } from "@/lib/types";
import { cn } from "@/lib/utils";

const AGENT_COLORS: Record<AgentKey, string> = {
  research_analysis: "bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30",
  math_algorithm: "bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/30",
  results_critique: "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30",
  paper_to_code: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
  architecture_flowchart: "bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30",
  general_qa: "bg-muted text-muted-foreground border-border",
};

export function AgentBadge({ agent }: { agent: AgentKey }) {
  return (
    <Badge variant="outline" className={cn("font-medium", AGENT_COLORS[agent])}>
      {AGENT_LABELS[agent]}
    </Badge>
  );
}
