"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AGENT_LABELS, type AgentKey } from "@/lib/types";

const AGENT_ORDER: AgentKey[] = [
  "research_analysis",
  "math_algorithm",
  "results_critique",
  "paper_to_code",
  "architecture_flowchart",
  "general_qa",
];

export function AgentTabs({
  value,
  onValueChange,
}: {
  value: AgentKey;
  onValueChange: (agent: AgentKey) => void;
}) {
  return (
    <Tabs
      value={value}
      onValueChange={(v) => onValueChange(v as AgentKey)}
      className="w-full"
    >
      <TabsList className="h-auto w-full flex-wrap justify-start gap-1 bg-transparent p-1">
        {AGENT_ORDER.map((agent) => (
          <TabsTrigger key={agent} value={agent} className="flex-none">
            {AGENT_LABELS[agent]}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );
}
