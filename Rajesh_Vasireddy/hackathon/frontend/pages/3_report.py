"""Page 3 – Remediation plan and runbook viewer."""

from __future__ import annotations
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import requests
import streamlit as st

st.set_page_config(page_title="Report", layout="wide")

st.title("Incident Report")
st.write("Executive summary, remediation plan, runbook download and integration status")

API_BASE = st.session_state.get("api_base_url", "http://localhost:8000")

_SEVERITY_STYLES = {
    "CRITICAL": ("#ef4444", "#ffffff"),
    "HIGH":     ("#f97316", "#ffffff"),
    "MEDIUM":   ("#eab308", "#000000"),
    "LOW":      ("#22c55e", "#ffffff"),
    "UNKNOWN":  ("#64748b", "#ffffff"),
}


def _severity_badge(severity: str) -> str:
    bg, fg = _SEVERITY_STYLES.get(severity, _SEVERITY_STYLES["UNKNOWN"])
    return (
        f'<span style="display:inline-block;padding:0.35rem 0.8rem;border-radius:999px;'
        f'background:{bg};color:{fg};font-size:0.9rem;font-weight:700;' 
        f'">{severity}</span>'
    )


def _severity_tile(severity: str, count: int) -> str:
    bg, fg = _SEVERITY_STYLES.get(severity, _SEVERITY_STYLES["UNKNOWN"])
    return (
        f'<div style="background:{bg};color:{fg};padding:1rem;border-radius:0.75rem;text-align:center;">'
        f'<div style="font-size:2rem;font-weight:800">{count}</div>'
        f'<div style="margin-top:0.35rem;font-size:0.95rem;font-weight:700">{severity}</div></div>'
    )

# ── Run ID input ──────────────────────────────────────────────────────────────
run_id = st.text_input(
    "Run ID",
    value=st.session_state.get("last_run_id", ""),
    placeholder="Paste run_id from the Upload page",
)

if st.button("Load Report", type="primary"):
    if not run_id:
        st.warning("Enter a run ID.")
    else:
        try:
            r = requests.get(f"{API_BASE}/status/{run_id}", timeout=10)
            r.raise_for_status()
            st.session_state["report_data"] = r.json()
        except Exception as exc:
            st.error(f"Failed to fetch report: {exc}")

data = st.session_state.get("report_data")

if not data:
    st.info("Enter a run_id above and click Load Report")
    st.stop()

if not data.get("finished"):
    st.warning("Pipeline is still running — refresh in a few seconds")

log_report = data.get("log_report") or {}
sub_incidents = log_report.get("sub_incidents") or []
plan = data.get("remediation_plan") or {}
steps = plan.get("steps", [])
cookbook_md = data.get("cookbook_md", "")

# ── Executive Summary ─────────────────────────────────────────────────────────
st.header("Executive Summary")

if sub_incidents:
    from collections import defaultdict
    groups = defaultdict(list)
    for inc in sub_incidents:
        groups[inc.get("severity", "LOW")].append(inc)

    # Count tiles
    cols = st.columns(4)
    for col, sev in zip(cols, ["CRITICAL", "HIGH", "MEDIUM", "LOW"]):
        count = len(groups.get(sev, []))
        col.markdown(_severity_tile(sev, count), unsafe_allow_html=True)

    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        incidents = groups.get(sev, [])
        if not incidents:
            continue
        label = f"{sev} — {len(incidents)} issue{'s' if len(incidents) > 1 else ''}"
        with st.expander(label, expanded=(sev == "CRITICAL")):
            for inc in incidents:
                st.markdown(
                    f"**{inc.get('incident_type', '—')}** { _severity_badge(sev) }",
                    unsafe_allow_html=True,
                )
                st.write(f"Component: {inc.get('affected_component', '—')}")
                st.write(f"Description: {inc.get('description', '—')}")

elif data.get("raw_summary"):
    st.write(data["raw_summary"])
else:
    st.write("No summary available yet.")

st.write("---")

# ── Remediation steps ─────────────────────────────────────────────────────────
st.header("Remediation Steps")

if steps:
    for i, step in enumerate(steps):
        with st.expander(
            f"Step {step['order']}: {step['action']} [{step.get('owner', 'SRE')}]",
            expanded=(i == 0),
        ):
            st.write(f"Owner: {step.get('owner', 'SRE')}")
            st.write(f"Estimated time: ~{step.get('estimated_minutes', '?')} min")
            if step.get("rationale"):
                st.write(f"Rationale: {step['rationale']}")
            cmd = step.get("command", "")
            if cmd:
                st.code(cmd, language="bash")

    for key, label in [
        ("rollback_plan", "Rollback Plan"),
        ("prevention_notes", "Prevention Notes"),
    ]:
        val = plan.get(key)
        if val:
            st.subheader(label)
            st.write(val)
else:
    st.write("Remediation plan not ready yet.")

st.write("---")

# ── Runbook ───────────────────────────────────────────────────────────────────
st.header("Runbook")

if cookbook_md:
    st.download_button(
        "Download Runbook (.md)",
        data=cookbook_md,
        file_name=f"runbook_{run_id[:8]}.md",
        mime="text/markdown",
        use_container_width=True,
    )
    st.write(f"{len(cookbook_md):,} characters · Markdown format")
    with st.expander("Preview Runbook"):
        st.markdown(cookbook_md)
else:
    st.write("Runbook not available yet.")

st.write("---")

# ── Integration status ────────────────────────────────────────────────────────
st.header("Integration Status")

cols = st.columns(2)

with cols[0]:
    slack = data.get("slack_sent")
    if slack is True:
        st.success("Slack — Sent\n\nBlock Kit alert delivered")
    else:
        st.info("Slack — Not sent\n\nCheck SLACK_WEBHOOK_URL")

with cols[1]:
    jira = data.get("jira_ticket")
    if jira:
        st.success(f"JIRA — {jira}\n\nTicket created successfully")
    elif data.get("severity") == "CRITICAL":
        st.warning("JIRA — Not created\n\nCheck JIRA_URL, JIRA_USER, JIRA_API_TOKEN")
    else:
        st.info("JIRA — Skipped\n\nOnly CRITICAL severity creates tickets")

