# Hackathon Presentation Script — DevOps Incident Analysis Suite

**Duration: ~5 minutes**
**Timing guide: ~130 words per minute. This script runs ~680 words — target 5:00–5:10 at a comfortable pace.**

---

## [SLIDE 1 — HOOK] (0:00 – 0:30)

> "It's 2 AM. Your phone buzzes. Production is down. You scramble to open five different tools — logs, Slack, JIRA, runbooks, dashboards — and you're reading through thousands of lines of logs trying to figure out what broke, what to fix, and who to tell. Sound familiar?"

That war story is the reality for every DevOps and SRE team in the world. Incident response is slow, manual, and error-prone — precisely when you can least afford it to be.

**We built something to change that.**

---

## [SLIDE 2 — SOLUTION] (0:30 – 1:15)

Introducing the **DevOps Incident Analysis Suite** — a multi-agent AI system that takes your raw ops logs and, in seconds, gives you a full incident analysis, a remediation plan, a Slack alert, an incident runbook, and JIRA tickets — all automatically.

You upload your logs. The system does the rest.

No more manually reading through log files. No more copying error messages into chat. No more forgetting to open a ticket. The entire incident response workflow — automated, end to end.

---

## [SLIDE 3 — ARCHITECTURE] (1:15 – 2:30)

Here's how it works under the hood.

At the core is a **LangGraph orchestrator** — think of it as the incident commander that coordinates five specialized AI agents, each with a distinct job.

**Agent 1 — the Log Classifier.** It reads your raw log file and uses Claude to extract every incident: the severity, the affected service, the error pattern, the timestamp. Raw noise becomes structured intelligence.

**Agent 2 — the Remediation Agent.** It takes those classified incidents and maps each one to a concrete fix. Root cause, immediate action, step-by-step instructions, actual bash commands you can run right now, and a prevention strategy for the future.

**Agent 3 — the Notification Agent.** It formats the top critical issues and fires them directly to your Slack channel using the Slack Block Kit API — so your team is informed before they even open their laptops.

**Agent 4 — the Cookbook Synthesizer.** It generates a full incident runbook — a four-phase playbook: Detection, Containment, Resolution, and Post-Incident review — complete with an escalation path and lessons learned.

**Agent 5 — the JIRA Ticket Agent.** It creates one ticket per issue in your JIRA project, with severity mapped to priority, full context attached, and remediation steps pre-populated. Nothing falls through the cracks.

Each agent hands its output to the next. The state flows through the pipeline. Every result is traceable.

---

## [SLIDE 4 — LIVE DEMO] (2:30 – 4:00)

Let me show you this in action.

*(Open the app at https://devops-incidentiq.streamlit.app/)*

Here's our web interface. I'm going to upload a real incident log — this is a multi-service cascade failure: database timeouts, API gateway 503s, auth service cache misses, disk and memory saturation all happening within the same minute.

I'll click **Analyze Incident**.

Watch the pipeline execute in real time — you can see each agent light up as it completes.

*(Point to results as they appear)*

Agent 1 has already identified **ten distinct issues** — classified by severity, with the affected service and error pattern for each one.

Agent 2 has generated a remediation plan — look at this: root cause analysis, immediate actions, the exact kubectl commands to run, and an estimated time to resolve. For each issue.

Agent 3 — the Slack notification has been sent. Your team already knows.

Agent 4 — here's the runbook. Four phases, pre-flight checks, an escalation hierarchy from on-call engineer up to CTO, and key metrics to watch during recovery.

Agent 5 — JIRA tickets created. Every critical issue is now tracked, assigned a priority, and ready for your sprint board.

The entire pipeline — **under thirty seconds**.

And we also expose this as a **REST API with full Swagger documentation** at localhost:8000/docs — so this can be integrated into any existing CI/CD pipeline or alerting system.

---

## [SLIDE 5 — WHY IT MATTERS] (4:00 – 4:45)

The average time to detect and respond to a production incident is **over four hours**. Every minute of downtime costs real money and real trust.

What we've built compresses that entire first-response cycle — log triage, remediation mapping, team notification, ticket creation — from hours to seconds.

This isn't a demo toy. The architecture is production-ready: modular agents, a typed state machine, mock mode for safe testing, a REST API for integration, and full JSON export for audit trails.

---

## [CLOSING] (4:45 – 5:00)

We built this because the best incident response is the one that's already half done by the time the engineer sits down.

**That's the DevOps Incident Analysis Suite. Thank you.**
