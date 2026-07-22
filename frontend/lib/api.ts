"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type {
  AgentKey,
  ChatEvent,
  Citation,
  Conversation,
  CreateMessageResponse,
  IngestEvent,
  Message,
  Paper,
  PaperDetail,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// --- Papers ---

export function listPapers(): Promise<Paper[]> {
  return request<Paper[]>("/api/papers");
}

export function getPaper(paperId: string): Promise<PaperDetail> {
  return request<PaperDetail>(`/api/papers/${paperId}`);
}

export async function uploadPaper(file: File): Promise<Paper> {
  const formData = new FormData();
  formData.append("file", file);
  return request<Paper>("/api/papers", { method: "POST", body: formData });
}

export function deletePaper(paperId: string): Promise<{ deleted: boolean }> {
  return request(`/api/papers/${paperId}`, { method: "DELETE" });
}

export function paperFileUrl(paperId: string): string {
  return `${API_BASE}/api/papers/${paperId}/file`;
}

// --- Conversations ---

export function listConversations(paperId: string): Promise<Conversation[]> {
  return request<Conversation[]>(`/api/papers/${paperId}/conversations`);
}

export function createConversation(paperId: string, title = "New conversation"): Promise<Conversation> {
  return request<Conversation>(`/api/papers/${paperId}/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
}

export function deleteConversation(conversationId: string): Promise<{ deleted: boolean }> {
  return request(`/api/conversations/${conversationId}`, { method: "DELETE" });
}

export function listMessages(conversationId: string): Promise<Message[]> {
  return request<Message[]>(`/api/conversations/${conversationId}/messages`);
}

export function postMessage(conversationId: string, content: string): Promise<CreateMessageResponse> {
  return request<CreateMessageResponse>(`/api/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
}

// --- Streaming hooks ---

export function usePaperIngestStream(paperId: string | null) {
  const [status, setStatus] = useState<IngestEvent | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!paperId) return;
    setDone(false);
    const es = new EventSource(`${API_BASE}/api/papers/${paperId}/ingest/stream`);

    es.onmessage = (msg) => {
      const data = JSON.parse(msg.data) as IngestEvent;
      setStatus(data);
      if (data.event === "ingestion_completed" || data.event === "ingestion_failed") {
        setDone(true);
        es.close();
      }
    };
    es.onerror = () => {
      setDone(true);
      es.close();
    };

    return () => es.close();
  }, [paperId]);

  return { status, done };
}

interface ChatStreamState {
  content: string;
  streamingAgent: AgentKey | null;
  agentsUsed: AgentKey[];
  citations: Citation[];
  done: boolean;
  error: string | null;
}

export function useChatStream(conversationId: string | null, runId: string | null) {
  const [state, setState] = useState<ChatStreamState>({
    content: "",
    streamingAgent: null,
    agentsUsed: [],
    citations: [],
    done: false,
    error: null,
  });
  const contentRef = useRef("");

  useEffect(() => {
    if (!conversationId || !runId) return;
    contentRef.current = "";
    setState({ content: "", streamingAgent: null, agentsUsed: [], citations: [], done: false, error: null });

    const es = new EventSource(
      `${API_BASE}/api/conversations/${conversationId}/messages/${runId}/stream`
    );

    es.onmessage = (msg) => {
      const data = JSON.parse(msg.data) as ChatEvent;

      if (data.event === "agent_started") {
        setState((s) => ({ ...s, streamingAgent: data.agent }));
      } else if (data.event === "token") {
        contentRef.current += data.content;
        setState((s) => ({ ...s, content: contentRef.current }));
      } else if (data.event === "message_completed") {
        setState((s) => ({
          ...s,
          content: data.content,
          citations: data.citations,
          agentsUsed: data.agents_used,
          done: true,
        }));
        es.close();
      } else if (data.event === "error") {
        setState((s) => ({ ...s, error: data.error, done: true }));
        es.close();
      }
    };
    es.onerror = () => {
      setState((s) => ({ ...s, done: true }));
      es.close();
    };

    return () => es.close();
  }, [conversationId, runId]);

  return state;
}

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const reload = useCallback(() => {
    setLoading(true);
    fn()
      .then((d) => setData(d))
      .catch((e) => setError(e instanceof Error ? e : new Error(String(e))))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    reload();
  }, [reload]);

  return { data, loading, error, reload };
}
