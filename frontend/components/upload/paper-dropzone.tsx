"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { uploadPaper } from "@/lib/api";
import { UploadCloud, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export function PaperDropzone() {
  const [uploading, setUploading] = useState(false);
  const router = useRouter();

  const onDrop = useCallback(
    async (accepted: File[]) => {
      const file = accepted[0];
      if (!file) return;
      setUploading(true);
      try {
        const paper = await uploadPaper(file);
        toast.success("Upload started — parsing paper...");
        router.push(`/papers/${paper.id}`);
      } catch {
        toast.error("Upload failed");
      } finally {
        setUploading(false);
      }
    },
    [router]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    multiple: false,
    disabled: uploading,
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-10 text-center transition-colors",
        isDragActive ? "border-primary bg-primary/5" : "border-border hover:bg-muted/50"
      )}
    >
      <input {...getInputProps()} />
      {uploading ? (
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      ) : (
        <UploadCloud className="size-8 text-muted-foreground" />
      )}
      <div>
        <p className="text-sm font-medium">
          {uploading ? "Uploading..." : "Drop a research paper PDF here, or click to browse"}
        </p>
        <p className="text-xs text-muted-foreground">PDF files only</p>
      </div>
    </div>
  );
}
