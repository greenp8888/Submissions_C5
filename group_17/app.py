import streamlit as st
import json
import time
from orchestrator.graph import run_incident_analysis

st.set_page_config(
    page_title="Incidentiq — DevOps AI Suite",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Theme state ───────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

dark = st.session_state.dark_mode

# ── Theme tokens ──────────────────────────────────────────────────────────────
if dark:
    BG       = "#111217"
    BG2      = "#181B1F"
    BG3      = "#0D0F12"
    BORDER   = "#22252B"
    BORDER2  = "#32363F"
    TEXT     = "#D9D9D9"
    TEXT2    = "#8E9BB5"
    TEXT3    = "#4A4F5A"
    HEADING  = "#F0F0F0"
    ACCENT   = "#FF7D00"
    GREEN    = "#73BF69"
    BLUE     = "#5794F2"
    PURPLE   = "#B877D9"
    RED      = "#FF5757"
    YELLOW   = "#FADE2A"
    ORANGE   = "#FF9900"
    BTN_BG   = "#1F60C4"
    BTN_HV   = "#3274D9"
    STEP_BG  = "#1F60C4"
    CODE_BG  = "#0D0F12"
    PANEL_BG = "#181B1F"
    GREEN_BG = "#162114"
    YELLOW_BG= "#1C1400"
    TOGGLE_LABEL = "☀️  Light mode"
else:
    BG       = "#F5F6FA"
    BG2      = "#FFFFFF"
    BG3      = "#F0F1F5"
    BORDER   = "#E1E4ED"
    BORDER2  = "#C8CCDA"
    TEXT     = "#2C3047"
    TEXT2    = "#5F6680"
    TEXT3    = "#9BA3BF"
    HEADING  = "#1A1D2E"
    ACCENT   = "#FF7D00"
    GREEN    = "#2E9E52"
    BLUE     = "#1F5FBF"
    PURPLE   = "#7C3AED"
    RED      = "#DC2626"
    YELLOW   = "#B45309"
    ORANGE   = "#C2610F"
    BTN_BG   = "#1F5FBF"
    BTN_HV   = "#1A4FA0"
    STEP_BG  = "#1F5FBF"
    CODE_BG  = "#1A1D2E"
    PANEL_BG = "#FFFFFF"
    GREEN_BG = "#F0FDF4"
    YELLOW_BG= "#FFFBEB"
    TOGGLE_LABEL = "🌙  Dark mode"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {{
    background: {BG} !important;
    font-family: 'Inter', sans-serif !important;
    color: {TEXT} !important;
    transition: background 0.25s, color 0.25s;
}}

[data-testid="stSidebar"] {{
    background: {BG2} !important;
    border-right: 1px solid {BORDER} !important;
}}

#MainMenu, footer, header {{ visibility: hidden; }}
[data-testid="stDecoration"] {{ display: none; }}
.block-container {{
    padding: 1.5rem 2rem 4rem !important;
    max-width: 1300px !important;
}}

h1,h2,h3,h4,h5 {{
    font-family: 'Inter', sans-serif !important;
    color: {HEADING} !important;
    letter-spacing: -0.01em !important;
}}

.stButton > button {{
    background: {BTN_BG} !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 4px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    padding: 0.55rem 1.2rem !important;
    transition: background 0.15s !important;
}}
.stButton > button:hover {{ background: {BTN_HV} !important; }}


.stTextArea textarea {{
    background: {BG2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 4px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.8rem !important;
    color: {TEXT} !important;
}}

.stTabs [data-baseweb="tab-list"] {{
    background: transparent !important;
    border-bottom: 1px solid {BORDER} !important;
    gap: 0 !important;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    border: none !important;
    color: {TEXT2} !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 0.6rem 1.1rem !important;
    border-bottom: 2px solid transparent !important;
}}
.stTabs [aria-selected="true"] {{
    color: {HEADING} !important;
    border-bottom: 2px solid {ACCENT} !important;
    background: transparent !important;
}}

.stProgress > div > div {{
    background: {GREEN} !important;
    border-radius: 2px !important;
}}
.stProgress > div {{
    background: {BORDER} !important;
    border-radius: 2px !important;
    height: 3px !important;
}}

[data-testid="stMetric"] {{
    background: {BG2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 4px !important;
    padding: 1rem 1.25rem !important;
}}
[data-testid="stMetricLabel"] {{
    font-size: 0.72rem !important;
    color: {TEXT2} !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}}
[data-testid="stMetricValue"] {{
    font-size: 1.8rem !important;
    font-weight: 600 !important;
    color: {HEADING} !important;
}}

[data-testid="stExpander"] {{
    background: {BG2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 4px !important;
    margin-bottom: 0.5rem !important;
}}

.stDownloadButton > button {{
    background: {BG2} !important;
    color: {TEXT} !important;
    border: 1px solid {BORDER2} !important;
    border-radius: 4px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}}
.stDownloadButton > button:hover {{
    background: {BG3} !important;
    border-color: {TEXT2} !important;
}}

pre, code {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
}}
pre {{
    background: {CODE_BG} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 4px !important;
    padding: 0.85rem 1rem !important;
    color: #D9D9D9 !important;
}}

::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER2}; border-radius: 3px; }}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def sev_color(sev):
    if dark:
        return {
            "CRITICAL": ("#FF5757", "#2B1515"),
            "HIGH":     ("#FF9900", "#291D0A"),
            "MEDIUM":   ("#FADE2A", "#272309"),
            "LOW":      ("#73BF69", "#162114"),
        }.get(str(sev).upper(), ("#8E9BB5", "#1C1F26"))
    else:
        return {
            "CRITICAL": ("#DC2626", "#FEF2F2"),
            "HIGH":     ("#C2610F", "#FFF7ED"),
            "MEDIUM":   ("#B45309", "#FFFBEB"),
            "LOW":      ("#2E9E52", "#F0FDF4"),
        }.get(str(sev).upper(), ("#5F6680", "#F5F6FA"))


def safe_str(val):
    if val is None: return "—"
    if isinstance(val, str): return val
    if isinstance(val, (dict, list)): return json.dumps(val, indent=2)
    return str(val)


def safe_list(val):
    if isinstance(val, list): return val
    if isinstance(val, str):
        val = val.strip()
        if val.startswith("["):
            try: return json.loads(val)
            except: pass
        return [val] if val else []
    return []


def panel_html(content, title=None):
    header = f"""<div style="font-size:0.72rem; font-weight:600; color:{TEXT2};
                              text-transform:uppercase; letter-spacing:0.08em;
                              margin-bottom:0.75rem; padding-bottom:0.5rem;
                              border-bottom:1px solid {BORDER};">{title}</div>""" if title else ""
    return f"""
    <div style="background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:4px;
                padding:1rem 1.25rem; margin-bottom:0.75rem;">
        {header}{content}
    </div>"""


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(f"""
    <div style="padding:1.25rem 1rem 1.1rem; border-bottom:1px solid {BORDER}; margin-bottom:1.25rem;">
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="width:36px; height:36px; background:{ACCENT}; border-radius:6px;
                        display:flex; align-items:center; justify-content:center;
                        font-size:18px; font-weight:700; color:#111217; flex-shrink:0;">⬡</div>
            <div>
                <div style="font-size:1.35rem; font-weight:700; color:{HEADING};
                             letter-spacing:-0.03em; line-height:1.1;">Incidentiq</div>
                <div style="font-size:0.7rem; color:{TEXT2}; margin-top:1px;">DevOps AI Suite</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="height:1px; background:{BORDER}; margin:0.5rem 0;"></div>
    <div style="padding:0 0.75rem; margin-bottom:1.5rem;">
        <div style="font-size:0.65rem; font-weight:600; color:{TEXT3};
                     text-transform:uppercase; letter-spacing:0.1em;
                     margin-bottom:0.6rem;">Agent Pipeline</div>
    """, unsafe_allow_html=True)

    agents = [
        ("Log Classifier",       GREEN),
        ("Remediation Agent",    BLUE),
        ("Notification Agent",   ORANGE),
        ("Cookbook Synthesizer", PURPLE),
        ("JIRA Ticket Agent",    RED),
    ]
    for name, color in agents:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:10px; padding:0.4rem 0.5rem;
                    border-radius:3px; margin-bottom:2px;">
            <div style="width:5px; height:5px; border-radius:50%;
                        background:{color}; flex-shrink:0;"></div>
            <span style="font-size:0.82rem; color:{TEXT};">{name}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    </div>
    <div style="height:1px; background:{BORDER}; margin:0 0 1rem;"></div>
    <div style="padding:0 0.75rem; margin-bottom:1.5rem;">
        <div style="font-size:0.65rem; font-weight:600; color:{TEXT3};
                     text-transform:uppercase; letter-spacing:0.1em;
                     margin-bottom:0.6rem;">Integrations</div>
    """, unsafe_allow_html=True)

    for name in ["Claude Sonnet 4.5", "LangGraph", "Slack", "JIRA"]:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:8px; padding:0.35rem 0.5rem;">
            <div style="width:5px; height:5px; border-radius:50%; background:{GREEN};"></div>
            <span style="font-size:0.82rem; color:{TEXT};">{name}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    </div>
    <div style="padding:0 1rem; margin-top:0.75rem;">
        <div style="background:{BG3}; border:1px solid {BORDER}; border-radius:4px;
                    padding:0.6rem 0.85rem; margin-bottom:0.6rem;">
            <div style="font-size:0.65rem; color:{TEXT3}; margin-bottom:2px;">VERSION</div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem;
                        color:{TEXT2};">v1.0.0 · hackathon</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Theme toggle — small button
    st.markdown(f"""
    <style>
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] div[data-testid="stButton"] > button {{
        background: {BG3} !important;
        color: {TEXT2} !important;
        border: 1px solid {BORDER2} !important;
        border-radius: 3px !important;
        font-size: 0.65rem !important;
        font-weight: 400 !important;
        font-family: 'Inter', sans-serif !important;
        padding: 0 0.5rem !important;
        height: 20px !important;
        min-height: 20px !important;
        line-height: 20px !important;
        width: auto !important;
        display: inline-flex !important;
        align-items: center !important;
        letter-spacing: 0.01em !important;
        box-shadow: none !important;
    }}
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] div[data-testid="stButton"] > button:hover {{
        background: {BORDER} !important;
        color: {HEADING} !important;
        border-color: {TEXT2} !important;
    }}
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] div[data-testid="stButton"] {{
        width: auto !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    if st.button(TOGGLE_LABEL, key="theme_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()


# ── Top nav ───────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between;
            padding:0.75rem 0 1.25rem; border-bottom:1px solid {BORDER};
            margin-bottom:1.5rem;">
    <div>
        <div style="font-size:1.3rem; font-weight:600; color:{HEADING};
                     letter-spacing:-0.02em;">
            Incident Analysis
            <span style="font-size:0.72rem; font-weight:500; color:{ACCENT};
                          background:{'#291D0A' if dark else '#FFF7ED'};
                          border:1px solid {ACCENT}40;
                          padding:2px 7px; border-radius:3px; margin-left:8px;
                          vertical-align:middle; font-family:'JetBrains Mono',monospace;">
                LIVE
            </span>
        </div>
        <div style="font-size:0.8rem; color:{TEXT2}; margin-top:2px;">
            Multi-agent AI pipeline · Powered by Claude Sonnet 4.5
        </div>
    </div>
    <div style="display:flex; align-items:center; gap:8px;">
        <div style="background:{GREEN_BG}; border:1px solid {GREEN}40; border-radius:4px;
                    padding:0.3rem 0.75rem; font-size:0.75rem; color:{GREEN};
                    font-family:'JetBrains Mono',monospace;">
            ● 5 agents ready
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Pipeline diagram ──────────────────────────────────────────────────────────

def render_pipeline():
    nodes = [
        ("Log Reader",  GREEN,  "classifier"),
        ("Remediation", BLUE,   "fixes+cmds"),
        ("Slack Alert", ORANGE, "notification"),
        ("Cookbook",    PURPLE, "runbook"),
        ("JIRA",        RED,    "tickets"),
        ("OUTPUT",      GREEN,  "dashboard"),
    ]
    parts = []
    for i, (label, color, sub) in enumerate(nodes):
        bg_node = GREEN_BG if label == "OUTPUT" else BG3
        parts.append(
            f'<div style="display:flex;flex-direction:column;align-items:center;gap:5px;flex-shrink:0;">'            f'<div style="background:{bg_node};border:1px solid {color};border-radius:4px;'            f'width:82px;height:36px;display:flex;align-items:center;justify-content:center;'            f'font-size:0.72rem;color:{color};font-weight:600;">{label}</div>'            f'<div style="font-size:0.62rem;color:{TEXT3};">{sub}</div></div>'
        )
        if i < len(nodes) - 1:
            parts.append(
                f'<div style="height:1px;width:24px;background:{BORDER2};'                f'flex-shrink:0;margin-bottom:14px;"></div>'
            )
    return "".join(parts)

pipeline_html = render_pipeline()
st.markdown(
    f'<div style="background:{PANEL_BG};border:1px solid {BORDER};border-radius:4px;'    f'padding:1rem 1.5rem;margin-bottom:1.5rem;">'    f'<div style="font-size:0.65rem;font-weight:600;color:{TEXT3};'    f'text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.85rem;">Pipeline</div>'    f'<div style="display:flex;align-items:center;overflow-x:auto;">{pipeline_html}</div></div>',
    unsafe_allow_html=True
)

# ── Input ─────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="font-size:0.72rem; font-weight:600; color:{TEXT2};
             text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.6rem;">
    Log Input
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Upload log file", "Paste logs"])
log_content = None

with tab1:
    uploaded_file = st.file_uploader("Upload", type=["log","txt"], label_visibility="collapsed")
    if uploaded_file:
        log_content = uploaded_file.read().decode("utf-8")
        st.markdown(f"""
        <div style="background:{GREEN_BG}; border:1px solid {GREEN}40; border-radius:4px;
                    padding:0.5rem 0.85rem; font-size:0.82rem; color:{GREEN};
                    font-family:'JetBrains Mono',monospace; margin-top:0.5rem;">
            ✓ {uploaded_file.name} · {len(log_content.splitlines())} lines loaded
        </div>
        """, unsafe_allow_html=True)
        with st.expander("Preview"):
            st.code(log_content[:2000], language="bash")

with tab2:
    pasted = st.text_area(
        "Logs", height=160,
        placeholder="2024-01-15 08:23:11 ERROR [payment-service] Database connection timeout...",
        label_visibility="collapsed"
    )
    if pasted:
        log_content = pasted

if log_content:
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        go = st.button("▶  Analyze", use_container_width=True)

    if go:
        st.markdown(f"""
        <div style="font-size:0.72rem; font-weight:600; color:{TEXT2};
                     text-transform:uppercase; letter-spacing:0.08em;
                     margin:1.5rem 0 0.75rem;">Pipeline Status</div>
        """, unsafe_allow_html=True)

        prog  = st.progress(0)
        stati = st.empty()

        agent_names  = ["Log Classifier","Remediation","Notification","Cookbook","JIRA"]
        agent_colors = [GREEN, BLUE, ORANGE, PURPLE, RED]
        cols = st.columns(5)
        phs  = {}
        for col, name, color in zip(cols, agent_names, agent_colors):
            phs[name] = col.empty()
            phs[name].markdown(f"""
            <div style="background:{BG2}; border:1px solid {BORDER}; border-radius:4px;
                        padding:0.65rem 0.75rem; text-align:center;">
                <div style="font-size:0.62rem; color:{TEXT3}; font-weight:600;
                             text-transform:uppercase; letter-spacing:0.06em;
                             margin-bottom:4px;">{name}</div>
                <div style="font-size:0.75rem; color:{TEXT3};
                             font-family:'JetBrains Mono',monospace;">waiting</div>
            </div>
            """, unsafe_allow_html=True)

        prog.progress(5)

        try:
            with st.spinner(""):
                t0     = time.time()
                result = run_incident_analysis(log_content)
                t1     = time.time()

            prog.progress(100)
            for name, color in zip(agent_names, agent_colors):
                phs[name].markdown(f"""
                <div style="background:{GREEN_BG}; border:1px solid {color}50;
                            border-radius:4px; padding:0.65rem 0.75rem; text-align:center;">
                    <div style="font-size:0.62rem; color:{color}; font-weight:600;
                                 text-transform:uppercase; letter-spacing:0.06em;
                                 margin-bottom:4px;">{name}</div>
                    <div style="font-size:0.75rem; color:{color};
                                 font-family:'JetBrains Mono',monospace;">✓ done</div>
                </div>
                """, unsafe_allow_html=True)

            elapsed = round(t1 - t0, 2)
            stati.markdown(f"""
            <div style="background:{GREEN_BG}; border:1px solid {GREEN}40; border-radius:4px;
                        padding:0.5rem 1rem; font-size:0.82rem; color:{GREEN};
                        font-family:'JetBrains Mono',monospace; margin-top:0.5rem;">
                ✓ pipeline complete · {elapsed}s · 5 agents · 0 errors
            </div>
            """, unsafe_allow_html=True)

            # ── Data ──────────────────────────────────────────────────────────
            classified   = result.get("classified_logs", {}) or {}
            remediation  = result.get("remediation", {})     or {}
            notification = result.get("notification", {})    or {}
            cookbook     = result.get("cookbook", {})        or {}
            jira         = result.get("jira_tickets", {})    or {}

            issues   = safe_list(classified.get("issues", []))
            critical = len([i for i in issues if isinstance(i,dict) and i.get("severity")=="CRITICAL"])
            high     = len([i for i in issues if isinstance(i,dict) and i.get("severity")=="HIGH"])
            medium   = len([i for i in issues if isinstance(i,dict) and i.get("severity")=="MEDIUM"])
            services = safe_list(classified.get("affected_services", []))

            # ── Overview ──────────────────────────────────────────────────────
            st.markdown(f"""
            <div style="font-size:0.72rem; font-weight:600; color:{TEXT2};
                         text-transform:uppercase; letter-spacing:0.08em;
                         margin:1.75rem 0 0.75rem;">Incident Overview</div>
            """, unsafe_allow_html=True)

            c1,c2,c3,c4,c5 = st.columns(5)
            c1.metric("Total Issues",  len(issues))
            c2.metric("Critical",      critical)
            c3.metric("High",          high)
            c4.metric("Medium",        medium)
            c5.metric("Services Hit",  len(services))

            svc_tags = "".join(f'<span style="background:{BG3}; border:1px solid {BORDER2}; border-radius:3px; padding:2px 8px; font-size:0.72rem; color:{TEXT2}; font-family:JetBrains Mono,monospace;">{s}</span>' for s in services)
            st.markdown(panel_html(
                f'<div style="font-size:0.88rem; color:{TEXT}; line-height:1.65; margin-bottom:0.75rem;">{safe_str(classified.get("summary"))}</div>'
                f'<div style="display:flex; gap:6px; flex-wrap:wrap;">{svc_tags}</div>',
                title="Summary · " + safe_str(classified.get("time_range"))
            ), unsafe_allow_html=True)

            # ── Agent 1 ───────────────────────────────────────────────────────
            st.markdown(f"""
            <div style="font-size:0.72rem; font-weight:600; color:{GREEN};
                         text-transform:uppercase; letter-spacing:0.08em;
                         margin:1.75rem 0 0.75rem; display:flex; align-items:center; gap:8px;">
                <div style="width:3px; height:14px; background:{GREEN}; border-radius:2px;"></div>
                Agent 1 — Log Classifier
            </div>
            """, unsafe_allow_html=True)

            for issue in issues:
                if not isinstance(issue, dict): continue
                sev = issue.get("severity","LOW")
                color, bg = sev_color(sev)
                st.markdown(f"""
                <div style="background:{PANEL_BG}; border:1px solid {BORDER};
                            border-left:3px solid {color}; border-radius:4px;
                            padding:0.85rem 1.1rem; margin-bottom:0.4rem;">
                    <div style="display:flex; justify-content:space-between;
                                align-items:center; margin-bottom:5px;">
                        <span style="font-size:0.9rem; font-weight:500; color:{HEADING};">
                            {safe_str(issue.get('title'))}
                        </span>
                        <span style="background:{bg}; color:{color}; border:1px solid {color}40;
                                     font-size:0.65rem; font-weight:600; letter-spacing:0.06em;
                                     text-transform:uppercase; padding:2px 7px; border-radius:3px;
                                     font-family:'JetBrains Mono',monospace;">{sev}</span>
                    </div>
                    <div style="font-size:0.75rem; color:{TEXT3}; margin-bottom:4px;
                                 font-family:'JetBrains Mono',monospace;">
                        service: {safe_str(issue.get('affected_service'))}
                    </div>
                    <div style="font-size:0.83rem; color:{TEXT2}; line-height:1.55;">
                        {safe_str(issue.get('description'))}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # ── Agent 2 ───────────────────────────────────────────────────────
            st.markdown(f"""
            <div style="font-size:0.72rem; font-weight:600; color:{BLUE};
                         text-transform:uppercase; letter-spacing:0.08em;
                         margin:1.75rem 0 0.75rem; display:flex; align-items:center; gap:8px;">
                <div style="width:3px; height:14px; background:{BLUE}; border-radius:2px;"></div>
                Agent 2 — Remediation Plan
            </div>
            """, unsafe_allow_html=True)

            st.markdown(panel_html(
                f'<div style="font-size:0.88rem; color:{TEXT}; line-height:1.6;">{safe_str(remediation.get("overall_recommendation"))}</div>',
                title="Overall Recommendation"
            ), unsafe_allow_html=True)

            for rem in safe_list(remediation.get("remediations",[])):
                if not isinstance(rem, dict): continue
                sev = rem.get("severity","LOW")
                color, bg = sev_color(sev)
                with st.expander(f"[{sev}]  {safe_str(rem.get('title'))}  ·  ⏱ {safe_str(rem.get('estimated_time'))}", expanded=False):
                    col1,col2,col3 = st.columns(3)
                    with col1:
                        st.markdown(f"""
                        <div style="background:{BG3}; border:1px solid {BORDER}; border-radius:4px;
                                    padding:0.85rem; min-height:100px;">
                            <div style="font-size:0.65rem; color:{TEXT3}; font-weight:600;
                                         text-transform:uppercase; letter-spacing:0.08em;
                                         margin-bottom:6px;">Root Cause</div>
                            <div style="font-size:0.83rem; color:{TEXT}; line-height:1.55;">
                                {safe_str(rem.get('root_cause'))}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                        <div style="background:{GREEN_BG}; border:1px solid {GREEN}40; border-radius:4px;
                                    padding:0.85rem; min-height:100px;">
                            <div style="font-size:0.65rem; color:{GREEN}; font-weight:600;
                                         text-transform:uppercase; letter-spacing:0.08em;
                                         margin-bottom:6px;">Immediate Action</div>
                            <div style="font-size:0.83rem; color:{TEXT}; line-height:1.55;">
                                {safe_str(rem.get('immediate_action'))}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"""
                        <div style="background:{YELLOW_BG}; border:1px solid {YELLOW}40; border-radius:4px;
                                    padding:0.85rem; min-height:100px;">
                            <div style="font-size:0.65rem; color:{YELLOW}; font-weight:600;
                                         text-transform:uppercase; letter-spacing:0.08em;
                                         margin-bottom:6px;">Prevention</div>
                            <div style="font-size:0.83rem; color:{TEXT}; line-height:1.55;">
                                {safe_str(rem.get('prevention'))}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    steps = safe_list(rem.get("steps",[]))
                    if steps:
                        st.markdown(f'<div style="font-size:0.65rem; color:{TEXT3}; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; margin:1rem 0 0.5rem;">Steps</div>', unsafe_allow_html=True)
                        for i, step in enumerate(steps):
                            step_text = step if isinstance(step,str) else safe_str(step.get("action","")) if isinstance(step,dict) else str(step)
                            st.markdown(f"""
                            <div style="display:flex; align-items:flex-start; gap:10px;
                                        padding:0.55rem 0; border-bottom:1px solid {BORDER};">
                                <div style="width:20px; height:20px; border-radius:3px;
                                            background:{STEP_BG}; color:white; font-size:0.65rem;
                                            font-weight:600; display:flex; align-items:center;
                                            justify-content:center; flex-shrink:0;
                                            font-family:'JetBrains Mono',monospace;">{i+1}</div>
                                <div style="font-size:0.85rem; color:{TEXT}; line-height:1.5;
                                             padding-top:1px;">{step_text}</div>
                            </div>
                            """, unsafe_allow_html=True)

                    commands = safe_list(rem.get("commands",[]))
                    if commands:
                        st.markdown(f'<div style="font-size:0.65rem; color:{TEXT3}; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; margin:1rem 0 0.5rem;">Commands</div>', unsafe_allow_html=True)
                        st.code("\n".join([safe_str(c) for c in commands]), language="bash")

            # ── Agent 3 ───────────────────────────────────────────────────────
            st.markdown(f"""
            <div style="font-size:0.72rem; font-weight:600; color:{ORANGE};
                         text-transform:uppercase; letter-spacing:0.08em;
                         margin:1.75rem 0 0.75rem; display:flex; align-items:center; gap:8px;">
                <div style="width:3px; height:14px; background:{ORANGE}; border-radius:2px;"></div>
                Agent 3 — Slack Notification
            </div>
            """, unsafe_allow_html=True)

            slack_status = notification.get("status","unknown")
            slack_map = {
                "sent":   (f"✓ Message delivered to Slack", GREEN,  GREEN_BG,  f"{GREEN}40"),
                "mocked": (f"⬡ Mock mode — message generated", TEXT2, BG3,      BORDER),
                "error":  (f"✕ Delivery failed", RED, f"{'#1A0A0A' if dark else '#FEF2F2'}", f"{RED}40"),
            }
            slabel,sfg,sbg,sborder = slack_map.get(slack_status, slack_map["mocked"])
            st.markdown(f"""
            <div style="background:{sbg}; border:1px solid {sborder}; border-radius:4px;
                        padding:0.65rem 1rem; font-size:0.83rem; font-weight:500; color:{sfg};
                        font-family:'JetBrains Mono',monospace; margin-bottom:0.75rem;">
                {slabel}
            </div>
            """, unsafe_allow_html=True)
            with st.expander("View message payload", expanded=False):
                st.markdown(panel_html(
                    f'<div style="font-size:0.85rem; color:{TEXT}; line-height:1.6;">{safe_str(notification.get("message"))}</div>',
                    title="Message"
                ), unsafe_allow_html=True)
                st.json(notification.get("blocks",[]))

            # ── Agent 4 ───────────────────────────────────────────────────────
            st.markdown(f"""
            <div style="font-size:0.72rem; font-weight:600; color:{PURPLE};
                         text-transform:uppercase; letter-spacing:0.08em;
                         margin:1.75rem 0 0.75rem; display:flex; align-items:center; gap:8px;">
                <div style="width:3px; height:14px; background:{PURPLE}; border-radius:2px;"></div>
                Agent 4 — Incident Cookbook
            </div>
            """, unsafe_allow_html=True)

            cb_title   = safe_str(cookbook.get("title","Incident Cookbook"))
            cb_for     = safe_str(cookbook.get("created_for",""))
            cb_type    = safe_str(cookbook.get("incident_type","—"))
            cb_sev     = safe_str(cookbook.get("severity_level","—"))
            pre_checks = safe_list(cookbook.get("pre_checks",[]))
            checklist  = safe_list(cookbook.get("checklist",[]))
            escalation = safe_list(cookbook.get("escalation_path",[]))
            metrics    = safe_list(cookbook.get("key_metrics_to_monitor",[]))
            prevention = safe_list(cookbook.get("prevention_measures",[]))
            lessons    = safe_str(cookbook.get("lessons_learned","—"))
            cb_color,_ = sev_color(cb_sev)
            total_steps= sum(len(safe_list(p.get("steps",[]))) for p in checklist if isinstance(p,dict))

            st.markdown(f"""
            <div style="background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:4px;
                        padding:1rem 1.25rem; margin-bottom:0.75rem;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div style="font-size:1rem; font-weight:600; color:{HEADING}; margin-bottom:4px;">
                            {cb_title}</div>
                        <div style="font-size:0.8rem; color:{TEXT2}; line-height:1.5; max-width:600px;">
                            {cb_for}</div>
                    </div>
                    <div style="display:flex; gap:6px; flex-shrink:0; margin-left:1rem; flex-wrap:wrap; justify-content:flex-end;">
                        <span style="background:{BG3}; border:1px solid {BORDER2}; border-radius:3px; padding:2px 8px; font-size:0.72rem; color:{TEXT2}; font-family:'JetBrains Mono',monospace;">{cb_type}</span>
                        <span style="background:{BG3}; border:1px solid {cb_color}40; border-radius:3px; padding:2px 8px; font-size:0.72rem; color:{cb_color}; font-family:'JetBrains Mono',monospace;">{cb_sev}</span>
                        <span style="background:{BG3}; border:1px solid {BORDER2}; border-radius:3px; padding:2px 8px; font-size:0.72rem; color:{TEXT2}; font-family:'JetBrains Mono',monospace;">{total_steps} steps</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if pre_checks:
                with st.expander("Pre-checks", expanded=True):
                    for i, check in enumerate(pre_checks):
                        st.markdown(f"""
                        <div style="display:flex; gap:10px; padding:0.5rem 0;
                                    border-bottom:1px solid {BORDER}; align-items:flex-start;">
                            <span style="font-family:'JetBrains Mono',monospace; font-size:0.7rem;
                                          color:{TEXT3}; min-width:20px; padding-top:1px;">
                                {str(i+1).zfill(2)}</span>
                            <span style="font-size:0.85rem; color:{TEXT}; line-height:1.5;">
                                {safe_str(check)}</span>
                        </div>
                        """, unsafe_allow_html=True)

            phase_styles = {
                "Detection":     (GREEN,  "🔍"),
                "Containment":   (ORANGE, "🛡"),
                "Resolution":    (BLUE,   "✓"),
                "Post-Incident": (PURPLE, "📝"),
            }

            if checklist:
                with st.expander("Response checklist", expanded=True):
                    for phase in checklist:
                        if not isinstance(phase, dict): continue
                        phase_name = safe_str(phase.get("phase","Phase"))
                        p_color, p_icon = phase_styles.get(phase_name, (TEXT2,"▶"))
                        st.markdown(f"""
                        <div style="display:flex; align-items:center; gap:8px;
                                    margin:1rem 0 0.5rem; padding-bottom:0.4rem;
                                    border-bottom:1px solid {BORDER};">
                            <div style="width:3px; height:12px; background:{p_color}; border-radius:2px;"></div>
                            <span style="font-size:0.72rem; font-weight:600; color:{p_color};
                                          text-transform:uppercase; letter-spacing:0.08em;">
                                {phase_name}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        for step in safe_list(phase.get("steps",[])):
                            if not isinstance(step, dict): continue
                            action  = safe_str(step.get("action",""))
                            expected= safe_str(step.get("expected_output","—"))
                            eta     = safe_str(step.get("time_estimate","—"))
                            command = safe_str(step.get("command",""))
                            stepnum = safe_str(step.get("step",""))
                            col1,col2 = st.columns([5,1])
                            with col1:
                                st.markdown(f"""
                                <div style="padding:0.55rem 0 0.35rem;">
                                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
                                        <span style="background:{STEP_BG}; color:white; font-size:0.62rem;
                                                     font-weight:600; width:18px; height:18px; border-radius:3px;
                                                     display:flex; align-items:center; justify-content:center;
                                                     flex-shrink:0; font-family:'JetBrains Mono',monospace;">
                                            {stepnum}</span>
                                        <span style="font-size:0.87rem; color:{HEADING}; font-weight:500;
                                                     line-height:1.4;">{action}</span>
                                    </div>
                                    <div style="font-size:0.75rem; color:{TEXT3}; margin-left:26px; line-height:1.4;">
                                        expected: {expected}</div>
                                </div>
                                """, unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"""
                                <div style="text-align:right; padding-top:0.6rem;">
                                    <span style="font-size:0.7rem; color:{TEXT3};
                                                  font-family:'JetBrains Mono',monospace;">{eta}</span>
                                </div>
                                """, unsafe_allow_html=True)
                            if command and command != "—":
                                st.code(command, language="bash")
                            st.markdown(f'<div style="height:1px; background:{BORDER};"></div>', unsafe_allow_html=True)

            if escalation:
                with st.expander("Escalation path", expanded=False):
                    icons = ["👤","👥","🏢","🔱"]
                    cols  = st.columns(len(escalation))
                    for i,(col,level) in enumerate(zip(cols,escalation)):
                        with col:
                            st.markdown(f"""
                            <div style="background:{BG3}; border:1px solid {BORDER}; border-radius:4px;
                                        padding:0.85rem; text-align:center;">
                                <div style="font-size:1.2rem; margin-bottom:6px;">
                                    {icons[i] if i<len(icons) else '👤'}</div>
                                <div style="font-size:0.62rem; color:{TEXT3}; font-weight:600;
                                             text-transform:uppercase; letter-spacing:0.08em;
                                             margin-bottom:4px; font-family:'JetBrains Mono',monospace;">
                                    level {i+1}</div>
                                <div style="font-size:0.8rem; color:{TEXT}; line-height:1.4;">
                                    {safe_str(level)}</div>
                            </div>
                            """, unsafe_allow_html=True)

            if metrics:
                with st.expander("Key metrics to monitor", expanded=False):
                    cols = st.columns(2)
                    for i,metric in enumerate(metrics):
                        with cols[i%2]:
                            st.markdown(f"""
                            <div style="display:flex; align-items:center; gap:8px;
                                        padding:0.5rem 0; border-bottom:1px solid {BORDER};">
                                <span style="color:{PURPLE}; font-size:0.8rem; flex-shrink:0;">↗</span>
                                <span style="font-size:0.83rem; color:{TEXT};">{safe_str(metric)}</span>
                            </div>
                            """, unsafe_allow_html=True)

            if prevention:
                with st.expander("Prevention measures", expanded=False):
                    for measure in prevention:
                        st.markdown(f"""
                        <div style="display:flex; align-items:flex-start; gap:8px;
                                    padding:0.5rem 0; border-bottom:1px solid {BORDER};">
                            <span style="color:{GREEN}; font-size:0.8rem; flex-shrink:0; margin-top:1px;
                                          font-family:'JetBrains Mono',monospace;">✓</span>
                            <span style="font-size:0.83rem; color:{TEXT}; line-height:1.5;">
                                {safe_str(measure)}</span>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background:{YELLOW_BG}; border:1px solid {YELLOW}30;
                        border-left:3px solid {YELLOW}; border-radius:4px;
                        padding:0.85rem 1.1rem; margin-top:0.75rem;">
                <div style="font-size:0.65rem; color:{YELLOW}; font-weight:600;
                             text-transform:uppercase; letter-spacing:0.08em;
                             margin-bottom:6px; font-family:'JetBrains Mono',monospace;">
                    ⚡ Lessons Learned</div>
                <div style="font-size:0.88rem; color:{TEXT}; line-height:1.7;">{lessons}</div>
            </div>
            """, unsafe_allow_html=True)

            # ── Agent 5 ───────────────────────────────────────────────────────
            st.markdown(f"""
            <div style="font-size:0.72rem; font-weight:600; color:{RED};
                         text-transform:uppercase; letter-spacing:0.08em;
                         margin:1.75rem 0 0.75rem; display:flex; align-items:center; gap:8px;">
                <div style="width:3px; height:14px; background:{RED}; border-radius:2px;"></div>
                Agent 5 — JIRA Tickets
            </div>
            """, unsafe_allow_html=True)

            jira_status = jira.get("status","unknown")
            jira_count  = jira.get("total_created",0)
            jira_map2 = {
                "success": (f"✓ {jira_count} tickets created in JIRA", GREEN, GREEN_BG, f"{GREEN}40"),
                "mocked":  (f"⬡ Mock mode — {jira_count} tickets generated", TEXT2, BG3, BORDER),
                "error":   (f"✕ {safe_str(jira.get('error'))}", RED, f"{'#1A0A0A' if dark else '#FEF2F2'}", f"{RED}40"),
            }
            jlabel,jfg,jbg,jborder = jira_map2.get(jira_status, jira_map2["mocked"])
            st.markdown(f"""
            <div style="background:{jbg}; border:1px solid {jborder}; border-radius:4px;
                        padding:0.65rem 1rem; font-size:0.83rem; font-weight:500; color:{jfg};
                        font-family:'JetBrains Mono',monospace; margin-bottom:0.75rem;">
                {jlabel}
            </div>
            """, unsafe_allow_html=True)

            for ticket in safe_list(jira.get("tickets",[])):
                if not isinstance(ticket, dict): continue
                sev = ticket.get("severity","LOW")
                color,bg = sev_color(sev)
                st.markdown(f"""
                <div style="background:{PANEL_BG}; border:1px solid {BORDER};
                            border-left:3px solid {color}; border-radius:4px;
                            padding:0.85rem 1.1rem; margin-bottom:0.4rem;
                            display:flex; align-items:flex-start; gap:1rem;">
                    <div style="flex-shrink:0;">
                        <span style="font-family:'JetBrains Mono',monospace; font-size:0.72rem;
                                     color:{TEXT3}; background:{BG3}; border:1px solid {BORDER};
                                     border-radius:3px; padding:2px 7px; white-space:nowrap;">
                            {safe_str(ticket.get('ticket_id'))}</span>
                    </div>
                    <div style="flex:1;">
                        <div style="display:flex; justify-content:space-between;
                                    align-items:flex-start; margin-bottom:5px;">
                            <span style="font-size:0.88rem; font-weight:500; color:{HEADING};
                                         line-height:1.4;">{safe_str(ticket.get('title'))}</span>
                            <span style="background:{bg}; color:{color}; border:1px solid {color}40;
                                         font-size:0.65rem; font-weight:600; letter-spacing:0.06em;
                                         text-transform:uppercase; padding:2px 7px; border-radius:3px;
                                         font-family:'JetBrains Mono',monospace; flex-shrink:0;
                                         margin-left:8px;">{sev}</span>
                        </div>
                        <div style="font-size:0.8rem; color:{TEXT2}; margin-bottom:4px; line-height:1.4;">
                            {safe_str(ticket.get('description'))}</div>
                        <div style="font-size:0.8rem; color:{GREEN};">
                            ⚡ {safe_str(ticket.get('immediate_action'))}</div>
                        {"" if jira_status!="success" else f'<a href="{ticket.get("url","")}" style="font-size:0.75rem; color:{BLUE}; text-decoration:none; font-family:JetBrains Mono,monospace;">→ open in JIRA</a>'}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # ── Export ────────────────────────────────────────────────────────
            st.markdown(f"""
            <div style="font-size:0.72rem; font-weight:600; color:{TEXT2};
                         text-transform:uppercase; letter-spacing:0.08em;
                         margin:1.75rem 0 0.75rem;">Export</div>
            """, unsafe_allow_html=True)
            col1,col2 = st.columns(2)
            with col1:
                st.download_button("⬇  incident_report.json",
                    data=json.dumps(result,indent=2),
                    file_name="incident_report.json",
                    mime="application/json", use_container_width=True)
            with col2:
                st.download_button("⬇  incident_cookbook.json",
                    data=json.dumps(cookbook,indent=2),
                    file_name="incident_cookbook.json",
                    mime="application/json", use_container_width=True)

        except Exception as e:
            prog.progress(0)
            st.error(f"Pipeline failed: {str(e)}")
            st.exception(e)

else:
    st.markdown(f"""
    <div style="background:{PANEL_BG}; border:1px solid {BORDER}; border-radius:4px;
                padding:3rem; text-align:center; margin-top:1rem;">
        <div style="font-size:0.82rem; color:{TEXT3}; margin-bottom:0.5rem;
                     font-family:'JetBrains Mono',monospace;">no data · awaiting log input</div>
        <div style="font-size:0.78rem; color:{BORDER2};">
            Upload a .log or .txt file, or paste log content above
        </div>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("Sample log format"):
        st.code("""2024-01-15 08:23:11 ERROR [payment-service] Database connection timeout after 30s
2024-01-15 08:23:12 CRITICAL [payment-service] Failed to process payment for order #45231
2024-01-15 08:23:15 ERROR [api-gateway] Upstream service payment-service returning 503
2024-01-15 08:23:20 ERROR [auth-service] Redis cache miss rate at 98%
2024-01-15 08:23:22 CRITICAL [auth-service] JWT token validation failing
2024-01-15 08:23:35 ERROR [monitoring] Disk usage at 94% on db-prod-01
2024-01-15 08:23:45 CRITICAL [payment-service] Deadlock detected in transaction_logs table""", language="bash")
