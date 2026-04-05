"""Agent collaboration trace panel – styled per-agent output sections."""

from typing import Any, Dict
import streamlit as st
from components.styles import severity_pill

_SEV_COLOR = {
    "CRITICAL": "#ef4444", "HIGH": "#f97316",
    "MEDIUM":   "#eab308", "LOW":  "#22c55e",
}


def _section_header(number: str, title: str, color: str, done: bool, running: bool) -> str:
    if done:
        status_html = f'<span style="background:rgba({_rgb(color)},.15);color:{color};padding:2px 10px;border-radius:99px;font-size:.7rem;font-weight:700">COMPLETE</span>'
    elif running:
        status_html = '<span style="background:rgba(234,179,8,.15);color:#eab308;padding:2px 10px;border-radius:99px;font-size:.7rem;font-weight:700">RUNNING</span>'
    else:
        status_html = '<span style="background:#1a2540;color:#334155;padding:2px 10px;border-radius:99px;font-size:.7rem;font-weight:600">PENDING</span>'
    return (
        f'<div style="display:flex;align-items:center;gap:.7rem">'
        f'<span style="background:{color};color:#fff;width:22px;height:22px;border-radius:50%;'
        f'display:inline-flex;align-items:center;justify-content:center;'
        f'font-size:.7rem;font-weight:800;flex-shrink:0">{number}</span>'
        f'<span style="font-weight:700;color:#e2e8f0;font-size:.92rem">{title}</span>'
        f'<div style="margin-left:auto">{status_html}</div>'
        f'</div>'
    )


def _rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


def _kv(label: str, value: str, accent: str = "#3b82f6") -> str:
    return (
        f'<div style="margin:.3rem 0">'
        f'<span style="color:#475569;font-size:.72rem;letter-spacing:.4px;text-transform:uppercase;font-weight:600">{label}</span>'
        f'<div style="color:#e2e8f0;font-size:.83rem;margin-top:1px">{value}</div>'
        f'</div>'
    )


def agent_trace(data: Dict[str, Any]) -> None:
    """Render the full agent pipeline trace with styled expanders."""
    st.markdown(
        """<div style="color:#64748b;font-size:.72rem;letter-spacing:.8px;
                       text-transform:uppercase;font-weight:600;margin-bottom:.6rem">
            Agent Pipeline Trace
        </div>""",
        unsafe_allow_html=True,
    )

    completed = set(data.get("completed_steps", []))
    errors    = data.get("errors", [])

    # ── 1. Log Classifier ─────────────────────────────────────────────────────
    with st.expander(
        _section_header("1", "Log Classifier Agent", "#3b82f6", "classify" in completed, False),
        expanded="classify" in completed,
    ):
        if "classify" not in completed:
            st.markdown('<div style="color:#334155;font-size:.83rem;padding:.5rem">Not yet run.</div>', unsafe_allow_html=True)
        else:
            report  = data.get("log_report") or {}
            sev     = report.get("severity", "UNKNOWN")
            conf    = report.get("confidence", 0)
            sev_c   = _SEV_COLOR.get(sev, "#64748b")

            c1, c2 = st.columns(2)
            c1.markdown(
                f"""<div style="background:#111827;border:1px solid {sev_c};border-radius:10px;
                                padding:.8rem 1rem;text-align:center">
                    <div style="color:{sev_c};font-size:1.4rem;font-weight:800">{sev}</div>
                    <div style="color:#475569;font-size:.7rem">Overall Severity</div>
                </div>""",
                unsafe_allow_html=True,
            )
            c2.markdown(
                f"""<div style="background:#111827;border:1px solid #1e3a5f;border-radius:10px;
                                padding:.8rem 1rem;text-align:center">
                    <div style="color:#3b82f6;font-size:1.4rem;font-weight:800">{conf*100:.0f}%</div>
                    <div style="color:#475569;font-size:.7rem">Confidence</div>
                </div>""",
                unsafe_allow_html=True,
            )

            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
            st.markdown(_kv("Primary Incident Type", report.get("incident_type", "—")), unsafe_allow_html=True)
            st.markdown(_kv("Root Cause", report.get("root_cause", "—")), unsafe_allow_html=True)

            # Sub-incidents
            sub = report.get("sub_incidents") or []
            if sub:
                st.markdown(
                    '<div style="color:#64748b;font-size:.72rem;text-transform:uppercase;'
                    'font-weight:600;letter-spacing:.5px;margin:.6rem 0 .3rem">All Detected Incidents</div>',
                    unsafe_allow_html=True,
                )
                for inc in sub:
                    s = inc.get("severity", "LOW")
                    c = _SEV_COLOR.get(s, "#64748b")
                    st.markdown(
                        f"""<div style="background:#0d1321;border:1px solid #1e3a5f;border-left:3px solid {c};
                                        border-radius:8px;padding:.55rem .9rem;margin-bottom:.3rem;
                                        display:flex;align-items:flex-start;gap:.7rem">
                            <div style="margin-top:2px">{severity_pill(s, "sm")}</div>
                            <div>
                                <div style="color:#e2e8f0;font-weight:600;font-size:.82rem">{inc.get("incident_type","—")}</div>
                                <div style="color:#64748b;font-size:.75rem">{inc.get("affected_component","—")} — {inc.get("description","")}</div>
                            </div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

            services = report.get("affected_services") or []
            if services:
                pills = "".join(
                    f'<span style="background:#1a2540;border:1px solid #1e3a5f;color:#93c5fd;'
                    f'padding:2px 9px;border-radius:99px;font-size:.72rem;margin:2px;display:inline-block">{s}</span>'
                    for s in services
                )
                st.markdown(
                    f'<div style="color:#64748b;font-size:.72rem;font-weight:600;text-transform:uppercase;'
                    f'letter-spacing:.5px;margin:.5rem 0 .2rem">Affected Services</div>{pills}',
                    unsafe_allow_html=True,
                )

            timestamps = report.get("key_timestamps") or []
            if timestamps:
                ts_html = "".join(
                    f'<div style="font-family:monospace;font-size:.72rem;color:#64748b;padding:1px 0">· {t}</div>'
                    for t in timestamps
                )
                st.markdown(
                    f'<div style="color:#64748b;font-size:.72rem;font-weight:600;text-transform:uppercase;'
                    f'letter-spacing:.5px;margin:.5rem 0 .2rem">Key Timestamps</div>{ts_html}',
                    unsafe_allow_html=True,
                )

            patterns = report.get("error_patterns") or []
            if patterns:
                p_html = "".join(
                    f'<span style="background:#0a0e1a;border:1px solid #1e3a5f;color:#93c5fd;'
                    f'font-family:monospace;font-size:.7rem;padding:2px 8px;border-radius:6px;'
                    f'margin:2px;display:inline-block">{p}</span>'
                    for p in patterns
                )
                st.markdown(
                    f'<div style="color:#64748b;font-size:.72rem;font-weight:600;text-transform:uppercase;'
                    f'letter-spacing:.5px;margin:.5rem 0 .2rem">Error Patterns</div>{p_html}',
                    unsafe_allow_html=True,
                )

            if report.get("raw_summary"):
                with st.expander("Full narrative summary"):
                    st.markdown(
                        f'<div style="color:#94a3b8;font-size:.83rem;line-height:1.7">{report["raw_summary"]}</div>',
                        unsafe_allow_html=True,
                    )

    # ── 2. Remediation Agent ──────────────────────────────────────────────────
    with st.expander(
        _section_header("2", "Remediation Agent", "#6366f1", "remediate" in completed, False),
        expanded="remediate" in completed,
    ):
        if "remediate" not in completed:
            st.markdown('<div style="color:#334155;font-size:.83rem;padding:.5rem">Not yet run.</div>', unsafe_allow_html=True)
        else:
            plan  = data.get("remediation_plan") or {}
            steps = plan.get("steps") or []
            if steps:
                st.markdown(
                    f'<div style="color:#6366f1;font-size:.82rem;font-weight:700;margin-bottom:.5rem">'
                    f'{len(steps)} remediation step{"s" if len(steps)>1 else ""} generated</div>',
                    unsafe_allow_html=True,
                )
                for step in steps:
                    cmd = step.get("command", "")
                    st.markdown(
                        f"""<div style="background:#0d1321;border:1px solid #1e3a5f;border-left:3px solid #6366f1;
                                        border-radius:8px;padding:.7rem .9rem;margin-bottom:.5rem">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.3rem">
                                <span style="color:#e2e8f0;font-weight:700;font-size:.85rem">
                                    Step {step['order']} — {step['action']}
                                </span>
                                <span style="color:#475569;font-size:.7rem">
                                    [{step.get('owner','SRE')}] · ~{step.get('estimated_minutes','?')} min
                                </span>
                            </div>
                            {"<div style='margin-top:.3rem'>" + _kv("Rationale", step.get('rationale','')) + "</div>" if step.get('rationale') else ""}
                        </div>""",
                        unsafe_allow_html=True,
                    )
                    if cmd:
                        st.code(cmd, language="bash")

            for key, label, col in [
                ("rollback_plan",    "Rollback Plan",    "#f97316"),
                ("prevention_notes", "Prevention Notes", "#22c55e"),
            ]:
                val = plan.get(key)
                if val:
                    st.markdown(
                        f"""<div style="background:rgba({_rgb(col)},.08);border:1px solid rgba({_rgb(col)},.25);
                                        border-left:3px solid {col};border-radius:8px;
                                        padding:.7rem .9rem;margin-top:.3rem">
                            <div style="color:{col};font-size:.72rem;font-weight:700;text-transform:uppercase;
                                        letter-spacing:.5px;margin-bottom:.3rem">{label}</div>
                            <div style="color:#e2e8f0;font-size:.83rem">{val}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
            if not steps:
                st.markdown('<div style="color:#475569;font-size:.83rem">Remediation plan is empty.</div>', unsafe_allow_html=True)

    # ── 3. Cookbook Agent ─────────────────────────────────────────────────────
    with st.expander(
        _section_header("3", "Cookbook Synthesizer", "#8b5cf6", "cookbook" in completed, False),
        expanded="cookbook" in completed,
    ):
        if "cookbook" not in completed:
            st.markdown('<div style="color:#334155;font-size:.83rem;padding:.5rem">Not yet run.</div>', unsafe_allow_html=True)
        else:
            md = data.get("cookbook_md") or ""
            if md:
                st.markdown(
                    f'<div style="color:#8b5cf6;font-size:.82rem;font-weight:700;margin-bottom:.5rem">'
                    f'Runbook generated — {len(md):,} characters</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div style="background:#0a0e1a;border:1px solid #1e3a5f;border-radius:10px;'
                    f'padding:.9rem 1.1rem;font-size:.78rem;color:#94a3b8;line-height:1.8;'
                    f'max-height:200px;overflow-y:auto;font-family:monospace">'
                    f'{md[:800].replace(chr(10),"<br>")}{"…" if len(md)>800 else ""}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<div style="color:#475569;font-size:.83rem">Runbook not available.</div>', unsafe_allow_html=True)

    # ── 4. Notification Agent ─────────────────────────────────────────────────
    with st.expander(
        _section_header("4", "Notification Agent (Slack)", "#f97316", "notify" in completed, False),
        expanded="notify" in completed,
    ):
        if "notify" not in completed:
            st.markdown('<div style="color:#334155;font-size:.83rem;padding:.5rem">Not yet run.</div>', unsafe_allow_html=True)
        else:
            slack_sent = data.get("slack_sent")
            severity   = data.get("severity", "")
            if slack_sent is True:
                st.markdown(
                    '<div style="background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.3);'
                    'border-left:3px solid #22c55e;border-radius:8px;padding:.7rem .9rem;'
                    'color:#86efac;font-size:.85rem;font-weight:600">Slack alert sent successfully</div>',
                    unsafe_allow_html=True,
                )
            elif slack_sent is False:
                if severity in ("CRITICAL", "HIGH", "MEDIUM"):
                    st.markdown(
                        '<div style="background:rgba(234,179,8,.1);border:1px solid rgba(234,179,8,.3);'
                        'border-left:3px solid #eab308;border-radius:8px;padding:.7rem .9rem;'
                        'color:#fef08a;font-size:.85rem">Slack alert not sent — check SLACK_WEBHOOK_URL</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div style="background:#111827;border:1px solid #1e3a5f;border-radius:8px;'
                        f'padding:.7rem .9rem;color:#475569;font-size:.83rem">'
                        f'Skipped — severity {severity} is below MEDIUM threshold</div>',
                        unsafe_allow_html=True,
                    )

    # ── 5. JIRA Agent ─────────────────────────────────────────────────────────
    with st.expander(
        _section_header("5", "JIRA Ticket Agent", "#ef4444", "jira" in completed, False),
        expanded="jira" in completed,
    ):
        if "jira" not in completed:
            st.markdown('<div style="color:#334155;font-size:.83rem;padding:.5rem">Not yet run.</div>', unsafe_allow_html=True)
        else:
            jira_ticket = data.get("jira_ticket")
            severity    = data.get("severity", "")
            if jira_ticket:
                st.markdown(
                    f'<div style="background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.3);'
                    f'border-left:3px solid #22c55e;border-radius:8px;padding:.7rem .9rem">'
                    f'<span style="color:#86efac;font-size:.85rem;font-weight:600">Ticket created: </span>'
                    f'<code style="color:#22c55e;font-size:.88rem;font-weight:800">{jira_ticket}</code></div>',
                    unsafe_allow_html=True,
                )
            elif severity == "CRITICAL":
                st.markdown(
                    '<div style="background:rgba(234,179,8,.1);border:1px solid rgba(234,179,8,.3);'
                    'border-left:3px solid #eab308;border-radius:8px;padding:.7rem .9rem;'
                    'color:#fef08a;font-size:.83rem">JIRA credentials not configured — check JIRA_URL, JIRA_USER, JIRA_API_TOKEN</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="background:#111827;border:1px solid #1e3a5f;border-radius:8px;'
                    f'padding:.7rem .9rem;color:#475569;font-size:.83rem">'
                    f'Skipped — severity {severity} is below CRITICAL threshold</div>',
                    unsafe_allow_html=True,
                )

    # ── Pipeline errors ───────────────────────────────────────────────────────
    if errors:
        st.markdown(
            '<div style="background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);'
            'border-left:3px solid #ef4444;border-radius:8px;padding:.7rem .9rem;margin-top:.5rem">'
            '<div style="color:#ef4444;font-weight:700;font-size:.82rem;margin-bottom:.4rem">Pipeline Errors</div>'
            + "".join(f'<div style="color:#fca5a5;font-family:monospace;font-size:.75rem;margin:.2rem 0">· {e}</div>' for e in errors)
            + "</div>",
            unsafe_allow_html=True,
        )
