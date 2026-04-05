"""Retrieval tools for the Multi-Agent Researcher."""

from multi_agent_researcher.tools.arxiv_tools import search_arxiv
from multi_agent_researcher.tools.tavily_tools import tavily_web_search
from multi_agent_researcher.tools.wikipedia_tools import wikipedia_search
from multi_agent_researcher.tools.serpapi_tools import google_search
from multi_agent_researcher.tools.pdf_tools import load_pdf_document

ALL_TOOLS = [
    search_arxiv,
    tavily_web_search,
    wikipedia_search,
    google_search,
    load_pdf_document,
]

__all__ = [
    "search_arxiv",
    "tavily_web_search",
    "wikipedia_search",
    "google_search",
    "load_pdf_document",
    "ALL_TOOLS",
]
