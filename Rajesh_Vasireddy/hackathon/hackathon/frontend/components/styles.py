"""Global CSS injector – call inject_css() at the top of every page."""

import streamlit as st

# Design tokens
CRITICAL = "#ef4444"
HIGH     = "#f97316"
MEDIUM   = "#eab308"
LOW      = "#22c55e"
ACCENT   = "#3b82f6"
PURPLE   = "#8b5cf6"

SEVERITY_HEX = {
    "CRITICAL": CRITICAL,
    "HIGH":     HIGH,
    "MEDIUM":   MEDIUM,
    "LOW":      LOW,
    "UNKNOWN":  "#64748b",
}

_CSS = """
<style>
/* ── Design tokens ─────────────────────────────── */
:root {
  --bg:        #070b14;
  --surface:   #0d1321;
  --surface2:  #111827;
  --surface3:  #1a2540;
  --border:    #1e3a5f;
  --border2:   #243352;
  --accent:    #3b82f6;
  --accent2:   #8b5cf6;
  --critical:  #ef4444;
  --high:      #f97316;
  --medium:    #eab308;
  --low:       #22c55e;
  --text:      #e2e8f0;
  --text2:     #94a3b8;
  --text3:     #475569;
  --radius:    10px;
  --radius-lg: 16px;
}

/* ── App background ────────────────────────────── */
.stApp {
  background: var(--bg);
  color: var(--text);
}
.stApp > header { background: transparent !important; }

/* ── Main container padding ────────────────────── */
.block-container {
  padding-top: 1.8rem !important;
  padding-bottom: 2rem !important;
  max-width: 1300px !important;
}

/* ── Sidebar ───────────────────────────────────── */
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption { color: var(--text2) !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: var(--text) !important; }
[data-testid="stSidebar"] input {
  background: var(--surface3) !important;
  border: 1px solid var(--border2) !important;
  color: var(--text) !important;
  border-radius: var(--radius) !important;
}

/* ── Headings ──────────────────────────────────── */
h1 { color: var(--text) !important; font-size: 1.9rem !important; font-weight: 700 !important; letter-spacing: -0.5px; }
h2 { color: var(--text) !important; font-size: 1.4rem !important; font-weight: 600 !important; }
h3 { color: var(--text2) !important; font-size: 1.1rem !important; font-weight: 500 !important; }
p, li { color: var(--text) !important; }

/* ── Metric cards ──────────────────────────────── */
[data-testid="stMetric"] {
  background: var(--surface2) !important;
  border: 1px solid var(--border2) !important;
  border-radius: var(--radius) !important;
  padding: 1rem 1.2rem !important;
  transition: border-color .2s;
}
[data-testid="stMetric"]:hover { border-color: var(--accent) !important; }
[data-testid="stMetricLabel"] { color: var(--text2) !important; font-size: .8rem !important; letter-spacing: .5px; }
[data-testid="stMetricValue"] { color: var(--text) !important; font-size: 1.6rem !important; font-weight: 700 !important; }

/* ── Buttons ───────────────────────────────────── */
.stButton > button {
  background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
  color: #fff !important;
  border: none !important;
  border-radius: var(--radius) !important;
  padding: .5rem 1.4rem !important;
  font-weight: 600 !important;
  font-size: .875rem !important;
  letter-spacing: .3px !important;
  transition: opacity .2s, transform .1s !important;
  box-shadow: 0 0 16px rgba(59,130,246,.25) !important;
}
.stButton > button:hover {
  opacity: .88 !important;
  transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
  background: var(--surface3) !important;
  border: 1px solid var(--border2) !important;
  box-shadow: none !important;
}

/* ── Download button ───────────────────────────── */
[data-testid="stDownloadButton"] > button {
  background: var(--surface3) !important;
  color: var(--accent) !important;
  border: 1px solid var(--accent) !important;
  border-radius: var(--radius) !important;
  font-weight: 600 !important;
}

/* ── Tabs ──────────────────────────────────────── */
[data-testid="stTabs"] [role="tablist"] {
  background: var(--surface2) !important;
  border-radius: var(--radius) !important;
  padding: 4px !important;
  border: 1px solid var(--border) !important;
  gap: 4px !important;
}
[data-testid="stTabs"] [role="tab"] {
  background: transparent !important;
  color: var(--text2) !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  transition: all .2s !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  background: var(--accent) !important;
  color: #fff !important;
}
[data-testid="stTabContent"] { padding-top: 1rem !important; }

/* ── Expanders ─────────────────────────────────── */
[data-testid="stExpander"] {
  background: var(--surface2) !important;
  border: 1px solid var(--border2) !important;
  border-radius: var(--radius) !important;
  margin-bottom: .5rem !important;
  overflow: hidden !important;
}
[data-testid="stExpander"] summary {
  color: var(--text) !important;
  font-weight: 600 !important;
  padding: .75rem 1rem !important;
}
[data-testid="stExpander"] summary:hover { background: var(--surface3) !important; }

/* ── Alerts / info boxes ───────────────────────── */
[data-testid="stAlert"] {
  border-radius: var(--radius) !important;
  border-left-width: 4px !important;
  font-size: .875rem !important;
}
.stAlert[data-baseweb="notification"] { background: var(--surface2) !important; }
[data-testid="stAlert"][data-type="info"]    { background: rgba(59,130,246,.1) !important; border-color: var(--accent) !important; }
[data-testid="stAlert"][data-type="success"] { background: rgba(34,197,94,.1) !important;  border-color: var(--low) !important; }
[data-testid="stAlert"][data-type="warning"] { background: rgba(234,179,8,.1) !important;  border-color: var(--medium) !important; }
[data-testid="stAlert"][data-type="error"]   { background: rgba(239,68,68,.1) !important;  border-color: var(--critical) !important; }

/* ── Text input / select ───────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
  background: var(--surface2) !important;
  border: 1px solid var(--border2) !important;
  color: var(--text) !important;
  border-radius: var(--radius) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(59,130,246,.2) !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label,
.stFileUploader label { color: var(--text2) !important; font-size: .85rem !important; }

/* ── File uploader ─────────────────────────────── */
[data-testid="stFileUploader"] {
  background: var(--surface2) !important;
  border: 2px dashed var(--border2) !important;
  border-radius: var(--radius-lg) !important;
  transition: border-color .2s !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--accent) !important; }

/* ── Progress bar ──────────────────────────────── */
[data-testid="stProgressBar"] > div {
  background: var(--surface3) !important;
  border-radius: 99px !important;
  height: 8px !important;
}
[data-testid="stProgressBar"] > div > div {
  background: linear-gradient(90deg, var(--accent), var(--accent2)) !important;
  border-radius: 99px !important;
}

/* ── Code blocks ───────────────────────────────── */
.stCodeBlock, pre, code {
  background: #0a0e1a !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  color: #93c5fd !important;
}

/* ── Dataframe / table ─────────────────────────── */
[data-testid="stDataFrame"] { border: 1px solid var(--border2) !important; border-radius: var(--radius) !important; }

/* ── Divider ───────────────────────────────────── */
hr { border-color: var(--border) !important; margin: 1.2rem 0 !important; }

/* ── Spinner ───────────────────────────────────── */
[data-testid="stSpinner"] { color: var(--accent) !important; }

/* ── Scrollbar ─────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--surface); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* ── Caption / small text ──────────────────────── */
.stCaption, small { color: var(--text3) !important; }

/* ── Balloons override ─────────────────────────── */
.stSuccess { color: var(--low) !important; }
</style>
"""


def inject_css() -> None:
    """Inject the global design-system CSS. Call once per page."""
    st.markdown(_CSS, unsafe_allow_html=True)


def card(content_html: str, accent: str = "#3b82f6", padding: str = "1.2rem") -> None:
    """Render a styled glass card with a coloured left border."""
    st.markdown(
        f"""<div style="
            background:#111827;
            border:1px solid #1e3a5f;
            border-left:4px solid {accent};
            border-radius:10px;
            padding:{padding};
            margin-bottom:.6rem;
        ">{content_html}</div>""",
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "", icon: str = "") -> None:
    """Render a gradient page header banner."""
    icon_html = f'<span style="font-size:1.6rem;margin-right:.5rem">{icon}</span>' if icon else ""
    sub_html  = f'<p style="color:#64748b;font-size:.88rem;margin:.2rem 0 0">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""<div style="
            background:linear-gradient(135deg,#0d1321 0%,#111827 60%,#1a2540 100%);
            border:1px solid #1e3a5f;
            border-radius:14px;
            padding:1.4rem 1.8rem;
            margin-bottom:1.4rem;
        ">
            <h1 style="margin:0;font-size:1.7rem;font-weight:700;
                       background:linear-gradient(90deg,#e2e8f0,#93c5fd);
                       -webkit-background-clip:text;-webkit-text-fill-color:transparent">
                {icon_html}{title}
            </h1>
            {sub_html}
        </div>""",
        unsafe_allow_html=True,
    )


def severity_pill(severity: str, size: str = "md") -> str:
    """Return an HTML severity pill string."""
    colors = {
        "CRITICAL": ("#ef4444", "#fff"),
        "HIGH":     ("#f97316", "#fff"),
        "MEDIUM":   ("#eab308", "#111"),
        "LOW":      ("#22c55e", "#fff"),
        "UNKNOWN":  ("#64748b", "#fff"),
    }
    bg, fg = colors.get(severity.upper(), colors["UNKNOWN"])
    fs = ".72rem" if size == "sm" else ".82rem"
    px = "3px 10px" if size == "sm" else "4px 14px"
    return (
        f'<span style="background:{bg};color:{fg};padding:{px};border-radius:99px;'
        f'font-weight:700;font-size:{fs};letter-spacing:.5px">{severity.upper()}</span>'
    )
