import { useMemo } from "react";

// Lightweight pure-CSS beacon dots — no canvas, no Three.js
const BEACON_COLORS = [
  "rgba(139,92,246,0.55)",  // purple
  "rgba(59,130,246,0.45)",  // blue
  "rgba(6,182,212,0.4)",    // cyan
  "rgba(16,185,129,0.4)",   // green
];

export default function DotField({ count = 22 }) {
  const dots = useMemo(() =>
    Array.from({ length: count }, (_, i) => ({
      x: 4 + Math.random() * 92,
      y: 4 + Math.random() * 92,
      color: BEACON_COLORS[i % BEACON_COLORS.length],
      size: Math.random() > 0.72 ? 4 : 2.5,
      delay: (Math.random() * 4).toFixed(2),
      duration: (2.2 + Math.random() * 2).toFixed(2),
    })), [count],
  );

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden" style={{ zIndex: 0 }}>
      {dots.map((d, i) => (
        <span
          key={i}
          className="beacon"
          style={{
            left: `${d.x}%`,
            top: `${d.y}%`,
            width: d.size,
            height: d.size,
            background: d.color,
            boxShadow: `0 0 ${d.size * 3}px ${d.color}`,
            animationDelay: `${d.delay}s`,
            animationDuration: `${d.duration}s`,
            // subtle float
            animation: `pulseDotFade ${d.duration}s ${d.delay}s ease-in-out infinite`,
          }}
        />
      ))}

      {/* A few larger "station" dots that stay fixed and glow steadily */}
      {[
        { x: 12, y: 28, c: "rgba(139,92,246,0.5)", s: 6 },
        { x: 78, y: 15, c: "rgba(6,182,212,0.4)",  s: 5 },
        { x: 55, y: 75, c: "rgba(59,130,246,0.45)", s: 5 },
        { x: 88, y: 62, c: "rgba(139,92,246,0.35)", s: 4 },
        { x: 30, y: 85, c: "rgba(16,185,129,0.4)",  s: 4 },
      ].map((d, i) => (
        <span
          key={`station-${i}`}
          style={{
            position: "absolute",
            left: `${d.x}%`,
            top: `${d.y}%`,
            width: d.s,
            height: d.s,
            borderRadius: "50%",
            background: d.c,
            boxShadow: `0 0 12px ${d.c}, 0 0 24px ${d.c}`,
            animation: `pulseDot ${2 + i * 0.4}s ease-in-out infinite`,
          }}
        />
      ))}

      <style>{`
        @keyframes pulseDotFade {
          0%,100% { opacity: 0.15; transform: scale(1); }
          50%      { opacity: 0.8;  transform: scale(1.5); }
        }
      `}</style>
    </div>
  );
}
