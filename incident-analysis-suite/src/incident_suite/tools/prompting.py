from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from incident_suite.tools.llm import build_llm


def render_prompt(system_prompt: str, human_prompt: str) -> list:
    template = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", human_prompt),
        ]
    )
    rendered = template.invoke({})
    return rendered.to_messages()


def ask_llm(system_prompt: str, human_prompt: str, fallback: str = "") -> str:
    llm = build_llm()
    if llm is None:
        return fallback
    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]
        return llm.invoke(messages).content  # type: ignore[return-value]
    except Exception:
        return fallback
