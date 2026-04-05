"use client";

import { useId } from "react";

const MARK_BOX_GRADIENT = "linear-gradient(135deg, #3b82f6, #22d3ee)";

/** White mark for use inside the gradient app icon (currentColor = white from parent). */
export function SignalForgeMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <path
        d="M2 16c3.5-6 7-8 11.5-6.5S21 13 22 11"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path
        d="M2 19.5c2.5-4.5 5.5-6 9.5-5S20.5 18 22 16.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity={0.88}
      />
      <path d="M17.5 7.5V16M14.5 15.5h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

/** Gradient icon for SignalForge Knowledge Base row (matches cyan/blue product accents). */
export function SignalForgeKnowledgeIcon({ className }: { className?: string }) {
  const uid = useId().replace(/:/g, "");
  const gid = `sf-kb-grad-${uid}`;
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      role="img"
      aria-label="SignalForge Knowledge Base"
    >
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#22d3ee" />
          <stop offset="100%" stopColor="#3b82f6" />
        </linearGradient>
      </defs>
      <path
        d="M2 15c3.5-5.5 7-7 11-5.5S21 14 22 12"
        stroke={`url(#${gid})`}
        strokeWidth="2"
        strokeLinecap="round"
      />
      <path d="M17 7v9M14 15.5h6" stroke={`url(#${gid})`} strokeWidth="2" strokeLinecap="round" />
      <circle cx="5" cy="18.5" r="1.25" fill="#22d3ee" />
    </svg>
  );
}

type HeaderVariant = "default" | "compact";

/**
 * App header lockup: gradient mark + SignalForge wordmark.
 * Use `wordmarkColor` on dark report chrome where text should stay near-white.
 */
export function SignalForgeHeaderBrand({
  variant = "default",
  wordmarkColor,
}: {
  variant?: HeaderVariant;
  wordmarkColor?: string;
}) {
  const compact = variant === "compact";
  const box = compact ? 28 : 32;
  const gap = compact ? 8 : 12;
  const fontSize = compact ? 14 : 17;
  const iconClass = compact ? "w-[14px] h-[14px]" : "w-5 h-5";

  return (
    <div className="flex items-center flex-shrink-0" style={{ gap }}>
      <div
        className="flex items-center justify-center rounded-lg text-white"
        style={{
          width: box,
          height: box,
          minWidth: box,
          background: MARK_BOX_GRADIENT,
        }}
        aria-hidden="true"
      >
        <SignalForgeMark className={iconClass} />
      </div>
      <span
        style={{
          fontSize,
          fontWeight: 700,
          letterSpacing: "-0.02em",
          color: wordmarkColor ?? "inherit",
        }}
      >
        SignalForge
      </span>
    </div>
  );
}
