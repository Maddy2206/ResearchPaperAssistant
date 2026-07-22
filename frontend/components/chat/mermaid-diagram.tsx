"use client";

import { useEffect, useId, useRef, useState } from "react";
import mermaid from "mermaid";
import { Button } from "@/components/ui/button";
import { Download, Copy, Image as ImageIcon } from "lucide-react";

let initialized = false;
function ensureInitialized() {
  if (initialized) return;
  mermaid.initialize({ startOnLoad: false, theme: "neutral", securityLevel: "loose" });
  initialized = true;
}

// LLM-generated Mermaid source occasionally has small, mechanical syntax
// mistakes. Fix the common ones rather than showing a raw parse error.
function sanitizeMermaidSource(source: string): string {
  return source
    // `-->|label|>` / `-->|label|-->` — stray trailing arrow after a pipe label.
    .replace(/(\|[^|\n]*\|)\s*-*>+/g, "$1")
    .trim();
}

export function MermaidDiagram({ source }: { source: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const id = useId().replace(/:/g, "-");

  useEffect(() => {
    ensureInitialized();
    let cancelled = false;
    mermaid
      .render(`mermaid-${id}`, sanitizeMermaidSource(source))
      .then(({ svg }) => {
        if (!cancelled) setSvg(svg);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
    };
  }, [source, id]);

  function downloadSvg() {
    if (!svg) return;
    const blob = new Blob([svg], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "diagram.svg";
    a.click();
    URL.revokeObjectURL(url);
  }

  function downloadPng() {
    if (!svg || !containerRef.current) return;
    const svgEl = containerRef.current.querySelector("svg");
    if (!svgEl) return;
    const svgData = new XMLSerializer().serializeToString(svgEl);
    const img = new Image();
    const svgBlob = new Blob([svgData], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);

    img.onload = () => {
      const canvas = document.createElement("canvas");
      const bbox = svgEl.getBoundingClientRect();
      canvas.width = bbox.width * 2;
      canvas.height = bbox.height * 2;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.fillStyle = "white";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.scale(2, 2);
      ctx.drawImage(img, 0, 0);
      URL.revokeObjectURL(url);
      canvas.toBlob((blob) => {
        if (!blob) return;
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "diagram.png";
        a.click();
      });
    };
    img.src = url;
  }

  function copySource() {
    navigator.clipboard.writeText(source);
  }

  if (error) {
    return (
      <pre className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive overflow-x-auto">
        Failed to render diagram: {error}
        {"\n\n"}
        {source}
      </pre>
    );
  }

  return (
    <div className="my-2 rounded-lg border bg-card">
      <div
        ref={containerRef}
        className="overflow-x-auto p-4"
        dangerouslySetInnerHTML={svg ? { __html: svg } : undefined}
      />
      <div className="flex items-center gap-2 border-t px-3 py-2">
        <Button variant="ghost" size="sm" onClick={downloadSvg} disabled={!svg}>
          <Download className="mr-1 size-3.5" /> SVG
        </Button>
        <Button variant="ghost" size="sm" onClick={downloadPng} disabled={!svg}>
          <ImageIcon className="mr-1 size-3.5" /> PNG
        </Button>
        <Button variant="ghost" size="sm" onClick={copySource}>
          <Copy className="mr-1 size-3.5" /> Copy source
        </Button>
      </div>
    </div>
  );
}
