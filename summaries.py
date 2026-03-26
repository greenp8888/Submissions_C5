import json

from openrouter_client import call_openrouter
from storage import ChatData, ChatMessage, load_chat_from_file


def quick_summary_from_messages(messages: list[ChatMessage]) -> str:
    if not messages:
        return "No messages in this chat."
    user_msgs = len([m for m in messages if m.get("role") == "user"])
    assistant_msgs = len([m for m in messages if m.get("role") == "assistant"])
    first_msg = str(messages[0].get("content", ""))[:100]
    return (
        f"Quick summary: {user_msgs} user messages, {assistant_msgs} assistant responses. "
        f"Started with: {first_msg}..."
    )


def local_conversation_summary(messages: list[ChatMessage]) -> str:
    if not messages:
        return "No conversation summary available."

    user_messages = [str(m.get("content", "")) for m in messages if m.get("role") == "user"]
    assistant_messages = [str(m.get("content", "")) for m in messages if m.get("role") == "assistant"]

    first_user = user_messages[0][:180] if user_messages else ""
    last_user = user_messages[-1][:180] if user_messages else ""
    last_assistant = assistant_messages[-1][:220] if assistant_messages else ""

    lines = ["Conversation focused on the user's requests and assistant responses."]
    if first_user:
        lines.append(f"Started with user asking: {first_user}")
    if last_user and last_user != first_user:
        lines.append(f"Most recent user request: {last_user}")
    if last_assistant:
        lines.append(f"Latest assistant response: {last_assistant}")
    return "\n".join(lines)


def build_chat_export_text(
    chat_id: str,
    chat_data: ChatData,
    quick_summary_text: str,
    conversation_summary_text: str,
) -> str:
    lines = [
        f"Chat ID: {chat_id}",
        f"Chat Name: {chat_data.get('name', chat_id)}",
        f"Created: {chat_data.get('created', '')}",
        f"Model: {chat_data.get('model', '')}",
        "",
        "Summary",
        "-------",
        quick_summary_text or "No quick summary available.",
        "",
        "Conversation Summary",
        "--------------------",
        conversation_summary_text or local_conversation_summary(chat_data.get("messages", [])),
        "",
        "Messages",
        "--------",
    ]
    for i, message in enumerate(chat_data.get("messages", []), start=1):
        role = str(message.get("role", "unknown")).upper()
        content = message.get("content", "")
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        lines.append(f"{i}. {role}")
        lines.append(str(content))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def summarize_chat(chat_id: str, api_key: str, model: str) -> str:
    chat_data = load_chat_from_file(chat_id)
    messages = chat_data.get("messages", [])

    if not messages:
        return "No messages in this chat."

    summary_messages = [
        {
            "role": "system",
            "content": (
                "Summarize the conversation clearly in 4-6 bullet points. "
                "Include user goal, key decisions, open questions, and next steps."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(messages, ensure_ascii=False),
        },
    ]

    try:
        return call_openrouter(api_key, model, summary_messages, temperature=0.2)
    except RuntimeError:
        return f"Summary unavailable from API. {quick_summary_from_messages(messages)}"
