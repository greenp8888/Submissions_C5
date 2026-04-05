import streamlit as st
from ui.components import log_card, remediation_card, jira_card, trace_bar


def _render_metrics_row(state: dict):
    """Render summary metric cards at the top of the analysis."""
    entries = state.get("classified_entries", [])
    remediations = state.get("remediations", [])
    traces = state.get("agent_trace", [])

    total_issues = len(entries)
    critical_count = sum(1 for e in entries if e.get("severity") in ("CRITICAL", "HIGH"))
    remediation_count = len(remediations)
    total_time = sum(t.get("end_time", 0) - t.get("start_time", 0) for t in traces)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""<div class="metric-card">
                <div class="metric-value" style="color:#e6edf3;">{total_issues}</div>
                <div class="metric-label">Total Issues</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""<div class="metric-card">
                <div class="metric-value" style="color:#ff7b72;">{critical_count}</div>
                <div class="metric-label">Critical / High</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""<div class="metric-card">
                <div class="metric-value" style="color:#58a6ff;">{remediation_count}</div>
                <div class="metric-label">Remediations</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""<div class="metric-card">
                <div class="metric-value" style="color:#56d364;">{total_time:.1f}s</div>
                <div class="metric-label">Pipeline Time</div>
            </div>""",
            unsafe_allow_html=True,
        )


def render_analysis_tab(state: dict):
    entries = state.get("classified_entries", [])
    if not entries:
        st.info("No classified entries yet. Upload logs and run analysis.")
        return

    # Metrics row
    _render_metrics_row(state)
    st.markdown("")

    # Severity filter
    severities = sorted(set(e.get("severity", "LOW") for e in entries),
                        key=lambda s: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(s, 4))
    selected = st.multiselect("Filter by severity", severities, default=severities, key="sev_filter")

    filtered = [e for e in entries if e.get("severity") in selected]

    # Two columns: issues list + summary sidebar
    col_main, col_side = st.columns([3, 1])

    with col_main:
        st.markdown(f"**Showing {len(filtered)} of {len(entries)} log entries**")
        for i, entry in enumerate(filtered):
            log_card(entry, index=i)

    with col_side:
        # Category breakdown
        st.markdown("**Categories**")
        categories = {}
        for entry in entries:
            cat = entry.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            st.markdown(
                f'<div style="display:flex; justify-content:space-between; padding:6px 0; '
                f'border-bottom:1px solid #1c2430;">'
                f'<span style="color:#b0bec8; font-size:13px;">{cat}</span>'
                f'<span style="color:#e6edf3; font-weight:600;">{count}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("")
        st.markdown("**Quick Navigation**")
        remediations = state.get("remediations", [])
        tickets = state.get("jira_tickets", [])
        slack = state.get("slack_notifications", [])

        nav_items = [
            (f"Remediations ({len(remediations)})", "Switch to the Remediations tab to see fix recommendations"),
            (f"JIRA Tickets ({len(tickets)})", "Switch to JIRA Tickets tab for generated tickets"),
            (f"Slack Alerts ({len(slack)})", "Switch to Slack Log tab for notification status"),
        ]
        for label, help_text in nav_items:
            st.markdown(
                f'<div style="background:#1c2430; padding:8px 12px; border-radius:6px; '
                f'margin-bottom:6px; border:1px solid #2a3442;">'
                f'<span style="color:#58a6ff; font-size:13px; font-weight:500;">{label}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


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
        status_class = "status-sent" if notif["status"] == "sent" else "status-failed"
        status_label = "Sent" if notif["status"] == "sent" else "Failed"
        st.markdown(
            f"""<div style="background:#111820; border:1px solid #2a3442; border-radius:10px; padding:16px; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:#e6edf3; font-weight:500; font-size:15px;">{notif['channel']}</span>
                    <span class="status-pill {status_class}">{status_label}</span>
                </div>
                <p style="color:#b0bec8; font-size:14px; margin-top:8px; line-height:1.5;">{notif['text']}</p>
            </div>""",
            unsafe_allow_html=True,
        )


def render_jira_tab(state: dict):
    tickets = state.get("jira_tickets", [])
    if not tickets:
        st.info("No JIRA tickets created.")
        return

    st.markdown(
        '<p style="color:#8b9ab0; font-size:13px; margin-bottom:14px;">'
        'These tickets are mocked \u2014 no real JIRA API calls were made.</p>',
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
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Status:** {trace['status']}")
                st.markdown(f"**Duration:** {duration:.1f}s")
            with col2:
                st.markdown(f"**Input:** {trace.get('input_summary', 'N/A')}")
                st.markdown(f"**Output:** {trace.get('output_summary', 'N/A')}")
