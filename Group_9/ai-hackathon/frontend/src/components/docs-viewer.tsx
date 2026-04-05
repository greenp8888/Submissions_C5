import { useEffect, useId, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import mermaid from "mermaid";

import { fetchProjectDoc } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const DOC_OPTIONS = [
  { value: "project-reference", label: "Project Reference" },
  { value: "architecture", label: "Architecture" },
  { value: "workflows", label: "Workflows" },
] as const;

const MarkdownRenderer = ReactMarkdown as any;

export function DocsViewer() {
  const [activeDoc, setActiveDoc] = useState<(typeof DOC_OPTIONS)[number]["value"]>("project-reference");
  const docQuery = useQuery({
    queryKey: ["project-doc", activeDoc],
    queryFn: () => fetchProjectDoc(activeDoc),
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Evaluation Docs</CardTitle>
          <CardDescription>Review the project reference, implemented architecture, components, workflows, and evaluation-facing documentation directly inside the product UI.</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeDoc} onValueChange={(value) => setActiveDoc(value as typeof activeDoc)}>
            <TabsList>
              {DOC_OPTIONS.map((item) => (
                <TabsTrigger key={item.value} value={item.value}>{item.label}</TabsTrigger>
              ))}
            </TabsList>
            {DOC_OPTIONS.map((item) => (
              <TabsContent key={item.value} value={item.value}>
                <div className="rounded-3xl border border-border bg-white/85 p-6">
                  {docQuery.isLoading ? (
                    <p className="text-sm text-muted-foreground">Loading {item.label.toLowerCase()}...</p>
                  ) : docQuery.data ? (
                    <div className="docs-markdown">
                      <MarkdownRenderer
                        components={{
                          code(props: { className?: string; children?: React.ReactNode }) {
                            const { className, children } = props;
                            const match = /language-(\w+)/.exec(className || "");
                            const code = String(children).replace(/\n$/, "");
                            if (match?.[1] === "mermaid") {
                              return <MermaidBlock chart={code} />;
                            }
                            return (
                              <code className="rounded bg-slate-100 px-1.5 py-0.5 text-[0.9em] text-amber-700">
                                {children}
                              </code>
                            );
                          },
                          pre(props: React.HTMLAttributes<HTMLPreElement>) {
                            return <pre className="overflow-auto rounded-2xl border border-border bg-slate-50 p-4 text-sm text-slate-700" {...props} />;
                          },
                          a(props: React.AnchorHTMLAttributes<HTMLAnchorElement>) {
                            return <a className="text-primary hover:text-primary/80" target="_blank" rel="noreferrer" {...props} />;
                          },
                        }}
                      >
                        {docQuery.data.content}
                      </MarkdownRenderer>
                    </div>
                  ) : (
                    <p className="text-sm text-rose-600">Document unavailable.</p>
                  )}
                </div>
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

function MermaidBlock({ chart }: { chart: string }) {
  const [svg, setSvg] = useState<string>("");
  const id = useId().replace(/:/g, "-");

  useEffect(() => {
    let active = true;
    mermaid.initialize({ startOnLoad: false, theme: "default" });
    mermaid.render(`mermaid-${id}`, chart).then((result: { svg: string }) => {
      if (active) {
        setSvg(result.svg);
      }
    }).catch(() => {
      if (active) {
        setSvg("");
      }
    });
    return () => {
      active = false;
    };
  }, [chart, id]);

  if (!svg) {
    return <pre className="overflow-auto rounded-2xl border border-border bg-slate-50 p-4 text-sm text-slate-700">{chart}</pre>;
  }

  return <div className="overflow-auto rounded-2xl border border-border bg-white p-4" dangerouslySetInnerHTML={{ __html: svg }} />;
}
