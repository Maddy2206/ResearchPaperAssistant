export type PaperStatus = "uploaded" | "processing" | "ready" | "failed";

export interface Section {
  id: string;
  title: string;
  level: number;
  order_index: number;
  page_start: number | null;
  page_end: number | null;
}

export interface Paper {
  id: string;
  filename: string;
  original_filename: string;
  title: string | null;
  authors: string[] | null;
  abstract: string | null;
  num_pages: number | null;
  status: PaperStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaperDetail extends Paper {
  sections: Section[];
}

export type AgentKey =
  | "research_analysis"
  | "math_algorithm"
  | "results_critique"
  | "paper_to_code"
  | "architecture_flowchart"
  | "general_qa";

export const AGENT_LABELS: Record<AgentKey, string> = {
  research_analysis: "Research Analysis",
  math_algorithm: "Math & Algorithm",
  results_critique: "Results & Critique",
  paper_to_code: "Paper-to-Code",
  architecture_flowchart: "Architecture & Flowchart",
  general_qa: "General Q&A",
};

export interface Citation {
  index: number;
  chunk_id: string;
  page_number: number | null;
  section_title: string | null;
  content_type: string;
  snippet: string;
}

export type MessageRole = "user" | "assistant";

export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  agent_used: AgentKey[] | null;
  citations: Citation[] | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  paper_id: string;
  title: string;
  agent_key: AgentKey;
  created_at: string;
  updated_at: string;
}

export interface CreateMessageResponse {
  message_id: string;
  run_id: string;
}

// --- SSE event unions ---

export type IngestEvent =
  | { event: "parsing_started"; paper_id: string }
  | { event: "sections_extracted"; paper_id: string; count: number }
  | { event: "embedding_progress"; paper_id: string; done: number; total: number }
  | { event: "ingestion_completed"; paper_id: string }
  | { event: "ingestion_failed"; paper_id: string; error: string };

export type ChatEvent =
  | { event: "agent_started"; agent: AgentKey; run_id: string }
  | { event: "token"; agent: AgentKey; run_id: string; content: string }
  | { event: "agent_completed"; agent: AgentKey; run_id: string }
  | { event: "agent_failed"; agent: AgentKey; run_id: string; error: string }
  | {
      event: "message_completed";
      run_id: string;
      message_id: string;
      content: string;
      citations: Citation[];
      agents_used: AgentKey[];
    }
  | { event: "error"; run_id: string; error: string };
