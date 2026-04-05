// Swiss-grade geometric mark — diamond with ascending bar chart inside
export function LogoMark({ size = 32 }) {
  const s = size;
  const cx = s / 2;
  // Diamond points
  const top = `${cx},${s * 0.04}`;
  const right = `${s * 0.96},${cx}`;
  const bottom = `${cx},${s * 0.96}`;
  const left = `${s * 0.04},${cx}`;

  // Bar chart inside (3 ascending bars)
  const bw = s * 0.1;
  const b1x = s * 0.28, b1h = s * 0.18, b1y = cx - s * 0.01;
  const b2x = s * 0.44, b2h = s * 0.27, b2y = cx + s * 0.08;
  const b3x = s * 0.60, b3h = s * 0.36, b3y = cx + s * 0.17;
  const r = s * 0.025;

  const gradId = `lgm-${size}`;
  const filtId = `lgf-${size}`;

  return (
    <svg width={s} height={s} viewBox={`0 0 ${s} ${s}`} fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2={s} y2={s} gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#8B5CF6" />
          <stop offset="50%" stopColor="#3B82F6" />
          <stop offset="100%" stopColor="#06B6D4" />
        </linearGradient>
        <filter id={filtId} x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation={s * 0.04} result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      {/* Outer glow ring */}
      <polygon
        points={`${top} ${right} ${bottom} ${left}`}
        stroke={`url(#${gradId})`}
        strokeWidth={s * 0.025}
        fill="none"
        opacity="0.25"
        strokeLinejoin="round"
        filter={`url(#${filtId})`}
      />
      {/* Main diamond outline */}
      <polygon
        points={`${top} ${right} ${bottom} ${left}`}
        stroke={`url(#${gradId})`}
        strokeWidth={s * 0.04}
        fill="none"
        strokeLinejoin="round"
      />

      {/* Bar 1 (shortest) */}
      <rect x={b1x} y={b1y - b1h} width={bw} height={b1h} rx={r} fill={`url(#${gradId})`} opacity="0.65" />
      {/* Bar 2 (medium) */}
      <rect x={b2x} y={b2y - b2h} width={bw} height={b2h} rx={r} fill={`url(#${gradId})`} opacity="0.82" />
      {/* Bar 3 (tallest) */}
      <rect x={b3x} y={b3y - b3h} width={bw} height={b3h} rx={r} fill={`url(#${gradId})`} />

      {/* Apex data point */}
      <circle cx={b3x + bw / 2} cy={b3y - b3h - s * 0.05} r={s * 0.055} fill="#06B6D4" />
    </svg>
  );
}

export function LogoFull({ size = 32, showTagline = false }) {
  return (
    <div className="flex items-center gap-2.5 select-none">
      <LogoMark size={size} />
      <div className="flex flex-col leading-none">
        <span className="font-black tracking-tight" style={{ fontSize: size * 0.56, color: "#F8FAFF", letterSpacing: "-0.02em" }}>
          Finance<span style={{ background: "linear-gradient(90deg,#8B5CF6,#06B6D4)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>IQ</span>
        </span>
        {showTagline && (
          <span className="font-mono text-slate-500" style={{ fontSize: size * 0.22, letterSpacing: "0.08em", textTransform: "uppercase" }}>
            Intelligence · Precision · Growth
          </span>
        )}
      </div>
    </div>
  );
}

export default LogoFull;
