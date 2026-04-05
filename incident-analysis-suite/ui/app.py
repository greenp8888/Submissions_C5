from __future__ import annotations

import difflib
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
import streamlit as st
import streamlit.components.v1 as components
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
SECRETS_PATH = REPO_ROOT / ".streamlit" / "secrets.toml"
SECRETS_EXAMPLE_PATH = REPO_ROOT / ".streamlit" / "secrets.toml.example"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from incident_suite.models.schemas import AnalyzeIncidentRequest, AnalyzeIncidentResponse, StageEvent  # noqa: E402
from incident_suite.service import stream_incident  # noqa: E402
from incident_suite.tools.llm import build_llm  # noqa: E402


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def load_default_keys() -> dict[str, str]:
    defaults = {
        "slack_bot_token": "",
        "slack_channel": "",
        "jira_base_url": "https://your-domain.atlassian.net",
        "jira_email": "",
        "jira_api_token": "",
        "jira_project_key": "OPS",
        "salesforce_client_id": "",
        "salesforce_client_secret": "",
        "salesforce_instance_url": "",
        "salesforce_access_token": "",
        "salesforce_auth_domain": "test",
        "salesforce_redirect_uri": "http://localhost:8501",
        "openrouter_api_key": "",
        "openrouter_model": "openai/gpt-4.1-mini",
    }

    secrets_data: dict[str, Any] = {}
    try:
        if st.secrets:
            secrets_data = {key: dict(value) if hasattr(value, "items") else value for key, value in st.secrets.items()}
    except Exception:
        secrets_data = {}

    if not secrets_data:
        candidate = SECRETS_PATH if SECRETS_PATH.exists() else SECRETS_EXAMPLE_PATH
        if candidate.exists():
            secrets_data = tomllib.loads(candidate.read_text(encoding="utf-8"))

    slack = secrets_data.get("slack", {})
    jira = secrets_data.get("jira", {})
    salesforce = secrets_data.get("salesforce", {})
    openrouter = secrets_data.get("openrouter", {})

    defaults["slack_bot_token"] = slack.get("bot_token", defaults["slack_bot_token"])
    defaults["slack_channel"] = slack.get("channel_id", defaults["slack_channel"])
    defaults["jira_base_url"] = jira.get("base_url", defaults["jira_base_url"])
    defaults["jira_email"] = jira.get("email", defaults["jira_email"])
    defaults["jira_api_token"] = jira.get("api_token", defaults["jira_api_token"])
    defaults["jira_project_key"] = jira.get("project_key", defaults["jira_project_key"])
    defaults["salesforce_client_id"] = salesforce.get("client_id", defaults["salesforce_client_id"])
    defaults["salesforce_client_secret"] = salesforce.get("client_secret", defaults["salesforce_client_secret"])
    defaults["salesforce_instance_url"] = salesforce.get("instance_url", defaults["salesforce_instance_url"])
    defaults["salesforce_access_token"] = salesforce.get("access_token", defaults["salesforce_access_token"])
    defaults["salesforce_auth_domain"] = salesforce.get("auth_domain", defaults["salesforce_auth_domain"])
    defaults["salesforce_redirect_uri"] = salesforce.get("redirect_uri", defaults["salesforce_redirect_uri"])
    defaults["openrouter_api_key"] = openrouter.get("api_key", defaults["openrouter_api_key"])
    defaults["openrouter_model"] = openrouter.get("model", defaults["openrouter_model"])
    return defaults


st.set_page_config(
    page_title="SignalSmith AI",
    page_icon=":satellite:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_state() -> None:
    parsed_defaults = load_default_keys()
    query_params = st.query_params
    auth_code_from_url = query_params.get("code", "")
    defaults = {
        "theme_mode": "light",
        "analysis_result": None,
        "stage_events": [],
        "chat_messages": [
            {"role": "assistant", "content": "Run an analysis and then ask follow-up questions here."}
        ],
        "salesforce_token": parsed_defaults["salesforce_access_token"],
        "salesforce_instance_url": parsed_defaults["salesforce_instance_url"],
        "salesforce_class_name": "",
        "salesforce_class_body": "",
        "editable_class_body": "",
        "generated_patch_diff": "",
        "git_status_message": "",
        "salesforce_exchange_message": "",
        "salesforce_exchange_status": "",
        "default_slack_bot_token": parsed_defaults["slack_bot_token"],
        "default_slack_channel": parsed_defaults["slack_channel"],
        "default_jira_base_url": parsed_defaults["jira_base_url"],
        "default_jira_email": parsed_defaults["jira_email"],
        "default_jira_api_token": parsed_defaults["jira_api_token"],
        "default_jira_project_key": parsed_defaults["jira_project_key"] or "OPS",
        "default_salesforce_client_id": parsed_defaults["salesforce_client_id"],
        "default_salesforce_client_secret": parsed_defaults["salesforce_client_secret"],
        "default_salesforce_instance_url": parsed_defaults["salesforce_instance_url"],
        "default_salesforce_access_token": parsed_defaults["salesforce_access_token"],
        "default_salesforce_auth_domain": parsed_defaults["salesforce_auth_domain"],
        "default_salesforce_redirect_uri": parsed_defaults["salesforce_redirect_uri"],
        "default_openrouter_api_key": parsed_defaults["openrouter_api_key"],
        "default_openrouter_model": parsed_defaults["openrouter_model"],
        "salesforce_auth_code": auth_code_from_url,
        "connection_test_results": {},
        "logs_input": "2026-04-04T09:18:12Z ERROR payments-api timeout calling AccountSyncService\n2026-04-04T09:18:20Z CRITICAL AccountSyncService failed after retry exhaustion",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if auth_code_from_url:
        st.session_state.salesforce_auth_code = auth_code_from_url


init_state()


def apply_theme(theme_mode: str) -> None:
    is_dark = theme_mode == "dark"
    bg = "#07111f" if is_dark else "#f6f8fc"
    card = "#0f1b2d" if is_dark else "#ffffff"
    text = "#ebf3ff" if is_dark else "#0f172a"
    muted = "#93a4bf" if is_dark else "#475569"
    accent = "#5eead4" if is_dark else "#0f766e"
    border = "#18304f" if is_dark else "#dbe4f0"
    glow = "rgba(94,234,212,0.18)" if is_dark else "rgba(15,118,110,0.10)"
    st.markdown(
        f"""
        <style>
          .stApp {{
            background:
              radial-gradient(circle at top left, {glow}, transparent 36%),
              radial-gradient(circle at top right, rgba(99,102,241,0.10), transparent 22%),
              {bg};
            color: {text};
          }}
          .stApp, .stApp p, .stApp li, .stApp span, .stApp label, .stApp div,
          h1, h2, h3, h4, h5, h6, [data-testid="stMarkdownContainer"] * {{
            color: {text};
          }}
          .block-container {{
            padding-top: 3.1rem;
            padding-bottom: 2rem;
          }}
          [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {card} 0%, {bg} 100%);
            border-right: 1px solid {border};
          }}
          [data-testid="stSidebar"] * {{
            color: {text};
          }}
          .stTextInput input,
          .stTextArea textarea,
          .stSelectbox div[data-baseweb="select"] > div,
          .stMultiSelect div[data-baseweb="select"] > div,
          button[kind],
          [data-testid="stBaseButton-secondary"],
          [data-testid="stBaseButton-primary"] {{
            background: {card} !important;
            color: {text} !important;
            border-color: {border} !important;
          }}
          button[kind] p,
          [data-testid="stBaseButton-secondary"] p,
          [data-testid="stBaseButton-primary"] p {{
            color: {text} !important;
          }}
          .stTextInput input::placeholder,
          .stTextArea textarea::placeholder {{
            color: {muted} !important;
          }}
          .stRadio label, .stCheckbox label, .stToggle label, .stFileUploader label {{
            color: {text} !important;
          }}
          [data-testid="stMetric"] {{
            background: {card};
            border: 1px solid {border};
            border-radius: 18px;
            padding: 0.65rem 0.85rem;
          }}
          [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {{
            color: {text} !important;
          }}
          .stTabs [data-baseweb="tab-list"] button {{
            color: {muted};
          }}
          .stTabs [aria-selected="true"] {{
            color: {text} !important;
          }}
          .stChatMessage {{
            background: rgba(255,255,255,0.03);
            border: 1px solid {border};
            border-radius: 18px;
          }}
          .agent-card, .hero-card, .panel-card {{
            background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01));
            border: 1px solid {border};
            border-radius: 22px;
            padding: 1rem 1.15rem;
            box-shadow: 0 12px 42px rgba(0,0,0,0.14);
          }}
          .hero-card {{
            position: relative;
            overflow: hidden;
            margin-top: 0.75rem;
          }}
          .hero-card::before {{
            content: "";
            position: absolute;
            inset: -2px;
            background: linear-gradient(90deg, transparent, {glow}, transparent);
            animation: beam 4s linear infinite;
          }}
          .hero-card > * {{
            position: relative;
            z-index: 1;
          }}
          .eyebrow {{
            display: inline-flex;
            align-items: center;
            gap: 0.65rem;
            font-size: 0.75rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: {accent};
            margin-bottom: 0.4rem;
          }}
          .brand-mark {{
            width: 2.1rem;
            height: 2.1rem;
            border-radius: 0.8rem;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, {accent}, #38bdf8);
            color: #f8fafc;
            font-size: 1rem;
            font-weight: 800;
            letter-spacing: 0;
            box-shadow: 0 8px 24px rgba(15, 118, 110, 0.22);
          }}
          .brand-title {{
            display: inline-flex;
            flex-direction: column;
            gap: 0.08rem;
          }}
          .brand-name {{
            font-size: 0.82rem;
            letter-spacing: 0.16em;
          }}
          .brand-tag {{
            font-size: 0.68rem;
            letter-spacing: 0.08em;
            text-transform: none;
            color: {muted};
          }}
          .headline {{
            font-size: 2.2rem;
            line-height: 1.08;
            font-weight: 700;
            color: {text};
            margin: 0;
          }}
          .subhead {{
            color: {muted};
            margin-top: 0.55rem;
            font-size: 1rem;
          }}
          .stage-list {{
            display: grid;
            gap: 0.75rem;
            margin-top: 0.5rem;
          }}
          .stage-item {{
            border: 1px solid {border};
            background: {card};
            border-radius: 18px;
            padding: 0.85rem 1rem;
            animation: rise 0.45s ease both;
          }}
          .stage-top {{
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 0.2rem;
          }}
          .stage-name {{
            font-weight: 600;
            color: {text};
          }}
          .stage-status {{
            color: {accent};
            font-size: 0.84rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
          }}
          .stage-message {{
            color: {muted};
            font-size: 0.93rem;
          }}
          .metric-strip {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.85rem;
          }}
          .metric-card {{
            border: 1px solid {border};
            border-radius: 18px;
            padding: 0.85rem 1rem;
            background: {card};
          }}
          .metric-label {{
            color: {muted};
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
          }}
          .metric-value {{
            color: {text};
            font-size: 1.2rem;
            font-weight: 700;
            margin-top: 0.25rem;
          }}
          @keyframes beam {{
            0% {{ transform: translateX(-45%); }}
            100% {{ transform: translateX(100%); }}
          }}
          @keyframes rise {{
            from {{ opacity: 0; transform: translateY(12px); }}
            to {{ opacity: 1; transform: translateY(0); }}
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


apply_theme(st.session_state.theme_mode)


def mask_secret(value: str) -> str:
    if not value:
        return "Not set"
    if len(value) <= 6:
        return "*" * len(value)
    return f"{value[:3]}...{value[-3:]}"


def ensure_http_url(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    if cleaned.startswith(("http://", "https://")):
        return cleaned.rstrip("/")
    return f"https://{cleaned.rstrip('/')}"


def salesforce_oauth_url(client_id: str, redirect_uri: str, sandbox_domain: str) -> str:
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "api refresh_token",
    }
    return f"https://{sandbox_domain}.salesforce.com/services/oauth2/authorize?{urlencode(params)}"


def exchange_salesforce_code(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    sandbox_domain: str,
    auth_code: str,
) -> tuple[bool, dict[str, Any]]:
    try:
        response = httpx.post(
            f"https://{sandbox_domain}.salesforce.com/services/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "code": auth_code,
            },
            timeout=30.0,
        )
        payload = response.json()
        response.raise_for_status()
        return True, payload
    except Exception as exc:
        return False, {"error": str(exc)}


def test_openrouter_connection(api_key: str, model: str) -> tuple[bool, str]:
    if not api_key.strip():
        return False, "Missing OpenRouter API key."
    try:
        response = httpx.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "incident-analysis-suite",
            },
            json={"model": model, "messages": [{"role": "user", "content": "Reply with OK"}], "max_tokens": 8},
            timeout=20.0,
        )
        payload = response.json()
        response.raise_for_status()
        if payload.get("choices"):
            return True, "OpenRouter connected."
        return False, "OpenRouter test did not return a valid response."
    except Exception as exc:
        return False, str(exc)


def test_slack_connection(bot_token: str, channel_id: str) -> tuple[bool, str]:
    if not bot_token.strip():
        return False, "Missing Slack bot token."
    if not channel_id.strip():
        return False, "Missing Slack channel ID."
    try:
        headers = {"Authorization": f"Bearer {bot_token}"}
        response = httpx.post("https://slack.com/api/auth.test", headers=headers, timeout=20.0)
        payload = response.json()
        if not payload.get("ok"):
            return False, payload.get("error", "Slack auth test failed.")

        post_response = httpx.post(
            "https://slack.com/api/chat.postMessage",
            headers={**headers, "Content-Type": "application/json; charset=utf-8"},
            json={
                "channel": channel_id,
                "text": "SignalSmith AI test message: Slack posting is configured correctly.",
            },
            timeout=20.0,
        )
        post_payload = post_response.json()
        if post_payload.get("ok"):
            return True, "Slack connected."
        return False, post_payload.get("error", "Slack post test failed.")
    except Exception as exc:
        return False, str(exc)


def test_jira_connection(base_url: str, email: str, api_token: str, project_key: str) -> tuple[bool, str]:
    if not base_url.strip() or not email.strip() or not api_token.strip():
        return False, "Missing Jira base URL, email, or API token."
    if not project_key.strip():
        return False, "Missing Jira project key."
    try:
        normalized_base_url = ensure_http_url(base_url)
        response = httpx.get(f"{normalized_base_url}/rest/api/3/myself", auth=(email, api_token), timeout=20.0)
        payload = response.json()
        response.raise_for_status()
        project_response = httpx.get(
            f"{normalized_base_url}/rest/api/3/project/{project_key}",
            auth=(email, api_token),
            timeout=20.0,
        )
        if project_response.status_code >= 400:
            project_payload = project_response.json()
            return False, project_payload.get("errorMessages", ["Jira project validation failed."])[0]
        project_payload = project_response.json()
        return True, "Jira connected."
    except Exception as exc:
        return False, str(exc)


def test_salesforce_connection(instance_url: str, access_token: str) -> tuple[bool, str]:
    if not instance_url.strip():
        return False, "Salesforce instance URL is missing."
    if not access_token.strip():
        return False, "Complete OAuth exchange first."
    try:
        response = httpx.get(
            f"{ensure_http_url(instance_url)}/services/data/",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=20.0,
        )
        payload = response.json()
        response.raise_for_status()
        return True, "Salesforce connected."
    except Exception as exc:
        return False, str(exc)


def fetch_salesforce_class(instance_url: str, access_token: str, class_name: str) -> tuple[bool, dict[str, Any]]:
    if not class_name.strip():
        return False, {"error": "No Salesforce class name could be inferred from the logs yet."}
    safe_class_name = class_name.replace("'", "\\'")
    query = f"SELECT Id, Name, Body FROM ApexClass WHERE Name = '{safe_class_name}' LIMIT 1"
    try:
        response = httpx.get(
            f"{ensure_http_url(instance_url)}/services/data/v61.0/tooling/query",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"q": query},
            timeout=30.0,
        )
        payload = response.json()
        response.raise_for_status()
        records = payload.get("records", [])
        if not records:
            return False, {"error": f"No ApexClass named `{class_name}` was found in the sandbox."}
        return True, records[0]
    except Exception as exc:
        return False, {"error": str(exc)}


def infer_salesforce_class_name(raw_logs: str) -> str:
    lines = raw_logs.splitlines()
    for line in lines:
        if "METHOD_ENTRY" in line and "|" in line:
            candidate = line.split("|")[-1].split("(")[0].strip()
            if "." in candidate:
                class_name = candidate.split(".")[0].strip()
                if class_name:
                    return class_name
    for line in lines:
        if "CODE_UNIT_STARTED" in line and " trigger event" in line:
            tail = line.split("|")[-1].strip()
            candidate = tail.split(" on ")[0].strip()
            if candidate:
                return candidate
    for token in raw_logs.replace(":", " ").replace("/", " ").split():
        cleaned = token.strip(".,()[]{}")
        if cleaned.endswith(".cls"):
            return cleaned.removesuffix(".cls")
        if cleaned.endswith(("Controller", "Service", "TriggerHandler", "Trigger")):
            return cleaned
    return ""


def normalize_stage_events(events: list[StageEvent | dict]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for event in events:
        payload = event if isinstance(event, dict) else event.model_dump()
        normalized.append(
            {
                "stage": str(payload.get("stage", "")),
                "status": str(payload.get("status", "")),
                "message": str(payload.get("message", "")),
            }
        )
    return normalized


def render_stage_summary(events: list[StageEvent | dict]) -> str:
    normalized = normalize_stage_events(events)
    if not normalized:
        return "Waiting for analysis to begin."
    lines = []
    for event in normalized[-8:]:
        stage_name = event["stage"].replace("_", " ").title()
        lines.append(f"- `{stage_name}`: {event['message']}")
    return "\n".join(lines)


def build_live_workflow_diagram(events: list[StageEvent | dict]) -> str:
    normalized = normalize_stage_events(events)
    completed = {event["stage"] for event in normalized}
    current = normalized[-1]["stage"] if normalized else ""
    ordered = [
        ("orchestrator", "Orchestrator"),
        ("planner", "Planner"),
        ("decomposer", "Query Decomposer"),
        ("ingestion", "Log Ingestion"),
        ("retriever", "Context Retriever"),
        ("normalizer", "Source Normalizer"),
        ("evidence", "Evidence Extraction"),
        ("verifier", "Fact Verification"),
        ("critical_analysis", "Critical Analysis"),
        ("insight_generator", "Insight Generator"),
        ("code_generator", "Code Generator"),
        ("cookbook", "Cookbook Synthesizer"),
        ("qa", "QA Gate"),
        ("notification", "Slack Notify"),
        ("jira", "Jira Escalation"),
        ("export", "Report Export"),
    ]

    def node_fill(stage: str) -> str:
        if stage == current:
            return "#14b8a6"
        if stage in completed:
            return "#d1fae5"
        return "#eef2ff"

    def node_font(stage: str) -> str:
        if stage == current:
            return "#ffffff"
        return "#0f172a"

    nodes = "\n".join(
        f'    {stage} [label="{label}", fillcolor="{node_fill(stage)}", fontcolor="{node_font(stage)}"];'
        for stage, label in ordered
    )
    edges = [
        "orchestrator -> planner -> decomposer -> ingestion -> retriever -> normalizer -> evidence -> verifier -> critical_analysis -> insight_generator -> code_generator -> cookbook -> qa;",
        'qa -> notification [label="pass"];',
        'qa -> jira [label="critical"];',
        "notification -> export;",
        "jira -> export;",
    ]
    return (
        "digraph IncidentProgress {\n"
        '    rankdir=LR;\n'
        '    graph [pad="0.65", nodesep="0.95", ranksep="1.2", bgcolor="transparent"];\n'
        '    node [shape=box, style="rounded,filled", color="#94a3b8", fontname="Helvetica", fontsize=14, margin="0.34,0.28", penwidth=1.7];\n'
        '    edge [color="#64748b", penwidth=1.8, arrowsize=0.9, fontname="Helvetica", fontsize=11];\n'
        f"{nodes}\n"
        + "\n".join(f"    {edge}" for edge in edges)
        + "\n}\n"
    )


def build_workflow_diagram() -> str:
    return """
digraph IncidentOrchestration {
    rankdir=LR;
    graph [pad="0.45", nodesep="0.6", ranksep="0.95", bgcolor="transparent"];
    node [shape=box, style="rounded,filled", color="#24415f", fontname="Helvetica", fontsize=12, margin="0.24,0.18", penwidth=1.4];
    edge [color="#50657f", penwidth=1.6, arrowsize=0.9];

    user [label="User Query + Logs", fillcolor="#dbeafe"];
    orchestrator [label="Orchestrator", fillcolor="#fef3c7"];
    planner [label="Planner", fillcolor="#fde68a"];
    decomposer [label="Query Decomposer", fillcolor="#fed7aa"];
    ingestion [label="Document Ingestion", fillcolor="#e0f2fe"];
    retriever [label="Retriever\\nLanceDB", fillcolor="#cffafe"];
    normalize [label="Normalize Sources", fillcolor="#fae8ff"];
    evidence [label="Evidence Extraction", fillcolor="#fbcfe8"];
    verify [label="Fact Verification", fillcolor="#ddd6fe"];
    critical [label="Critical Analysis", fillcolor="#fecaca"];
    insights [label="Insight Generator", fillcolor="#dcfce7"];
    codegen [label="Code Generator", fillcolor="#bbf7d0"];
    cookbook [label="Cookbook Synthesizer", fillcolor="#a7f3d0"];
    qa [label="QA Gate", fillcolor="#fef08a"];
    selfcorrect [label="Self Corrector", fillcolor="#fdba74"];
    export [label="Export + Report", fillcolor="#bfdbfe"];

    user -> orchestrator -> planner -> decomposer -> ingestion -> retriever -> normalize -> evidence -> verify -> critical -> insights -> codegen -> cookbook -> qa;
    qa -> selfcorrect [label="retry"];
    selfcorrect -> cookbook;
    qa -> export [label="pass"];
}
"""


def run_streaming_analysis(request: AnalyzeIncidentRequest) -> AnalyzeIncidentResponse:
    progress_text = st.empty()
    progress_graph = st.empty()
    stage_feed = []
    merged_state: dict[str, Any] = {}
    with st.spinner("Collaborating agents are analyzing the incident..."):
        for update in stream_incident(request):
            for _, payload in update.items():
                merged_state.update(payload)
                if payload.get("stage_events"):
                    stage_feed = payload["stage_events"]
                    progress_text.markdown(render_stage_summary(stage_feed))
                    progress_graph.graphviz_chart(build_live_workflow_diagram(stage_feed), use_container_width=True)
    st.session_state.stage_events = stage_feed
    result = AnalyzeIncidentResponse(**merged_state)
    st.session_state.analysis_result = result
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "The multi-agent analysis is complete. Ask about the evidence, fixes, diagram, or export output."}
    ]
    return result


def ask_followup(api_key: str, model: str, question: str, result: AnalyzeIncidentResponse | None, class_body: str) -> str:
    llm = build_llm(api_key=api_key, model=model)
    if llm is None:
        return "Add an OpenRouter API key to enable follow-up chat."
    messages = [
        SystemMessage(
            content=(
                "You are an AI-powered incident analyst. Answer follow-up questions using the incident evidence, report, code fixes, "
                "cookbook, and any Salesforce Apex code that was retrieved."
            )
        )
    ]
    for item in st.session_state.chat_messages[-8:]:
        if item["role"] == "assistant":
            messages.append(AIMessage(content=item["content"]))
        else:
            messages.append(HumanMessage(content=item["content"]))
    context_blob = {
        "analysis": result.model_dump() if result else {},
        "salesforce_class_excerpt": class_body[:8000],
    }
    messages.append(HumanMessage(content=f"Context:\n{json.dumps(context_blob, indent=2)}\n\nQuestion:\n{question}"))
    try:
        return llm.invoke(messages).content  # type: ignore[return-value]
    except Exception as exc:
        return f"Follow-up chat failed: {exc}"


def generate_patch(api_key: str, model: str, class_name: str, original_body: str, result: AnalyzeIncidentResponse | None) -> tuple[bool, str]:
    llm = build_llm(api_key=api_key, model=model)
    if llm is None:
        return False, "Add an OpenRouter API key to generate a patch."
    if not original_body.strip():
        return False, "Fetch a Salesforce class first."
    fix_context = [fix.model_dump() if hasattr(fix, "model_dump") else fix for fix in (result.code_fixes if result else [])]
    messages = [
        SystemMessage(
            content=(
                "You are a senior Salesforce Apex engineer. Apply the minimal safe fix to the supplied Apex class using the incident analysis. "
                "Return only the full updated Apex class with no markdown."
            )
        ),
        HumanMessage(
            content=(
                f"Class name: {class_name}\n\n"
                f"Fix context:\n{json.dumps(fix_context, indent=2)}\n\n"
                f"Original class:\n{original_body}"
            )
        ),
    ]
    try:
        return True, llm.invoke(messages).content.strip()  # type: ignore[return-value]
    except Exception as exc:
        return False, f"Patch generation failed: {exc}"


def build_diff(original_text: str, updated_text: str, file_label: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            original_text.splitlines(),
            updated_text.splitlines(),
            fromfile=f"{file_label} (original)",
            tofile=f"{file_label} (patched)",
            lineterm="",
        )
    )


def render_evidence_panel(result: AnalyzeIncidentResponse) -> None:
    if not result.evidence_items:
        st.write("No evidence extracted yet.")
        return

    for idx, item in enumerate(result.evidence_items, start=1):
        title = item.claim or f"Evidence {idx}"
        with st.container(border=True):
            st.markdown(f"### Evidence {idx}")
            st.write(title)
            confidence_value = max(0, min(100, int(round(item.confidence * 100))))
            left_col, right_col = st.columns([3, 1])
            with left_col:
                st.progress(confidence_value)
            with right_col:
                st.metric("Confidence", f"{confidence_value}%")
            verdict = "Verified" if item.verified else "Needs review"
            st.caption(f"{verdict} • Sources: {', '.join(item.source_doc_ids) if item.source_doc_ids else 'log trace'}")
            if item.supporting_evidence:
                st.markdown("#### Evidence Blocks")
                for block in item.supporting_evidence:
                    st.code(block, language="text")


def render_mermaid_diagram(diagram: str, height: int = 420) -> None:
    if not diagram.strip():
        st.write("No Mermaid diagram generated yet.")
        return
    escaped = json.dumps(diagram)
    html = f"""
    <div style="background:#ffffff;border:1px solid #dbe4f0;border-radius:18px;padding:16px;overflow:auto;">
      <pre id="mermaid-diagram" class="mermaid" style="margin:0;"></pre>
    </div>
    <script type="module">
      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
      mermaid.initialize({{ startOnLoad: true, securityLevel: 'loose', theme: 'default' }});
      document.getElementById('mermaid-diagram').textContent = {escaped};
      await mermaid.run({{ querySelector: '.mermaid' }});
    </script>
    """
    components.html(html, height=height, scrolling=True)


def commit_fixed_class(repo_path: str, file_path: str, class_body: str, commit_message: str) -> tuple[bool, str]:
    repo = Path(repo_path).expanduser()
    target = Path(file_path).expanduser()
    if not repo.exists() or not (repo / ".git").exists():
        return False, f"Git repo not found at {repo}"
    if not class_body.strip():
        return False, "No patched class body to commit."
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(class_body, encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", str(target)], check=True, capture_output=True, text=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", commit_message], check=True, capture_output=True, text=True)
        return True, f"Committed {target.name} with message: {commit_message}"
    except subprocess.CalledProcessError as exc:
        return False, exc.stderr.strip() or exc.stdout.strip() or str(exc)


with st.sidebar:
    st.subheader("Experience")
    theme_toggle = st.toggle("Dark mode", value=st.session_state.theme_mode == "dark")
    st.session_state.theme_mode = "dark" if theme_toggle else "light"

    st.divider()
    st.subheader("OpenRouter")
    openrouter_api_key = st.text_input("OpenRouter API key", type="password", value=st.session_state.default_openrouter_api_key)
    openrouter_model = st.selectbox(
        "Analysis model",
        [
            "openai/gpt-4.1-mini",
            "openai/gpt-4.1",
            "anthropic/claude-3.7-sonnet",
            "google/gemini-2.5-pro-preview",
        ],
        index=max(0, ["openai/gpt-4.1-mini", "openai/gpt-4.1", "anthropic/claude-3.7-sonnet", "google/gemini-2.5-pro-preview"].index(st.session_state.default_openrouter_model)) if st.session_state.default_openrouter_model in ["openai/gpt-4.1-mini", "openai/gpt-4.1", "anthropic/claude-3.7-sonnet", "google/gemini-2.5-pro-preview"] else 0,
    )
    custom_model = st.text_input("Custom model id", value="")
    active_model = custom_model.strip() or openrouter_model
    st.caption(f"Active model: `{active_model}`")
    if st.button("Test OpenRouter Connection", use_container_width=True):
        ok, message = test_openrouter_connection(openrouter_api_key, active_model)
        st.session_state.connection_test_results["openrouter"] = (ok, message)
    if "openrouter" in st.session_state.connection_test_results:
        ok, message = st.session_state.connection_test_results["openrouter"]
        st.success(message) if ok else st.error(message)

    st.divider()
    st.subheader("Slack")
    slack_bot_token = st.text_input("Slack bot token", type="password", value=st.session_state.default_slack_bot_token)
    slack_channel = st.text_input("Slack channel ID", value=st.session_state.default_slack_channel)
    st.caption(f"Slack token: {mask_secret(slack_bot_token)}")
    if st.button("Test Slack Connection", use_container_width=True):
        ok, message = test_slack_connection(slack_bot_token, slack_channel)
        st.session_state.connection_test_results["slack"] = (ok, message)
    if "slack" in st.session_state.connection_test_results:
        ok, message = st.session_state.connection_test_results["slack"]
        st.success(message) if ok else st.error(message)

    st.divider()
    st.subheader("Jira")
    jira_base_url = st.text_input("Jira base URL", value=st.session_state.default_jira_base_url)
    jira_email = st.text_input("Jira email", value=st.session_state.default_jira_email)
    jira_api_token = st.text_input("Jira API token", type="password", value=st.session_state.default_jira_api_token)
    jira_project_key = st.text_input("Jira project key", value=st.session_state.default_jira_project_key)
    st.caption(f"Jira token: {mask_secret(jira_api_token)}")
    if st.button("Test Jira Connection", use_container_width=True):
        ok, message = test_jira_connection(jira_base_url, jira_email, jira_api_token, jira_project_key)
        st.session_state.connection_test_results["jira"] = (ok, message)
    if "jira" in st.session_state.connection_test_results:
        ok, message = st.session_state.connection_test_results["jira"]
        st.success(message) if ok else st.error(message)

    st.divider()
    st.subheader("Salesforce Sandbox")
    salesforce_sandbox_domain = st.text_input("Auth domain", value=st.session_state.default_salesforce_auth_domain)
    salesforce_client_id = st.text_input("Client ID", type="password", value=st.session_state.default_salesforce_client_id)
    salesforce_client_secret = st.text_input("Client secret", type="password", value=st.session_state.default_salesforce_client_secret)
    salesforce_redirect_uri = st.text_input("Redirect URI", value=st.session_state.default_salesforce_redirect_uri)
    salesforce_manual_token = st.text_input(
        "Bearer access token",
        type="password",
        value=st.session_state.salesforce_token or st.session_state.default_salesforce_access_token,
        help="Optional fast path. If you already have a Salesforce bearer token, paste it here or store it in `.streamlit/secrets.toml` to skip OAuth exchange.",
    )
    st.session_state.salesforce_token = salesforce_manual_token.strip()
    salesforce_auth_code = st.text_input("Authorization code", type="password", key="salesforce_auth_code")
    st.caption("Use either a bearer token or the OAuth code exchange flow below. Bearer token is the fastest path for demos.")
    if salesforce_client_id:
        st.link_button(
            "Login to Salesforce Sandbox",
            salesforce_oauth_url(salesforce_client_id, salesforce_redirect_uri, salesforce_sandbox_domain),
            use_container_width=True,
        )
    if st.button("Exchange Salesforce OAuth Code", use_container_width=True):
        if not salesforce_auth_code.strip():
            st.session_state.salesforce_exchange_status = "error"
            st.session_state.salesforce_exchange_message = "Paste the Salesforce authorization code first."
        else:
            ok, payload = exchange_salesforce_code(
                salesforce_client_id,
                salesforce_client_secret,
                salesforce_redirect_uri,
                salesforce_sandbox_domain,
                salesforce_auth_code,
            )
            if ok:
                st.session_state.salesforce_token = payload.get("access_token", "")
                st.session_state.salesforce_instance_url = payload.get("instance_url", "") or st.session_state.default_salesforce_instance_url
                st.session_state.salesforce_exchange_status = "success"
                st.session_state.salesforce_exchange_message = "Salesforce sandbox connected for this session."
            else:
                st.session_state.salesforce_exchange_status = "error"
                st.session_state.salesforce_exchange_message = payload.get("error", "Salesforce OAuth exchange failed.")
    if st.button("Test Salesforce Connection", use_container_width=True):
        ok, message = test_salesforce_connection(
            st.session_state.salesforce_instance_url or st.session_state.default_salesforce_instance_url,
            st.session_state.salesforce_token,
        )
        st.session_state.connection_test_results["salesforce"] = (ok, message)
    if st.session_state.salesforce_exchange_status == "success":
        st.success(st.session_state.salesforce_exchange_message)
    elif st.session_state.salesforce_exchange_status == "error" and st.session_state.salesforce_exchange_message:
        st.error(st.session_state.salesforce_exchange_message)
    if "salesforce" in st.session_state.connection_test_results:
        ok, message = st.session_state.connection_test_results["salesforce"]
        st.success(message) if ok else st.error(message)
    if st.session_state.default_salesforce_instance_url:
        st.caption(f"Default sandbox instance from project secrets: `{st.session_state.default_salesforce_instance_url}`")
    st.caption(f"Salesforce token: {mask_secret(st.session_state.salesforce_token)}")


st.markdown(
    """
    <div class="hero-card">
      <div class="eyebrow">
        <div class="brand-mark">S∿</div>
        <div class="brand-title">
          <div class="brand-name">SignalSmith AI</div>
          <div class="brand-tag">Multi-agent incident studio</div>
        </div>
      </div>
      <h1 class="headline">Signal faster. Fix smarter.</h1>
      <p class="subhead">A collaborative AI workspace for incident analysis, Apex fixes, evidence trails, and live system flows.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

left, center, right = st.columns([0.98, 1.2, 0.82], gap="large")

with left:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.subheader("Investigation Input")
    query = st.text_input("User query", value="Analyze this production incident, verify the evidence, generate a fix, and prepare an exportable report.")
    uploaded_file = st.file_uploader("Upload logs", type=["log", "txt", "json"])
    if uploaded_file is not None:
        st.session_state.logs_input = uploaded_file.read().decode("utf-8", errors="ignore")
        st.success(f"Loaded `{uploaded_file.name}`.")
    raw_logs = st.text_area("Logs", height=220, key="logs_input")
    st.caption("The logs box is the active incident context passed into the agents. Uploading a file should replace it, and you can still edit it before running analysis.")

    severity_override = st.selectbox("Severity override", ["Auto", "Medium", "High", "Critical"])
    inferred_class = infer_salesforce_class_name(raw_logs)
    class_name = st.text_input("Salesforce class inferred from logs", value=inferred_class)
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Fetch Salesforce Class", use_container_width=True):
            ok, payload = fetch_salesforce_class(
                st.session_state.salesforce_instance_url or st.session_state.default_salesforce_instance_url,
                st.session_state.salesforce_token,
                class_name,
            )
            if ok:
                st.session_state.salesforce_class_name = payload.get("Name", class_name)
                st.session_state.salesforce_class_body = payload.get("Body", "")
                st.session_state.editable_class_body = payload.get("Body", "")
                st.success(f"Fetched `{st.session_state.salesforce_class_name}` from sandbox.")
            else:
                st.error(payload["error"])
    with col_b:
        analyze_clicked = st.button("Run Multi-Agent Analysis", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with center:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.subheader("Live Agent Progress")
    stage_placeholder = st.empty()
    stage_placeholder.markdown(render_stage_summary(st.session_state.stage_events))
    st.markdown("<div style='padding-top: 0.8rem;'></div>", unsafe_allow_html=True)
    st.subheader("Collaborating Orchestration")
    st.graphviz_chart(build_live_workflow_diagram(st.session_state.stage_events), use_container_width=True)
    st.caption("Each node lights up as LangGraph advances through orchestration, retrieval, verification, fix generation, and escalation.")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.subheader("Salesforce Class")
    st.code(st.session_state.salesforce_class_body or "// No Salesforce Apex class fetched yet.", language="java")
    st.markdown("</div>", unsafe_allow_html=True)

if analyze_clicked:
    request = AnalyzeIncidentRequest(
        source="streamlit-ui",
        query=query,
        raw_logs=raw_logs,
        salesforce_class_name=st.session_state.salesforce_class_name or class_name,
        salesforce_class_body=st.session_state.salesforce_class_body,
        severity_override=severity_override.lower() if severity_override != "Auto" else None,
        runtime_salesforce_instance_url=st.session_state.salesforce_instance_url or st.session_state.default_salesforce_instance_url,
        runtime_salesforce_access_token=st.session_state.salesforce_token,
        runtime_slack_bot_token=slack_bot_token,
        runtime_slack_channel_id=slack_channel,
        runtime_jira_base_url=jira_base_url,
        runtime_jira_email=jira_email,
        runtime_jira_api_token=jira_api_token,
        runtime_jira_project_key=jira_project_key,
        openrouter_api_key=openrouter_api_key,
        openrouter_model=active_model,
    )
    result = run_streaming_analysis(request)
    stage_placeholder.markdown(render_stage_summary(result.stage_events))


if st.session_state.analysis_result:
    result: AnalyzeIncidentResponse = st.session_state.analysis_result
    st.markdown(
        f"""
        <div class="metric-strip">
          <div class="metric-card"><div class="metric-label">Incident</div><div class="metric-value">{result.incident_id}</div></div>
          <div class="metric-card"><div class="metric-label">Severity</div><div class="metric-value">{result.severity}</div></div>
          <div class="metric-card"><div class="metric-label">Issues</div><div class="metric-value">{len(result.detected_issues)}</div></div>
          <div class="metric-card"><div class="metric-label">Evidence</div><div class="metric-value">{len(result.evidence_items)}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Report", "Code Fixes", "Cookbook", "Evidence", "Mermaid", "Exports", "Git"])
    with tabs[0]:
        st.markdown(result.report_markdown or "No report available.")
        if result.insights:
            st.write([item.model_dump() for item in result.insights])
    with tabs[1]:
        for fix in result.code_fixes:
            st.markdown(f"### {fix.issue_title}")
            st.write(f"Target component: `{fix.target_component}`")
            st.write(fix.recommended_change)
            st.info(f"Analogy: {fix.analogy}")
            code_language = "java" if "salesforce" in fix.target_component.lower() or "apex" in fix.target_component.lower() else "python"
            st.code(fix.suggested_code, language=code_language)
            if fix.validation_notes:
                st.caption("Validation checks")
                for note in fix.validation_notes:
                    st.write(f"- {note}")
    with tabs[2]:
        if result.cookbook:
            st.markdown(f"### {result.cookbook.title}")
            st.write(result.cookbook.summary)
            st.markdown("#### Checklist")
            for item in result.cookbook.checklist:
                st.write(f"- {item}")
            st.markdown("#### Escalation Rules")
            for item in result.cookbook.escalation_rules:
                st.write(f"- {item}")
            st.markdown("#### Prevention Steps")
            for item in result.cookbook.prevention_steps:
                st.write(f"- {item}")
    with tabs[3]:
        render_evidence_panel(result)
        if result.detected_issues:
            st.markdown("#### Linked Issues")
            for issue in result.detected_issues:
                with st.container(border=True):
                    st.write(f"**{issue.title}**")
                    st.write(issue.probable_root_cause)
                    st.caption(f"Severity: {issue.severity} • Confidence: {int(round(issue.confidence * 100))}%")
    with tabs[4]:
        render_mermaid_diagram(result.mermaid_diagram)
        with st.expander("View Mermaid source"):
            st.code(result.mermaid_diagram, language="mermaid")
        st.graphviz_chart(build_live_workflow_diagram(result.stage_events), use_container_width=True)
    with tabs[5]:
        for artifact in result.export_artifacts:
            st.download_button(
                label=f"Download {artifact.name}",
                data=artifact.content,
                file_name=artifact.name,
                mime="text/plain",
            )
    with tabs[6]:
        repo_path = st.text_input("Git repo path", value=str(REPO_ROOT))
        target_path = st.text_input(
            "Target file path",
            value=str(REPO_ROOT / f"{st.session_state.salesforce_class_name or 'AccountSyncService'}.cls"),
        )
        commit_message = st.text_input(
            "Commit message",
            value=f"Apply AI-generated fix for {st.session_state.salesforce_class_name or 'Salesforce class'}",
        )
        st.session_state.editable_class_body = st.text_area(
            "Patched Salesforce class",
            value=st.session_state.editable_class_body or st.session_state.salesforce_class_body,
            height=280,
        )
        col_patch, col_commit = st.columns(2)
        with col_patch:
            if st.button("Generate Smart Patch", use_container_width=True):
                ok, payload = generate_patch(
                    api_key=openrouter_api_key,
                    model=active_model,
                    class_name=st.session_state.salesforce_class_name,
                    original_body=st.session_state.salesforce_class_body,
                    result=result,
                )
                if ok:
                    st.session_state.editable_class_body = payload
                    st.session_state.generated_patch_diff = build_diff(
                        st.session_state.salesforce_class_body,
                        payload,
                        st.session_state.salesforce_class_name or "SalesforceClass.cls",
                    )
                    st.success("Generated a reviewed patch proposal.")
                else:
                    st.error(payload)
        with col_commit:
            if st.button("Commit Patched Class", use_container_width=True):
                ok, payload = commit_fixed_class(repo_path, target_path, st.session_state.editable_class_body, commit_message)
                st.session_state.git_status_message = payload
                if ok:
                    st.success(payload)
                else:
                    st.error(payload)
        if st.session_state.generated_patch_diff:
            st.code(st.session_state.generated_patch_diff, language="diff")
        if st.session_state.git_status_message:
            st.caption(st.session_state.git_status_message)


st.subheader("Follow-up Chat")
for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("Ask about the evidence, the fix, the report, or the Mermaid diagram..."):
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    answer = ask_followup(
        api_key=openrouter_api_key,
        model=active_model,
        question=prompt,
        result=st.session_state.analysis_result,
        class_body=st.session_state.salesforce_class_body,
    )
    st.session_state.chat_messages.append({"role": "assistant", "content": answer})
    st.rerun()
