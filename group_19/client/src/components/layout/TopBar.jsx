import { useState, useEffect } from "react";
import { useFinancialStore } from "../../store/financialStore.js";
import LogoFull from "./Logo.jsx";

const TAGLINES = [
  "Intelligence That Compounds™",
  "Precision-Grade Financial Analysis",
  "Your CFO. In 60 Seconds.",
  "Where Data Meets Financial Wisdom",
  "Institutional-Grade AI for Everyone",
];

function LiveClock() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return (
    <span className="font-mono text-slate-400 text-xs tabular-nums">
      {now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
      <span className="text-slate-600 ml-2 hidden sm:inline">
        {now.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })}
      </span>
    </span>
  );
}

function RotatingTagline() {
  const [idx, setIdx] = useState(0);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const id = setInterval(() => {
      setVisible(false);
      setTimeout(() => {
        setIdx(i => (i + 1) % TAGLINES.length);
        setVisible(true);
      }, 300);
    }, 4000);
    return () => clearInterval(id);
  }, []);

  return (
    <span
      className="hidden md:block text-[20px] font-semibold tracking-widest uppercase"
      style={{
        background: "linear-gradient(90deg,#8B5CF6,#06B6D4)",
        WebkitBackgroundClip: "text",
        WebkitTextFillColor: "transparent",
        opacity: visible ? 1 : 0,
        transition: "opacity 0.3s ease",
        letterSpacing: "0.10em",
      }}
    >
      {TAGLINES[idx]}
    </span>
  );
}

export default function TopBar() {
  const { result } = useFinancialStore();

  return (
    <header
      className="sticky top-0 z-50 w-full flex items-center justify-between px-6 py-3"
      style={{
        background: "rgba(5,6,15,0.95)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        borderBottom: "1px solid rgba(139,92,246,0.35)",
        boxShadow: "0 1px 24px rgba(139,92,246,0.10), 0 1px 0 rgba(6,182,212,0.12)",
      }}
    >
      {/* Left — Logo */}
      <div className="flex items-center gap-5">
        <LogoFull size={56} />
        <div className="hidden sm:block w-px h-4 bg-white/10" />
        <RotatingTagline />
      </div>

      {/* Right — Status + clock */}
      <div className="flex items-center gap-3">
        {/* System status */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full"
          style={{ background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.2)" }}
        >
          <span className="dot-live" style={{ width: 6, height: 6 }} />
          <span className="text-green-400 text-[10px] font-medium">All Systems Operational</span>
        </div>

        {/* Result badge */}
        {result && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full"
            style={{ background: "rgba(139,92,246,0.1)", border: "1px solid rgba(139,92,246,0.25)" }}
          >
            <span className="text-accent-purple text-[10px] font-mono font-semibold">
              Score: {Math.round(result.health_score || 0)}/100
            </span>
          </div>
        )}

        <LiveClock />

        {/* Version badge */}
        <span className="hidden lg:flex text-[9px] text-slate-600 font-mono px-2 py-1 rounded bg-white/[0.03] border border-white/[0.06]">
          v1.0 β
        </span>
      </div>
    </header>
  );
}
