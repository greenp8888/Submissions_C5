"use client";

import { useEffect, useState, use } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { REPORT_API_BASE } from "@/lib/backendUrl";
import StreamingProgress from "@/components/StreamingProgress";
import FeatureTable from "@/components/FeatureTable";
import SourceCard from "@/components/SourceCard";
import { SignalForgeHeaderBrand } from "@/components/SignalForgeLogo";
import { useAppTheme } from "@/lib/appTheme";

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
    <div data-report-card style={{ background: "var(--rp-card)", border: "1px solid var(--rp-border)", borderRadius: 16, padding: 20 }}>
      <h3 style={{ fontSize: 16, fontWeight: 800, color: "var(--rp-heading)", marginBottom: 14, fontFamily: "var(--font-display, system-ui)" }}>
        {title}
      </h3>
      {children}
    </div>
  );
}

function KpiCard({ label, value, sub, accent }: { label: string; value: React.ReactNode; sub?: string; accent?: string }) {
  const accentStyle = accent
    ? ({ ["--report-accent-color" as string]: accent } as React.CSSProperties)
    : undefined;
  return (
    <div data-report-kpi style={{ background: "var(--rp-inset)", border: "1px solid var(--rp-border)", borderRadius: 14, padding: 16 }}>
      <p style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--rp-muted)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>
        {label}
      </p>
      <div
        {...(accent ? { "data-report-accent": true } : {})}
        style={{
          fontSize: 24,
          fontWeight: 800,
          color: accent ?? "var(--rp-heading)",
          lineHeight: 1.2,
          ...accentStyle,
        }}
      >
        {value}
      </div>
      {sub && <p style={{ fontSize: 12, color: "var(--rp-muted)", marginTop: 4 }}>{sub}</p>}
    </div>
  );
}

/* ─── Page ───────────────────────────────────────────────────────── */
export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { isDark, setIsDark, mounted } = useAppTheme();
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
    document.title = "SignalForge-Report";
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
    fetch(`${REPORT_API_BASE}/tagline`, {
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

    fetch(`${REPORT_API_BASE}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idea_description: ideaDescription, audience, product_url: productUrl }),
    })
      .then(async (res) => {
        if (!res.ok) {
          let detail = res.statusText || "Unknown error";
          try {
            const text = await res.text();
            const j = JSON.parse(text) as {
              detail?: string | Array<{ msg?: string }>;
              message?: string;
            };
            if (typeof j.detail === "string") detail = j.detail;
            else if (Array.isArray(j.detail) && j.detail[0]?.msg) detail = String(j.detail[0].msg);
            else if (typeof j.message === "string") detail = j.message;
            else if (text) detail = text.slice(0, 200);
          } catch {
            /* use statusText */
          }
          throw new Error(`Backend returned ${res.status}: ${detail}`);
        }
        return res.body;
      })
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
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : String(err);
        const hint =
          msg.includes("Failed to fetch") || msg.includes("NetworkError") || msg.includes("Load failed")
            ? "Could not reach the Next.js app. If the app is up, start FastAPI: cd backend && uvicorn main:app --reload --port 8000 (optional: set BACKEND_URL in frontend/.env.local if it runs elsewhere)."
            : msg;
        setError(hint);
        setLoading(false);
      });
  }, [id, searchParams]);

  const pageShell: React.CSSProperties = {
    background: "var(--rp-bg)",
    color: "var(--rp-body)",
    fontFamily: "var(--font-display, system-ui), sans-serif",
    minHeight: "100vh",
  };

  const reportTheme = isDark ? "dark" : "light";

  /* ── Error ── */
  if (error) {
    return (
      <div data-report-page data-theme={reportTheme} style={{ ...pageShell, display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
        <div style={{ textAlign: "center" }}>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: "var(--rp-heading)", marginBottom: 8 }}>Error</h1>
          <p style={{ color: "var(--rp-muted)" }}>{error}</p>
        </div>
      </div>
    );
  }

  const tl = report ? TL_META[report.traffic_light] : null;
  const totalItems = report
    ? Object.values(report.sources_count).reduce((s, n) => s + n, 0)
    : 0;

  return (
    <div data-report-page data-theme={reportTheme} style={pageShell}>
      {/* ── Header ── */}
      <div className="no-print" style={{ borderBottom: "1px solid var(--rp-header-border)", padding: "10px 20px", display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        {/* Logo */}
        <SignalForgeHeaderBrand variant="compact" wordmarkColor="var(--rp-heading)" />

        {/* Pipeline progress (during loading) */}
        {loading && (
          <div style={{ flex: 1, overflow: "hidden" }}>
            <StreamingProgress currentNode={currentNode} />
          </div>
        )}
        {!loading && report && (
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--rp-muted)", letterSpacing: "0.06em", flex: 1 }}>
            ANALYSIS COMPLETE
          </span>
        )}
        {!loading && !report && <span style={{ flex: 1 }} />}

        {/* Action buttons */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0, flexWrap: "wrap" }}>
          {mounted && (
            <div
              className="no-print"
              role="group"
              aria-label="Theme"
              style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 600,
                    letterSpacing: "0.06em",
                    textTransform: "uppercase",
                    color: "var(--rp-muted)",
                    fontFamily: "var(--font-mono)",
                    whiteSpace: "nowrap",
                  }}
                >
                  Theme
                </span>
                <div
                  style={{
                    display: "flex",
                    borderRadius: 8,
                    border: "1px solid var(--rp-border)",
                    overflow: "hidden",
                    background: "var(--rp-inset)",
                  }}
                >
                  <button
                    type="button"
                    onClick={() => setIsDark(true)}
                    aria-pressed={isDark}
                    style={{
                      padding: "6px 12px",
                      fontSize: 12,
                      fontWeight: 600,
                      border: "none",
                      cursor: "pointer",
                      fontFamily: "var(--font-display, system-ui), sans-serif",
                      background: isDark ? "color-mix(in srgb, var(--accent-cyan) 18%, var(--rp-inset))" : "transparent",
                      color: isDark ? "var(--accent-cyan)" : "var(--rp-muted)",
                      boxShadow: isDark ? "inset 0 0 0 1px color-mix(in srgb, var(--accent-cyan) 35%, transparent)" : "none",
                    }}
                  >
                    Dark
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsDark(false)}
                    aria-pressed={!isDark}
                    style={{
                      padding: "6px 12px",
                      fontSize: 12,
                      fontWeight: 600,
                      border: "none",
                      borderLeft: "1px solid var(--rp-border)",
                      cursor: "pointer",
                      fontFamily: "var(--font-display, system-ui), sans-serif",
                      background: !isDark ? "color-mix(in srgb, var(--accent-cyan) 18%, var(--rp-inset))" : "transparent",
                      color: !isDark ? "var(--accent-cyan)" : "var(--rp-muted)",
                      boxShadow: !isDark ? "inset 0 0 0 1px color-mix(in srgb, var(--accent-cyan) 35%, transparent)" : "none",
                    }}
                  >
                    Light
                  </button>
                </div>
              </div>
              <span
                style={{
                  fontSize: 10,
                  color: "var(--rp-faint)",
                  fontFamily: "var(--font-mono)",
                  letterSpacing: "0.02em",
                  maxWidth: 200,
                  textAlign: "right",
                  lineHeight: 1.35,
                }}
              >
                Same as home — saved on this device
              </span>
            </div>
          )}

          {/* Back to Home */}
          <button
            type="button"
            onClick={() => router.push("/")}
            aria-label="Back to home"
            style={{
              display: "flex", alignItems: "center", gap: 6,
              padding: "7px 12px", borderRadius: 7, fontSize: 13, fontWeight: 500,
              background: "transparent", border: "1px solid var(--rp-btn-border)",
              color: "var(--rp-muted)", cursor: "pointer", transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "var(--rp-btn-border-hover)"; (e.currentTarget as HTMLElement).style.color = "var(--rp-body)"; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "var(--rp-btn-border)"; (e.currentTarget as HTMLElement).style.color = "var(--rp-muted)"; }}
          >
            <ArrowLeftIcon /> Home
          </button>

          {/* Save (stub) */}
          {report && (
            <button
              type="button"
              onClick={handleSave}
              aria-label="Save report to profile"
              style={{
                display: "flex", alignItems: "center", gap: 6,
                padding: "7px 12px", borderRadius: 7, fontSize: 13, fontWeight: 500,
                background: "transparent", border: "1px solid var(--rp-btn-border)",
                color: "var(--rp-muted)", cursor: "pointer", transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "rgba(139,92,246,0.5)"; (e.currentTarget as HTMLElement).style.color = "#a78bfa"; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "var(--rp-btn-border)"; (e.currentTarget as HTMLElement).style.color = "var(--rp-muted)"; }}
            >
              <BookmarkIcon /> Save
            </button>
          )}

          {/* Download PDF */}
          {report && (
            <button
              type="button"
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
            background: "var(--rp-toast-bg)", border: "1px solid rgba(167,139,250,0.35)",
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
              <div key={i} style={{ height: h, background: "var(--rp-card)", borderRadius: 16, border: "1px solid var(--rp-border)", animation: "fadeIn 0.4s ease both", animationDelay: `${i * 0.08}s`, position: "relative", overflow: "hidden" }}>
                <div style={{ position: "absolute", inset: 0, background: `linear-gradient(90deg,transparent 0%,var(--rp-skeleton-shimmer) 50%,transparent 100%)`, backgroundSize: "200% 100%", animation: "shimmer 1.8s linear infinite" }} />
              </div>
            ))}
          </div>
        )}

        {/* ── Full report ── */}
        {report && tl && (
          <div data-report-surface style={{ display: "flex", flexDirection: "column", gap: 20, animation: "fadeInUp 0.5s ease both" }}>

            {/* ── Hero card ── */}
            <div data-report-hero-card style={{ background: "var(--rp-card)", border: "1px solid var(--rp-border)", borderRadius: 16, padding: 24 }}>
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
                        color: "var(--rp-muted)",
                        fontFamily: "var(--font-mono)",
                        marginBottom: 4,
                      }}>
                        Product Intelligence Report
                      </span>
                      <span
                        data-report-headline
                        style={{
                        display: "block",
                        fontSize: 26,
                        fontWeight: 800,
                        letterSpacing: "-0.025em",
                        lineHeight: 1.15,
                        background: "linear-gradient(90deg, #22d3ee, #3b82f6)",
                        WebkitBackgroundClip: "text",
                        WebkitTextFillColor: "transparent",
                        backgroundClip: "text",
                      }}
                      >
                        {tagline}
                      </span>
                    </h1>
                  ) : (
                    <div style={{
                      height: 32,
                      width: 260,
                      borderRadius: 6,
                      backgroundImage: "linear-gradient(90deg,var(--rp-shimmer-a) 0%,var(--rp-shimmer-b) 50%,var(--rp-shimmer-a) 100%)",
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
                      color: "var(--rp-muted)",
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
                          backgroundImage: "linear-gradient(90deg,var(--rp-shimmer-a) 0%,var(--rp-shimmer-b) 50%,var(--rp-shimmer-a) 100%)",
                          backgroundSize: "200% 100%",
                          animation: "shimmer 1.8s linear infinite",
                          animationDelay: `${i * 0.1}s`,
                        }} />
                      ))}
                    </div>
                  )}

                  <p style={{ fontSize: 11, color: "var(--rp-faint)", margin: "10px 0 0 0", fontFamily: "var(--font-mono)", letterSpacing: "0.06em", textTransform: "uppercase" }}>
                    Multi-Source Analysis · AI Layer · SignalForge
                  </p>
                </div>
                {/* Status pill */}
                <div
                  data-report-accent={true}
                  style={{
                    padding: "8px 14px",
                    borderRadius: 999,
                    fontSize: 13,
                    fontWeight: 800,
                    letterSpacing: "0.04em",
                    background: tl.bg,
                    color: tl.text,
                    border: `1px solid ${tl.border}`,
                    fontFamily: "var(--font-mono)",
                    flexShrink: 0,
                    ["--report-accent-color" as string]: tl.text,
                  }}
                >
                  <span style={{ marginRight: 6 }}>●</span>
                  {tl.label}
                </div>
              </div>

              <div style={{ height: 1, background: "var(--rp-border)", margin: "16px 0" }} />

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
                <p style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--rp-muted)", letterSpacing: "0.08em", marginBottom: 10, textTransform: "uppercase" }}>
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
                        <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--rp-body)", fontWeight: 600 }}>{label}</span>
                        <div
                          data-report-bar-track=""
                          style={{ height: 8, background: "var(--rp-row)", borderRadius: 999, overflow: "hidden", border: "1px solid var(--rp-border)" }}
                        >
                          <div data-report-bar-fill="" style={{ height: "100%", width: `${pct}%`, background: fill, borderRadius: 999 }} />
                        </div>
                        <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--rp-muted)", textAlign: "right" }}>{count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* ── Competitive landscape + Executive Snapshot ── */}
            <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 16 }}>
              <SectionCard title="Competitive Landscape">
                <p style={{ fontSize: 15, lineHeight: 1.65, color: "var(--rp-body)", margin: 0 }}>
                  {report.competitive_landscape}
                </p>
              </SectionCard>
              <SectionCard title="Executive Snapshot">
                <div style={{ display: "flex", alignItems: "flex-start", gap: 10, marginBottom: 12 }}>
                  <div data-report-dot="" style={{ width: 10, height: 10, borderRadius: "50%", background: tl.dot, boxShadow: tl.glow, marginTop: 4, flexShrink: 0 }} />
                  <p
                    data-report-accent={true}
                    style={{
                      fontSize: 14,
                      fontWeight: 700,
                      color: tl.text,
                      margin: 0,
                      lineHeight: 1.4,
                      ["--report-accent-color" as string]: tl.text,
                    }}
                  >
                    {tl.label}
                  </p>
                </div>
                <p style={{ fontSize: 14, lineHeight: 1.65, color: "var(--rp-muted)", margin: 0 }}>
                  {report.traffic_light_reason}
                </p>
                <div style={{ marginTop: 12, height: 1, background: "var(--rp-border)" }} />
                <p style={{ fontSize: 13, color: "var(--rp-muted)", marginTop: 12, lineHeight: 1.6 }}>
                  <strong style={{ color: "var(--rp-body)" }}>Overall sentiment:</strong>{" "}
                  {report.sentiment.overall}
                </p>
              </SectionCard>
            </div>

            {/* ── Gap Analysis ── */}
            <SectionCard title="Gap Analysis">
              <ol style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 10 }}>
                {report.gap_analysis.map((gap, idx) => (
                  <li key={idx} style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
                    <span
                      data-report-accent={true}
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: 13,
                        color: tl.text,
                        fontWeight: 700,
                        flexShrink: 0,
                        minWidth: 24,
                        ["--report-accent-color" as string]: tl.text,
                      }}
                    >
                      {String(idx + 1).padStart(2, "0")}
                    </span>
                    <span style={{ fontSize: 14, color: "var(--rp-body)", lineHeight: 1.6 }}>{gap}</span>
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

            {/* ── Market Signals (above source drill-down) ── */}
            {report.market_signals.length > 0 && (
              <SectionCard title="Market Signals">
                <p
                  style={{
                    fontSize: 13,
                    color: "var(--rp-muted)",
                    margin: "0 0 16px 0",
                    lineHeight: 1.55,
                    fontFamily: "var(--font-display, system-ui), sans-serif",
                  }}
                >
                  High-level patterns distilled from live sources — use them for narrative, positioning, and what to validate next.
                </p>
                <ul
                  role="list"
                  aria-label="Key market signals"
                  style={{
                    listStyle: "none",
                    padding: 0,
                    margin: 0,
                    display: "flex",
                    flexDirection: "column",
                    gap: 10,
                  }}
                >
                  {report.market_signals.map((signal, idx) => (
                    <li
                      key={idx}
                      data-report-market-signal=""
                      style={{
                        display: "flex",
                        gap: 0,
                        alignItems: "stretch",
                        borderRadius: 12,
                        overflow: "hidden",
                        border: "1px solid var(--rp-border)",
                        background: "var(--rp-inset)",
                        boxShadow: "inset 0 1px 0 var(--rp-market-inset)",
                      }}
                    >
                      <div
                        data-report-signal-rail=""
                        aria-hidden="true"
                        style={{
                          width: 4,
                          flexShrink: 0,
                          minHeight: 52,
                          background: "linear-gradient(180deg, #22d3ee 0%, #3b82f6 100%)",
                        }}
                      />
                      <div
                        style={{
                          flex: 1,
                          minWidth: 0,
                          padding: "14px 16px",
                          display: "flex",
                          alignItems: "flex-start",
                          gap: 12,
                        }}
                      >
                        <span
                          style={{
                            fontFamily: "var(--font-mono)",
                            fontSize: 11,
                            fontWeight: 700,
                            letterSpacing: "0.06em",
                            color: "var(--accent-cyan)",
                            background: "var(--rp-market-badge-bg)",
                            border: "1px solid var(--rp-market-badge-border)",
                            borderRadius: 6,
                            padding: "4px 8px",
                            lineHeight: 1,
                            flexShrink: 0,
                            marginTop: 2,
                          }}
                        >
                          {String(idx + 1).padStart(2, "0")}
                        </span>
                        <p
                          style={{
                            margin: 0,
                            fontSize: 14,
                            lineHeight: 1.65,
                            color: "var(--rp-body)",
                            fontFamily: "var(--font-display, system-ui), sans-serif",
                          }}
                        >
                          {signal}
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              </SectionCard>
            )}

            {/* ── Sources ── */}
            <SectionCard title="Source Intelligence">
              {/* Header row labels */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 140px 80px 28px", gap: 12, padding: "0 16px 8px", marginBottom: 4 }}>
                {["Source", "Avg Relevance", "Score", ""].map((h) => (
                  <span key={h} style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--rp-muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
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
                      <div data-report-dot="" style={{ width: 10, height: 10, borderRadius: "50%", background: m.dot, boxShadow: `0 0 8px ${m.dot}`, marginTop: 3, flexShrink: 0 }} />
                      <div>
                        <span
                          data-report-accent={true}
                          style={{
                            fontFamily: "var(--font-mono)",
                            fontSize: 12,
                            fontWeight: 700,
                            color: m.text,
                            letterSpacing: "0.04em",
                            ["--report-accent-color" as string]: m.text,
                          }}
                        >
                          {key.toUpperCase()}
                        </span>
                        <p style={{ fontSize: 13, color: "var(--rp-muted)", margin: "2px 0 0 0", lineHeight: 1.55 }}>
                          {descriptions[key]}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </SectionCard>

            {/* ── Footer note ── */}
            <p style={{ fontSize: 12, color: "var(--rp-muted)", textAlign: "center", marginTop: 8, lineHeight: 1.6 }}>
              This report is a strategic screening layer, not legal or investment advice.
              It is designed to quickly surface market signals and differentiation opportunities.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
