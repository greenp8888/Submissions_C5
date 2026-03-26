import json
from socket import timeout as SocketTimeout
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
REQUEST_TIMEOUT_SECONDS = 30


def _extract_text_content(content: Any) -> str:
    if isinstance(content, list):
        return "".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        ).strip()
    return str(content).strip()


def call_openrouter(
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float | None = None,
) -> str:
    payload_data = {
        "model": model,
        "messages": messages,
    }
    if temperature is not None:
        payload_data["temperature"] = temperature

    request = Request(
        url=OPENROUTER_URL,
        data=json.dumps(payload_data).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            res = json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        try:
            details = e.read().decode("utf-8")
        except Exception:
            details = ""
        raise RuntimeError(f"OpenRouter HTTP {e.code}. {details[:300]}".strip())
    except (URLError, SocketTimeout) as e:
        raise RuntimeError(f"OpenRouter connection failed: {e}")
    except ValueError:
        raise RuntimeError("OpenRouter returned invalid JSON.")

    if "choices" not in res or not res["choices"]:
        error_msg = ""
        if isinstance(res.get("error"), dict):
            error_msg = res["error"].get("message", "")
        raise RuntimeError(f"OpenRouter returned no choices. {error_msg}".strip())

    try:
        return _extract_text_content(res["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError):
        raise RuntimeError("OpenRouter response format was unexpected.")
