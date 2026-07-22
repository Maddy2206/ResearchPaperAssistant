import { PaperDropzone } from "@/components/upload/paper-dropzone";
import { PaperGrid } from "@/components/library/paper-grid";

export default function HomePage() {
  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-8 px-6 py-10">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Research Paper Assistant</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Upload a paper and chat with specialized agents for analysis, math, results, code, and
          architecture.
        </p>
      </div>

      <PaperDropzone />

      <div>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">Your papers</h2>
        <PaperGrid />
      </div>
    </main>
  );
}
