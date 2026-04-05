"""Page 2 – Incidents dashboard."""

from __future__ import annotations
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import requests
import streamlit as st

st.set_page_config(page_title="Dashboard", layout="wide")

st.title("Incidents Dashboard")
st.write("All submitted runs with full UUID copy and one-click inspect.")

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
        f'<span style="display:inline-block;padding:0.25rem 0.7rem;' 
        f'border-radius:999px;background:{bg};color:{fg};font-size:0.85rem;' 
        f'font-weight:700;letter-spacing:0.03em">{severity}</span>'
    )

recent_runs = []
try:
    resp = requests.get(f"{API_BASE}/runs", timeout=5)
    if resp.status_code == 200:
        recent_runs = resp.json().get("runs", [])
except requests.exceptions.RequestException:
    st.warning("Unable to load recent runs. Please check that the backend is running.")

if recent_runs:
    st.subheader("Recent incidents")
    st.write("Showing the latest incidents from the system.")

    header_cols = st.columns([3, 2, 1, 2, 1, 1])
    for col, label in zip(header_cols, ["Run ID", "File", "Severity", "Incident Type", "Status", "Action"]):
        col.write(f"**{label}**")

    for run in recent_runs[-20:]:
        full_id = run.get("run_id", "")
        severity = (run.get("severity") or "UNKNOWN").upper()
        filename = run.get("filename", "-")
        incident_type = run.get("incident_type") or "-"
        finished = run.get("finished", False)
        current_step = run.get("current_step", "running")

        if finished:
            status = "Done"
        elif current_step.lower() == "cookbook":
            status = "Cookbook"
        else:
            status = current_step.title()

        cols = st.columns([3, 2, 1.1, 2, 1, 1])
        cols[0].write(full_id)
        cols[1].write(filename)
        cols[2].markdown(_severity_badge(severity), unsafe_allow_html=True)
        cols[3].write(incident_type)
        cols[4].write(status)

        if cols[5].button("Inspect", key=f"inspect_{full_id}"):
            st.session_state["last_run_id"] = full_id
            st.session_state["current_run_data"] = None

    st.write("---")
    st.write(
        "Available incident details include classifier output, remediation steps, runbook preview, Slack status, and JIRA ticket information."
    )
else:
    st.info("No incidents yet — submit a log on the Upload page.")

st.write("---")
st.header("Inspect Incident")
run_id = st.text_input(
    "Run ID",
    value=st.session_state.get("last_run_id", ""),
    placeholder="Paste or click Inspect above to auto-fill",
)

if st.button("Fetch"):
    if not run_id:
        st.warning("Enter a run ID before fetching.")
    else:
        try:
            r = requests.get(f"{API_BASE}/status/{run_id}", timeout=10)
            if r.status_code == 404:
                st.error(f"run_id `{run_id}` not found.")
            else:
                r.raise_for_status()
                st.session_state["current_run_data"] = r.json()
        except requests.exceptions.ConnectionError:
            st.error(f"Cannot connect to API at `{API_BASE}`.")
        except requests.exceptions.RequestException as exc:
            st.error(f"Failed to fetch incident data: {exc}")

current_data = st.session_state.get("current_run_data")
if not current_data:
    st.stop()

st.subheader("Incident details")
st.write("**Severity:**", current_data.get("severity", "UNKNOWN"))
st.write("**Current step:**", current_data.get("current_step", ""))
st.write("**Completed steps:**", ", ".join(current_data.get("completed_steps", []) or ["None"]))
st.write("**Incident type:**", current_data.get("incident_type", "-"))
st.write("**JIRA ticket:**", current_data.get("jira_ticket") or "None")
st.write("**Slack sent:**", current_data.get("slack_sent"))
st.write(
    "**Affected services:**",
    ", ".join(current_data.get("affected_services", []) or ["None"]),
)
st.write("**Root cause:**", current_data.get("root_cause") or "None")

raw_summary = current_data.get("raw_summary")
if raw_summary:
    st.subheader("Executive summary")
    st.write(raw_summary)

with st.expander("Agent pipeline trace"):
    completed_steps = set(current_data.get("completed_steps", []))
    step_order = [
        ("classify", "Log Classifier"),
        ("remediate", "Remediation Agent"),
        ("cookbook", "Cookbook Synthesizer"),
        ("notify", "Notification Agent"),
        ("jira", "JIRA Ticket Agent"),
    ]
    for step_key, step_label in step_order:
        if step_key in completed_steps:
            status = "Complete"
        elif step_key == current_data.get("current_step"):
            status = "Running"
        else:
            status = "Pending"
        st.write(f"**{step_label}:** {status}")

    report = current_data.get("log_report") or {}
    if report:
        st.write("---")
        st.write("### Log classifier report")
        st.write("**Severity:**", report.get("severity", "UNKNOWN"))
        st.write("**Confidence:**", f"{report.get('confidence', 0) * 100:.0f}%")
        st.write("**Primary incident type:**", report.get("incident_type", "-"))
        st.write("**Root cause:**", report.get("root_cause", "-"))
        sub_incidents = report.get("sub_incidents", [])
        if sub_incidents:
            st.write("**Sub-incidents:**")
            for sub in sub_incidents:
                st.write(f"- {sub.get('incident_type', '-')}: {sub.get('description', '-')}")

with st.expander("Raw JSON"):
    st.json(current_data)
