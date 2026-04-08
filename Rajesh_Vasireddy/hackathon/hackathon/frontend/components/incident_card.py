"""Incident summary card component."""

from typing import Any, Dict
import streamlit as st
from components.styles import severity_pill


def incident_card(data: Dict[str, Any]) -> None:
    """Render a styled incident summary card with metrics and details."""
    severity     = (data.get("severity") or "UNKNOWN").upper()
    incident     = data.get("incident_type") or "Unknown Incident"
    jira         = data.get("jira_ticket") or "—"
    slack_sent   = data.get("slack_sent")
    services     = data.get("affected_services") or []
    root_cause   = data.get("root_cause") or ""
    raw_summary  = data.get("raw_summary") or ""
    errors       = data.get("errors") or []

    # ── Header row ────────────────────────────────────────────────────────────
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:.8rem;margin-bottom:.8rem">
            {severity_pill(severity, size="md")}
            <span style="color:#e2e8f0;font-size:1.05rem;font-weight:700">{incident}</span>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Metrics row ───────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)

    _SEVERITY_COLORS = {
        "CRITICAL": "#ef4444", "HIGH": "#f97316",
        "MEDIUM":   "#eab308", "LOW":  "#22c55e", "UNKNOWN": "#64748b",
    }
    sev_color = _SEVERITY_COLORS.get(severity, "#64748b")

    m1.markdown(
        f"""<div style="background:#111827;border:1px solid #1e3a5f;border-top:2px solid {sev_color};
                        border-radius:10px;padding:.9rem 1rem;text-align:center">
            <div style="color:{sev_color};font-size:1.3rem;font-weight:800">{severity}</div>
            <div style="color:#475569;font-size:.72rem;margin-top:2px">Severity</div>
        </div>""",
        unsafe_allow_html=True,
    )

    slack_color = "#22c55e" if slack_sent else "#ef4444"
    slack_label = "Sent" if slack_sent else "Not sent"
    m2.markdown(
        f"""<div style="background:#111827;border:1px solid #1e3a5f;border-top:2px solid {slack_color};
                        border-radius:10px;padding:.9rem 1rem;text-align:center">
            <div style="color:{slack_color};font-size:1.3rem;font-weight:800">{slack_label}</div>
            <div style="color:#475569;font-size:.72rem;margin-top:2px">Slack</div>
        </div>""",
        unsafe_allow_html=True,
    )

    jira_color = "#22c55e" if jira != "—" else "#475569"
    m3.markdown(
        f"""<div style="background:#111827;border:1px solid #1e3a5f;border-top:2px solid {jira_color};
                        border-radius:10px;padding:.9rem 1rem;text-align:center">
            <div style="color:{jira_color};font-size:1.1rem;font-weight:800">{jira}</div>
            <div style="color:#475569;font-size:.72rem;margin-top:2px">JIRA Ticket</div>
        </div>""",
        unsafe_allow_html=True,
    )

    svc_count = len(services)
    m4.markdown(
        f"""<div style="background:#111827;border:1px solid #1e3a5f;border-top:2px solid #3b82f6;
                        border-radius:10px;padding:.9rem 1rem;text-align:center">
            <div style="color:#3b82f6;font-size:1.3rem;font-weight:800">{svc_count}</div>
            <div style="color:#475569;font-size:.72rem;margin-top:2px">Affected Services</div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

    # ── Affected services ─────────────────────────────────────────────────────
    if services:
        pills = "".join(
            f'<span style="background:#1a2540;border:1px solid #1e3a5f;color:#93c5fd;'
            f'padding:2px 10px;border-radius:99px;font-size:.75rem;margin:2px;display:inline-block">'
            f'{s}</span>'
            for s in services
        )
        st.markdown(
            f"""<div style="background:#111827;border:1px solid #1e3a5f;border-radius:10px;
                            padding:.8rem 1rem;margin-bottom:.5rem">
                <div style="color:#64748b;font-size:.72rem;letter-spacing:.5px;text-transform:uppercase;
                            font-weight:600;margin-bottom:.4rem">Affected Services</div>
                <div>{pills}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    # ── Root cause ────────────────────────────────────────────────────────────
    if root_cause:
        st.markdown(
            f"""<div style="background:rgba(59,130,246,.08);border:1px solid rgba(59,130,246,.3);
                            border-left:3px solid #3b82f6;border-radius:10px;
                            padding:.8rem 1rem;margin-bottom:.5rem">
                <div style="color:#64748b;font-size:.72rem;font-weight:600;
                            text-transform:uppercase;letter-spacing:.5px;margin-bottom:.3rem">Root Cause</div>
                <div style="color:#e2e8f0;font-size:.88rem;line-height:1.6">{root_cause}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    # ── Executive summary ─────────────────────────────────────────────────────
    if raw_summary:
        with st.expander("Executive Summary", expanded=False):
            st.markdown(
                f'<div style="color:#94a3b8;font-size:.85rem;line-height:1.7">{raw_summary}</div>',
                unsafe_allow_html=True,
            )

    # ── Errors ────────────────────────────────────────────────────────────────
    if errors:
        with st.expander("Pipeline Errors", expanded=True):
            for e in errors:
                st.markdown(
                    f"""<div style="background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);
                                    border-left:3px solid #ef4444;border-radius:8px;
                                    padding:.6rem .9rem;font-family:monospace;
                                    font-size:.78rem;color:#fca5a5;margin-bottom:.3rem">{e}</div>""",
                    unsafe_allow_html=True,
                )
