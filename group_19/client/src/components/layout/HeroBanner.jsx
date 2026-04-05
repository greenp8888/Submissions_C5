import { useEffect, useRef } from "react";

// ── Pure-CSS 3D Cube ──────────────────────────────────────────────────────
function Cube3D({ size = 56, color = "rgba(139,92,246,0.35)", speed = "14s", delay = "0s" }) {
  const faceStyle = {
    position: "absolute",
    width: size,
    height: size,
    border: `1px solid ${color}`,
    background: `${color.replace("0.35", "0.04")}`,
    backdropFilter: "blur(2px)",
  };
  const half = size / 2;
  return (
    <div style={{ perspective: 600, width: size, height: size, flexShrink: 0 }}>
      <div style={{
        width: size, height: size, position: "relative",
        transformStyle: "preserve-3d",
        animation: `spinCube ${speed} linear infinite`,
        animationDelay: delay,
      }}>
        <div style={{ ...faceStyle, transform: `translateZ(${half}px)` }} />
        <div style={{ ...faceStyle, transform: `rotateY(180deg) translateZ(${half}px)` }} />
        <div style={{ ...faceStyle, transform: `rotateY(-90deg) translateZ(${half}px)` }} />
        <div style={{ ...faceStyle, transform: `rotateY(90deg) translateZ(${half}px)` }} />
        <div style={{ ...faceStyle, transform: `rotateX(90deg) translateZ(${half}px)` }} />
        <div style={{ ...faceStyle, transform: `rotateX(-90deg) translateZ(${half}px)` }} />
      </div>
    </div>
  );
}

// ── CSS Diamond (rotated square) ─────────────────────────────────────────
function Diamond({ size = 40, color = "rgba(6,182,212,0.4)", speed = "10s", delay = "0s" }) {
  return (
    <div style={{
      width: size, height: size, flexShrink: 0,
      border: `1.5px solid ${color}`,
      background: `${color.replace("0.4", "0.04")}`,
      transform: "rotate(45deg)",
      animation: `spinDiamond ${speed} linear infinite`,
      animationDelay: delay,
      boxShadow: `0 0 16px ${color.replace("0.4", "0.25")}`,
    }} />
  );
}

// ── Animated SVG chart (GIF-like) ─────────────────────────────────────────
function AnimatedChart() {
  return (
    <svg width="80" height="48" viewBox="0 0 80 48" fill="none" style={{ flexShrink: 0 }}>
      <defs>
        <linearGradient id="cg" x1="0" y1="0" x2="80" y2="0" gradientUnits="userSpaceOnUse">
          <stop stopColor="#8B5CF6" />
          <stop offset="1" stopColor="#06B6D4" />
        </linearGradient>
      </defs>
      {/* Baseline */}
      <line x1="4" y1="44" x2="76" y2="44" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
      {/* Animated bars */}
      {[
        { x: 8,  maxH: 12, dur: "1.8s", delay: "0s" },
        { x: 19, maxH: 22, dur: "1.8s", delay: "0.15s" },
        { x: 30, maxH: 16, dur: "1.8s", delay: "0.3s" },
        { x: 41, maxH: 30, dur: "1.8s", delay: "0.45s" },
        { x: 52, maxH: 20, dur: "1.8s", delay: "0.6s" },
        { x: 63, maxH: 38, dur: "1.8s", delay: "0.75s" },
      ].map((b, i) => (
        <rect key={i} x={b.x} y={44 - b.maxH} width="8" height={b.maxH} rx="2" fill="url(#cg)" opacity="0.75">
          <animate attributeName="height" values={`0;${b.maxH};${b.maxH * 0.7};${b.maxH}`}
            dur={b.dur} begin={b.delay} repeatCount="indefinite" />
          <animate attributeName="y" values={`44;${44 - b.maxH};${44 - b.maxH * 0.7};${44 - b.maxH}`}
            dur={b.dur} begin={b.delay} repeatCount="indefinite" />
        </rect>
      ))}
      {/* Trend line */}
      <polyline
        points="12,40 23,32 34,36 45,20 56,28 71,10"
        stroke="url(#cg)" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round"
        strokeDasharray="120" strokeDashoffset="120"
      >
        <animate attributeName="stroke-dashoffset" values="120;0;0;120" dur="3s" repeatCount="indefinite" />
      </polyline>
      {/* End dot */}
      <circle cx="71" cy="10" r="3" fill="#06B6D4">
        <animate attributeName="opacity" values="0;1;1;0" dur="3s" repeatCount="indefinite" />
        <animate attributeName="r" values="2;3;4;3" dur="1.5s" repeatCount="indefinite" />
      </circle>
    </svg>
  );
}

// ── Animated pulse ring ───────────────────────────────────────────────────
function PulseOrb({ color = "#8B5CF6" }) {
  return (
    <div style={{ position: "relative", width: 36, height: 36, flexShrink: 0 }}>
      {[0, 1, 2].map(i => (
        <div key={i} style={{
          position: "absolute", inset: 0, borderRadius: "50%",
          border: `1px solid ${color}`,
          animation: `orbRing 2.4s ease-out infinite`,
          animationDelay: `${i * 0.8}s`,
        }} />
      ))}
      <div style={{
        position: "absolute", inset: "30%", borderRadius: "50%",
        background: color, boxShadow: `0 0 10px ${color}`,
      }} />
    </div>
  );
}

// ── Floating sparkle dots ─────────────────────────────────────────────────
function Sparkle({ x, y, delay }) {
  return (
    <div style={{
      position: "absolute", left: x, top: y,
      width: 3, height: 3, borderRadius: "50%",
      background: "rgba(139,92,246,0.7)",
      boxShadow: "0 0 6px rgba(139,92,246,0.8)",
      animation: `floatSparkle 3s ease-in-out infinite`,
      animationDelay: delay,
    }} />
  );
}

export default function HeroBanner() {
  return (
    <>
      {/* Inject keyframes */}
      <style>{`
        @keyframes spinCube {
          from { transform: rotateY(0deg) rotateX(15deg) rotateZ(0deg); }
          to   { transform: rotateY(360deg) rotateX(15deg) rotateZ(10deg); }
        }
        @keyframes spinDiamond {
          from { transform: rotate(45deg); }
          to   { transform: rotate(405deg); }
        }
        @keyframes orbRing {
          0%   { transform: scale(1); opacity: 0.7; }
          100% { transform: scale(2.5); opacity: 0; }
        }
        @keyframes floatSparkle {
          0%,100% { transform: translateY(0); opacity: 0.4; }
          50%      { transform: translateY(-8px); opacity: 1; }
        }
        @keyframes scanLine {
          0%   { transform: translateX(-100%); }
          100% { transform: translateX(400%); }
        }
      `}</style>

      <div
        className="relative w-full overflow-hidden flex-shrink-0"
        style={{
          background: "linear-gradient(180deg, rgba(139,92,246,0.07) 0%, rgba(5,6,15,0) 100%)",
          borderBottom: "1px solid rgba(255,255,255,0.05)",
          minHeight: 110,
        }}
      >
        {/* Sparkle dots */}
        <Sparkle x="8%"  y="20%" delay="0s" />
        <Sparkle x="15%" y="65%" delay="0.6s" />
        <Sparkle x="82%" y="25%" delay="1.1s" />
        <Sparkle x="90%" y="70%" delay="0.3s" />
        <Sparkle x="50%" y="15%" delay="1.8s" />

        {/* Scan line shimmer */}
        <div style={{
          position: "absolute", inset: 0, pointerEvents: "none",
          overflow: "hidden",
        }}>
          <div style={{
            position: "absolute", top: 0, bottom: 0, width: "25%",
            background: "linear-gradient(90deg, transparent, rgba(139,92,246,0.04), transparent)",
            animation: "scanLine 4s ease-in-out infinite",
          }} />
        </div>

        {/* Content row */}
        <div className="relative flex items-center justify-between px-6 py-5 gap-4 flex-wrap">
          {/* Left — 3D shapes cluster */}
          <div className="flex items-center gap-5 flex-shrink-0">
            <Cube3D size={48} color="rgba(139,92,246,0.4)" speed="14s" delay="0s" />
            <Diamond size={32} color="rgba(6,182,212,0.5)" speed="10s" delay="-3s" />
            <Cube3D size={28} color="rgba(59,130,246,0.35)" speed="18s" delay="-6s" />
          </div>

          {/* Center — tagline */}
          <div className="flex flex-col items-center gap-1 flex-1 min-w-0 text-center">
            <p className="text-xs font-medium tracking-widest uppercase text-slate-500" style={{ letterSpacing: "0.18em" }}>
              AI · Multi-Agent · Real-Time
            </p>
            <h1 className="text-lg sm:text-xl font-black leading-tight whitespace-nowrap">
              <span style={{
                background: "linear-gradient(90deg,#a78bfa,#60a5fa,#22d3ee)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}>
                Intelligence That Compounds™
              </span>
            </h1>
            <p className="text-slate-500 text-[11px] max-w-xs">
              Six specialist agents · Bank-grade analysis · 60 seconds
            </p>
          </div>

          {/* Right — animated elements */}
          <div className="flex items-center gap-4 flex-shrink-0">
            <AnimatedChart />
            <PulseOrb color="#8B5CF6" />
            <Diamond size={24} color="rgba(139,92,246,0.45)" speed="8s" delay="-2s" />
          </div>
        </div>
      </div>
    </>
  );
}
