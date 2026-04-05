"""
Python bridge: called by the Node.js server via child_process.
Reads JSON config from argv[1], streams JSON events to stdout.
"""
import sys
import json
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.file_parser import parse_financial_file
from utils.llm_config import validate_model
from agents.orchestrator import stream_financial_coach


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"type": "error", "message": "No config provided"}), flush=True)
        sys.exit(1)

    config = json.loads(sys.argv[1])

    # Set environment variables from config
    if config.get("openrouter_key"):
        os.environ["OPENROUTER_API_KEY"] = config["openrouter_key"]
    if config.get("tavily_key"):
        os.environ["TAVILY_API_KEY"] = config["tavily_key"]
    model_id = config.get("model", "openai/gpt-4o-mini")
    os.environ["PRIMARY_MODEL"] = model_id

    file_path = config.get("file_path")
    user_goals = config.get("goals", "")
    location = config.get("location", "")

    # ── Pre-flight: verify the selected model has active endpoints ────────────
    # A tiny 1-token call; fails instantly on 404, <3s for valid models.
    model_err = validate_model(model_id)
    if model_err:
        print(json.dumps({"type": "error", "message": model_err}), flush=True)
        sys.exit(1)

    # Parse the uploaded file
    try:
        raw_data = parse_financial_file(file_path)
    except Exception as e:
        print(json.dumps({"type": "error", "message": f"File parse error: {str(e)}"}), flush=True)
        sys.exit(1)

    # Stream pipeline events
    try:
        for event in stream_financial_coach(raw_data=raw_data, user_goals=user_goals, location=location):
            if event.get("type") == "done":
                result = event.get("result", {})
                result = dict(result)

                # Strip raw_data — contains raw_dataframe with pandas/numpy types
                result.pop("raw_data", None)

                # Strip raw_dataframe from financial_snapshot if it leaked in
                snap = result.get("financial_snapshot") or {}
                if "raw_dataframe" in snap:
                    result["financial_snapshot"] = {k: v for k, v in snap.items() if k != "raw_dataframe"}

                # Safety: use default=str so any residual numpy/pandas types don't crash
                print(json.dumps({"type": "done", "result": result}, default=str), flush=True)
            else:
                print(json.dumps(event, default=str), flush=True)
    except Exception as e:
        print(json.dumps({"type": "error", "message": str(e)}), flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
