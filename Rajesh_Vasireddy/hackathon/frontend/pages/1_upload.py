"""Page 1 – Upload a log file and trigger the analysis pipeline."""

from __future__ import annotations
import os
import sys
import time

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import requests
import streamlit as st

st.set_page_config(page_title="Upload Log", layout="wide")

st.title("Upload & Analyze")
st.write("Submit a log file to start the AI incident analysis pipeline")

API_BASE = st.session_state.get("api_base_url", "http://localhost:8000")

# ── Input tabs ────────────────────────────────────────────────────────────────
raw_log = ""
filename = "upload.log"

tab_file, tab_paste, tab_fixture = st.tabs(["Upload File", "Paste Text", "Use Fixture"])

with tab_file:
    uploaded = st.file_uploader("Drop a .log or .txt file", type=["log", "txt"])
    if uploaded:
        raw_log = uploaded.read().decode("utf-8", errors="replace")
        filename = uploaded.name
        st.success(f"Loaded {filename} — {len(raw_log):,} characters")

with tab_paste:
    pasted = st.text_area("Paste log content", height=220, placeholder="Paste your log output here…")
    if pasted.strip():
        raw_log = pasted
        filename = "pasted.log"

with tab_fixture:
    fixture_map = {
        "OOM Kill": "oom_kill.log",
        "Gateway 502": "gateway_502.log",
        "DB Timeout": "db_timeout.log",
        "Deploy Failure": "deploy_failure.log",
        "Linux System": "linux_system.log",
    }
    fixture_badges = {
        "OOM Kill": "CRITICAL",
        "Gateway 502": "HIGH",
        "DB Timeout": "HIGH",
        "Deploy Failure": "HIGH",
        "Linux System": "CRITICAL",
    }
    cols = st.columns(len(fixture_map))
    for col, (name, fname) in zip(cols, fixture_map.items()):
        sev = fixture_badges[name]
        with col:
            st.write(f"**{name}**")
            st.write(f"Severity: {sev}")
            st.write(f"File: {fname}")
            if st.button("Load", key=f"fix_{name}"):
                path = os.path.join(os.path.dirname(__file__), "..", "..", "fixtures", fname)
                try:
                    with open(path, encoding="utf-8", errors="replace") as f:
                        raw_log = f.read()
                    filename = fname
                    st.success(f"Loaded fixture: {fname}")
                except FileNotFoundError:
                    st.error(f"Fixture not found: {path}")

# ── Preview ───────────────────────────────────────────────────────────────────
if raw_log:
    with st.expander("Log Preview (first 1,000 chars)"):
        st.code(raw_log[:1000], language="bash")

# ── Submit ────────────────────────────────────────────────────────────────────
if raw_log:
    if st.button("Run Analysis Pipeline", type="primary", use_container_width=True):
        with st.spinner("Submitting to pipeline…"):
            try:
                resp = requests.post(
                    f"{API_BASE}/analyze",
                    json={"filename": filename, "content": raw_log},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                run_id = data["run_id"]
                st.session_state["last_run_id"] = run_id

                st.info(f"Run ID: {run_id}")

                # ── Live progress ─────────────────────────────────────────────
                STEPS = ["classify", "remediate", "cookbook", "notify", "jira"]
                STEP_DESCRIPTIONS = {
                    "classify": "Log Classifier — parsing log, detecting all incidents",
                    "remediate": "Remediation Agent — generating step-by-step fix plan",
                    "cookbook": "Cookbook Synthesizer — building actionable runbook",
                    "notify": "Notification Agent — sending Slack alert",
                    "jira": "JIRA Agent — creating ticket for CRITICAL incidents",
                }

                progress_bar = st.progress(0)
                status_box = st.empty()
                steps_display = st.container()
                shown = set()
                poll = {}

                for _ in range(120):
                    time.sleep(2)
                    try:
                        poll = requests.get(f"{API_BASE}/status/{run_id}", timeout=10).json()
                    except Exception:
                        continue

                    completed = poll.get("completed_steps", [])
                    current = poll.get("current_step", "")
                    done = len(completed)
                    progress_bar.progress(min(done / len(STEPS), 1.0))
                    status_box.write(f"Step {done}/{len(STEPS)} — {STEP_DESCRIPTIONS.get(current, current or 'Queued…')}")

                    for step in completed:
                        if step not in shown:
                            shown.add(step)
                            with steps_display:
                                st.write(f"✓ {step.capitalize()} complete")

                    if poll.get("finished"):
                        break

                progress_bar.empty()
                status_box.empty()

                # ── Final result ──────────────────────────────────────────────
                if poll.get("errors"):
                    st.error("Pipeline errors: " + "; ".join(poll["errors"]))
                else:
                    st.balloons()
                    sev = poll.get("severity", "UNKNOWN")
                    incident_type = poll.get("incident_type", "—")
                    steps_done = f"{len(poll.get('completed_steps', []))}/{len(STEPS)}"
                    slack_status = "Sent" if poll.get("slack_sent") else "Skipped"
                    jira_ticket = poll.get("jira_ticket") or "—"

                    cols = st.columns(5)
                    cols[0].metric("Severity", sev)
                    cols[1].metric("Type", incident_type)
                    cols[2].metric("Steps", steps_done)
                    cols[3].metric("Slack", slack_status)
                    cols[4].metric("JIRA", jira_ticket)

                    st.info("Navigate to Dashboard or Report to see full results.")

            except requests.exceptions.ConnectionError:
                st.error(f"Cannot connect to API at `{API_BASE}`. Is the backend running?")
            except Exception as exc:
                st.error(f"Error: {exc}")
else:
    st.info("Load a log file using one of the tabs above to begin")

