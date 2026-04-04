interface Feature {
  feature: string;
  rationale: string;
  priority: "high" | "medium" | "low";
  source_urls?: string[];
}

interface FeatureTableProps {
  features: Feature[];
}

const PRIORITY_META = {
  high:   { label: "HIGH",   bar: 88, color: "#3fb950", bg: "rgba(35,134,54,0.18)",   border: "rgba(63,185,80,0.35)",   text: "#3fb950",  fill: "linear-gradient(90deg,#2ea043,#3fb950)" },
  medium: { label: "MED",    bar: 58, color: "#d29922", bg: "rgba(187,128,9,0.18)",   border: "rgba(210,153,34,0.35)",  text: "#d29922",  fill: "linear-gradient(90deg,#bb8009,#d29922)" },
  low:    { label: "LOW",    bar: 30, color: "#f85149", bg: "rgba(248,81,73,0.16)",   border: "rgba(248,81,73,0.35)",   text: "#f85149",  fill: "linear-gradient(90deg,#da3633,#f85149)" },
};

export default function FeatureTable({ features }: FeatureTableProps) {
  return (
    <div
      style={{
        border: "1px solid #30363d",
        borderRadius: 14,
        overflow: "hidden",
      }}
    >
      {/* Table header */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 160px 80px",
          background: "#161b22",
          borderBottom: "1px solid #30363d",
          padding: "10px 16px",
          gap: 12,
        }}
      >
        {["Feature & Rationale", "Signal Strength", "Status"].map((h) => (
          <span
            key={h}
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 11,
              letterSpacing: "0.08em",
              color: "#8b949e",
              fontWeight: 500,
              textTransform: "uppercase",
            }}
          >
            {h}
          </span>
        ))}
      </div>

      {/* Rows */}
      {features.map((item, idx) => {
        const meta = PRIORITY_META[item.priority];
        return (
          <div
            key={idx}
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 160px 80px",
              padding: "14px 16px",
              gap: 12,
              borderBottom: idx < features.length - 1 ? "1px solid #21262d" : "none",
              background: "#0d1117",
              alignItems: "start",
            }}
          >
            {/* Feature + rationale + source links */}
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                <span
                  style={{
                    fontSize: 14,
                    fontWeight: 600,
                    color: "#f0f6fc",
                  }}
                >
                  {item.feature}
                </span>
                <span
                  style={{
                    padding: "1px 7px",
                    borderRadius: 999,
                    fontSize: 10,
                    fontWeight: 700,
                    fontFamily: "var(--font-mono)",
                    letterSpacing: "0.06em",
                    background: meta.bg,
                    color: meta.text,
                    border: `1px solid ${meta.border}`,
                    flexShrink: 0,
                  }}
                >
                  {meta.label}
                </span>
              </div>
              <p style={{ fontSize: 13, color: "#8b949e", lineHeight: 1.55, margin: 0 }}>
                {item.rationale}
              </p>
              {item.source_urls && item.source_urls.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
                  {item.source_urls.map((url, i) => (
                    <a
                      key={i}
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        fontFamily: "var(--font-mono)",
                        fontSize: 11,
                        color: "#58a6ff",
                        textDecoration: "none",
                        padding: "2px 7px",
                        borderRadius: 4,
                        background: "rgba(88,166,255,0.08)",
                        border: "1px solid rgba(88,166,255,0.2)",
                      }}
                      onMouseEnter={(e) => { (e.currentTarget as HTMLAnchorElement).style.textDecoration = "underline"; }}
                      onMouseLeave={(e) => { (e.currentTarget as HTMLAnchorElement).style.textDecoration = "none"; }}
                    >
                      source {i + 1} ↗
                    </a>
                  ))}
                </div>
              )}
            </div>

            {/* Mini bar */}
            <div style={{ paddingTop: 4 }}>
              <div
                style={{
                  width: "100%",
                  height: 8,
                  background: "#21262d",
                  borderRadius: 999,
                  overflow: "hidden",
                  border: "1px solid #30363d",
                }}
              >
                <div
                  style={{
                    height: "100%",
                    width: `${meta.bar}%`,
                    background: meta.fill,
                    borderRadius: 999,
                    transition: "width 0.6s cubic-bezier(0.16,1,0.3,1)",
                  }}
                />
              </div>
              <p
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: 11,
                  color: "#8b949e",
                  marginTop: 4,
                  margin: "4px 0 0 0",
                }}
              >
                {meta.bar}%
              </p>
            </div>

            {/* Status dot */}
            <div style={{ paddingTop: 4 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    background: meta.color,
                    boxShadow: `0 0 6px ${meta.color}`,
                    flexShrink: 0,
                  }}
                />
                <span
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 11,
                    color: meta.text,
                    fontWeight: 600,
                  }}
                >
                  {item.priority.toUpperCase()}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
