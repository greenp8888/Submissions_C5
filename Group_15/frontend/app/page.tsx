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
/* ─── Brand logos ────────────────────────────────────────────────── */
const GitHubLogo = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-label="GitHub" className="w-5 h-5">
    <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
  </svg>
);
const RedditLogo = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-label="Reddit" className="w-5 h-5">
    <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z" />
  </svg>
);
const HackerNewsLogo = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-label="Hacker News" className="w-5 h-5">
    <path d="M0 24V0h24v24H0zM6.951 5.896l4.112 7.708v5.064h1.583v-4.972l4.148-7.799h-1.749l-2.457 4.875c-.372.745-.688 1.434-.688 1.434s-.297-.708-.651-1.434L8.831 5.896h-1.88z" />
  </svg>
);
const ProductHuntLogo = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-label="Product Hunt" className="w-5 h-5">
    <path d="M13.604 8.4h-3.405V12h3.405c.995 0 1.801-.806 1.801-1.8 0-.995-.806-1.8-1.801-1.8zM12 0C5.372 0 0 5.372 0 12s5.372 12 12 12 12-5.372 12-12S18.628 0 12 0zm1.604 13.799H10.2v3.4H8.4V6.6h5.204c1.96 0 3.55 1.58 3.55 3.6-.001 1.972-1.59 3.599-3.55 3.599z" />
  </svg>
);
const YCLogo = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" aria-label="Y Combinator" className="w-5 h-5">
    <path d="M0 24V0h24v24H0zM6.951 5.896l4.112 7.708v5.064h1.583v-4.972l4.148-7.799h-1.749l-2.457 4.875c-.372.745-.688 1.434-.688 1.434s-.297-.708-.651-1.434L8.831 5.896h-1.88z" />
  </svg>
);
const AI4ThatLogo = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} aria-label="AI For That" className="w-5 h-5">
    <path d="M12 2a2 2 0 1 1 0 4 2 2 0 0 1 0-4z" fill="currentColor" stroke="none" />
    <path d="M12 6v4M8 8l2.5 2.5M16 8l-2.5 2.5" />
    <rect x="4" y="10" width="16" height="9" rx="3" />
    <path d="M8 14h.01M12 14h.01M16 14h.01" strokeWidth={2} strokeLinecap="round" />
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

/* ─── Coming-soon tab icons ─────────────────────────────────────── */
const PlatformIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} aria-hidden="true" className="w-8 h-8">
    <rect x="2" y="3" width="20" height="14" rx="2" />
    <path d="M8 21h8M12 17v4" />
  </svg>
);
const SolutionIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} aria-hidden="true" className="w-8 h-8">
    <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-5 0V4.5A2.5 2.5 0 0 1 9.5 2z" />
    <path d="M14.5 8A2.5 2.5 0 0 1 17 10.5v9a2.5 2.5 0 0 1-5 0v-9A2.5 2.5 0 0 1 14.5 8z" />
    <path d="M4.5 13A2.5 2.5 0 0 1 7 15.5v4a2.5 2.5 0 0 1-5 0v-4A2.5 2.5 0 0 1 4.5 13z" />
  </svg>
);
const PricingIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} aria-hidden="true" className="w-8 h-8">
    <line x1="12" y1="1" x2="12" y2="23" />
    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
  </svg>
);

/* ─── Types ──────────────────────────────────────────────────────── */
type SampleIdea = { prompt: string; tag: string };
type NavTab = "home" | "platform" | "solution" | "pricing";

/* ─── Data ───────────────────────────────────────────────────────── */
const pipeline = [
  { num: "01", name: "Query Builder",  desc: "Parsing idea structure & domain" },
  { num: "02", name: "Market Scout",   desc: "Live web research · competitor scan" },
  { num: "03", name: "Report Builder", desc: "Scoring · synthesis · recommendations" },
];

const sources = [
  { icon: <GitHubLogo />,      name: "GitHub",        color: "#e2e8f0", bg: "rgba(226,232,240,0.1)"  },
  { icon: <RedditLogo />,      name: "Reddit",        color: "#FF4500", bg: "rgba(255,69,0,0.12)"    },
  { icon: <HackerNewsLogo />,  name: "Hacker News",   color: "#FF6600", bg: "rgba(255,102,0,0.12)"   },
  { icon: <ProductHuntLogo />, name: "Product Hunt",  color: "#DA552F", bg: "rgba(218,85,47,0.12)"   },
  { icon: <YCLogo />,          name: "Y Combinator",  color: "#FB651E", bg: "rgba(251,101,30,0.12)"  },
  { icon: <AI4ThatLogo />,     name: "AI For That",   color: "#818cf8", bg: "rgba(129,140,248,0.12)" },
];

const comingSoonContent: Record<Exclude<NavTab, "home">, {
  icon: React.ReactNode;
  title: string;
  tagline: string;
  bullets: string[];
  accent: string;
  glow: string;
}> = {
  platform: {
    icon: <PlatformIcon />,
    title: "Platform",
    tagline: "One workspace for your entire product research workflow.",
    bullets: [
      "Unified dashboard for all your idea analyses",
      "Team collaboration & shared workspaces",
      "API access & custom integrations",
      "Version history & comparison mode",
    ],
    accent: "#818cf8",
    glow: "rgba(129,140,248,0.18)",
  },
  solution: {
    icon: <SolutionIcon />,
    title: "Solutions",
    tagline: "Purpose-built workflows for every stage of your product journey.",
    bullets: [
      "Early-stage validation for solo founders",
      "Portfolio analysis for VCs & accelerators",
      "Competitive intelligence for product teams",
      "Market sizing for enterprise strategy",
    ],
    accent: "#34d399",
    glow: "rgba(52,211,153,0.18)",
  },
  pricing: {
    icon: <PricingIcon />,
    title: "Pricing",
    tagline: "Simple, transparent plans that scale with your ambition.",
    bullets: [
      "Free tier — 3 analyses per month",
      "Pro — unlimited analyses, priority queue",
      "Team — shared credits, admin controls",
      "Enterprise — custom models & SLA",
    ],
    accent: "#f59e0b",
    glow: "rgba(245,158,11,0.18)",
  },
};

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
  const [activeTab, setActiveTab] = useState<NavTab>("home");

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
        className="relative z-10 flex items-center justify-between px-6 py-0"
        style={{ borderBottom: "1px solid var(--dark-border)", height: 56 }}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <div
            className="flex items-center justify-center w-8 h-8 rounded-lg"
            style={{ background: "linear-gradient(135deg, #3b82f6, #22d3ee)" }}
            aria-hidden="true"
          >
            <BoltIcon />
          </div>
          <span style={{ fontSize: 17, fontWeight: 700, letterSpacing: "-0.02em" }}>
            IdeaScope
          </span>
        </div>

        {/* ── Center nav tabs ── */}
        {mounted && (
          <nav
            className="flex items-center"
            aria-label="Main navigation"
            style={{
              position: "absolute",
              left: "50%",
              transform: "translateX(-50%)",
              background: "var(--dark-surface)",
              border: "1px solid var(--dark-border)",
              borderRadius: 10,
              padding: "3px",
              display: "flex",
              gap: 2,
            }}
          >
            {(["platform", "solution", "pricing"] as const).map((tab) => {
              const isActive = activeTab === tab;
              const label = tab === "solution" ? "Solution" : tab.charAt(0).toUpperCase() + tab.slice(1);
              return (
                <button
                  key={tab}
                  onClick={() => setActiveTab(isActive ? "home" : tab)}
                  aria-current={isActive ? "page" : undefined}
                  className="cursor-pointer transition-all duration-200"
                  style={{
                    padding: "6px 16px",
                    borderRadius: 7,
                    fontSize: 13,
                    fontWeight: isActive ? 600 : 500,
                    letterSpacing: "-0.01em",
                    border: "none",
                    background: isActive
                      ? "linear-gradient(135deg, rgba(59,130,246,0.2), rgba(34,211,238,0.2))"
                      : "transparent",
                    color: isActive ? "var(--accent-cyan)" : "var(--dark-muted)",
                    boxShadow: isActive ? "inset 0 0 0 1px rgba(34,211,238,0.25)" : "none",
                    outline: "none",
                    position: "relative",
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) (e.currentTarget as HTMLElement).style.color = "var(--dark-text)";
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) (e.currentTarget as HTMLElement).style.color = "var(--dark-muted)";
                  }}
                >
                  {label}
                  {/* "Soon" badge */}
                  <span
                    style={{
                      position: "absolute",
                      top: -6,
                      right: -4,
                      fontSize: 8,
                      fontWeight: 600,
                      letterSpacing: "0.06em",
                      padding: "1px 5px",
                      borderRadius: 4,
                      background: "linear-gradient(135deg, #3b82f6, #22d3ee)",
                      color: "#fff",
                      fontFamily: "var(--font-mono)",
                      lineHeight: 1.6,
                    }}
                  >
                    SOON
                  </span>
                </button>
              );
            })}
          </nav>
        )}

        {/* Right controls */}
        <div className="flex items-center gap-3 flex-shrink-0">
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
                BETA
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
                  width: 34,
                  height: 34,
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
      <main className="relative z-10 grid grid-cols-1 lg:grid-cols-2" style={{ minHeight: "calc(100vh - 56px)" }}>

        {/* ── Left: hero + form ── */}
        <div
          className="flex flex-col px-8 py-10 lg:px-12 lg:py-12"
          style={{ borderRight: "1px solid var(--dark-border)" }}
        >
          {/* Eyebrow label */}
          <p
            className="mb-6"
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
            className="mb-4"
            style={{ animation: "fadeInUp 0.6s ease both", animationDelay: "0.05s" }}
          >
            <h1
              style={{
                fontSize: "clamp(36px, 5vw, 64px)",
                fontWeight: 800,
                lineHeight: 1.08,
                letterSpacing: "-0.03em",
                color: "var(--dark-text)",
              }}
            >
              Upload your idea.
            </h1>
            <h2
              style={{
                fontSize: "clamp(36px, 5vw, 64px)",
                fontWeight: 800,
                lineHeight: 1.08,
                letterSpacing: "-0.03em",
                background: "linear-gradient(90deg, #22d3ee 0%, #3b82f6 60%, #818cf8 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              Get instant strategy.
            </h2>
          </div>

          {/* Sub-copy */}
          <p
            className="mb-6 max-w-md"
            style={{
              fontSize: 15,
              lineHeight: 1.65,
              color: "var(--dark-muted)",
              animation: "fadeInUp 0.6s ease both",
              animationDelay: "0.12s",
            }}
          >
            Three AI agents analyse your concept in parallel — competitor landscape, UX gaps,
            market signals, and open-source tools — in under 60 seconds.
          </p>

          {/* Stats bar */}
          <div
            className="flex items-center gap-6 mb-7"
            style={{ animation: "fadeInUp 0.6s ease both", animationDelay: "0.15s" }}
          >
            {[
              { val: "6+", label: "Sources" },
              { val: "<60s", label: "Analysis" },
              { val: "3", label: "AI Agents" },
            ].map(({ val, label }) => (
              <div key={label} className="flex flex-col">
                <span
                  style={{
                    fontSize: 20,
                    fontWeight: 700,
                    letterSpacing: "-0.02em",
                    color: "var(--dark-text)",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  {val}
                </span>
                <span
                  style={{
                    fontSize: 11,
                    color: "var(--dark-muted)",
                    fontFamily: "var(--font-mono)",
                    letterSpacing: "0.08em",
                  }}
                >
                  {label}
                </span>
              </div>
            ))}
            <div
              style={{
                width: 1,
                height: 28,
                background: "var(--dark-border-hover)",
                marginLeft: 4,
                marginRight: 4,
              }}
            />
            <div
              className="flex items-center gap-1.5"
              style={{
                fontSize: 11,
                color: "var(--dark-muted)",
                fontFamily: "var(--font-mono)",
                letterSpacing: "0.04em",
              }}
            >
              <span
                className="inline-block w-2 h-2 rounded-full"
                style={{ background: "#22c55e", boxShadow: "0 0 6px #22c55e" }}
              />
              LIVE · AI-POWERED
            </div>
          </div>

          {/* ── Sample idea prompts ── */}
          <div className="w-full max-w-md mb-6">
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

            <div className="grid grid-cols-2 gap-2">
              {ideasLoading
                ? Array.from({ length: 4 }).map((_, i) => (
                    <div
                      key={i}
                      className="animate-pulse flex flex-col gap-2"
                      style={{
                        padding: "10px 12px",
                        borderRadius: 10,
                        border: "1px solid var(--dark-border)",
                        background: "var(--dark-surface)",
                        animationDelay: `${i * 0.08}s`,
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <div style={{ width: 44, height: 16, borderRadius: 4, background: "var(--dark-border-hover)" }} />
                        <div style={{ width: 12, height: 12, borderRadius: "50%", background: "var(--dark-border-hover)" }} />
                      </div>
                      <div style={{ height: 10, borderRadius: 4, background: "var(--dark-border-hover)" }} />
                      <div style={{ height: 10, width: "70%", borderRadius: 4, background: "var(--dark-border-hover)" }} />
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
                        className="flex flex-col w-full text-left cursor-pointer"
                        style={{
                          padding: "10px 12px",
                          borderRadius: 10,
                          border: `1px solid ${isSelected ? "var(--accent-cyan)" : "var(--dark-border)"}`,
                          background: isSelected ? "rgba(34,211,238,0.06)" : "var(--dark-surface)",
                          boxShadow: isSelected ? "0 0 0 1px rgba(34,211,238,0.15), 0 0 16px rgba(34,211,238,0.08)" : "none",
                          transition: "border-color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease, transform 0.15s ease",
                          animation: "fadeInUp 0.5s ease both",
                          animationDelay: `${i * 0.07}s`,
                          outline: "none",
                          gap: 6,
                        }}
                        onMouseEnter={(e) => {
                          if (!isSelected) {
                            const el = e.currentTarget;
                            el.style.borderColor = "rgba(34,211,238,0.35)";
                            el.style.background = "var(--dark-surface-2)";
                            el.style.transform = "translateY(-1px)";
                          }
                        }}
                        onMouseLeave={(e) => {
                          if (!isSelected) {
                            const el = e.currentTarget;
                            el.style.borderColor = "var(--dark-border)";
                            el.style.background = "var(--dark-surface)";
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
                        {/* Tag + check row */}
                        <div className="flex items-center justify-between gap-1">
                          <span
                            style={{
                              fontFamily: "var(--font-mono)",
                              fontSize: 9,
                              fontWeight: 600,
                              letterSpacing: "0.1em",
                              color: isSelected ? "var(--accent-cyan)" : "var(--dark-muted)",
                              border: `1px solid ${isSelected ? "rgba(34,211,238,0.3)" : "var(--dark-border)"}`,
                              background: isSelected ? "rgba(34,211,238,0.06)" : "transparent",
                              padding: "2px 6px",
                              borderRadius: 4,
                              transition: "all 0.18s ease",
                            }}
                          >
                            {idea.tag}
                          </span>
                          <span
                            style={{
                              color: "var(--accent-cyan)",
                              display: "flex",
                              alignItems: "center",
                              opacity: isSelected ? 1 : 0.4,
                              transition: "opacity 0.15s ease",
                              flexShrink: 0,
                            }}
                          >
                            {isSelected ? <CheckIcon /> : <ChevronRightIcon />}
                          </span>
                        </div>
                        {/* Prompt text */}
                        <span
                          style={{
                            fontSize: 12,
                            lineHeight: 1.5,
                            color: isSelected ? "var(--dark-text)" : "var(--dark-muted)",
                            transition: "color 0.18s ease",
                            fontFamily: "var(--font-display), system-ui, sans-serif",
                            display: "-webkit-box",
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: "vertical",
                            overflow: "hidden",
                          }}
                        >
                          {idea.prompt}
                        </span>
                      </button>
                    );
                  })}
            </div>
          </div>

          {/* Form */}
          <form
            onSubmit={handleSubmit}
            className="flex flex-col gap-4 w-full max-w-md"
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
                placeholder="Describe your product: what it does, who it's for, the core problem it solves…"
                required
                rows={3}
                className="w-full resize-none transition-all duration-200"
                style={{
                  background: "var(--dark-surface)",
                  border: "1px solid var(--dark-border)",
                  borderRadius: 8,
                  padding: "11px 14px",
                  fontSize: 14,
                  lineHeight: 1.6,
                  color: "var(--dark-text)",
                  outline: "none",
                }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "rgba(34,211,238,0.4)"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(34,211,238,0.08)"; }}
                onBlur={(e)  => { e.currentTarget.style.borderColor = "var(--dark-border)"; e.currentTarget.style.boxShadow = "none"; }}
              />
            </div>

            {/* Two-column: audience + URL */}
            <div className="grid grid-cols-2 gap-3">
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
                  placeholder="e.g. indie devs…"
                  className="transition-all duration-200"
                  style={{
                    background: "var(--dark-surface)",
                    border: "1px solid var(--dark-border)",
                    borderRadius: 8,
                    padding: "10px 12px",
                    fontSize: 13,
                    color: "var(--dark-text)",
                    outline: "none",
                  }}
                  onFocus={(e) => { e.currentTarget.style.borderColor = "rgba(34,211,238,0.4)"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(34,211,238,0.08)"; }}
                  onBlur={(e)  => { e.currentTarget.style.borderColor = "var(--dark-border)"; e.currentTarget.style.boxShadow = "none"; }}
                />
              </div>
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
                    padding: "10px 12px",
                    fontSize: 13,
                    color: "var(--dark-text)",
                    outline: "none",
                  }}
                  onFocus={(e) => { e.currentTarget.style.borderColor = "rgba(34,211,238,0.4)"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(34,211,238,0.08)"; }}
                  onBlur={(e)  => { e.currentTarget.style.borderColor = "var(--dark-border)"; e.currentTarget.style.boxShadow = "none"; }}
                />
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading || !ideaDescription.trim()}
              className="cursor-pointer transition-all duration-200"
              style={{
                padding: "12px 28px",
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

        {/* ── Right: dynamic panel ── */}
        <div className="flex flex-col px-8 py-10 lg:px-12 lg:py-12">
          {activeTab === "home" ? (
            /* ── Pipeline + features (default) ── */
            <>
              <p
                className="mb-6"
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

              <div className="flex flex-col gap-3 mb-6">
                {pipeline.map((step, i) => (
                  <div
                    key={step.num}
                    className="flex items-center gap-4 rounded-xl transition-all duration-200"
                    style={{
                      padding: "15px 18px",
                      background: "var(--dark-surface)",
                      border: "1px solid var(--dark-border)",
                      animation: "fadeInUp 0.5s ease both",
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
                      <p style={{ fontSize: 14, fontWeight: 600, color: "var(--dark-text)", marginBottom: 2 }}>
                        {step.name}
                      </p>
                      <p style={{ fontSize: 12, color: "var(--dark-muted)" }}>
                        {step.desc}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              <p
                className="mb-4"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  fontWeight: 500,
                  letterSpacing: "0.14em",
                  color: "var(--dark-muted)",
                }}
              >
                INTELLIGENCE SOURCES
              </p>

              <div className="grid grid-cols-3 gap-2 mb-8">
                {sources.map((src, i) => (
                  <div
                    key={src.name}
                    className="flex flex-col items-center gap-2 rounded-xl transition-all duration-200 cursor-default"
                    style={{
                      padding: "12px 8px",
                      background: "var(--dark-surface)",
                      border: "1px solid var(--dark-border)",
                      animation: "fadeInUp 0.5s ease both",
                      animationDelay: `${0.35 + i * 0.06}s`,
                      textAlign: "center",
                    }}
                    onMouseEnter={(e) => {
                      const el = e.currentTarget as HTMLElement;
                      el.style.borderColor = src.color + "55";
                      el.style.boxShadow = `0 0 14px ${src.bg}`;
                    }}
                    onMouseLeave={(e) => {
                      const el = e.currentTarget as HTMLElement;
                      el.style.borderColor = "var(--dark-border)";
                      el.style.boxShadow = "none";
                    }}
                  >
                    <div
                      className="flex items-center justify-center rounded-lg flex-shrink-0"
                      style={{ width: 34, height: 34, background: src.bg, color: src.color }}
                    >
                      {src.icon}
                    </div>
                    <span style={{ fontSize: 11, fontWeight: 600, color: "var(--dark-muted)", lineHeight: 1.2 }}>
                      {src.name}
                    </span>
                  </div>
                ))}
              </div>

              {/* Explore tabs nudge */}
              <div
                style={{
                  padding: "14px 18px",
                  borderRadius: 12,
                  background: "linear-gradient(135deg, rgba(59,130,246,0.07), rgba(34,211,238,0.05))",
                  border: "1px solid rgba(34,211,238,0.12)",
                  animation: "fadeInUp 0.5s ease both",
                  animationDelay: "0.6s",
                }}
              >
                <p style={{ fontSize: 12, color: "var(--dark-muted)", lineHeight: 1.6 }}>
                  <span style={{ color: "var(--accent-cyan)", fontWeight: 600 }}>More coming soon —</span>{" "}
                  explore <strong style={{ color: "var(--dark-text)" }}>Platform</strong>,{" "}
                  <strong style={{ color: "var(--dark-text)" }}>Solution</strong> &amp;{" "}
                  <strong style={{ color: "var(--dark-text)" }}>Pricing</strong> in the top navigation.
                </p>
              </div>
            </>
          ) : (
            /* ── Coming Soon panel ── */
            <ComingSoonPanel tab={activeTab as Exclude<NavTab, "home">} onBack={() => setActiveTab("home")} />
          )}
        </div>
      </main>
    </div>
  );
}

/* ─── Coming Soon Panel ──────────────────────────────────────────── */
function ComingSoonPanel({
  tab,
  onBack,
}: {
  tab: Exclude<NavTab, "home">;
  onBack: () => void;
}) {
  const content = comingSoonContent[tab];

  return (
    <div
      className="flex flex-col h-full"
      style={{ animation: "fadeInUp 0.4s ease both" }}
    >
      {/* Back link */}
      <button
        onClick={onBack}
        className="flex items-center gap-1.5 mb-8 cursor-pointer transition-all duration-150 self-start"
        style={{
          background: "none",
          border: "none",
          padding: 0,
          fontFamily: "var(--font-mono)",
          fontSize: 11,
          letterSpacing: "0.1em",
          color: "var(--dark-muted)",
          fontWeight: 500,
        }}
        onMouseEnter={(e) => (e.currentTarget as HTMLElement).style.color = "var(--dark-text)"}
        onMouseLeave={(e) => (e.currentTarget as HTMLElement).style.color = "var(--dark-muted)"}
      >
        ← BACK TO PIPELINE
      </button>

      {/* Card */}
      <div
        className="flex-1 flex flex-col rounded-2xl relative overflow-hidden"
        style={{
          background: "var(--dark-surface)",
          border: `1px solid ${content.accent}30`,
          boxShadow: `0 0 60px ${content.glow}, inset 0 1px 0 ${content.accent}20`,
          padding: "40px 36px",
        }}
      >
        {/* Glow blob */}
        <div
          aria-hidden="true"
          style={{
            position: "absolute",
            top: -60,
            right: -60,
            width: 280,
            height: 280,
            borderRadius: "50%",
            background: `radial-gradient(circle, ${content.glow} 0%, transparent 70%)`,
            pointerEvents: "none",
          }}
        />

        {/* Icon */}
        <div
          className="flex items-center justify-center rounded-2xl mb-6 flex-shrink-0"
          style={{
            width: 64,
            height: 64,
            background: `${content.accent}18`,
            border: `1px solid ${content.accent}30`,
            color: content.accent,
          }}
        >
          {content.icon}
        </div>

        {/* Coming soon badge */}
        <div
          className="flex items-center gap-2 mb-4"
          style={{ animation: "fadeIn 0.5s ease both", animationDelay: "0.1s" }}
        >
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              fontWeight: 600,
              letterSpacing: "0.16em",
              color: content.accent,
              background: `${content.accent}18`,
              border: `1px solid ${content.accent}30`,
              padding: "3px 10px",
              borderRadius: 20,
            }}
          >
            COMING SOON
          </span>
        </div>

        {/* Title */}
        <h2
          style={{
            fontSize: "clamp(28px, 3.5vw, 48px)",
            fontWeight: 800,
            letterSpacing: "-0.03em",
            lineHeight: 1.1,
            color: "var(--dark-text)",
            marginBottom: 12,
          }}
        >
          {content.title}
        </h2>

        {/* Tagline */}
        <p
          style={{
            fontSize: 15,
            lineHeight: 1.65,
            color: "var(--dark-muted)",
            marginBottom: 28,
            maxWidth: 400,
          }}
        >
          {content.tagline}
        </p>

        {/* Bullet list */}
        <ul className="flex flex-col gap-3 mb-auto">
          {content.bullets.map((bullet, i) => (
            <li
              key={i}
              className="flex items-start gap-3"
              style={{
                animation: "fadeInUp 0.4s ease both",
                animationDelay: `${0.15 + i * 0.07}s`,
              }}
            >
              <span
                style={{
                  flexShrink: 0,
                  marginTop: 3,
                  width: 16,
                  height: 16,
                  borderRadius: "50%",
                  background: `${content.accent}20`,
                  border: `1px solid ${content.accent}40`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <svg width="8" height="8" viewBox="0 0 8 8" fill="none" aria-hidden="true">
                  <path d="M1.5 4L3 5.5L6.5 2" stroke={content.accent} strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </span>
              <span style={{ fontSize: 14, color: "var(--dark-muted)", lineHeight: 1.55 }}>
                {bullet}
              </span>
            </li>
          ))}
        </ul>

        {/* Divider */}
        <div
          style={{
            height: 1,
            background: `linear-gradient(90deg, ${content.accent}20, transparent)`,
            margin: "28px 0 20px",
          }}
        />

        {/* Stay tuned message */}
        <p
          style={{
            fontSize: 12,
            color: "var(--dark-muted)",
            fontFamily: "var(--font-mono)",
            letterSpacing: "0.04em",
          }}
        >
          <span style={{ color: content.accent }}>★</span> This feature is in development. Stay tuned for updates.
        </p>
      </div>
    </div>
  );
}
