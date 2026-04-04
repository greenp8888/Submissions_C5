"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

/* ─── Theme toggle icons ──────────────────────────────────────────── */
const SunIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className="w-4 h-4">
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
  </svg>
);
const MoonIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className="w-4 h-4">
    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
  </svg>
);

/* ─── SVG Icons ─────────────────────────────────────────────────── */
const BoltIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" className="w-5 h-5">
    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
  </svg>
);
const SearchIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} aria-hidden="true" className="w-5 h-5">
    <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
  </svg>
);
const TrafficIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} aria-hidden="true" className="w-5 h-5">
    <rect x="5" y="2" width="14" height="20" rx="3" />
    <circle cx="12" cy="7"  r="2" fill="#ef4444" stroke="none" />
    <circle cx="12" cy="12" r="2" fill="#f97316" stroke="none" />
    <circle cx="12" cy="17" r="2" fill="#22c55e" stroke="none" />
  </svg>
);
const SourcesIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} aria-hidden="true" className="w-5 h-5">
    <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z" />
    <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
  </svg>
);

const ChevronRightIcon = () => (
  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
    <path d="M4.5 2.5L8 6L4.5 9.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);
const CheckIcon = () => (
  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
    <path d="M2 6L4.5 8.5L10 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

/* ─── Types ──────────────────────────────────────────────────────── */
type SampleIdea = { prompt: string; tag: string };

/* ─── Data ───────────────────────────────────────────────────────── */
const pipeline = [
  { num: "01", name: "Query Builder",  desc: "Parsing idea structure & domain" },
  { num: "02", name: "Market Scout",   desc: "Live web research · competitor scan" },
  { num: "03", name: "Report Builder", desc: "Scoring · synthesis · recommendations" },
];

const features = [
  { icon: <SearchIcon />,  name: "Web Search",       desc: "Multi-source live data aggregation" },
  { icon: <TrafficIcon />, name: "RED / AMBER / GREEN", desc: "Scored across 3 viability dimensions" },
  { icon: <SourcesIcon />, name: "6 Sources",         desc: "GitHub · Reddit · HN · Product Hunt · YC · AI4That" },
];

/* ─── Component ──────────────────────────────────────────────────── */
export default function Home() {
  const router = useRouter();
  const [ideaDescription, setIdeaDescription] = useState("");
  const [audience, setAudience] = useState("");
  const [productUrl, setProductUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [isDark, setIsDark] = useState(true);
  const [selectedIdea, setSelectedIdea] = useState<number | null>(null);
  const [sampleIdeas, setSampleIdeas] = useState<SampleIdea[]>([]);
  const [ideasLoading, setIdeasLoading] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    fetch("/api/ideas")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data.ideas)) setSampleIdeas(data.ideas);
      })
      .catch(() => {})
      .finally(() => setIdeasLoading(false));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ideaDescription.trim()) return;
    setLoading(true);
    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea_description: ideaDescription, audience, product_url: productUrl }),
      });
      if (!response.ok) throw new Error("Failed to start analysis");
      const data = await response.json();
      router.push(
        `/report/${data.id}?idea=${encodeURIComponent(ideaDescription)}&audience=${encodeURIComponent(audience)}&url=${encodeURIComponent(productUrl)}`
      );
    } catch {
      setLoading(false);
    }
  };

  return (
    <div
      className={`min-h-screen relative overflow-hidden${isDark ? "" : " theme-light"}`}
      style={{
        background: "var(--dark-bg)",
        color: "var(--dark-text)",
        fontFamily: "var(--font-display), system-ui, sans-serif",
      }}
    >
      {/* ── Ambient background blobs ── */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
        <div
          style={{
            position: "absolute", top: "10%", left: "5%",
            width: 500, height: 500, borderRadius: "50%",
            background: "radial-gradient(circle, rgba(59,130,246,0.08) 0%, transparent 70%)",
            animation: "blobFloat 18s ease-in-out infinite",
          }}
        />
        <div
          style={{
            position: "absolute", bottom: "5%", right: "10%",
            width: 600, height: 600, borderRadius: "50%",
            background: "radial-gradient(circle, rgba(34,211,238,0.06) 0%, transparent 70%)",
            animation: "blobFloat 24s ease-in-out infinite reverse",
          }}
        />
      </div>

      {/* ── Header ── */}
      <header
        className="relative z-10 flex items-center justify-between px-6 py-4"
        style={{ borderBottom: "1px solid var(--dark-border)" }}
      >
        <div className="flex items-center gap-3">
          <div
            className="flex items-center justify-center w-9 h-9 rounded-lg"
            style={{ background: "linear-gradient(135deg, #3b82f6, #22d3ee)" }}
            aria-hidden="true"
          >
            <BoltIcon />
          </div>
          <span style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.02em" }}>
            IdeaScope
          </span>
        </div>

        <div className="flex items-center gap-3">
          {mounted && (
            <>
              {/* BETA pill */}
              <div
                className="flex items-center gap-1.5 px-3 py-1 rounded-full"
                style={{
                  border: "1px solid var(--dark-border-hover)",
                  background: "var(--dark-surface)",
                  fontSize: 11,
                  fontWeight: 500,
                  color: "var(--dark-muted)",
                  fontFamily: "var(--font-mono)",
                  letterSpacing: "0.08em",
                }}
              >
                <span
                  className="inline-block w-1.5 h-1.5 rounded-full"
                  style={{ background: "var(--accent-cyan)", boxShadow: "0 0 6px var(--accent-cyan)" }}
                />
                BETA · AI-POWERED
              </div>

              {/* Theme toggle */}
              <button
                onClick={() => setIsDark(!isDark)}
                aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
                className="cursor-pointer transition-all duration-200"
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: 36,
                  height: 36,
                  borderRadius: 8,
                  border: "1px solid var(--dark-border-hover)",
                  background: "var(--dark-surface)",
                  color: "var(--dark-muted)",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.borderColor = "var(--accent-cyan)";
                  (e.currentTarget as HTMLElement).style.color = "var(--accent-cyan)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.borderColor = "var(--dark-border-hover)";
                  (e.currentTarget as HTMLElement).style.color = "var(--dark-muted)";
                }}
              >
                {isDark ? <SunIcon /> : <MoonIcon />}
              </button>
            </>
          )}
        </div>
      </header>

      {/* ── Main two-column ── */}
      <main className="relative z-10 grid grid-cols-1 lg:grid-cols-2 min-h-[calc(100vh-57px)]">

        {/* ── Left: hero + form ── */}
        <div
          className="flex flex-col px-8 py-12 lg:px-12 lg:py-16"
          style={{ borderRight: "1px solid var(--dark-border)" }}
        >
          {/* Eyebrow label */}
          <p
            className="mb-8"
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 11,
              fontWeight: 500,
              letterSpacing: "0.14em",
              color: "var(--accent-cyan)",
              animation: "fadeIn 0.5s ease both",
            }}
          >
            MULTI-AGENT PRODUCT INTELLIGENCE
          </p>

          {/* Hero headline */}
          <div
            className="mb-6"
            style={{ animation: "fadeInUp 0.6s ease both", animationDelay: "0.05s" }}
          >
            <h1
              style={{
                fontSize: "clamp(44px, 6vw, 80px)",
                fontWeight: 800,
                lineHeight: 1.05,
                letterSpacing: "-0.03em",
                color: "var(--dark-text)",
              }}
            >
              Upload your
              <br />idea.
            </h1>
            <h2
              style={{
                fontSize: "clamp(44px, 6vw, 80px)",
                fontWeight: 800,
                lineHeight: 1.05,
                letterSpacing: "-0.03em",
                background: "linear-gradient(90deg, #22d3ee 0%, #3b82f6 60%, #818cf8 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              Get instant<br />strategy.
            </h2>
          </div>

          {/* Sub-copy */}
          <p
            className="mb-8 max-w-md"
            style={{
              fontSize: 16,
              lineHeight: 1.65,
              color: "var(--dark-muted)",
              animation: "fadeInUp 0.6s ease both",
              animationDelay: "0.12s",
            }}
          >
            Three AI agents analyse your concept in parallel — competitor landscape, UX gaps,
            market signals, and open-source tools — in under 60 seconds.
          </p>

          {/* ── Sample idea prompts ── */}
          <div className="w-full max-w-md mb-8">
            {/* Section label */}
            <div
              className="flex items-center gap-3 mb-3"
              style={{ animation: "fadeIn 0.5s ease both", animationDelay: "0.17s" }}
            >
              <span
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 10,
                  fontWeight: 500,
                  letterSpacing: "0.16em",
                  color: "var(--dark-muted)",
                }}
              >
                TRY AN EXAMPLE
              </span>
              <div
                style={{
                  flex: 1,
                  height: 1,
                  background: "linear-gradient(90deg, var(--dark-border-hover) 0%, transparent 100%)",
                }}
              />
            </div>

            {/* Chips — skeleton while loading, real chips once ready */}
            <div className="flex flex-col gap-2">
              {ideasLoading
                ? Array.from({ length: 4 }).map((_, i) => (
                    <div
                      key={i}
                      className="animate-pulse"
                      style={{
                        minHeight: 48,
                        padding: "10px 14px",
                        borderRadius: 10,
                        border: "1px solid var(--dark-border)",
                        background: "var(--dark-surface)",
                        display: "flex",
                        alignItems: "center",
                        gap: 12,
                        animationDelay: `${i * 0.08}s`,
                      }}
                    >
                      <div style={{ width: 12, height: 12, borderRadius: "50%", background: "var(--dark-border-hover)", flexShrink: 0 }} />
                      <div style={{ flex: 1, height: 12, borderRadius: 4, background: "var(--dark-border-hover)" }} />
                      <div style={{ width: 48, height: 20, borderRadius: 5, background: "var(--dark-border-hover)", flexShrink: 0 }} />
                    </div>
                  ))
                : sampleIdeas.map((idea, i) => {
                    const isSelected = selectedIdea === i;
                    return (
                      <button
                        key={i}
                        type="button"
                        aria-pressed={isSelected}
                        onClick={() => {
                          setIdeaDescription(idea.prompt);
                          setSelectedIdea(i);
                        }}
                        className="flex items-center gap-3 w-full text-left cursor-pointer"
                        style={{
                          minHeight: 48,
                          padding: "10px 14px",
                          borderRadius: 10,
                          border: `1px solid ${isSelected ? "var(--accent-cyan)" : "var(--dark-border)"}`,
                          background: isSelected ? "rgba(34,211,238,0.06)" : "var(--dark-surface)",
                          boxShadow: isSelected ? "0 0 0 1px rgba(34,211,238,0.15), 0 0 16px rgba(34,211,238,0.08)" : "none",
                          transition: "border-color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease, transform 0.15s ease",
                          animation: "fadeInUp 0.5s ease both",
                          animationDelay: `${i * 0.07}s`,
                          outline: "none",
                        }}
                        onMouseEnter={(e) => {
                          if (!isSelected) {
                            const el = e.currentTarget;
                            el.style.borderColor = "rgba(34,211,238,0.35)";
                            el.style.background = "var(--dark-surface-2)";
                            el.style.boxShadow = "0 0 12px rgba(34,211,238,0.06)";
                            el.style.transform = "translateY(-1px)";
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!isSelected) {
                            const el = e.currentTarget;
                            el.style.borderColor = "var(--dark-border)";
                            el.style.background = "var(--dark-surface)";
                            el.style.boxShadow = "none";
                            el.style.transform = "translateY(0)";
                          }
                        }}
                        onFocus={(e) => {
                          if (!isSelected) {
                            e.currentTarget.style.borderColor = "rgba(34,211,238,0.35)";
                            e.currentTarget.style.boxShadow = "0 0 0 3px rgba(34,211,238,0.10)";
                          }
                        }}
                        onBlur={(e) => {
                          if (!isSelected) {
                            e.currentTarget.style.borderColor = "var(--dark-border)";
                            e.currentTarget.style.boxShadow = "none";
                          }
                        }}
                      >
                        {/* State indicator */}
                        <span
                          style={{
                            flexShrink: 0,
                            color: "var(--accent-cyan)",
                            display: "flex",
                            alignItems: "center",
                            transition: "opacity 0.15s ease",
                            opacity: isSelected ? 1 : 0.5,
                          }}
                        >
                          {isSelected ? <CheckIcon /> : <ChevronRightIcon />}
                        </span>

                        {/* Prompt text */}
                        <span
                          style={{
                            flex: 1,
                            fontSize: 13,
                            lineHeight: 1.5,
                            color: isSelected ? "var(--dark-text)" : "var(--dark-muted)",
                            transition: "color 0.18s ease",
                            fontFamily: "var(--font-display), system-ui, sans-serif",
                          }}
                        >
                          {idea.prompt}
                        </span>

                        {/* Tag pill */}
                        <span
                          style={{
                            flexShrink: 0,
                            fontFamily: "var(--font-mono)",
                            fontSize: 9,
                            fontWeight: 500,
                            letterSpacing: "0.1em",
                            color: isSelected ? "var(--accent-cyan)" : "var(--dark-muted)",
                            border: `1px solid ${isSelected ? "rgba(34,211,238,0.3)" : "var(--dark-border)"}`,
                            background: isSelected ? "rgba(34,211,238,0.06)" : "transparent",
                            padding: "3px 7px",
                            borderRadius: 5,
                            transition: "all 0.18s ease",
                          }}
                        >
                          {idea.tag}
                        </span>
                      </button>
                    );
                  })}
            </div>
          </div>

          {/* Form */}
          <form
            onSubmit={handleSubmit}
            className="flex flex-col gap-5 w-full max-w-md"
            style={{ animation: "fadeInUp 0.6s ease both", animationDelay: "0.2s" }}
          >
            {/* Idea description */}
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="idea"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  letterSpacing: "0.1em",
                  color: "var(--accent-cyan)",
                  fontWeight: 500,
                }}
              >
                IDEA DESCRIPTION <span style={{ color: "#ef4444" }}>*</span>
              </label>
              <textarea
                id="idea"
                value={ideaDescription}
                onChange={(e) => { setIdeaDescription(e.target.value); setSelectedIdea(null); }}
                placeholder="Describe your product: what it does, who it's for, the core problem it solves, and any key features…"
                required
                rows={4}
                className="w-full resize-none transition-all duration-200"
                style={{
                  background: "var(--dark-surface)",
                  border: "1px solid var(--dark-border)",
                  borderRadius: 8,
                  padding: "12px 14px",
                  fontSize: 14,
                  lineHeight: 1.6,
                  color: "var(--dark-text)",
                  outline: "none",
                }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "rgba(34,211,238,0.4)"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(34,211,238,0.08)"; }}
                onBlur={(e)  => { e.currentTarget.style.borderColor = "var(--dark-border)"; e.currentTarget.style.boxShadow = "none"; }}
              />
            </div>

            {/* Target audience */}
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="audience"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  letterSpacing: "0.1em",
                  color: "var(--dark-muted)",
                  fontWeight: 500,
                }}
              >
                TARGET AUDIENCE
              </label>
              <input
                id="audience"
                type="text"
                value={audience}
                onChange={(e) => setAudience(e.target.value)}
                placeholder="e.g. indie developers, busy executives…"
                className="transition-all duration-200"
                style={{
                  background: "var(--dark-surface)",
                  border: "1px solid var(--dark-border)",
                  borderRadius: 8,
                  padding: "11px 14px",
                  fontSize: 14,
                  color: "var(--dark-text)",
                  outline: "none",
                }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "rgba(34,211,238,0.4)"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(34,211,238,0.08)"; }}
                onBlur={(e)  => { e.currentTarget.style.borderColor = "var(--dark-border)"; e.currentTarget.style.boxShadow = "none"; }}
              />
            </div>

            {/* Product URL */}
            <div className="flex flex-col gap-1.5">
              <label
                htmlFor="product-url"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  letterSpacing: "0.1em",
                  color: "var(--dark-muted)",
                  fontWeight: 500,
                }}
              >
                PRODUCT URL
              </label>
              <input
                id="product-url"
                type="url"
                value={productUrl}
                onChange={(e) => setProductUrl(e.target.value)}
                placeholder="https://…"
                className="transition-all duration-200"
                style={{
                  background: "var(--dark-surface)",
                  border: "1px solid var(--dark-border)",
                  borderRadius: 8,
                  padding: "11px 14px",
                  fontSize: 14,
                  color: "var(--dark-text)",
                  outline: "none",
                }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "rgba(34,211,238,0.4)"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(34,211,238,0.08)"; }}
                onBlur={(e)  => { e.currentTarget.style.borderColor = "var(--dark-border)"; e.currentTarget.style.boxShadow = "none"; }}
              />
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading || !ideaDescription.trim()}
              className="cursor-pointer transition-all duration-200"
              style={{
                marginTop: 4,
                padding: "13px 28px",
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 600,
                letterSpacing: "0.02em",
                border: "none",
                cursor: loading || !ideaDescription.trim() ? "not-allowed" : "pointer",
                background: loading || !ideaDescription.trim()
                  ? "rgba(255,255,255,0.06)"
                  : "linear-gradient(135deg, #22d3ee, #3b82f6)",
                color: loading || !ideaDescription.trim() ? "var(--dark-muted)" : "#fff",
                opacity: loading || !ideaDescription.trim() ? 0.5 : 1,
                animation: loading || !ideaDescription.trim() ? "none" : "glowPulse 3s ease-in-out infinite",
                alignSelf: "flex-start",
              }}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4" strokeDashoffset="10" />
                  </svg>
                  Analyzing…
                </span>
              ) : (
                "Analyze idea →"
              )}
            </button>
          </form>
        </div>

        {/* ── Right: pipeline + features ── */}
        <div className="flex flex-col px-8 py-12 lg:px-12 lg:py-16">
          {/* Section label */}
          <p
            className="mb-8"
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 11,
              fontWeight: 500,
              letterSpacing: "0.14em",
              color: "var(--dark-muted)",
              animation: "fadeIn 0.5s ease both",
            }}
          >
            ANALYSIS PIPELINE
          </p>

          {/* Numbered pipeline steps */}
          <div className="flex flex-col gap-3 mb-8">
            {pipeline.map((step, i) => (
              <div
                key={step.num}
                className="flex items-center gap-4 rounded-xl transition-all duration-200"
                style={{
                  padding: "16px 18px",
                  background: "var(--dark-surface)",
                  border: "1px solid var(--dark-border)",
                  animation: `fadeInUp 0.5s ease both`,
                  animationDelay: `${0.1 + i * 0.08}s`,
                }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "var(--dark-border-hover)"; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "var(--dark-border)"; }}
              >
                <div
                  className="flex items-center justify-center rounded-lg flex-shrink-0"
                  style={{
                    width: 40, height: 40,
                    background: "var(--dark-surface-2)",
                    fontFamily: "var(--font-mono)",
                    fontSize: 13,
                    fontWeight: 600,
                    color: "var(--accent-cyan)",
                    letterSpacing: "0.04em",
                  }}
                >
                  {step.num}
                </div>
                <div>
                  <p style={{ fontSize: 15, fontWeight: 600, color: "var(--dark-text)", marginBottom: 2 }}>
                    {step.name}
                  </p>
                  <p style={{ fontSize: 13, color: "var(--dark-muted)" }}>
                    {step.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Feature items */}
          <div className="flex flex-col gap-3">
            {features.map((feat, i) => (
              <div
                key={feat.name}
                className="flex items-center gap-4 rounded-xl transition-all duration-200"
                style={{
                  padding: "14px 18px",
                  background: "var(--dark-surface)",
                  border: "1px solid var(--dark-border)",
                  animation: `fadeInUp 0.5s ease both`,
                  animationDelay: `${0.35 + i * 0.08}s`,
                }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "var(--dark-border-hover)"; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = "var(--dark-border)"; }}
              >
                <div
                  className="flex items-center justify-center rounded-lg flex-shrink-0"
                  style={{
                    width: 36, height: 36,
                    background: "var(--dark-surface-2)",
                    color: "var(--dark-muted)",
                  }}
                >
                  {feat.icon}
                </div>
                <div>
                  <p style={{ fontSize: 14, fontWeight: 600, color: "var(--dark-text)", marginBottom: 2 }}>
                    {feat.name}
                  </p>
                  <p style={{ fontSize: 12, color: "var(--dark-muted)" }}>
                    {feat.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
