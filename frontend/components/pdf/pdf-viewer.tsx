"use client";

import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from "lucide-react";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url
).toString();

export interface PdfViewerHandle {
  scrollToPage: (pageNumber: number) => void;
}

export const PdfViewer = forwardRef<PdfViewerHandle, { fileUrl: string }>(function PdfViewer(
  { fileUrl },
  ref
) {
  const [numPages, setNumPages] = useState<number>(0);
  const [scale, setScale] = useState(1.1);
  const [currentPage, setCurrentPage] = useState(1);
  const containerRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Record<number, HTMLDivElement | null>>({});

  useImperativeHandle(ref, () => ({
    scrollToPage(pageNumber: number) {
      const el = pageRefs.current[pageNumber];
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
        setCurrentPage(pageNumber);
      }
    },
  }));

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between gap-2 border-b px-3 py-2">
        <span className="text-xs text-muted-foreground">
          Page {currentPage} {numPages ? `of ${numPages}` : ""}
        </span>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" onClick={() => setScale((s) => Math.max(0.5, s - 0.15))}>
            <ZoomOut className="size-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setScale((s) => Math.min(2.5, s + 0.15))}>
            <ZoomIn className="size-4" />
          </Button>
        </div>
      </div>

      <div ref={containerRef} className="flex-1 overflow-y-auto bg-muted/30 p-4">
        <Document
          file={fileUrl}
          onLoadSuccess={({ numPages }) => setNumPages(numPages)}
          loading={<p className="text-sm text-muted-foreground">Loading PDF...</p>}
          error={<p className="text-sm text-destructive">Failed to load PDF.</p>}
        >
          {Array.from({ length: numPages }, (_, i) => i + 1).map((pageNumber) => (
            <div
              key={pageNumber}
              ref={(el) => {
                pageRefs.current[pageNumber] = el;
              }}
              className="mb-4 flex justify-center"
            >
              <Page pageNumber={pageNumber} scale={scale} />
            </div>
          ))}
        </Document>
      </div>
    </div>
  );
});
