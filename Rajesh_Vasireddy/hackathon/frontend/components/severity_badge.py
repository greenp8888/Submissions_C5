"""Color-coded severity badge component."""

import streamlit as st

_PALETTE = {
    "CRITICAL": ("#ef4444", "#fff", "rgba(239,68,68,.15)"),
    "HIGH":     ("#f97316", "#fff", "rgba(249,115,22,.15)"),
    "MEDIUM":   ("#eab308", "#111", "rgba(234,179,8,.15)"),
    "LOW":      ("#22c55e", "#fff", "rgba(34,197,94,.15)"),
    "UNKNOWN":  ("#64748b", "#fff", "rgba(100,116,139,.15)"),
}


def severity_badge(severity: str) -> None:
    """Render a large styled severity banner."""
    sev = severity.upper()
    border, fg, glow = _PALETTE.get(sev, _PALETTE["UNKNOWN"])
    st.markdown(
        f"""<div style="
            display:inline-flex;align-items:center;gap:.6rem;
            background:{glow};
            border:1px solid {border};
            border-radius:12px;
            padding:.6rem 1.4rem;
            margin-bottom:.5rem;
        ">
            <span style="width:10px;height:10px;border-radius:50%;
                         background:{border};
                         box-shadow:0 0 8px {border};
                         animation:pulse 2s infinite;display:inline-block"></span>
            <span style="color:{border};font-size:1rem;font-weight:800;letter-spacing:1.5px">{sev}</span>
        </div>
        <style>
            @keyframes pulse {{
                0%,100% {{ opacity:1; }}
                50% {{ opacity:.4; }}
            }}
        </style>""",
        unsafe_allow_html=True,
    )
