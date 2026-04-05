import { MessageSquare, Settings, BarChart2, RotateCcw, BookOpen } from "lucide-react";
import { useFinancialStore } from "../../store/financialStore.js";
import { LogoMark } from "./Logo.jsx";

const NAV = [
  { id: "chat",      Icon: MessageSquare, label: "Chat",    desc: "Conversation" },
  { id: "config",    Icon: Settings,      label: "Config",  desc: "API & Models" },
  { id: "dashboard", Icon: BarChart2,     label: "Results", desc: "Full Report", requiresResult: true },
  { id: "docs",      Icon: BookOpen,      label: "Docs",    desc: "Architecture" },
];

// ── Desktop sidebar ───────────────────────────────────────────────────────
export function Sidebar() {
  const { page, setPage, result, resetChat } = useFinancialStore();

  return (
    <aside className="hidden md:flex flex-col w-52 min-h-0 flex-shrink-0 px-3 py-4 gap-1"
      style={{
        background: "rgba(5,6,15,0.6)",
        borderRight: "1px solid rgba(255,255,255,0.05)",
        backdropFilter: "blur(12px)",
      }}
    >
      {/* Logo mark — wordmark lives in TopBar, sidebar keeps icon only */}
      <div className="flex items-center gap-2.5 px-2 py-3 mb-2">
        <LogoMark size={28} />
        <div className="h-5 w-px bg-white/[0.08]" />
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-green-400 flex-shrink-0"
            style={{ boxShadow: "0 0 5px rgba(16,185,129,0.7)" }} />
          <span className="text-green-500 text-[10px] font-mono font-medium">Live</span>
        </div>
      </div>

      {/* Nav items */}
      <p className="text-slate-700 text-[9px] font-medium uppercase tracking-widest px-2 mb-1" style={{ letterSpacing: "0.15em" }}>
        Navigation
      </p>
      {NAV.map(({ id, Icon, label, desc, requiresResult }) => {
        const disabled = requiresResult && !result;
        const active = page === id;
        return (
          <button
            key={id}
            onClick={() => !disabled && setPage(id)}
            className={`sidebar-item ${active ? "active" : ""} ${disabled ? "disabled" : ""}`}
          >
            <Icon size={15} className="flex-shrink-0" />
            <div className="flex flex-col items-start min-w-0">
              <span className="leading-none">{label}</span>
              <span className="text-[9px] opacity-50 leading-none mt-0.5">{desc}</span>
            </div>
            {active ? (
              <span className="ml-auto w-1.5 h-1.5 rounded-full bg-green-400 flex-shrink-0"
                style={{ boxShadow: "0 0 6px rgba(16,185,129,0.8)" }} />
            ) : id === "dashboard" && result ? (
              <span className="ml-auto w-1.5 h-1.5 rounded-full bg-green-400/30 flex-shrink-0" />
            ) : requiresResult && !result ? (
              <span className="ml-auto text-[8px] text-slate-700 font-mono">LOCKED</span>
            ) : null}
          </button>
        );
      })}

      {/* Divider */}
      <div className="my-3 h-px bg-white/[0.05]" />

      {/* Actions */}
      <p className="text-slate-700 text-[9px] font-medium uppercase tracking-widest px-2 mb-1" style={{ letterSpacing: "0.15em" }}>
        Actions
      </p>
      <button onClick={resetChat} className="sidebar-item">
        <RotateCcw size={13} className="flex-shrink-0" />
        <div className="flex flex-col items-start">
          <span>New Analysis</span>
          <span className="text-[9px] opacity-50 leading-none mt-0.5">Reset session</span>
        </div>
      </button>

      {/* Bottom info */}
      <div className="mt-auto pt-4 border-t border-white/[0.04]">
        <div className="px-2 flex flex-col gap-1">
          <p className="text-slate-700 text-[9px] font-mono leading-relaxed">
            OpenRouter · LangGraph
          </p>
          <p className="text-slate-700 text-[9px] font-mono">
            6 AI Agents · Real-time
          </p>
          <p className="text-slate-800 text-[8px] font-mono mt-0.5">v1.0 β</p>
        </div>
      </div>
    </aside>
  );
}

// ── Mobile bottom tab bar ─────────────────────────────────────────────────
export function BottomBar() {
  const { page, setPage, result } = useFinancialStore();

  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-50 flex items-center justify-around px-2 py-2"
      style={{
        background: "rgba(5,6,15,0.97)",
        backdropFilter: "blur(20px)",
        borderTop: "1px solid rgba(255,255,255,0.06)",
      }}
    >
      {NAV.map(({ id, Icon, label, requiresResult }) => {
        const disabled = requiresResult && !result;
        const active = page === id;
        return (
          <button
            key={id}
            onClick={() => !disabled && setPage(id)}
            disabled={disabled}
            className={`flex flex-col items-center gap-0.5 px-5 py-1 rounded-xl transition-all ${
              active ? "text-white" : "text-slate-500"
            } ${disabled ? "opacity-20" : ""}`}
          >
            <div className={`relative p-1.5 rounded-lg transition-all ${active ? "bg-accent-purple/20" : ""}`}>
              <Icon size={17} />
              {active && (
                <span className="absolute top-0.5 right-0.5 w-1.5 h-1.5 rounded-full bg-green-400"
                  style={{ boxShadow: "0 0 5px rgba(16,185,129,0.8)" }} />
              )}
              {!active && id === "dashboard" && result && (
                <span className="absolute top-0.5 right-0.5 w-1.5 h-1.5 rounded-full bg-green-400/40" />
              )}
            </div>
            <span className="text-[9px] font-medium">{label}</span>
          </button>
        );
      })}
    </nav>
  );
}
