# DevOps Incident Suite Demo Script (5 minutes)

## Introduction (30 seconds)
"Good [morning/afternoon], everyone. Today, I'll demonstrate the DevOps Incident Suite, an AI-powered tool that automates incident response in DevOps environments. It takes log files, classifies incidents by severity, generates remediation plans, and even notifies teams via Slack and JIRA. Let's dive in."

## Architecture Overview (1 minute)
"The application follows a modern microservices architecture:

- **Frontend**: Streamlit web app with three main pages - Upload for submitting logs, Dashboard for monitoring incidents, and Report for detailed remediation plans.

- **Backend**: FastAPI server handling API requests, orchestrating the AI pipeline.

- **AI Pipeline**: Built with LangGraph, it includes five agents:
  1. Log Classifier - analyzes logs and identifies incidents (CRITICAL, HIGH, MEDIUM, LOW)
  2. Remediation Agent - generates step-by-step fix instructions
  3. Cookbook Synthesizer - creates downloadable Markdown runbooks
  4. Notification Agent - sends Slack alerts for MEDIUM+ incidents
  5. JIRA Agent - creates tickets for CRITICAL incidents

- **Integrations**: REST API clients for Slack and JIRA, plus OpenAI for AI processing.

The pipeline runs asynchronously, updating status in real-time."

## Execution Steps Demo (2.5 minutes)
"Now, let's see it in action. I'll walk through a complete incident response cycle.

**Step 1: Setup (30 seconds)**
- Start the backend: `uvicorn api.main:app --reload`
- Start the frontend: `streamlit run frontend/app.py`
- Ensure API keys are set for OpenAI, Slack, and JIRA in environment variables.

**Step 2: Upload a Log (45 seconds)**
- Navigate to the Upload page
- Choose a sample log file (we have fixtures for OOM kills, 502 errors, etc.)
- Click 'Run Analysis Pipeline'
- Watch the live progress bar as the pipeline executes each agent

**Step 3: Monitor on Dashboard (45 seconds)**
- Switch to Dashboard page
- See the incident appear with colored severity badges (CRITICAL=red, HIGH=orange, etc.)
- Click 'Inspect' to view details like affected services, root cause, and pipeline status

**Step 4: Review Report (45 seconds)**
- Go to Report page
- Enter the run ID and load the full report
- View executive summary with incident counts by severity
- See remediation steps with commands and rationale
- Download the Markdown runbook
- Check integration status for Slack/JIRA notifications

The entire process takes about 2-3 minutes for a typical log file."

## What's Needed for Demo (45 seconds)
"To run this demo successfully, you'll need:

- Python 3.11+ with dependencies from requirements.txt
- OpenAI API key for AI processing
- Slack webhook URL and JIRA credentials (optional but recommended)
- Sample log files in the fixtures/ directory
- Two terminal windows: one for backend, one for frontend

The app is containerized with Docker for easy deployment."

## Conclusion (30 seconds)
"In summary, the DevOps Incident Suite transforms manual incident response into an automated, AI-driven process. It reduces MTTR by providing instant classification, actionable remediation plans, and automatic notifications. Questions?"

---

**Timing Breakdown:**
- Intro: 30s
- Architecture: 60s  
- Execution: 150s
- Requirements: 45s
- Conclusion: 30s
**Total: ~315 seconds (5.25 minutes) - trim as needed**

**Demo Tips:**
- Have sample logs ready
- Pre-configure API keys
- Practice the flow once
- Speak clearly and pause for UI loading
- Prepare backup slides if needed</content>
<parameter name="filePath">demo_script.md