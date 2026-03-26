import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict, NotRequired

CHAT_SESSIONS_DIR = Path("chat_sessions")
CHAT_SESSIONS_DIR.mkdir(exist_ok=True)


class ChatMessage(TypedDict):
    role: str
    content: Any


class ChatData(TypedDict):
    messages: list[ChatMessage]
    created: str
    model: str
    name: NotRequired[str]
    summary: NotRequired[str]


def _default_chat_data() -> ChatData:
    return {
        "messages": [],
        "created": datetime.now().isoformat(),
        "model": "openai/gpt-3.5-turbo",
    }


def load_chat_from_file(chat_id: str) -> ChatData:
    chat_file = CHAT_SESSIONS_DIR / f"{chat_id}.json"
    if chat_file.exists():
        try:
            with open(chat_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return _default_chat_data()
            data.setdefault("messages", [])
            data.setdefault("created", datetime.now().isoformat())
            data.setdefault("model", "openai/gpt-3.5-turbo")
            return data  # type: ignore[return-value]
        except (json.JSONDecodeError, OSError):
            return _default_chat_data()
    return _default_chat_data()


def save_chat_to_file(chat_id: str, chat_data: ChatData) -> None:
    chat_file = CHAT_SESSIONS_DIR / f"{chat_id}.json"
    temp_file = chat_file.with_suffix(f"{chat_file.suffix}.tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(chat_data, f, indent=2, ensure_ascii=False)
    temp_file.replace(chat_file)


def load_all_chats() -> list[str]:
    chat_files = list(CHAT_SESSIONS_DIR.glob("*.json"))
    return sorted([f.stem for f in chat_files], reverse=True)


def create_new_chat(selected_model: str, chat_name: str | None = None) -> str:
    chat_id = str(uuid.uuid4())[:8]
    if chat_name:
        chat_id = f"{chat_name}_{chat_id}"

    chat_data: ChatData = {
        "messages": [],
        "created": datetime.now().isoformat(),
        "model": selected_model,
        "name": chat_name or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    }
    save_chat_to_file(chat_id, chat_data)
    return chat_id


def delete_chat_file(chat_id: str) -> None:
    chat_file = CHAT_SESSIONS_DIR / f"{chat_id}.json"
    if chat_file.exists():
        chat_file.unlink()


def get_chat_mtime_ns(chat_id: str) -> int:
    chat_file = CHAT_SESSIONS_DIR / f"{chat_id}.json"
    if chat_file.exists():
        try:
            return chat_file.stat().st_mtime_ns
        except OSError:
            return 0
    return 0


def get_chats_version() -> int:
    try:
        chat_files = list(CHAT_SESSIONS_DIR.glob("*.json"))
        if not chat_files:
            return 0
        max_mtime = max(f.stat().st_mtime_ns for f in chat_files)
        return max_mtime ^ len(chat_files)
    except OSError:
        return 0
