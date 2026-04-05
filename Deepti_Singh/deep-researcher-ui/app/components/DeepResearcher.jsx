"use client";
import { useState, useRef, useCallback, useEffect } from "react";

const API_BASE = "http://localhost:8000";

/* ═══════════════════════════════════════════════════════════
   FUTURISTIC DESIGN SYSTEM
   ═══════════════════════════════════════════════════════════ */
const V = {
  void:      "#0B0B0F",
  lime:      "#CAFF04",
  uv:        "#8338EC",
  text:      "#EAEAEF",
  surface:   "#13131A",
  border:    "#1E1E2A",
  muted:     "#6B6B7A",
  limeDim:   "rgba(202,255,4,0.12)",
  uvDim:     "rgba(131,56,236,0.15)",
  limeGlow20:"rgba(202,255,4,0.2)",
  limeGlow40:"rgba(202,255,4,0.4)",
  uvGlow:    "rgba(131,56,236,0.35)",
  cyan:      "#00D4FF",
};

const STAGE_META = {
  clarifier:      { emoji: "🔍", label: "Clarifying",   short: "query clarity",      color: V.lime,    bg: V.limeDim },
  router:         { emoji: "🗺️", label: "Planning",     short: "search strategy",    color: V.uv,      bg: V.uvDim },
  retriever:      { emoji: "🌐", label: "Retrieving",   short: "web sources",        color: "#00D4FF", bg: "rgba(0,212,255,0.12)" },
  analyzer:       { emoji: "🧠", label: "Analyzing",    short: "key findings",       color: "#FF6B6B", bg: "rgba(255,107,107,0.12)" },
  insight:        { emoji: "💡", label: "Insights",     short: "patterns & trends",  color: "#FFB800", bg: "rgba(255,184,0,0.12)" },
  factcheck:      { emoji: "✅", label: "Fact-check",   short: "claim verification", color: "#00E676", bg: "rgba(0,230,118,0.12)" },
  visualizer:     { emoji: "📊", label: "Visualizing",  short: "charts & graphs",    color: "#00D4FF", bg: "rgba(0,212,255,0.12)" },
  report_builder: { emoji: "📝", label: "Writing",      short: "final report",       color: V.uv,      bg: V.uvDim },
};

const ALL_STAGES = Object.keys(STAGE_META);

/* ── Progress Ring ── */
function ProgressRing({ progress, size = 120, stroke = 8 }) {
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (progress / 100) * circ;
  return (
    <svg width={size} height={size} style={{ transform: "rotate(-90deg)", display: "block", filter: `drop-shadow(0 0 12px ${V.limeGlow40})` }}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={V.border} strokeWidth={stroke} />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none"
        stroke={V.lime} strokeWidth={stroke}
        strokeDasharray={circ} strokeDashoffset={offset}
        strokeLinecap="round"
        style={{ transition: "stroke-dashoffset .5s cubic-bezier(.4,0,.2,1)" }}
      />
    </svg>
  );
}

/* ── Agent Timeline ── */
function AgentTimeline({ events, currentStage }) {
  const done = new Set();
  events.forEach(e => { if (e.event === "progress" && e.data.stage) done.add(e.data.stage); });
  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      {ALL_STAGES.map((key, i) => {
        const m = STAGE_META[key];
        const isActive  = currentStage === key;
        const isDone    = done.has(key);
        const isPending = !isDone && !isActive;
        return (
          <div key={key} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", flexShrink: 0 }}>
              <div style={{
                width: 30, height: 30, borderRadius: 8,
                background: isDone ? m.color : isActive ? m.bg : V.border,
                border: isActive ? `2px solid ${m.color}` : "2px solid transparent",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 14,
                filter: isPending ? "grayscale(1) opacity(.3)" : "none",
                transition: "all .35s cubic-bezier(.16,1,.3,1)",
                boxShadow: isActive ? `0 0 14px ${m.bg}` : isDone ? `0 0 8px ${m.bg}` : "none",
              }}>
                {isDone
                  ? <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={V.void} strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                  : m.emoji}
              </div>
              {i < ALL_STAGES.length - 1 && (
                <div style={{
                  width: 2, height: 20, margin: "2px 0", borderRadius: 1,
                  background: isDone ? m.color : V.border,
                  transition: "background .3s",
                }} />
              )}
            </div>
            <div style={{ paddingTop: 4, paddingBottom: 2 }}>
              <p style={{
                margin: 0, fontSize: 12, fontWeight: isActive ? 700 : 500,
                color: isActive ? m.color : isDone ? V.text : V.muted,
                fontFamily: "'DM Sans', sans-serif",
                transition: "color .3s",
                textShadow: isActive ? `0 0 15px ${m.bg}` : "none",
              }}>{m.label}</p>
              {isActive && (
                <p style={{ margin: "1px 0 0", fontSize: 10, color: m.color, opacity: .6, fontFamily: "'JetBrains Mono', monospace", letterSpacing: ".5px" }}>{m.short}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ── Markdown Renderer (Dark Mode) ── */
function MD({ content }) {
  const html = content
    .replace(/^# (.+)$/gm,   `<h1 style="font-size:1.8rem;font-weight:800;color:#EAEAEF;margin:2rem 0 .75rem;letter-spacing:-.5px;line-height:1.2">$1</h1>`)
    .replace(/^## (.+)$/gm,  `<h2 style="font-size:1.2rem;font-weight:700;color:#CAFF04;margin:1.75rem 0 .6rem;letter-spacing:-.2px">$1</h2>`)
    .replace(/^### (.+)$/gm, `<h3 style="font-size:1.05rem;font-weight:600;color:#8338EC;margin:1.25rem 0 .4rem">$1</h3>`)
    .replace(/\*\*(.+?)\*\*/g, `<strong style="font-weight:700;color:#EAEAEF">$1</strong>`)
    .replace(/\*(.+?)\*/g,    `<em style="color:#9999A8">$1</em>`)
    .replace(/`(.+?)`/g,      `<code style="background:rgba(202,255,4,0.08);color:#CAFF04;padding:2px 7px;border-radius:4px;font-size:.85em;font-family:'JetBrains Mono',monospace">$1</code>`)
    .replace(/^> (.+)$/gm,    `<blockquote style="border-left:3px solid #8338EC;padding:.6rem 1rem;margin:.75rem 0;background:rgba(131,56,236,0.08);border-radius:0 8px 8px 0;color:#9999A8;font-style:italic">$1</blockquote>`)
    .replace(/^[-*] (.+)$/gm, `<li style="margin:.3rem 0;color:#B3B3C0;padding-left:.15rem">$1</li>`)
    .replace(/(<li.*?<\/li>\n?)+/gs, m => `<ul style="margin:.6rem 0 .6rem 1.4rem;list-style:disc">${m}</ul>`)
    .replace(/\n\n/g,          `</p><p style="margin:.8rem 0;color:#B3B3C0;line-height:1.85;font-size:.95rem">`)
    .replace(/^(?!<[hbulic])(.{10,})$/gm, `<p style="margin:.8rem 0;color:#B3B3C0;line-height:1.85;font-size:.95rem">$1</p>`);
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}

/* ── Source Card ── */
function SourceCard({ source, i }) {
  const CRED = {
    high:    ["#00E676", "rgba(0,230,118,0.12)"],
    medium:  ["#FFB800", "rgba(255,184,0,0.12)"],
    low:     ["#FF6B6B", "rgba(255,107,107,0.12)"],
    unknown: [V.muted,   "rgba(107,107,122,0.12)"],
  };
  const [c, bg] = CRED[source.credibility] || CRED.unknown;
  return (
    <a href={source.url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: "none", display: "block" }}>
      <div className="src-card" style={{
        background: V.surface, borderRadius: 14, border: `1px solid ${V.border}`,
        padding: "1rem 1.1rem", transition: "all .3s cubic-bezier(.16,1,.3,1)",
      }}>
        <div style={{ display: "flex", gap: 6, marginBottom: 8, flexWrap: "wrap" }}>
          <span style={{ display: "inline-block", padding: "2px 10px", borderRadius: 99, fontSize: 10, fontWeight: 700, letterSpacing: ".5px", color: V.lime, background: V.limeDim, fontFamily: "'JetBrains Mono', monospace", textTransform: "uppercase" }}>{source.source_type}</span>
          <span style={{ display: "inline-block", padding: "2px 10px", borderRadius: 99, fontSize: 10, fontWeight: 700, letterSpacing: ".5px", color: c, background: bg, fontFamily: "'JetBrains Mono', monospace", textTransform: "uppercase" }}>{source.credibility}</span>
          {source.published_at && (
            <span style={{ display: "inline-block", padding: "2px 10px", borderRadius: 99, fontSize: 10, fontWeight: 600, color: V.muted, background: "rgba(107,107,122,0.08)", fontFamily: "'JetBrains Mono', monospace" }}>{source.published_at.slice(0, 10)}</span>
          )}
        </div>
        <p style={{ margin: "0 0 4px", fontSize: 13, fontWeight: 700, color: V.text, lineHeight: 1.35 }}>
          {source.title || `Source ${i + 1}`}
        </p>
        {source.snippet && (
          <p style={{ margin: "0 0 6px", fontSize: 12, color: V.muted, lineHeight: 1.5, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
            {source.snippet}
          </p>
        )}
        <p style={{ margin: 0, fontSize: 11, color: "#4A4A5A", fontFamily: "'JetBrains Mono', monospace", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{source.url}</p>
      </div>
    </a>
  );
}

/* ═══════════════════════════════════════════════════════════
   MAIN COMPONENT
   ═══════════════════════════════════════════════════════════ */
export default function DeepResearcher() {
  const [phase, setPhase]        = useState("home");
  const [topic, setTopic]        = useState("");
  const [taskId, setTaskId]      = useState(null);
  const [events, setEvents]      = useState([]);
  const [currentStage, setStage] = useState("");
  const [progress, setProgress]  = useState(0);
  const [currentMsg, setMsg]     = useState("");
  const [expandedStep, setExpandedStep] = useState(null);
  const [clarifyQ, setClarifyQ]  = useState([]);
  const [clarifyA, setClarifyA]  = useState([]);
  const [result, setResult]      = useState(null);
  const [tab, setTab]            = useState("report");
  const [error, setError]        = useState(null);
  const [busy, setBusy]          = useState(false);
  const [activeWorkflowMsg, setActiveWorkflowMsg] = useState("Allocating multi-agent context...");
  const esRef = useRef(null);

  useEffect(() => {
    if (phase !== "researching") return;
    const msgs = [
      "Synthesizing knowledge graph components...",
      "Activating primary reasoning layer...",
      "Extracting structured metadata...",
      "Validating heuristic constraints across nodes...",
      "Building semantic embeddings...",
      "Executing sub-agent tool calls...",
      "Awaiting inference API token streams...",
      "Refining step-by-step logic iteratively...",
      "Collating scattered context vectors...",
      "Formatting intermediate internal thoughts..."
    ];
    let i = 0;
    const interval = setInterval(() => {
      i = (i + 1) % msgs.length;
      setActiveWorkflowMsg(msgs[i]);
    }, 3800);
    return () => clearInterval(interval);
  }, [phase]);

  /* ── Parallax mouse tracking ── */
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  useEffect(() => {
    const handleMouseMove = (e) => {
      requestAnimationFrame(() => {
        setMousePos({
          x: (e.clientX / window.innerWidth - 0.5) * 40,
          y: (e.clientY / window.innerHeight - 0.5) * 40,
        });
      });
    };
    window.addEventListener("mousemove", handleMouseMove, { passive: true });
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  /* ── SSE Connection (integrated with Deepti_Singh API) ── */
  const connectSSE = useCallback((id) => {
    if (esRef.current) esRef.current.close();
    const es = new EventSource(`${API_BASE}/research/${id}/stream`);
    esRef.current = es;
    let isTerminalEvent = false;

    es.addEventListener("message", async (e) => {
      try {
        const payload = JSON.parse(e.data);
        const { type, data } = payload;
        
        switch (type) {
          case "pipeline_start":
            break;
          case "pipeline_resumed":
            setPhase("researching");
            break;
          case "agent_update":
            const stageMap = {
              "QueryClarifier": "clarifier",
              "OrchestratorAgent": "router",
              "RetrieverAgent": "retriever",
              "AnalyzerAgent": "analyzer",
              "FactCheckerAgent": "factcheck",
              "InsightAgent": "insight",
              "VisualizerAgent": "visualizer",
              "ReportBuilderAgent": "report_builder"
            };
            const mappedStage = stageMap[data.agent] || "retriever";
            setStage(mappedStage);
            setMsg(data.notes || data.status || "");
            setProgress(p => Math.min(p + 10, 95));
            setEvents(p => {
               // Deduplicate to avoid repeating events if same instance
               if (p.some(ev => ev.data?.message === (data.notes || data.status))) return p;
               return [...p, { id: Math.random().toString(36).substr(2, 9), event: "progress", data: { stage: mappedStage, agent: data.agent, message: data.notes || data.status, notes: data.notes, status: data.status, error: data.error } }];
            });
            setError(null);
            break;
          case "clarification_needed":
            setClarifyQ(data.questions.map(q => q.question));
            setClarifyA(data.questions.map(() => ""));
            setPhase("clarifying");
            setEvents(p => [...p, { event: "clarification_needed", data }]);
            break;
          case "pipeline_complete":
            setProgress(100); setMsg("Done!"); setEvents(p => [...p, { event: "complete", data }]); isTerminalEvent = true; es.close();
            try {
              const r = await fetch(`${API_BASE}/research/${id}/report`);
              const baseResult = await r.json();
              const s_res = await fetch(`${API_BASE}/research/${id}/sources`);
              const s_data = await s_res.json();
              setResult({
                  topic: baseResult.query,
                  report_markdown: baseResult.report_markdown,
                  sources: s_data.sources || [],
                  charts: (baseResult.metadata.visualizations || []).map(v => ({ title: v, image: null, description: "Local path: " + v })),
                  queries_used: baseResult.metadata.sub_queries || [],
                  focus_areas: baseResult.metadata.key_themes || [],
              });
              setPhase("result");
            } catch (err) { setError("Could not fetch result"); }
            break;
          case "error":
            setError(data.message); setPhase("home"); isTerminalEvent = true; es.close();
            break;
          case "stream_end":
            isTerminalEvent = true; 
            es.close();
            break;
        }
      } catch (err) {}
    });

    es.addEventListener("open", () => setError(null));
    es.onerror = () => {
      if (!isTerminalEvent) {
        setError("⚠️ Backend connection lost. Checking...");
        fetch(`${API_BASE}/health`).then(r => {
          if (r.ok) setError("Backend is running but stream disconnected. Click 'New Research' to retry.");
          else setError("❌ Backend not responding. Make sure uvicorn is running on port 8000.");
        }).catch(() => setError("❌ Backend unreachable. Run: uvicorn controllers.api:app --reload --port 8000"));
      }
    };
  }, []);

  const startResearch = useCallback(async () => {
    if (!topic.trim() || busy) return;
    setBusy(true); setError(null); setEvents([]); setProgress(0); setStage(""); setResult(null);
    try {
      const res = await fetch(`${API_BASE}/research/start`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: topic.trim(), max_iterations: 2 }) });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "Failed to start");
      setTaskId(d.session_id); setPhase("researching"); connectSSE(d.session_id);
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }, [topic, busy, connectSSE]);

  const submitClarify = useCallback(async () => {
    if (!taskId || busy) return;
    setBusy(true);
    try {
      const answerText = clarifyA.join("\n");
      const res = await fetch(`${API_BASE}/research/${taskId}/clarify`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ answer: answerText }) });
      if (!res.ok) throw new Error((await res.json()).detail);
      setEvents([]); // Prevent duplication of timeline events upon reloading stream
      setPhase("researching"); connectSSE(taskId);
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }, [taskId, busy, clarifyA, connectSSE]);

  const reset = () => {
    if (esRef.current) esRef.current.close();
    setPhase("home"); setTopic(""); setTaskId(null); setEvents([]); setProgress(0);
    setStage(""); setMsg(""); setResult(null); setError(null); setClarifyQ([]); setClarifyA([]);
  };

  /* ═══════ RENDER ═══════ */
  return (
    <div style={{ minHeight: "100vh", background: V.void, fontFamily: "'DM Sans', sans-serif", position: "relative", overflow: "hidden" }}>

      {/* ── Inline keyframes ── */}
      <style>{`
        @keyframes fadeUp  { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
        @keyframes pop     { 0%{transform:scale(.94);opacity:0} 60%{transform:scale(1.02)} 100%{transform:scale(1);opacity:1} }
        @keyframes blink   { 0%,100%{opacity:1} 50%{opacity:.1} }
        @keyframes scan    { 0%{transform:translateY(-100%)} 100%{transform:translateY(100vh)} }
        @keyframes floatY  { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-20px)} }
        @keyframes pulseGlow { 0%,100%{box-shadow:0 0 20px rgba(202,255,4,0.15)} 50%{box-shadow:0 0 50px rgba(202,255,4,0.35)} }
        @keyframes borderGlow { 0%,100%{border-color:rgba(202,255,4,0.15)} 50%{border-color:rgba(202,255,4,0.4)} }
        @keyframes shimmer { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
        @keyframes fadePulse { 0%{opacity:0.4} 100%{opacity:1} }
        .src-card:hover{border-color:rgba(202,255,4,0.3)!important;box-shadow:0 0 25px rgba(202,255,4,0.06),inset 0 0 25px rgba(202,255,4,0.02);transform:translateY(-3px)!important}
        .hov-tab:hover{background:rgba(202,255,4,0.06)!important;color:#CAFF04!important}
        .input-glow:focus{border-color:#CAFF04!important;box-shadow:0 0 0 3px rgba(202,255,4,0.1),0 0 25px rgba(202,255,4,0.08)!important}
        .btn-lime-glow:hover{box-shadow:0 0 40px rgba(202,255,4,0.45),0 0 80px rgba(202,255,4,0.15)!important;transform:translateY(-2px) scale(1.02)!important}
        .btn-lime-glow:active{transform:translateY(0) scale(0.98)!important}
        .card-hover:hover{border-color:rgba(131,56,236,0.4)!important;box-shadow:0 0 25px rgba(131,56,236,0.1)!important}
        .event-card:hover{border-color:rgba(202,255,4,0.2)!important;background:#16161F!important}
        textarea,input{font-family:'DM Sans',sans-serif!important}
        textarea::placeholder{color:#4A4A5A!important}
      `}</style>

      {/* ── Scan Line ── */}
      <div style={{
        position: "fixed", top: 0, left: 0, right: 0, height: 2,
        background: "linear-gradient(to right, transparent, rgba(202,255,4,0.15), transparent)",
        animation: "scan 8s linear infinite",
        pointerEvents: "none", zIndex: 50,
      }} />

      {/* ── Parallax Orbs ── */}
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0, overflow: "hidden" }}>
        <div style={{ position: "absolute", top: "-12%", right: "-8%", transform: `translate(${mousePos.x * 0.5}px, ${mousePos.y * 0.5}px)`, transition: "transform 0.4s cubic-bezier(.16,1,.3,1)" }}>
          <div style={{ width: 550, height: 550, borderRadius: "50%", background: "radial-gradient(circle, rgba(202,255,4,0.06) 0%, transparent 70%)", animation: "floatY 8s ease-in-out infinite" }} />
        </div>
        <div style={{ position: "absolute", bottom: "-10%", left: "-5%", transform: `translate(${mousePos.x * -0.3}px, ${mousePos.y * -0.3}px)`, transition: "transform 0.4s cubic-bezier(.16,1,.3,1)" }}>
          <div style={{ width: 480, height: 480, borderRadius: "50%", background: "radial-gradient(circle, rgba(131,56,236,0.08) 0%, transparent 70%)", animation: "floatY 10s ease-in-out infinite 2s" }} />
        </div>
        <div style={{ position: "absolute", top: "35%", left: "45%", transform: `translate(${mousePos.x * 0.2}px, ${mousePos.y * 0.2}px)`, transition: "transform 0.4s cubic-bezier(.16,1,.3,1)" }}>
          <div style={{ width: 350, height: 350, borderRadius: "50%", background: "radial-gradient(circle, rgba(0,212,255,0.04) 0%, transparent 70%)", animation: "floatY 12s ease-in-out infinite 4s" }} />
        </div>
      </div>

      {/* ── Grid Background (home only) ── */}
      {phase === "home" && (
        <div style={{
          position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0,
          backgroundImage: "linear-gradient(rgba(30,30,42,0.35) 1px, transparent 1px), linear-gradient(90deg, rgba(30,30,42,0.35) 1px, transparent 1px)",
          backgroundSize: "50px 50px",
        }} />
      )}

      {/* ═══════════════════════════════
          HEADER
          ═══════════════════════════════ */}
      <header style={{
        background: "rgba(11,11,15,0.75)", backdropFilter: "blur(20px)", WebkitBackdropFilter: "blur(20px)",
        borderBottom: `1px solid ${V.border}`,
        padding: "0 2rem", height: 56,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        position: "sticky", top: 0, zIndex: 100,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 7,
            background: `linear-gradient(135deg, ${V.lime}, ${V.uv})`,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 13, boxShadow: `0 0 18px ${V.limeGlow20}`,
          }}>🔬</div>
          <span style={{ fontSize: 15, fontWeight: 800, color: V.text, letterSpacing: "-.3px" }}>
            deep<span style={{ color: V.lime }}>search</span>
          </span>
          <span style={{
            fontSize: 10, fontWeight: 600, color: V.void, background: V.lime,
            padding: "1px 8px", borderRadius: 99, marginLeft: 4,
            fontFamily: "'JetBrains Mono', monospace", letterSpacing: ".5px",
          }}>v2</span>
        </div>
        {phase !== "home" && (
          <button onClick={reset} style={{
            background: "transparent", border: `1px solid ${V.border}`, borderRadius: 99,
            padding: "5px 16px", fontSize: 12, fontWeight: 600, color: V.muted,
            cursor: "pointer", fontFamily: "'DM Sans', sans-serif",
            transition: "all .25s cubic-bezier(.16,1,.3,1)",
          }}
            onMouseEnter={e => { e.target.style.borderColor = V.lime; e.target.style.color = V.lime; }}
            onMouseLeave={e => { e.target.style.borderColor = V.border; e.target.style.color = V.muted; }}
          >← new search</button>
        )}
      </header>

      {/* ═══════════════════════════════
          HOME PHASE
          ═══════════════════════════════ */}
      {phase === "home" && (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "calc(100vh - 56px)", padding: "2rem", position: "relative", zIndex: 1 }}>
          <div style={{ maxWidth: 640, width: "100%", animation: "fadeUp .6s cubic-bezier(.16,1,.3,1)" }}>

            {/* Hero Text */}
            <div style={{ marginBottom: "2.25rem" }}>
              <div style={{
                display: "inline-flex", alignItems: "center", gap: 6,
                background: V.limeDim, border: "1px solid rgba(202,255,4,0.2)",
                borderRadius: 99, padding: "5px 14px",
                fontSize: 10, fontWeight: 700, color: V.lime,
                marginBottom: 16, letterSpacing: ".8px", textTransform: "uppercase",
                fontFamily: "'JetBrains Mono', monospace",
              }}>⚡ 8-AGENT AI PIPELINE</div>
              <h1 style={{
                fontSize: "clamp(2.2rem, 5vw, 3.4rem)", fontWeight: 900, color: V.text,
                margin: "0 0 .8rem", lineHeight: 1.05, letterSpacing: "-1.2px",
              }}>
                Research anything,<br />
                <span style={{ color: V.lime, textShadow: `0 0 40px ${V.limeGlow40}, 0 0 80px ${V.limeGlow20}` }}>deeply.</span>
              </h1>
              <p style={{ fontSize: 15, color: V.muted, margin: 0, lineHeight: 1.65, fontWeight: 500, maxWidth: 500 }}>
                Drop in a topic — our agents clarify, search, analyze, fact-check, and hand you a polished report with charts.
              </p>
            </div>

            {/* Input Card */}
            <div style={{
              background: V.surface, borderRadius: 18,
              border: `1px solid ${V.border}`, padding: "1.75rem",
              boxShadow: `0 0 50px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)`,
              animation: "pulseGlow 4s ease-in-out infinite",
            }}>
              <textarea
                value={topic}
                onChange={e => setTopic(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) startResearch(); }}
                rows={3}
                placeholder="e.g. What are the economic effects of remote work on mid-sized US cities?"
                className="input-glow"
                style={{
                  width: "100%", border: `1px solid ${V.border}`, borderRadius: 12,
                  padding: ".875rem 1rem", fontSize: 15, fontWeight: 500, color: V.text,
                  lineHeight: 1.6, outline: "none", background: "rgba(255,255,255,0.03)",
                  transition: "all .25s cubic-bezier(.16,1,.3,1)", resize: "vertical",
                  fontFamily: "'DM Sans', sans-serif",
                }}
              />
              {error && (
                <div style={{
                  margin: "10px 0 0", padding: "8px 14px",
                  background: "rgba(255,107,107,0.12)", border: "1px solid rgba(255,107,107,0.2)",
                  borderRadius: 10, fontSize: 13, fontWeight: 600, color: "#FF6B6B",
                }}>⚠️ {error}</div>
              )}
              <button
                className="btn-lime-glow"
                onClick={startResearch}
                disabled={!topic.trim() || busy}
                style={{
                  marginTop: 14, width: "100%", padding: ".9rem",
                  background: topic.trim() ? V.lime : V.border,
                  color: topic.trim() ? V.void : V.muted,
                  border: "none", borderRadius: 12, fontSize: 15, fontWeight: 800,
                  cursor: topic.trim() ? "pointer" : "not-allowed",
                  fontFamily: "'DM Sans', sans-serif", letterSpacing: "-.1px",
                  transition: "all .25s cubic-bezier(.16,1,.3,1)",
                  boxShadow: topic.trim() ? `0 0 30px ${V.limeGlow20}` : "none",
                }}>
                {busy ? "Initializing…" : "Start deep research →"}
              </button>
              <p style={{
                textAlign: "center", margin: "10px 0 0", fontSize: 10,
                color: V.muted, fontWeight: 600, letterSpacing: ".5px",
                fontFamily: "'JetBrains Mono', monospace",
              }}>⌘ + ENTER</p>
            </div>

            {/* Agent Badges */}
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 22, justifyContent: "center" }}>
              {Object.values(STAGE_META).map((m, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", gap: 5,
                  background: m.bg, border: `1px solid ${m.color}22`,
                  borderRadius: 99, padding: "4px 12px",
                  fontSize: 11, fontWeight: 600, color: m.color,
                  animation: `pop .4s ${i * 0.06}s ease both`,
                  fontFamily: "'DM Sans', sans-serif",
                }}>
                  <span style={{ fontSize: 12 }}>{m.emoji}</span>{m.label}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════
          RESEARCHING PHASE
          ═══════════════════════════════ */}
      {phase === "researching" && (
        <div style={{ maxWidth: 920, margin: "0 auto", padding: "2rem", display: "flex", gap: 24, animation: "fadeUp .4s ease", position: "relative", zIndex: 1 }}>

          {/* Sidebar */}
          <div style={{ width: 220, flexShrink: 0 }}>
            <div style={{
              background: V.surface, borderRadius: 16, border: `1px solid ${V.border}`,
              padding: "1.25rem", position: "sticky", top: 72,
              boxShadow: "0 0 35px rgba(0,0,0,0.25)",
            }}>
              <div style={{ textAlign: "center", marginBottom: "1.1rem" }}>
                <div style={{ position: "relative", display: "inline-block" }}>
                  <ProgressRing progress={progress} />
                  <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
                    <span style={{
                      fontSize: 24, fontWeight: 800, color: V.lime, letterSpacing: "-1px",
                      fontFamily: "'JetBrains Mono', monospace",
                      textShadow: `0 0 25px ${V.limeGlow40}`,
                    }}>{progress}%</span>
                    <span style={{ fontSize: 9, color: V.muted, fontWeight: 700, letterSpacing: "1px", fontFamily: "'JetBrains Mono', monospace" }}>COMPLETE</span>
                  </div>
                </div>
              </div>
              <AgentTimeline events={events} currentStage={currentStage} />
            </div>
          </div>

          {/* Main Content */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: ".5rem" }}>
              <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, color: V.text, letterSpacing: "-.3px" }}>Researching</h2>
              <div style={{ display: "flex", gap: 3 }}>
                {[0, 1, 2].map(i => (
                  <div key={i} style={{
                    width: 4, height: 4, borderRadius: "50%", background: V.lime,
                    animation: `blink 1.3s ${i * 0.22}s ease-in-out infinite`,
                    boxShadow: `0 0 8px ${V.limeGlow40}`,
                  }} />
                ))}
              </div>
            </div>
            <p style={{ margin: "0 0 1.25rem", fontSize: 13, fontWeight: 500, color: V.muted }}>
              Topic: <span style={{ color: V.text, fontWeight: 600 }}>{topic}</span>
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {events.filter(e => e.event === "progress").map((evt, i) => {
                const m = STAGE_META[evt.data.stage] || {};
                const isExpanded = expandedStep === evt.id;
                
                const parseNotes = (notes) => {
                   if (!notes) return null;
                   return (
                     <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                       {notes.split(",").map(n => n.trim()).map((n, idx) => (
                         <span key={idx} style={{ background: "rgba(255,255,255,0.03)", padding: "3px 8px", borderRadius: 6, border: `1px solid rgba(255,255,255,0.1)`, color: V.text, fontFamily: "'JetBrains Mono', monospace", fontSize: 10 }}>{n}</span>
                       ))}
                     </div>
                   );
                };
                
                return (
                  <div key={evt.id || i} onClick={() => setExpandedStep(isExpanded ? null : evt.id)} style={{
                    cursor: "pointer", background: isExpanded ? "rgba(255,255,255,0.02)" : V.surface, borderRadius: 12,
                    border: `1px solid ${isExpanded ? m.color : V.border}`, borderLeft: `3px solid ${m.color || V.lime}`,
                    padding: ".85rem 1rem", animation: "fadeUp .3s ease",
                    transition: "all .3s cubic-bezier(.16,1,.3,1)",
                  }} className={!isExpanded ? "event-card" : ""}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span style={{ fontSize: 14 }}>{m.emoji}</span>
                      <span style={{ fontSize: 13, fontWeight: 700, color: V.text }}>{evt.data.agent || m.label}</span>
                      <span style={{
                        marginLeft: "auto", fontSize: 10, fontWeight: 700,
                        background: (evt.data.status || "").toLowerCase().includes("fail") || evt.data.error ? "rgba(255,107,107,0.12)" : m.bg, 
                        color: (evt.data.status || "").toLowerCase().includes("fail") || evt.data.error ? "#FF6B6B" : m.color,
                        padding: "2px 10px", borderRadius: 99,
                        fontFamily: "'JetBrains Mono', monospace", textTransform: "uppercase",
                        boxShadow: `0 0 10px ${(evt.data.status || "").toLowerCase().includes("fail") || evt.data.error ? "rgba(255,107,107,0.2)" : "transparent"}`
                      }}>{evt.data.status || "updating"}</span>
                    </div>

                    <div style={{ margin: "5px 0 0 22px" }}>
                       {parseNotes(evt.data.notes || evt.data.message)}
                    </div>

                    {isExpanded && (
                       <div style={{ marginTop: 14, marginLeft: 22, paddingTop: 14, borderTop: `1px dashed ${V.border}`, animation: "fadeUp .2s ease" }}>
                          <p style={{ margin: "0 0 6px", fontSize: 11, color: V.lime, fontFamily: "'JetBrains Mono', monospace", textTransform: "uppercase" }}>Agent Introspection Log</p>
                          <div style={{ background: "#0B0B0F", padding: "12px", borderRadius: 8, border: `1px solid ${V.border}`, color: "#A0A0B0", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
                             {JSON.stringify(evt.data, null, 2)}
                          </div>
                          {evt.data.error && (
                            <div style={{ marginTop: 8, background: "rgba(255,107,107,0.12)", color: "#FF6B6B", border: "1px solid rgba(255,107,107,0.2)", padding: "10px", borderRadius: 6, fontSize: 11, fontFamily: "'JetBrains Mono', monospace" }}>
                              {evt.data.error}
                            </div>
                          )}
                       </div>
                    )}
                  </div>
                );
              })}
              {events.filter(e => e.event === "progress").length === 0 && (
                <div style={{ padding: "4rem", textAlign: "center", color: V.muted, background: V.surface, borderRadius: 16, border: `1px solid ${V.border}` }}>
                  <div style={{ fontSize: 38, marginBottom: 12 }}>🚀</div>
                  <p style={{ margin: 0, fontSize: 14, fontWeight: 600, color: V.text }}>Spinning up the pipeline…</p>
                  <p style={{ margin: "6px 0 0", fontSize: 11, color: V.muted, fontFamily: "'JetBrains Mono', monospace", letterSpacing: ".5px" }}>INITIALIZING AGENTS</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════
          CLARIFYING PHASE
          ═══════════════════════════════ */}
      {phase === "clarifying" && (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "calc(100vh - 56px)", padding: "2rem", position: "relative", zIndex: 1 }}>
          <div style={{ maxWidth: 560, width: "100%", animation: "pop .4s ease" }}>
            <div style={{
              background: V.surface, borderRadius: 18,
              border: `1px solid rgba(131,56,236,0.3)`,
              padding: "2rem",
              boxShadow: `0 0 40px rgba(131,56,236,0.08), 0 0 80px rgba(0,0,0,0.3)`,
            }}>
              <div style={{ display: "flex", gap: 12, alignItems: "flex-start", marginBottom: "1.5rem" }}>
                <span style={{ fontSize: 32, lineHeight: 1 }}>🤔</span>
                <div>
                  <h2 style={{ margin: "0 0 4px", fontSize: 18, fontWeight: 800, color: V.text, letterSpacing: "-.2px" }}>Quick questions first</h2>
                  <p style={{ margin: 0, fontSize: 13, color: V.muted, fontWeight: 500 }}>Helps focus the research for sharper results</p>
                </div>
              </div>
              {clarifyQ.map((q, i) => (
                <div key={i} style={{ marginBottom: "1.1rem" }}>
                  <label style={{ display: "block", fontSize: 13, fontWeight: 700, color: V.text, marginBottom: 6 }}>
                    <span style={{ color: V.uv, fontFamily: "'JetBrains Mono', monospace", fontSize: 12 }}>{String(i + 1).padStart(2, "0")}.</span> {q}
                  </label>
                  <textarea
                    value={clarifyA[i] || ""}
                    onChange={e => { const a = [...clarifyA]; a[i] = e.target.value; setClarifyA(a); }}
                    rows={2}
                    placeholder="Your answer…"
                    className="input-glow"
                    style={{
                      width: "100%", border: `1px solid ${V.border}`, borderRadius: 10,
                      padding: ".7rem .9rem", fontSize: 14, fontWeight: 500, color: V.text,
                      outline: "none", background: "rgba(255,255,255,0.03)",
                      transition: "all .25s cubic-bezier(.16,1,.3,1)", resize: "vertical",
                      fontFamily: "'DM Sans', sans-serif",
                    }}
                  />
                </div>
              ))}
              {error && (
                <div style={{ padding: "8px 14px", background: "rgba(255,107,107,0.12)", border: "1px solid rgba(255,107,107,0.2)", borderRadius: 10, fontSize: 13, fontWeight: 600, color: "#FF6B6B", marginBottom: 10 }}>⚠️ {error}</div>
              )}
              <button
                className="btn-lime-glow"
                onClick={submitClarify}
                disabled={busy || clarifyA.every(a => !a.trim())}
                style={{
                  width: "100%", padding: ".85rem", background: V.lime, color: V.void,
                  border: "none", borderRadius: 12, fontSize: 15, fontWeight: 800,
                  cursor: "pointer", fontFamily: "'DM Sans', sans-serif", letterSpacing: "-.1px",
                  transition: "all .25s cubic-bezier(.16,1,.3,1)",
                  boxShadow: `0 0 25px ${V.limeGlow20}`,
                }}>
                {busy ? "Resuming…" : "Continue research →"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════
          RESULT PHASE
          ═══════════════════════════════ */}
      {phase === "result" && result && (
        <div style={{ maxWidth: 1100, margin: "0 auto", padding: "2rem", animation: "fadeUp .45s ease", position: "relative", zIndex: 1 }}>

          {/* Hero Banner */}
          <div style={{
            background: `linear-gradient(135deg, ${V.surface} 0%, rgba(131,56,236,0.15) 50%, rgba(202,255,4,0.08) 100%)`,
            borderRadius: 18, padding: "1.6rem 2rem", marginBottom: "1.2rem",
            border: `1px solid ${V.border}`,
            boxShadow: "0 0 50px rgba(0,0,0,0.3)",
            position: "relative", overflow: "hidden",
          }}>
            {/* Subtle shimmer overlay */}
            <div style={{
              position: "absolute", inset: 0, pointerEvents: "none",
              background: "linear-gradient(90deg, transparent 0%, rgba(202,255,4,0.03) 50%, transparent 100%)",
              backgroundSize: "200% 100%", animation: "shimmer 6s linear infinite",
            }} />
            <div style={{ position: "relative", zIndex: 1 }}>
              <div style={{ display: "flex", gap: 7, flexWrap: "wrap", marginBottom: 10 }}>
                {[
                  result.depth && `${result.depth} depth`,
                  result.sources?.length && `${result.sources.length} sources`,
                  result.sources?.filter(s => s.credibility === "high").length + " highly credible",
                ].filter(Boolean).map((t, i) => (
                  <span key={i} style={{
                    background: V.limeDim, border: "1px solid rgba(202,255,4,0.2)",
                    borderRadius: 99, padding: "3px 12px",
                    fontSize: 10, fontWeight: 700, color: V.lime,
                    fontFamily: "'JetBrains Mono', monospace", letterSpacing: ".3px", textTransform: "uppercase",
                  }}>{t}</span>
                ))}
              </div>
              <h1 style={{ margin: 0, fontSize: "clamp(1.25rem, 3vw, 1.75rem)", fontWeight: 800, lineHeight: 1.2, letterSpacing: "-.4px", color: V.text }}>{result.topic}</h1>
            </div>
          </div>

          {/* Tab Bar */}
          <div style={{
            display: "flex", gap: 4, background: V.surface,
            borderRadius: 14, border: `1px solid ${V.border}`,
            padding: 4, marginBottom: "1.2rem",
          }}>
            {[
              { k: "report",  icon: "📄", label: "Report" },
              { k: "credibility",  icon: "🛡️", label: "Credibility" },
              { k: "sources", icon: "🔗", label: `Sources (${result.sources?.length || 0})` },
              { k: "queries", icon: "🔎", label: "Queries" },
            ].map(t => (
              <button key={t.k} className="hov-tab" onClick={() => setTab(t.k)} style={{
                flex: 1, padding: ".6rem .4rem", border: "none", borderRadius: 10,
                background: tab === t.k ? V.lime : "transparent",
                color: tab === t.k ? V.void : V.muted,
                fontSize: 13, fontWeight: tab === t.k ? 800 : 600, cursor: "pointer",
                fontFamily: "'DM Sans', sans-serif",
                transition: "all .25s cubic-bezier(.16,1,.3,1)", letterSpacing: "-.1px",
                boxShadow: tab === t.k ? `0 0 20px ${V.limeGlow20}` : "none",
              }}>{t.icon} {t.label}</button>
            ))}
          </div>

          {/* ── Report Tab ── */}
          {tab === "report" && (
            <div style={{
              background: V.surface, borderRadius: 16,
              border: `1px solid ${V.border}`,
              padding: "2.25rem 2.75rem",
              boxShadow: "0 0 35px rgba(0,0,0,0.15)",
            }}>
              {result.report_markdown ? <MD content={result.report_markdown} /> : <p style={{ color: V.muted }}>No report.</p>}
            </div>
          )}

          {/* ── Credibility Tab ── */}
          {tab === "credibility" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
              {result.sources?.length > 0 ? result.sources.map((src, i) => {
                const credColor = src.credibility === "high" ? "#00E676" : src.credibility === "medium" ? "#FFB800" : "#FF6B6B";
                const credBg = src.credibility === "high" ? "rgba(0,230,118,0.12)" : src.credibility === "medium" ? "rgba(255,184,0,0.12)" : "rgba(255,107,107,0.12)";
                return (
                  <div key={i} style={{ animation: `fadeUp .3s ${i * 0.05}s ease both`, background: V.surface, borderRadius: 16, border: `1px solid ${V.border}`, borderLeft: `4px solid ${credColor}`, padding: "1.5rem" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
                      <div>
                        <h3 style={{ margin: "0 0 6px", fontSize: 16, fontWeight: 700, color: V.text }}>{src.title || "Unnamed Source"}</h3>
                        <p style={{ margin: 0, fontSize: 12, color: V.muted, fontFamily: "'JetBrains Mono', monospace" }}>{src.url}</p>
                      </div>
                      <span style={{ background: credBg, color: credColor, padding: "4px 12px", borderRadius: 99, fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: "1px" }}>
                        {src.credibility} CREDIBILITY
                      </span>
                    </div>
                    
                    {src.summary && (
                      <div style={{ marginBottom: "1rem" }}>
                        <h4 style={{ margin: "0 0 6px", fontSize: 12, fontWeight: 700, color: V.muted, textTransform: "uppercase", letterSpacing: ".5px" }}>Source Summary</h4>
                        <p style={{ margin: 0, fontSize: 13, color: "#D0D0DA", lineHeight: 1.5 }}>{src.summary}</p>
                      </div>
                    )}
                    
                    {src.fact_check && Object.keys(src.fact_check).length > 0 && (
                      <div style={{ background: "rgba(255,255,255,0.02)", padding: "1rem", borderRadius: 12, border: `1px solid ${V.border}` }}>
                         <h4 style={{ margin: "0 0 10px", fontSize: 12, fontWeight: 700, color: V.lime, textTransform: "uppercase", letterSpacing: ".5px" }}>Fact Check Findings</h4>
                         <div style={{ fontSize: 13, color: "#B3B3C0", lineHeight: 1.5 }}>
                            {Object.entries(src.fact_check).map(([claim, details], idx) => (
                               <div key={idx} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: idx !== Object.keys(src.fact_check).length - 1 ? `1px solid ${V.border}` : "none", lastChild: { borderBottom: "none" } }}>
                                 <strong style={{ color: V.text }}>Claim: </strong> {claim} <br/>
                                 <div style={{ marginTop: 6, color: typeof details === "object" ? (details.status === "verified" || details.status === "true" ? "#00E676" : "#FFB800") : V.muted }}>
                                   {typeof details === "object" ? `[${(details.status || "UNKNOWN").toUpperCase()}] ${details.reasoning || ""}` : JSON.stringify(details)}
                                 </div>
                               </div>
                            ))}
                         </div>
                      </div>
                    )}
                  </div>
                );
              }) : (
                <div style={{ background: V.surface, borderRadius: 16, border: `1px solid ${V.border}`, padding: "4rem", textAlign: "center" }}>
                  <div style={{ fontSize: 44, marginBottom: 10 }}>🛡️</div>
                  <p style={{ color: V.muted, fontWeight: 600 }}>No credibility metrics available.</p>
                </div>
              )}
            </div>
          )}

          {/* ── Sources Tab ── */}
          {tab === "sources" && (
            result.sources?.length > 0 ? (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(300px,1fr))", gap: 12 }}>
                {result.sources.map((s, i) => (
                  <div key={i} style={{ animation: `fadeUp .3s ${i * 0.03}s ease both` }}>
                    <SourceCard source={s} i={i} />
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ background: V.surface, borderRadius: 16, border: `1px solid ${V.border}`, padding: "4rem", textAlign: "center" }}>
                <p style={{ color: V.muted, fontWeight: 600 }}>No sources.</p>
              </div>
            )
          )}

          {/* ── Queries Tab ── */}
          {tab === "queries" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              {result.queries_used?.length > 0 && (
                <div style={{ background: V.surface, borderRadius: 16, border: `1px solid ${V.border}`, padding: "1.5rem" }}>
                  <h3 style={{ margin: "0 0 1rem", fontSize: 15, fontWeight: 800, color: V.text, letterSpacing: "-.2px" }}>
                    <span style={{ color: V.lime }}>🔎</span> Search queries
                  </h3>
                  {result.queries_used.map((q, i) => (
                    <div key={i} style={{ display: "flex", gap: 8, marginBottom: 8, padding: ".6rem .8rem", background: V.limeDim, borderRadius: 10, border: `1px solid rgba(202,255,4,0.08)` }}>
                      <span style={{ fontSize: 11, fontWeight: 800, color: V.lime, flexShrink: 0, marginTop: 1, fontFamily: "'JetBrains Mono', monospace" }}>{String(i + 1).padStart(2, "0")}</span>
                      <p style={{ margin: 0, fontSize: 13, fontWeight: 500, color: V.text }}>{q}</p>
                    </div>
                  ))}
                </div>
              )}
              {result.focus_areas?.length > 0 && (
                <div style={{ background: V.surface, borderRadius: 16, border: `1px solid ${V.border}`, padding: "1.5rem" }}>
                  <h3 style={{ margin: "0 0 1rem", fontSize: 15, fontWeight: 800, color: V.text, letterSpacing: "-.2px" }}>
                    <span style={{ color: V.uv }}>🎯</span> Focus areas
                  </h3>
                  {result.focus_areas.map((f, i) => (
                    <div key={i} style={{ marginBottom: 8, padding: ".6rem .8rem", background: V.uvDim, borderRadius: 10, borderLeft: `3px solid ${V.uv}`, border: `1px solid rgba(131,56,236,0.15)`, borderLeftWidth: 3, borderLeftColor: V.uv }}>
                      <p style={{ margin: 0, fontSize: 13, fontWeight: 600, color: "#B57BFF" }}>{f}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
