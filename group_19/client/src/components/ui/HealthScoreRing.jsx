import { useEffect, useState } from "react";
import { scoreLabel } from "../../utils/formatters.js";

export default function HealthScoreRing({ score, size = 200 }) {
  const [animScore, setAnimScore] = useState(0);
  const { label, color } = scoreLabel(score || 0);

  useEffect(() => {
    let frame;
    let start = null;
    const end = score || 0;
    const animate = (ts) => {
      if (!start) start = ts;
      const p = Math.min((ts - start) / 1200, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      setAnimScore(eased * end);
      if (p < 1) frame = requestAnimationFrame(animate);
    };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [score]);

  const R = (size / 2) * 0.75;
  const cx = size / 2;
  const circumference = 2 * Math.PI * R;
  const strokeDash = (animScore / 100) * circumference;
  const strokeGap = circumference - strokeDash;
  // Start from top (-90deg offset)
  const rotation = -90;

  const gradientId = `health-grad-${size}`;
  const glowId = `health-glow-${size}`;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: `rotate(${rotation}deg)` }}>
          <defs>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#7C3AED" />
              <stop offset="50%" stopColor="#3B82F6" />
              <stop offset="100%" stopColor="#06B6D4" />
            </linearGradient>
            <filter id={glowId}>
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          {/* Background track */}
          <circle
            cx={cx} cy={cx} r={R}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={size * 0.065}
          />
          {/* Progress arc */}
          <circle
            cx={cx} cy={cx} r={R}
            fill="none"
            stroke={`url(#${gradientId})`}
            strokeWidth={size * 0.065}
            strokeDasharray={`${strokeDash} ${strokeGap}`}
            strokeLinecap="round"
            filter={`url(#${glowId})`}
            style={{ transition: "stroke-dasharray 0.05s linear" }}
          />
          {/* Outer decorative ring */}
          <circle
            cx={cx} cy={cx} r={R + size * 0.055}
            fill="none"
            stroke="rgba(139,92,246,0.15)"
            strokeWidth={1}
            strokeDasharray="4 6"
          />
        </svg>

        {/* Center text — no rotation needed, sits above the SVG layer */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="font-mono font-bold leading-none"
            style={{ fontSize: size * 0.22, color }}
          >
            {Math.round(animScore)}
          </span>
          <span className="text-slate-400 text-xs font-medium mt-1">/ 100</span>
        </div>
      </div>

      <div className="text-center">
        <span
          className="text-sm font-semibold px-3 py-1 rounded-full"
          style={{
            background: `${color}18`,
            color,
            border: `1px solid ${color}40`,
          }}
        >
          {label}
        </span>
      </div>
    </div>
  );
}
