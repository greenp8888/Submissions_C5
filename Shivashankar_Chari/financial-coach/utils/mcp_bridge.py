from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _mcp_server_path() -> Path:
    return _project_root() / "mcp_server.py"


def _load_mcp_server_module() -> Any:
    server_path = _mcp_server_path()

    if not server_path.exists():
        raise FileNotFoundError(f"mcp_server.py not found at: {server_path}")

    spec = importlib.util.spec_from_file_location(
        "financial_coach_mcp_server",
        server_path,
    )
    if spec is None or spec.loader is None:
        raise ImportError("Could not load spec for mcp_server.py")

    module = importlib.util.module_from_spec(spec)
    sys.modules["financial_coach_mcp_server"] = module
    spec.loader.exec_module(module)
    return module


def _normalize_result(result: Any, tool_name: str) -> Dict[str, Any]:
    if isinstance(result, dict):
        normalized = dict(result)
    else:
        normalized = {
            "status": "ok",
            "result": result,
        }

    normalized.setdefault("tool_name", tool_name)
    normalized.setdefault("name", tool_name)
    normalized.setdefault("source", "mcp_server")
    return normalized


def _call_tool(module: Any, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
    if not hasattr(module, tool_name):
        return {
            "tool_name": tool_name,
            "name": tool_name,
            "source": "mcp_server",
            "status": "error",
            "message": f"Tool '{tool_name}' not found in mcp_server.py",
        }

    tool_fn = getattr(module, tool_name)

    try:
        result = tool_fn(**kwargs)
        return _normalize_result(result, tool_name)
    except Exception as exc:
        return {
            "tool_name": tool_name,
            "name": tool_name,
            "source": "mcp_server",
            "status": "error",
            "message": str(exc),
        }


def run_mcp_financial_probe(
    records: List[Dict[str, Any]],
    monthly_income: float,
    primary_goal: str,
) -> Dict[str, Any]:
    """
    Run MCP-backed financial tools from mcp_server.py and return a UI-friendly payload.

    This payload intentionally includes multiple tool-call shapes so downstream
    Streamlit code can detect tool execution regardless of which extractor path it uses.
    """

    if not records:
        return {
            "status": "empty",
            "source": "external_mcp_probe",
            "message": "No transaction records supplied.",
            "server_file": str(_mcp_server_path()),
            "tools_called": [],
            "tool_calls": [],
            "invocations": [],
            "executed_tools": [],
        }

    try:
        module = _load_mcp_server_module()
    except Exception as exc:
        return {
            "status": "error",
            "source": "external_mcp_probe",
            "message": f"Failed to load MCP server module: {exc}",
            "server_file": str(_mcp_server_path()),
            "tools_called": [],
            "tool_calls": [],
            "invocations": [],
            "executed_tools": [],
        }

    summary_result = _call_tool(
        module,
        "summarize_transactions",
        records=records,
    )

    debt_result = _call_tool(
        module,
        "analyze_debt_pressure",
        records=records,
        monthly_income=monthly_income,
    )

    savings_result = _call_tool(
        module,
        "savings_plan",
        records=records,
        monthly_income=monthly_income,
        primary_goal=primary_goal,
    )

    tool_results = [
        summary_result,
        debt_result,
        savings_result,
    ]

    tools_called = [item.get("tool_name", "unknown_tool") for item in tool_results]

    if all(item.get("status") == "ok" for item in tool_results):
        overall_status = "ok"
    elif any(item.get("status") == "ok" for item in tool_results):
        overall_status = "partial_error"
    else:
        overall_status = "error"

    return {
        "status": overall_status,
        "source": "external_mcp_probe",
        "server_file": str(_mcp_server_path()),
        "message": "MCP financial probe completed.",
        # Flat tool keys
        "summarize_transactions": summary_result,
        "analyze_debt_pressure": debt_result,
        "savings_plan": savings_result,
        # Multiple call-shape variants for UI extractors
        "tools_called": tools_called,
        "tool_calls": tool_results,
        "invocations": tool_results,
        "executed_tools": tool_results,
        # Optional high-level summary block
        "summary": {
            "tools_attempted": len(tool_results),
            "tools_succeeded": sum(1 for item in tool_results if item.get("status") == "ok"),
            "tools_failed": sum(1 for item in tool_results if item.get("status") != "ok"),
        },
    }