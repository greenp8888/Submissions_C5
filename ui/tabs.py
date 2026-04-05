import streamlit as st
from ui.components import log_card, remediation_card, jira_card, trace_bar


def render_analysis_tab(state: dict):
    entries = state.get("classified_entries", [])
    if not entries:
        st.info("No classified entries yet. Upload logs and run analysis.")
        return

    st.markdown(f"**{len(entries)} log entries classified**")
    for entry in entries:
        log_card(entry)


def render_remediations_tab(state: dict):
    remediations = state.get("remediations", [])
    if not remediations:
        st.info("No remediations generated yet.")
        return

    st.markdown(f"**{len(remediations)} remediations generated**")
    for rem in remediations:
        remediation_card(rem)


def render_cookbook_tab(state: dict):
    cookbook = state.get("cookbook", "")
    if not cookbook:
        st.info("No cookbook generated yet.")
        return

    st.markdown(cookbook)


def render_slack_tab(state: dict):
    notifications = state.get("slack_notifications", [])
    if not notifications:
        st.info("No Slack notifications sent yet.")
        return

    for notif in notifications:
        status_icon = "\u2705" if notif["status"] == "sent" else "\u274c"
        st.markdown(
            f"""<div style="background:#161b22; border:1px solid #30363d; border-radius:8px; padding:12px; margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:#c9d1d9;">{status_icon} {notif['channel']}</span>
                    <span style="color:#8b949e; font-size:12px;">{notif['status']}</span>
                </div>
                <p style="color:#8b949e; font-size:13px; margin-top:6px;">{notif['text']}</p>
            </div>""",
            unsafe_allow_html=True,
        )


def render_jira_tab(state: dict):
    tickets = state.get("jira_tickets", [])
    if not tickets:
        st.info("No JIRA tickets created.")
        return

    st.markdown(
        '<p style="color:#8b949e; font-size:12px; margin-bottom:12px;">'
        '\u2139\ufe0f These tickets are mocked \u2014 no real JIRA API calls were made.</p>',
        unsafe_allow_html=True,
    )
    for ticket in tickets:
        jira_card(ticket)


def render_trace_tab(state: dict):
    traces = state.get("agent_trace", [])
    if not traces:
        st.info("No agent trace data yet.")
        return

    # Timeline view
    st.subheader("Execution Timeline")
    trace_bar(traces)

    # Detail view
    st.subheader("Agent Details")
    for trace in traces:
        status_icon = {"completed": "\u2705", "running": "\u2699\ufe0f", "skipped": "\u26aa", "failed": "\u274c"}.get(
            trace["status"], "\u26aa"
        )
        duration = trace.get("end_time", 0) - trace.get("start_time", 0)
        with st.expander(f"{status_icon} {trace['agent_name']} \u2014 {duration:.1f}s"):
            st.markdown(f"**Status:** {trace['status']}")
            st.markdown(f"**Duration:** {duration:.1f}s")
            st.markdown(f"**Input:** {trace.get('input_summary', 'N/A')}")
            st.markdown(f"**Output:** {trace.get('output_summary', 'N/A')}")
