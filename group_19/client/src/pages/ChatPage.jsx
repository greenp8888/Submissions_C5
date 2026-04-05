import { useEffect, useRef, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, BarChart2, Upload, ArrowLeft, Eye, EyeOff, Key } from "lucide-react";
import { useDropzone } from "react-dropzone";
import ChatMessage, { TypingIndicator } from "../components/chat/ChatMessage.jsx";
import { useFinancialStore, AGENT_ORDER } from "../store/financialStore.js";

// ── Bot conversation script ───────────────────────────────────────────────────
const SCRIPT = {
  welcome:  "Welcome to FinanceIQ — institutional-grade financial intelligence, built for everyone.\n\nI'll deploy 6 specialist AI agents on your transactions and deliver a personalised wealth-building blueprint in under 60 seconds.",
  apikey:   "To get started I need two API keys — both are **free to create** and stay saved in your browser. You'll never need to enter them again.\n\n🔑 **OpenRouter** — powers the AI analysis engine\n🔍 **Tavily** — enables live market & savings research\n\nPaste both keys below 👇",
  upload:   "Both keys saved! Now upload your transaction file. I support CSV and Excel (.xlsx). Just make sure it has Date, Amount, Category, and Type columns.",
  goals:    "What are your top financial goals right now? For example: pay off credit card debt, build an emergency fund, save for a house, or retire early.",
  confirm:  "Perfect — I have everything I need. I'm launching 6 specialist AI agents on your data. Each one is an expert in a different area of personal finance. This usually takes 30–60 seconds.",
};

const PLACEHOLDERS = {
  apikey:   "sk-or-v1-…  (paste your OpenRouter key)",
  goals:    "e.g. Pay off my credit card and save $10k this year…",
};

// ── Dual API-key input bar ────────────────────────────────────────────────────
function ApiKeyInputBar({ onSubmit, initialOpenRouter = "", initialTavily = "" }) {
  const [orKey, setOrKey]     = useState(initialOpenRouter);
  const [tavKey, setTavKey]   = useState(initialTavily);
  const [showOr, setShowOr]   = useState(false);
  const [showTav, setShowTav] = useState(false);

  const canSubmit = orKey.trim().length > 0 && tavKey.trim().length > 0;

  const submit = () => {
    if (!canSubmit) return;
    onSubmit({ openrouterKey: orKey.trim(), tavilyKey: tavKey.trim() });
  };

  return (
    <div className="px-4 py-4 glass border-t border-white/[0.06]" style={{ flexShrink: 0 }}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <Key size={12} className="text-amber-400" />
        <span className="text-amber-400 text-xs font-semibold tracking-wide">Required API Keys</span>
        <span className="ml-auto text-[10px] text-slate-600">Both required · Free to create</span>
      </div>

      <div className="flex flex-col gap-2.5">
        {/* OpenRouter */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-slate-400 font-medium">🔑 OpenRouter <span className="text-red-400">*</span></span>
            <a href="https://openrouter.ai/keys" target="_blank" rel="noreferrer"
              className="text-[10px] text-purple-400 hover:text-purple-300 transition-colors">
              Get free key ↗
            </a>
          </div>
          <div className="relative">
            <input
              type={showOr ? "text" : "password"}
              value={orKey}
              onChange={e => setOrKey(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && canSubmit) submit(); }}
              placeholder="sk-or-v1-…"
              autoFocus
              className="w-full field-input pr-10 py-2.5 text-sm font-mono"
            />
            <button type="button" onClick={() => setShowOr(!showOr)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
              {showOr ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
          </div>
        </div>

        {/* Tavily */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-slate-400 font-medium">🔍 Tavily <span className="text-red-400">*</span></span>
            <a href="https://tavily.com" target="_blank" rel="noreferrer"
              className="text-[10px] text-blue-400 hover:text-blue-300 transition-colors">
              Get free key ↗
            </a>
          </div>
          <div className="relative">
            <input
              type={showTav ? "text" : "password"}
              value={tavKey}
              onChange={e => setTavKey(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && canSubmit) submit(); }}
              placeholder="tvly-…"
              className="w-full field-input pr-10 py-2.5 text-sm font-mono"
            />
            <button type="button" onClick={() => setShowTav(!showTav)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
              {showTav ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
          </div>
        </div>
      </div>

      {/* Submit */}
      <button onClick={submit} disabled={!canSubmit}
        className="btn-primary w-full mt-3 py-2.5 flex items-center justify-center gap-2 text-sm font-semibold"
        style={{ opacity: canSubmit ? 1 : 0.4, cursor: canSubmit ? "pointer" : "not-allowed" }}>
        <Key size={14} />
        Save Keys &amp; Continue
      </button>

      <p className="text-slate-600 text-[10px] mt-2 text-center">
        Stored only in your browser · Never sent to our servers
      </p>
    </div>
  );
}

// ── Text input bar ────────────────────────────────────────────────────────────
function ChatInputBar({ onSend, placeholder = "Type a message…" }) {
  const [text, setText] = useState("");
  const submit = () => { if (!text.trim()) return; onSend(text.trim()); setText(""); };

  return (
    <div className="flex items-end gap-2 px-4 py-3 glass border-t border-white/[0.06]" style={{ flexShrink: 0 }}>
      <textarea
        rows={1}
        value={text}
        onChange={e => setText(e.target.value)}
        onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); } }}
        placeholder={placeholder}
        autoFocus
        className="flex-1 field-input resize-none py-2.5 min-h-[42px] max-h-32 leading-relaxed"
        style={{ fontFamily: "inherit" }}
      />
      <button onClick={submit} disabled={!text.trim()}
        className="btn-primary px-4 py-2.5 flex items-center gap-1.5 flex-shrink-0">
        <Send size={14} />
        Analyze
      </button>
    </div>
  );
}

// ── File icon by extension ────────────────────────────────────────────────────
const fileIcon = (name) => {
  const ext = name.split(".").pop().toLowerCase();
  if (ext === "xlsx" || ext === "xls") return "📊";
  if (ext === "csv") return "📋";
  return "📄";
};
const fileColor = (name) => {
  const ext = name.split(".").pop().toLowerCase();
  return ext === "csv" ? "#10B981" : "#8B5CF6";
};

// ── Centered upload zone ──────────────────────────────────────────────────────
function CenteredUpload({ onUploaded }) {
  const { file, setFile } = useFinancialStore();
  const [samples, setSamples] = useState([]);
  const [loadingSample, setLoadingSample] = useState(null);

  // Fetch available sample files on mount
  useEffect(() => {
    fetch("/api/samples").then(r => r.json()).then(setSamples).catch(() => {});
  }, []);

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop: accepted => { if (accepted[0]) { setFile(accepted[0]); onUploaded?.(accepted[0]); } },
    accept: {
      "text/csv": [".csv"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
    },
    maxFiles: 1,
  });

  const useSample = async (name) => {
    setLoadingSample(name);
    try {
      const res = await fetch(`/api/sample?file=${encodeURIComponent(name)}`);
      const blob = await res.blob();
      const f = new File([blob], name, { type: blob.type });
      setFile(f);
      onUploaded?.(f);
    } catch (e) {
      console.error("Failed to load sample", e);
    } finally {
      setLoadingSample(null);
    }
  };

  return (
    <div style={{ padding: "32px 24px 28px", display: "flex", flexDirection: "column", alignItems: "center", gap: 20 }}>
      {file ? (
        <div style={{
          width: "100%", maxWidth: 480, display: "flex", alignItems: "center", gap: 16,
          padding: "16px 20px", borderRadius: 16,
          background: "rgba(16,185,129,0.10)", border: "1px solid rgba(16,185,129,0.35)",
        }}>
          <div style={{ width: 48, height: 48, borderRadius: 12, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(16,185,129,0.2)", border: "1px solid rgba(16,185,129,0.4)", fontSize: 22 }}>
            ✓
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ color: "#fff", fontWeight: 600, fontSize: 14, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{file.name}</p>
            <p style={{ color: "#94a3b8", fontSize: 12, marginTop: 2 }}>{(file.size / 1024).toFixed(1)} KB · Ready to analyze</p>
          </div>
          <button onClick={() => setFile(null)} style={{ color: "#64748b", fontSize: 12, background: "none", border: "none", cursor: "pointer", padding: "4px 8px" }}>Remove</button>
        </div>
      ) : (
        <>
          {/* Drop zone */}
          <div {...getRootProps()} style={{
            width: "100%", maxWidth: 480,
            border: `2px dashed ${isDragActive ? "#8b5cf6" : "rgba(139,92,246,0.5)"}`,
            borderRadius: 20,
            background: isDragActive ? "rgba(139,92,246,0.12)" : "rgba(139,92,246,0.05)",
            padding: "32px 28px",
            display: "flex", flexDirection: "column", alignItems: "center", gap: 16,
            cursor: "pointer", transition: "all 0.2s ease",
            boxShadow: isDragActive ? "0 0 60px rgba(139,92,246,0.25)" : "0 0 30px rgba(139,92,246,0.08)",
          }}>
            <input {...getInputProps()} />
            <div style={{ width: 80, height: 80, borderRadius: 22, display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(139,92,246,0.15)", border: "1.5px solid rgba(139,92,246,0.5)", boxShadow: "0 0 40px rgba(139,92,246,0.2)" }}>
              <Upload size={36} color="#8b5cf6" />
            </div>
            <div style={{ textAlign: "center" }}>
              <p style={{ color: "#fff", fontWeight: 700, fontSize: 17, marginBottom: 6 }}>
                {isDragActive ? "Drop it right here!" : "Upload your transaction file"}
              </p>
              <p style={{ color: "#94a3b8", fontSize: 13 }}>Drag & drop, or click <strong style={{ color: "#8b5cf6" }}>Choose File</strong> below</p>
              <p style={{ color: "#475569", fontSize: 11, marginTop: 4 }}>Excel (.xlsx · .xls) · CSV · Max 10 MB</p>
            </div>
            <button type="button" onClick={e => { e.stopPropagation(); open(); }} style={{
              display: "flex", alignItems: "center", gap: 8, padding: "9px 24px",
              background: "linear-gradient(135deg,#7c3aed,#3b82f6)", border: "none", borderRadius: 10,
              color: "#fff", fontWeight: 600, fontSize: 14, cursor: "pointer",
              boxShadow: "0 4px 20px rgba(124,58,237,0.35)",
            }}>
              <Upload size={15} /> Choose File
            </button>
          </div>

          {/* Sample files */}
          {samples.length > 0 && (
            <div style={{ width: "100%", maxWidth: 480 }}>
              <p style={{ color: "#475569", fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 10, textAlign: "center" }}>
                — Or use a sample file —
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {samples.map(s => (
                  <button
                    key={s.name}
                    onClick={() => useSample(s.name)}
                    disabled={!!loadingSample}
                    style={{
                      display: "flex", alignItems: "center", gap: 12,
                      padding: "12px 16px", borderRadius: 12,
                      background: "rgba(255,255,255,0.03)",
                      border: `1px solid ${fileColor(s.name)}28`,
                      cursor: loadingSample ? "wait" : "pointer",
                      transition: "all 0.15s", textAlign: "left", width: "100%",
                    }}
                    onMouseEnter={e => { e.currentTarget.style.background = `${fileColor(s.name)}10`; e.currentTarget.style.borderColor = `${fileColor(s.name)}45`; }}
                    onMouseLeave={e => { e.currentTarget.style.background = "rgba(255,255,255,0.03)"; e.currentTarget.style.borderColor = `${fileColor(s.name)}28`; }}
                  >
                    <span style={{ fontSize: 22, flexShrink: 0 }}>{fileIcon(s.name)}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ color: "#e2e8f0", fontSize: 13, fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{s.name}</p>
                      <p style={{ color: "#64748b", fontSize: 11, marginTop: 1 }}>{(s.size / 1024).toFixed(1)} KB · Sample data</p>
                    </div>
                    <span style={{
                      flexShrink: 0, padding: "4px 12px", borderRadius: 8,
                      background: `${fileColor(s.name)}18`, color: fileColor(s.name),
                      fontSize: 11, fontWeight: 700, border: `1px solid ${fileColor(s.name)}30`,
                    }}>
                      {loadingSample === s.name ? "Loading…" : "Use this ↑"}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function ChatPage() {
  const {
    messages, chatStep, addMessage, setChatStep,
    file, config, setConfig, setPage,
    addStep, updateStep, setProgress, setResult, setAnalysisError,
    steps, progress, result,
  } = useFinancialStore();

  const [typing, setTyping] = useState(false);
  const [inputEnabled, setInputEnabled] = useState(false);
  const bottomRef = useRef(null);
  const analysisStarted = useRef(false);
  const initDone = useRef(false);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, typing]);

  // ── Boot: runs once per mount (resetKey increments remount this component) ─
  useEffect(() => {
    if (initDone.current) return;
    initDone.current = true;

    // Already has messages (user navigated away and came back) — don't re-init
    if (useFinancialStore.getState().messages.length > 0) return;

    addMessage({ role: "bot", type: "text", content: SCRIPT.welcome });

    const proceed = () => {
      const { config } = useFinancialStore.getState();
      if (!config.openrouterKey || !config.tavilyKey) {
        setTimeout(() => {
          addMessage({ role: "bot", type: "text", content: SCRIPT.apikey });
          setChatStep("apikey");
        }, 600);
      } else {
        setTimeout(() => {
          addMessage({ role: "bot", type: "text", content: SCRIPT.upload });
          setChatStep("upload");
        }, 600);
      }
    };

    // zustand persist rehydrates async — wait for it before checking keys
    if (useFinancialStore.persist.hasHydrated()) {
      proceed();
    } else {
      const unsub = useFinancialStore.persist.onFinishHydration(proceed);
      return () => unsub?.();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Handle API keys submitted ─────────────────────────────────────────────
  const handleApiKey = useCallback(({ openrouterKey, tavilyKey }) => {
    setConfig({ openrouterKey, tavilyKey });
    addMessage({ role: "user", type: "text", content: "🔑 OpenRouter: ●●●●●●●●●●●●  🔍 Tavily: ●●●●●●●●●●●● (both saved)" });
    setTyping(true);
    setTimeout(() => {
      setTyping(false);
      addMessage({ role: "bot", type: "text", content: "✅ Both keys saved to your browser — you won't need to enter them again.\n\n" + SCRIPT.upload });
      setChatStep("upload");
    }, 700);
  }, [addMessage, setChatStep, setConfig]);

  // ── Handle file uploaded ──────────────────────────────────────────────────
  const handleFileUploaded = useCallback((f) => {
    setTimeout(() => {
      addMessage({ role: "user", type: "text", content: `📎 ${f.name} (${(f.size / 1024).toFixed(0)} KB)` });
      setTyping(true);
      setTimeout(() => {
        setTyping(false);
        addMessage({ role: "bot", type: "text", content: SCRIPT.goals });
        setChatStep("goals");
        setInputEnabled(true);
      }, 900);
    }, 300);
  }, [addMessage, setChatStep]);

  // ── Handle text input ─────────────────────────────────────────────────────
  const handleUserInput = useCallback((text) => {
    if (chatStep === "goals") {
      useFinancialStore.getState().setConfig({ goals: text });
      addMessage({ role: "user", type: "text", content: text });
      setInputEnabled(false);
      setTyping(true);
      setTimeout(() => {
        setTyping(false);
        addMessage({ role: "bot", type: "text", content: SCRIPT.confirm });
        setChatStep("confirm");
      }, 700);
    }
  }, [chatStep, addMessage, setChatStep]);

  // ── Auto-start analysis when confirm step is reached ─────────────────────
  useEffect(() => {
    if (chatStep !== "confirm" || analysisStarted.current) return;
    analysisStarted.current = true;
    setTimeout(() => {
      addMessage({ role: "user", type: "text", content: "Start the analysis! 🚀" });
      runAnalysis();
    }, 2000);
  }, [chatStep]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── SSE analysis ─────────────────────────────────────────────────────────
  const runAnalysis = useCallback(async () => {
    const { file, config } = useFinancialStore.getState();
    if (!file || !config.openrouterKey) return;

    setChatStep("analyzing");
    addMessage({ role: "bot", type: "progress", content: "Running your data through 6 specialist AI agents. Watch their progress live:", meta: { steps: [], progress: 0 } });

    const formData = new FormData();
    formData.append("file", file);
    formData.append("openrouterKey", config.openrouterKey);
    formData.append("tavilyKey", config.tavilyKey || "");
    formData.append("model", config.model);
    formData.append("goals", config.goals);

    const updateProgress = (s, p) => {
      useFinancialStore.setState(state => ({
        messages: state.messages.map(m => m.type === "progress" ? { ...m, meta: { steps: s, progress: p } } : m),
      }));
    };

    try {
      const res = await fetch("/api/analyze", { method: "POST", body: formData });
      if (!res.ok) throw new Error("Server error " + res.status);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      let stepsDone = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop();

        for (const line of lines) {
          const raw = line.replace(/^data:\s*/, "").trim();
          if (!raw) continue;
          try {
            const ev = JSON.parse(raw);
            if (ev.type === "step_start") {
              addStep({ ...ev, status: "running" });
              updateProgress(useFinancialStore.getState().steps, useFinancialStore.getState().progress);
            } else if (ev.type === "step_done") {
              stepsDone++;
              updateStep(ev.agent, { status: "done", summary: ev.summary, errors: ev.errors || [] });
              const pct = Math.round((stepsDone / AGENT_ORDER.length) * 100);
              setProgress(pct);
              updateProgress(useFinancialStore.getState().steps, pct);
            } else if (ev.type === "done") {
              setProgress(100);
              setResult(ev.result);
              setChatStep("done");
              setTimeout(() => {
                addMessage({ role: "bot", type: "result", content: "Analysis complete! Here's your financial snapshot. Open the full dashboard for detailed insights, charts, and your action plan.", meta: { result: ev.result } });
              }, 600);
            } else if (ev.type === "error") {
              setAnalysisError(ev.message);
              addMessage({ role: "bot", type: "text", content: `❌ Something went wrong: ${ev.message}` });
            }
          } catch {}
        }
      }
    } catch (err) {
      setAnalysisError(err.message);
      addMessage({ role: "bot", type: "text", content: `❌ Connection error: ${err.message}` });
    }
  }, [addMessage, addStep, updateStep, setProgress, setResult, setAnalysisError, setChatStep]);

  // ── Render logic ─────────────────────────────────────────────────────────
  const isActive = !["analyzing", "done"].includes(chatStep);
  const showUpload = isActive && chatStep !== "apikey" && !file;
  const showMessages = !showUpload;

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0, overflow: "hidden" }}>

      {/* ── Sub-header ───────────────────────────────────────────────────── */}
      <div style={{ flexShrink: 0 }} className="flex items-center justify-between px-5 py-2.5 border-b border-white/[0.05]">
        <div className="flex items-center gap-2">
          {file && isActive && (
            <button onClick={() => useFinancialStore.getState().resetChat()}
              className="flex items-center gap-1 text-slate-500 hover:text-white transition-colors text-xs mr-1">
              <ArrowLeft size={13} /> Back
            </button>
          )}
          <div className="dot-live" />
          <span className="text-white font-semibold text-sm">FinanceIQ Chat</span>
          <span className="text-slate-600 text-[10px] font-mono ml-1 hidden sm:block">· 6 Agent Pipeline</span>
        </div>
        {result && (
          <button onClick={() => setPage("dashboard")}
            className="flex items-center gap-1.5 text-xs text-accent-purple hover:text-white transition-colors">
            <BarChart2 size={13} /> View Dashboard
          </button>
        )}
      </div>

      {/* ── Body ─────────────────────────────────────────────────────────── */}
      <div style={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
        {showUpload ? (
          <CenteredUpload onUploaded={handleFileUploaded} />
        ) : (
          <div className="px-4 py-5 flex flex-col">
            <AnimatePresence initial={false}>
              {messages.map(msg => (
                <ChatMessage key={msg.id} msg={msg}
                  onFileUploaded={handleFileUploaded}
                  onViewDashboard={() => setPage("dashboard")} />
              ))}
            </AnimatePresence>
            {typing && <TypingIndicator />}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* ── Bottom action bar ─────────────────────────────────────────────── */}
      <AnimatePresence>
        {chatStep === "apikey" && (
          <motion.div key="apikey-bar" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 10 }}>
            <ApiKeyInputBar
              onSubmit={handleApiKey}
              initialOpenRouter={config.openrouterKey || ""}
              initialTavily={config.tavilyKey || ""}
            />
          </motion.div>
        )}
        {inputEnabled && isActive && chatStep !== "apikey" && (
          <motion.div key="text-bar" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 10 }}>
            <ChatInputBar onSend={handleUserInput} placeholder={PLACEHOLDERS[chatStep] || "Type a message…"} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
