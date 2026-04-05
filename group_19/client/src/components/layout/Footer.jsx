import { LogoMark } from "./Logo.jsx";

const LINKS = [
  { label: "Privacy Policy",    href: "#" },
  { label: "Terms of Service",  href: "#" },
  { label: "Security",          href: "#" },
  { label: "Data Handling",     href: "#" },
];

const TRUST = [
  { icon: "🔒", label: "256-bit TLS Encryption" },
  { icon: "🛡️", label: "Zero Data Retention" },
  { icon: "⚡", label: "99.9% Uptime SLA" },
];

export default function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer
      className="w-full mt-auto"
      style={{
        background: "rgba(5,6,15,0.97)",
        borderTop: "1px solid rgba(255,255,255,0.05)",
      }}
    >
      {/* Tagline bar */}
      <div
        className="w-full flex items-center justify-center py-2 gap-8 flex-wrap"
        style={{
          background: "linear-gradient(90deg, rgba(139,92,246,0.06), rgba(6,182,212,0.06))",
          borderBottom: "1px solid rgba(255,255,255,0.04)",
        }}
      >
        {TRUST.map(t => (
          <span key={t.label} className="flex items-center gap-1.5 text-[10px] text-slate-500">
            <span>{t.icon}</span> {t.label}
          </span>
        ))}
      </div>

      {/* Main footer */}
      <div className="max-w-5xl mx-auto px-6 py-5 flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-2.5">
          <LogoMark size={20} />
          <div>
            <p className="text-white font-bold text-xs leading-none">FinanceIQ</p>
            <p className="text-slate-600 text-[10px] mt-0.5 font-mono">Intelligence · Precision · Growth</p>
          </div>
        </div>

        {/* Links */}
        <div className="flex items-center gap-4 flex-wrap justify-center">
          {LINKS.map(l => (
            <a key={l.label} href={l.href}
              className="text-slate-600 text-[11px] hover:text-slate-400 transition-colors"
            >
              {l.label}
            </a>
          ))}
        </div>

        {/* Copyright */}
        <div className="text-right">
          <p className="text-slate-600 text-[10px] font-mono">
            © {year} FinanceIQ Technologies, Inc.
          </p>
          <p className="text-slate-700 text-[10px] mt-0.5">
            Powered by OpenRouter · LangGraph · v1.0.0-β
          </p>
        </div>
      </div>
    </footer>
  );
}
