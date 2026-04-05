import ast
import os
import re
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def _extract_candidate(text: str) -> str:
    """Extract the outermost JSON object via brace matching."""
    start = text.find('{')
    if start == -1:
        raise ValueError("No JSON object found in LLM response")
    depth, end, in_string, escape_next = 0, -1, False, False
    for i, ch in enumerate(text[start:], start):
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = i
                break
    return text[start:end + 1] if end != -1 else text[start:]


def _clean_json(text: str) -> str:
    """Remove JS-style syntax issues from a JSON-like string."""
    text = re.sub(r'//[^\n"]*(?=\n|$)', '', text)   # line comments
    text = re.sub(r'/\*[\s\S]*?\*/', '', text)        # block comments
    text = re.sub(r',\s*([}\]])', r'\1', text)        # trailing commas
    return text


def parse_llm_json(text: str) -> dict:
    """
    Robustly extract and parse a JSON object from LLM output.
    Attempts (in order):
      1. Direct json.loads
      2. Strip markdown fences, then json.loads
      3. Brace-matched extraction + json.loads
      4. Clean trailing commas / JS comments + json.loads
      5. ast.literal_eval (handles single-quoted strings & trailing commas)
      6. Quote unquoted keys + json.loads
    """
    text = text.strip()

    # Pass 1 – raw
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Pass 2 – strip markdown fences
    text = re.sub(r'^```[a-zA-Z]*\n?', '', text)
    text = re.sub(r'\n?```\s*$', '', text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Pass 3 – extract outermost object
    candidate = _extract_candidate(text)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Pass 4 – clean JS issues
    cleaned = _clean_json(candidate)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Pass 5 – ast.literal_eval (handles single-quoted strings, trailing commas)
    try:
        py_text = re.sub(r'\btrue\b',  'True',  cleaned)
        py_text = re.sub(r'\bfalse\b', 'False', py_text)
        py_text = re.sub(r'\bnull\b',  'None',  py_text)
        result = ast.literal_eval(py_text)
        if isinstance(result, dict):
            # Round-trip through json to normalise types (None→null etc.)
            return json.loads(json.dumps(result))
    except Exception:
        pass

    # Pass 6 – quote unquoted keys  {key: val} → {"key": val}
    try:
        fixed = re.sub(r'(?<=[{,])\s*([a-zA-Z_]\w*)\s*(?=\s*:)', r'"\1"', cleaned)
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    raise ValueError(f"Could not parse LLM response as JSON after all attempts")

_OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://github.com/eng-accelerator/Submissions_C5",
    "X-Title": "AI Financial Coach - Group 19",
}


def get_llm(model: str = None, temperature: float = 0.1):
    """Returns an LLM connected to OpenRouter."""
    return ChatOpenAI(
        model=model or os.getenv("PRIMARY_MODEL", "openai/gpt-4o-mini"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        temperature=temperature,
        default_headers=_OPENROUTER_HEADERS,
    )


def get_fast_llm():
    """Cheap model for non-critical tasks."""
    return get_llm(model=os.getenv("FAST_MODEL", "google/gemini-flash-1.5"))


def is_model_unavailable(exc: Exception) -> bool:
    """
    Returns True when the exception clearly means the model ID has no
    active endpoints on OpenRouter (HTTP 404 / 'No endpoints found').
    """
    msg = str(exc)
    return (
        "404" in msg
        or "No endpoints found" in msg
        or "model_not_found" in msg.lower()
    )


def is_rate_limited(exc: Exception) -> bool:
    """Returns True when OpenRouter returns a 429 rate-limit error."""
    msg = str(exc)
    return "429" in msg or "rate_limit" in msg.lower() or "limit_rpm" in msg.lower()


def validate_model(model_id: str) -> str | None:
    """
    Sends a minimal single-token request to verify the model is reachable.
    Returns None on success, or a human-readable error string if the model
    is not available.  Rate-limit (429) and auth errors return None so the
    pipeline can surface them naturally per-agent.
    """
    try:
        llm = ChatOpenAI(
            model=model_id,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            temperature=0.0,
            max_tokens=1,
            default_headers=_OPENROUTER_HEADERS,
        )
        llm.invoke([("user", "hi")])
        return None
    except Exception as exc:
        if is_model_unavailable(exc):
            return (
                f"Model '{model_id}' has no active endpoints on OpenRouter. "
                f"Please select a different model in Config → AI Model."
            )
        # 429 rate-limit, auth errors, etc. — model exists, let agents handle
        return None


def llm_invoke(llm, messages, max_retries: int = 3):
    """
    Invoke the LLM with:
      - Proactive rate-limit throttle for :free models — sleeps
        RATE_LIMIT_DELAY_SECONDS (default 10) before every call so 5 LLM
        agents at 10 s spacing = 6 RPM, comfortably under the 8 RPM cap.
      - Reactive retry on 429 — waits 15 × attempt seconds (15 / 30 / 45 s)
        and retries up to max_retries times.
      - Re-raises immediately on any non-rate-limit error (404, auth, etc.)
    """
    import time

    model_name = getattr(llm, "model_name", None) or getattr(llm, "model", "") or ""
    is_free = model_name.endswith(":free")

    # Proactive sleep for free models — keeps pipeline well under 8 RPM
    if is_free:
        delay = float(os.getenv("RATE_LIMIT_DELAY_SECONDS", "10"))
        if delay > 0:
            time.sleep(delay)

    last_exc = None
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages)
        except Exception as exc:
            if is_rate_limited(exc):
                wait = 15 * (attempt + 1)
                last_exc = exc
                time.sleep(wait)
            else:
                raise
    raise last_exc