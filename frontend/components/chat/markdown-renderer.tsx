"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import "katex/dist/katex.min.css";
import { MermaidDiagram } from "./mermaid-diagram";

export function MarkdownRenderer({ content }: { content: string }) {
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          code(props) {
            const { children, className, ...rest } = props;
            const match = /language-(\w+)/.exec(className || "");
            const language = match?.[1];
            const codeText = String(children).replace(/\n$/, "");

            if (language === "mermaid") {
              return <MermaidDiagram source={codeText} />;
            }

            if (!language) {
              return (
                <code className={className} {...rest}>
                  {children}
                </code>
              );
            }

            return (
              <SyntaxHighlighter
                language={language}
                style={oneDark}
                PreTag="div"
                customStyle={{ borderRadius: "0.5rem", fontSize: "0.85rem" }}
              >
                {codeText}
              </SyntaxHighlighter>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
