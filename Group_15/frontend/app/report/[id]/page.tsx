"use client";

import { useEffect, useState, use } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import StreamingProgress from "@/components/StreamingProgress";
import FeatureTable from "@/components/FeatureTable";
import SourceCard from "@/components/SourceCard";

/* ─── Types ─────────────────────────────────────────────────────── */
interface ReportData {
  executive_summary: string;
  traffic_light: "green" | "amber" | "red";
  traffic_light_reason: string;
  sources_count: Record<string, number>;
  features: Array<{
    feature: string;
    rationale: string;
    priority: "high" | "medium" | "low";
    source_urls?: string[];
  }>;
  gap_analysis: string[];
  items_by_source: Record<string, any[]>;
  sentiment: { overall: string; by_source: Record<string, string> };
  competitive_landscape: string;
  market_signals: string[];
}

/* ─── Design tokens ──────────────────────────────────────────────── */
const TL_META = {
  green: {
    label:  "GREEN — GREAT OPPORTUNITY",
    pill:   "status-pill-green",
    dot:    "#3fb950",
    glow:   "0 0 12px rgba(63,185,80,0.4)",
    bg:     "rgba(35,134,54,0.18)",
    border: "rgba(63,185,80,0.35)",
    text:   "#3fb950",
    fill:   "linear-gradient(90deg,#2ea043,#3fb950)",
  },
  amber: {
    label:  "AMBER — PROCEED WITH CAUTION",
    pill:   "status-pill-amber",
    dot:    "#d29922",
    glow:   "0 0 12px rgba(210,153,34,0.4)",
    bg:     "rgba(187,128,9,0.18)",
    border: "rgba(210,153,34,0.35)",
    text:   "#d29922",
    fill:   "linear-gradient(90deg,#bb8009,#d29922)",
  },
  red: {
    label:  "RED — CROWDED MARKET",
    pill:   "status-pill-red",
    dot:    "#f85149",
    glow:   "0 0 12px rgba(248,81,73,0.4)",
    bg:     "rgba(248,81,73,0.16)",
    border: "rgba(248,81,73,0.35)",
    text:   "#f85149",
    fill:   "linear-gradient(90deg,#da3633,#f85149)",
  },
};

/* ─── SVG Icons ──────────────────────────────────────────────────── */
const ChartIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} style={{ width: 18, height: 18 }} aria-hidden="true">
    <rect x="3" y="12" width="4" height="9" rx="1" /><rect x="10" y="7" width="4" height="14" rx="1" /><rect x="17" y="3" width="4" height="18" rx="1" />
  </svg>
);
const ArrowLeftIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" style={{ width: 16, height: 16 }} aria-hidden="true">
    <path d="M19 12H5M12 5l-7 7 7 7" />
  </svg>
);
const DownloadIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" style={{ width: 15, height: 15 }} aria-hidden="true">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="7 10 12 15 17 10" />
    <line x1="12" y1="15" x2="12" y2="3" />
  </svg>
);
const BookmarkIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" style={{ width: 15, height: 15 }} aria-hidden="true">
    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
  </svg>
);

/* ─── Sub-components ─────────────────────────────────────────────── */
function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div data-report-card style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 16, padding: 20 }}>
      <h3 style={{ fontSize: 16, fontWeight: 800, color: "#f0f6fc", marginBottom: 14, fontFamily: "var(--font-display, system-ui)" }}>
        {title}
      </h3>
      {children}
    </div>
  );
}

function KpiCard({ label, value, sub, accent }: { label: string; value: React.ReactNode; sub?: string; accent?: string }) {
  return (
    <div style={{ background: "#0d1117", border: "1px solid #30363d", borderRadius: 14, padding: 16 }}>
      <p style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "#8b949e", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>
        {label}
      </p>
      <div style={{ fontSize: 24, fontWeight: 800, color: accent ?? "#f0f6fc", lineHeight: 1.2 }}>
        {value}
      </div>
      {sub && <p style={{ fontSize: 12, color: "#8b949e", marginTop: 4 }}>{sub}</p>}
    </div>
  );
}

/* ─── Page ───────────────────────────────────────────────────────── */
export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const searchParams = useSearchParams();
  const router = useRouter();
  const [currentNode, setCurrentNode] = useState("input");
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveToast, setSaveToast] = useState(false);
  const [tagline, setTagline] = useState<string | null>(null);
  const [summary, setSummary] = useState<string | null>(null);

  const handleDownload = () => {
    const prev = document.title;
    document.title = "IdeaScope-Report";
    window.print();
    document.title = prev;
  };

  const handleSave = () => {
    setSaveToast(true);
    setTimeout(() => setSaveToast(false), 3500);
  };

  useEffect(() => {
    const ideaDescription = searchParams.get("idea") || "";
    const audience        = searchParams.get("audience") || "";
    const productUrl      = searchParams.get("url") || "";

    if (!ideaDescription) { setError("No idea description provided"); setLoading(false); return; }

    // Fetch tagline in parallel — fire and forget alongside the main analysis
    fetch("http://localhost:8000/tagline", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idea_description: ideaDescription }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.tagline) setTagline(data.tagline);
        if (data.summary) setSummary(data.summary);
      })
      .catch(() => {});

    fetch("http://localhost:8000/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idea_description: ideaDescription, audience, product_url: productUrl }),
    })
      .then((res) => { if (!res.ok) throw new Error("Backend error"); return res.body; })
      .then((body) => {
        if (!body) throw new Error("No body");
        const reader  = body.getReader();
        const decoder = new TextDecoder();

        function processText({ done, value }: ReadableStreamReadResult<Uint8Array>): any {
          if (done) { setLoading(false); return; }
          const chunk = decoder.decode(value, { stream: true });
          for (const line of chunk.split("\n")) {
            if (!line.startsWith("data: ")) continue;
            const data = line.slice(6);
            if (data === "[DONE]") { setLoading(false); return; }
            try {
              const parsed = JSON.parse(data);
              setCurrentNode(parsed.node);
              if (parsed.node === "report" && parsed.update.report) {
                setReport(parsed.update.report);
              }
            } catch {}
          }
          return reader.read().then(processText);
        }
        return reader.read().then(processText);
      })
      .catch(() => { setError("Connection to backend failed"); setLoading(false); });
  }, [id, searchParams]);

  const dark: React.CSSProperties = {
    background: "var(--dark-bg, #0d1117)",
    color: "#c9d1d9",
    fontFamily: "var(--font-display, system-ui), sans-serif",
    minHeight: "100vh",
  };

  /* ── Error ── */
  if (error) {
    return (
      <div style={{ ...dark, display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
        <div style={{ textAlign: "center" }}>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: "#f0f6fc", marginBottom: 8 }}>Error</h1>
          <p style={{ color: "#8b949e" }}>{error}</p>
        </div>
      </div>
    );
  }

  const tl = report ? TL_META[report.traffic_light] : null;
  const totalItems = report
    ? Object.values(report.sources_count).reduce((s, n) => s + n, 0)
    : 0;

  return (
    <div style={dark}>
      {/* ── Header ── */}
      <div className="no-print" style={{ borderBottom: "1px solid rgba(255,255,255,0.07)", padding: "10px 20px", display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ width: 28, height: 28, borderRadius: 8, background: "linear-gradient(135deg,#3b82f6,#22d3ee)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <ChartIcon />
          </div>
          <span style={{ fontSize: 14, fontWeight: 700, color: "#f0f6fc", letterSpacing: "-0.01em" }}>IdeaScope</span>
        </div>

        {/* Pipeline progress (during loading) */}
        {loading && (
          <div style={{ flex: 1, overflow: "hidden" }}>
            <StreamingProgress currentNode={currentNode} />
          </div>
        )}
        {!loading && report && (
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "#8b949e", letterSpacing: "0.06em", flex: 1 }}>
            ANALYSIS COMPLETE
          </span>
        )}
        {!loading && !report && <span style={{ flex: 1 }} />}

        {/* Action buttons */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
          {/* Back to Home */}
          <button
            onClick={() => router.push("/")}
            aria-label="Back to home"
            style={{
              display: "flex", alignItems: "center", gap: 6,
              padding: "7px 12px", borderRadius: 7, fontSize: 13, fontWeight: 500,
              background: "transparent", border: "1px solid rgba(255,255,255,0.12)",
              color: "#8b949e", cursor: "pointer", transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.25)"; (e.currentTarget as HTMLElement).style.color = "#c9d1d9"; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.12)"; (e.currentTarget as HTMLElement).style.color = "#8b949e"; }}
          >
            <ArrowLeftIcon /> Home
          </button>

          {/* Save (stub) */}
          {report && (
            <button
              onClick={handleSave}
              aria-label="Save report to profile"
              style={{
                display: "flex", alignItems: "center", gap: 6,
                padding: "7px 12px", borderRadius: 7, fontSize: 13, fontWeight: 500,
                background: "transparent", border: "1px solid rgba(255,255,255,0.12)",
                color: "#8b949e", cursor: "pointer", transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(139,92,246,0.5)"; (e.currentTarget as HTMLElement).style.color = "#a78bfa"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.12)"; (e.currentTarget as HTMLElement).style.color = "#8b949e"; }}
            >
              <BookmarkIcon /> Save
            </button>
          )}

          {/* Download PDF */}
          {report && (
            <button
              onClick={handleDownload}
              aria-label="Download report as PDF"
              style={{
                display: "flex", alignItems: "center", gap: 6,
                padding: "7px 14px", borderRadius: 7, fontSize: 13, fontWeight: 600,
                background: "linear-gradient(135deg,#3b82f6,#22d3ee)",
                border: "none", color: "#fff", cursor: "pointer",
                transition: "opacity 0.15s ease",
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.opacity = "0.88"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.opacity = "1"; }}
            >
              <DownloadIcon /> Download PDF
            </button>
          )}
        </div>
      </div>

      {/* Save toast */}
      {saveToast && (
        <div
          role="status"
          aria-live="polite"
          style={{
            position: "fixed", bottom: 24, right: 24, zIndex: 1000,
            padding: "12px 18px", borderRadius: 10,
            background: "#161b22", border: "1px solid rgba(167,139,250,0.35)",
            color: "#a78bfa", fontSize: 13, fontWeight: 500,
            display: "flex", alignItems: "center", gap: 8,
            boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
            animation: "fadeInUp 0.25s ease both",
          }}
        >
          <BookmarkIcon />
          Save to profile coming soon — stay tuned!
        </div>
      )}

      <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px 20px 64px" }}>
        {/* ── Loading skeleton ── */}
        {loading && !report && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16, paddingTop: 32 }}>
            {[240, 160, 200, 180].map((h, i) => (
              <div key={i} style={{ height: h, background: "#161b22", borderRadius: 16, border: "1px solid #30363d", animation: "fadeIn 0.4s ease both", animationDelay: `${i * 0.08}s`, position: "relative", overflow: "hidden" }}>
                <div style={{ position: "absolute", inset: 0, background: "linear-gradient(90deg,transparent 0%,rgba(255,255,255,0.03) 50%,transparent 100%)", backgroundSize: "200% 100%", animation: "shimmer 1.8s linear infinite" }} />
              </div>
            ))}
          </div>
        )}

        {/* ── Full report ── */}
        {report && tl && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20, animation: "fadeInUp 0.5s ease both" }}>

            {/* ── Hero card ── */}
            <div style={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 16, padding: 24 }}>
              {/* Title row */}
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 12, marginBottom: 8 }}>
                <div style={{ flex: 1 }}>
                  {/* Tagline heading */}
                  {tagline ? (
                    <h1 style={{
                      margin: "0 0 10px 0",
                      animation: "fadeIn 0.4s ease both",
                    }}>
                      <span style={{
                        display: "block",
                        fontSize: 13,
                        fontWeight: 500,
                        letterSpacing: "0.06em",
                        textTransform: "uppercase",
                        color: "#8b949e",
                        fontFamily: "var(--font-mono)",
                        marginBottom: 4,
                      }}>
                        Product Intelligence Report
                      </span>
                      <span style={{
                        display: "block",
                        fontSize: 26,
                        fontWeight: 800,
                        letterSpacing: "-0.025em",
                        lineHeight: 1.15,
                        background: "linear-gradient(90deg, #22d3ee, #3b82f6)",
                        WebkitBackgroundClip: "text",
                        WebkitTextFillColor: "transparent",
                        backgroundClip: "text",
                      }}>
                        {tagline}
                      </span>
                    </h1>
                  ) : (
                    <div style={{
                      height: 32,
                      width: 260,
                      borderRadius: 6,
                      backgroundImage: "linear-gradient(90deg,#21262d 0%,#30363d 50%,#21262d 100%)",
                      backgroundSize: "200% 100%",
                      animation: "shimmer 1.8s linear infinite",
                      marginBottom: 10,
                    }} />
                  )}

                  {/* 2-sentence summary */}
                  {summary ? (
                    <p style={{
                      fontSize: 14,
                      lineHeight: 1.7,
                      color: "#8b949e",
                      margin: 0,
                      maxWidth: 560,
                      animation: "fadeIn 0.5s ease both",
                      animationDelay: "0.1s",
                    }}>
                      {summary}
                    </p>
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      {[100, 90, 75].map((w, i) => (
                        <div key={i} style={{
                          height: 11,
                          width: `${w}%`,
                          maxWidth: 420,
                          borderRadius: 4,
                          backgroundImage: "linear-gradient(90deg,#21262d 0%,#30363d 50%,#21262d 100%)",
                          backgroundSize: "200% 100%",
                          animation: "shimmer 1.8s linear infinite",
                          animationDelay: `${i * 0.1}s`,
                        }} />
                      ))}
                    </div>
                  )}

                  <p style={{ fontSize: 11, color: "#484f58", margin: "10px 0 0 0", fontFamily: "var(--font-mono)", letterSpacing: "0.06em", textTransform: "uppercase" }}>
                    Multi-Source Analysis · AI Layer · IdeaScope
                  </p>
                </div>
                {/* Status pill */}
                <div style={{ padding: "8px 14px", borderRadius: 999, fontSize: 13, fontWeight: 800, letterSpacing: "0.04em", background: tl.bg, color: tl.text, border: `1px solid ${tl.border}`, fontFamily: "var(--font-mono)", flexShrink: 0 }}>
                  <span style={{ marginRight: 6 }}>●</span>
                  {tl.label}
                </div>
              </div>

              <div style={{ height: 1, background: "#30363d", margin: "16px 0" }} />

              {/* KPI grid */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
                <KpiCard
                  label="Verdict"
                  value={<span style={{ fontSize: 20 }}>● {report.traffic_light.toUpperCase()}</span>}
                  sub={tl.label}
                  accent={tl.text}
                />
                <KpiCard
                  label="Items Analyzed"
                  value={totalItems}
                  sub={`across ${Object.keys(report.sources_count).length} sources`}
                />
                <KpiCard
                  label="Gaps Identified"
                  value={report.gap_analysis.length}
                  sub={`${report.features.length} feature suggestions`}
                />
              </div>

              {/* Mini bars per source */}
              <div style={{ marginTop: 20 }}>
                <p style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "#8b949e", letterSpacing: "0.08em", marginBottom: 10, textTransform: "uppercase" }}>
                  Source Coverage
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {Object.entries(report.sources_count).map(([src, count]) => {
                    const SOURCE_LABELS: Record<string, string> = {
                      github:   "GitHub",
                      reddit:   "Reddit",
                      hn:       "Hacker News",
                      ph:       "Product Hunt",
                      yc:       "Y Combinator",
                      ai4that:  "AI For That",
                    };
                    const label = SOURCE_LABELS[src.toLowerCase()] ?? src;
                    const maxCount = Math.max(...Object.values(report.sources_count), 1);
                    const pct = Math.max(5, (count / maxCount) * 100);
                    const avg = report.items_by_source[src]
                      ? report.items_by_source[src].reduce((s, i) => s + i.relevance_score, 0) / (report.items_by_source[src].length || 1)
                      : 0;
                    const fill = avg >= 0.7 ? "linear-gradient(90deg,#2ea043,#3fb950)" : avg >= 0.4 ? "linear-gradient(90deg,#bb8009,#d29922)" : "linear-gradient(90deg,#da3633,#f85149)";
                    return (
                      <div key={src} style={{ display: "grid", gridTemplateColumns: "140px 1fr 48px", gap: 10, alignItems: "center" }}>
                        <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "#c9d1d9", fontWeight: 600 }}>{label}</span>
                        <div style={{ height: 8, background: "#21262d", borderRadius: 999, overflow: "hidden", border: "1px solid #30363d" }}>
                          <div style={{ height: "100%", width: `${pct}%`, background: fill, borderRadius: 999 }} />
                        </div>
                        <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "#8b949e", textAlign: "right" }}>{count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* ── Competitive landscape + Executive Snapshot ── */}
            <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 16 }}>
              <SectionCard title="Competitive Landscape">
                <p style={{ fontSize: 15, lineHeight: 1.65, color: "#c9d1d9", margin: 0 }}>
                  {report.competitive_landscape}
                </p>
              </SectionCard>
              <SectionCard title="Executive Snapshot">
                <div style={{ display: "flex", alignItems: "flex-start", gap: 10, marginBottom: 12 }}>
                  <div style={{ width: 10, height: 10, borderRadius: "50%", background: tl.dot, boxShadow: tl.glow, marginTop: 4, flexShrink: 0 }} />
                  <p style={{ fontSize: 14, fontWeight: 700, color: tl.text, margin: 0, lineHeight: 1.4 }}>
                    {tl.label}
                  </p>
                </div>
                <p style={{ fontSize: 14, lineHeight: 1.65, color: "#8b949e", margin: 0 }}>
                  {report.traffic_light_reason}
                </p>
                <div style={{ marginTop: 12, height: 1, background: "#30363d" }} />
                <p style={{ fontSize: 13, color: "#8b949e", marginTop: 12, lineHeight: 1.6 }}>
                  <strong style={{ color: "#c9d1d9" }}>Overall sentiment:</strong>{" "}
                  {report.sentiment.overall}
                </p>
              </SectionCard>
            </div>

            {/* ── Gap Analysis ── */}
            <SectionCard title="Gap Analysis">
              <ol style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 10 }}>
                {report.gap_analysis.map((gap, idx) => (
                  <li key={idx} style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: 13, color: tl.text, fontWeight: 700, flexShrink: 0, minWidth: 24 }}>
                      {String(idx + 1).padStart(2, "0")}
                    </span>
                    <span style={{ fontSize: 14, color: "#c9d1d9", lineHeight: 1.6 }}>{gap}</span>
                  </li>
                ))}
              </ol>
            </SectionCard>

            {/* ── Features ── */}
            {report.features.length > 0 && (
              <SectionCard title="Suggested Features with Signal Strength">
                <FeatureTable features={report.features} />
              </SectionCard>
            )}

            {/* ── Sources ── */}
            <SectionCard title="Source Intelligence">
              {/* Header row labels */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 140px 80px 28px", gap: 12, padding: "0 16px 8px", marginBottom: 4 }}>
                {["Source", "Avg Relevance", "Score", ""].map((h) => (
                  <span key={h} style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "#8b949e", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                    {h}
                  </span>
                ))}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {Object.entries(report.items_by_source).map(([source, items]) => (
                  <SourceCard
                    key={source}
                    source={source}
                    items={items}
                    sentiment={report.sentiment.by_source[source] || "neutral"}
                  />
                ))}
              </div>
            </SectionCard>

            {/* ── Traffic Light Legend ── */}
            <SectionCard title="RED / AMBER / GREEN Interpretation">
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {(["green", "amber", "red"] as const).map((key) => {
                  const m = TL_META[key];
                  const descriptions: Record<string, string> = {
                    green: "Low competition with clear market gaps. Strong differentiation opportunity.",
                    amber: "Moderate competition exists. Some differentiation opportunities remain visible.",
                    red:   "Crowded market with limited differentiation potential. Rethink positioning.",
                  };
                  return (
                    <div key={key} style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                      <div style={{ width: 10, height: 10, borderRadius: "50%", background: m.dot, boxShadow: `0 0 8px ${m.dot}`, marginTop: 3, flexShrink: 0 }} />
                      <div>
                        <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 700, color: m.text, letterSpacing: "0.04em" }}>
                          {key.toUpperCase()}
                        </span>
                        <p style={{ fontSize: 13, color: "#8b949e", margin: "2px 0 0 0", lineHeight: 1.55 }}>
                          {descriptions[key]}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </SectionCard>

            {/* ── Market Signals ── */}
            {report.market_signals.length > 0 && (
              <SectionCard title="Market Signals">
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {report.market_signals.map((signal, idx) => (
                    <span
                      key={idx}
                      style={{
                        padding: "5px 12px",
                        borderRadius: 6,
                        fontSize: 12,
                        fontFamily: "var(--font-mono)",
                        color: "#c9d1d9",
                        background: "#0d1117",
                        border: "1px solid #30363d",
                        letterSpacing: "0.02em",
                      }}
                    >
                      {signal}
                    </span>
                  ))}
                </div>
              </SectionCard>
            )}

            {/* ── Footer note ── */}
            <p style={{ fontSize: 12, color: "#8b949e", textAlign: "center", marginTop: 8, lineHeight: 1.6 }}>
              This report is a strategic screening layer, not legal or investment advice.
              It is designed to quickly surface market signals and differentiation opportunities.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
