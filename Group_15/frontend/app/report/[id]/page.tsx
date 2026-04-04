"use client";

import { useEffect, useState, use } from "react";
import { useSearchParams } from "next/navigation";
import StreamingProgress from "@/components/StreamingProgress";
import TrafficLight from "@/components/TrafficLight";
import FeatureTable from "@/components/FeatureTable";
import SourceCard from "@/components/SourceCard";

interface ReportData {
  executive_summary: string;
  traffic_light: "green" | "amber" | "red";
  traffic_light_reason: string;
  sources_count: Record<string, number>;
  features: Array<{ feature: string; rationale: string; priority: "high" | "medium" | "low" }>;
  gap_analysis: string[];
  items_by_source: Record<string, any[]>;
  sentiment: {
    overall: string;
    by_source: Record<string, string>;
  };
  competitive_landscape: string;
  market_signals: string[];
}

export default function ReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const searchParams = useSearchParams();
  const [currentNode, setCurrentNode] = useState("input");
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ideaDescription = searchParams.get("idea") || "";
    const audience = searchParams.get("audience") || "";
    const productUrl = searchParams.get("url") || "";

    if (!ideaDescription) {
      setError("No idea description provided");
      setLoading(false);
      return;
    }

    const backendUrl = new URL("http://localhost:8000/analyze");

    fetch(backendUrl.toString(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        idea_description: ideaDescription,
        audience,
        product_url: productUrl,
      }),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to connect to backend");
        }
        return response.body;
      })
      .then((body) => {
        if (!body) {
          throw new Error("No response body");
        }

        const reader = body.getReader();
        const decoder = new TextDecoder();

        function processText({ done, value }: ReadableStreamReadResult<Uint8Array>): any {
          if (done) {
            setLoading(false);
            return;
          }

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6);

              if (data === "[DONE]") {
                setLoading(false);
                return;
              }

              try {
                const parsed = JSON.parse(data);
                setCurrentNode(parsed.node);

                if (parsed.node === "report" && parsed.update.report) {
                  setReport(parsed.update.report);
                }
              } catch (err) {
                console.error("Error parsing SSE data:", err);
              }
            }
          }

          return reader.read().then(processText);
        }

        return reader.read().then(processText);
      })
      .catch((err) => {
        console.error("Connection error:", err);
        setError("Connection to backend failed");
        setLoading(false);
      });
  }, [id, searchParams]);

  if (error) {
    return (
      <main className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center">
          <h1 className="font-serif text-3xl mb-4">Error</h1>
          <p className="text-muted">{error}</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="mb-8">
          <StreamingProgress currentNode={currentNode} />
        </div>

        {loading && !report && (
          <div className="text-center py-12">
            <div className="font-mono text-muted animate-pulse">Analyzing...</div>
          </div>
        )}

        {report && (
          <div className="space-y-12">
            <section>
              <div className="mb-6">
                <TrafficLight status={report.traffic_light} reason={report.traffic_light_reason} />
              </div>
              <p className="font-serif text-xl leading-relaxed">{report.competitive_landscape}</p>
            </section>

            <section>
              <h2 className="font-serif text-3xl mb-6">Gap Analysis</h2>
              <ol className="space-y-3">
                {report.gap_analysis.map((gap, idx) => (
                  <li key={idx} className="flex gap-4">
                    <span className="font-serif text-2xl text-muted">{idx + 1}.</span>
                    <span className="text-lg pt-1">{gap}</span>
                  </li>
                ))}
              </ol>
            </section>

            {report.features.length > 0 && (
              <section>
                <h2 className="font-serif text-3xl mb-6">Suggested Features</h2>
                <FeatureTable features={report.features} />
              </section>
            )}

            <section>
              <h2 className="font-serif text-3xl mb-6">Sources</h2>
              <div>
                {Object.entries(report.items_by_source).map(([source, items]) => (
                  <SourceCard
                    key={source}
                    source={source}
                    items={items}
                    sentiment={report.sentiment.by_source[source] || "neutral"}
                  />
                ))}
              </div>
            </section>

            {report.market_signals.length > 0 && (
              <section>
                <h2 className="font-serif text-3xl mb-6">Market Signals</h2>
                <div className="flex flex-wrap gap-2">
                  {report.market_signals.map((signal, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 border border-border font-mono text-xs"
                    >
                      {signal}
                    </span>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
