import os
from langchain_openai import ChatOpenAI


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.environ.get("LLM_MODEL", "openai/gpt-4o"),
        temperature=0,
    )
