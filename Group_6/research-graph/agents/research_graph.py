"""
Multi-stage research LangGraph: retrieve -> analyze -> insights -> (optional re-retrieve) -> report.
"""

from __future__ import annotations

import json
import operator
import re
from typing import Annotated, Any, Literal, NotRequired, TypedDict

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.language_models.chat_models import BaseChatModel

from langgraph.graph import END, START, StateGraph

MAX_SOURCE_CHARS = 6000
MAX_SNIPPET_PER_SOURCE = 1200

GROUNDING_RULES = """
Grounding rules (mandatory):
- Base every factual claim on the Evidence bundle or prior tool outputs shown above. Do not invent studies, quotes, numbers, URLs, or named entities not present there.
- If the evidence does not support an answer, say so explicitly (e.g. "Not stated in the provided sources").
- Clearly label speculation or inference as such; keep it separate from sourced facts.
- Do not present generic domain knowledge as if it came from these sources unless you can tie it to a specific Source id or PDF excerpt.
"""

INSUFFICIENT_EVIDENCE_ANALYSIS = """## Summary
**Insufficient evidence:** There are no usable retrieved excerpts or tool results for this question (or tools returned only errors / no results). A grounded analysis cannot be produced.

## Contradictions
N/A — not enough sources to compare.

## Limitations
Re-run with a clearer question, add PDFs, enable Tavily, or check that Wikipedia/ArXiv are reachable."""

INSUFFICIENT_EVIDENCE_INSIGHTS = """No evidence-backed hypotheses can be formed without retrieved content. Broaden the question, upload relevant PDFs, or fix retrieval (network/API keys) before drawing conclusions.

{"next_queries": []}"""

INSUFFICIENT_EVIDENCE_REPORT = """# Executive overview
The pipeline did not obtain usable evidence (no PDF context and no successful tool results). This report cannot summarize verified findings.

# Key findings
None — **do not rely on any prior model output** when this section appears.

# Evidence and citations
No Source ids available.

# Contradictions and caveats
N/A

# Hypotheses and open questions
Re-run investigation after improving retrieval.

# Suggested next steps
- Add PDFs or a Tavily API key if web context is needed.
- Rephrase the research question.
- Confirm Ollama is running and tool-calling works for your model."""


def _evidence_usable(sources: list[dict[str, Any]], rag_snippets: str) -> bool:
    """True if we have non-trivial content that is not only NO_RESULTS/ERROR stubs."""
    if (rag_snippets or "").strip():
        return True
    for s in sources or []:
        if s.get("tool") in ("retrieval_note", "retrieval_fallback"):
            continue
        c = (s.get("content") or "").strip()
        if len(c) < 30:
            continue
        upper = c.upper()
        if upper.startswith("NO_RESULTS") or c.startswith("ERROR:"):
            continue
        return True
    return False


try:
    from ollama import ResponseError as _OllamaResponseError
except Exception:
    _OllamaResponseError = None


def _is_tool_call_parse_error(exc: BaseException) -> bool:
    """Ollama/LC error when the model emits prose instead of JSON tool calls."""
    if _OllamaResponseError is not None and isinstance(exc, _OllamaResponseError):
        return True
    msg = str(exc).lower()
    if "parsing tool call" in msg:
        return True
    if "tool call" in msg and "invalid character" in msg:
        return True
    if "error parsing tool" in msg:
        return True
    return False


def _invoke_search_tool(tool: Any, query: str) -> str:
    """Call a LangChain tool that expects a single `query` string."""
    q = (query or "").strip()
    if not q:
        return "ERROR: empty query"
    try:
        out = tool.invoke({"query": q})
    except Exception:
        try:
            out = tool.invoke(q)
        except Exception as e2:
            return f"ERROR: {e2}"
    return out if isinstance(out, str) else str(out)


def _direct_retrieval_sources(
    tools: list[Any], queries: list[str]
) -> list[dict[str, Any]]:
    """
    If the LLM agent cannot emit valid tool calls (common with some Ollama models),
    run Wikipedia / ArXiv / Tavily once per query string without the agent.
    """
    by_name = {getattr(t, "name", ""): t for t in tools if getattr(t, "name", None)}
    order = ["tavily_search", "wikipedia_search", "arxiv_search"]
    flat: list[str] = []
    for q in queries:
        q = str(q).strip()
        if q and q not in flat:
            flat.append(q)
    if not flat:
        flat = [""]

    rows: list[dict[str, Any]] = []
    n = 0
    for q in flat:
        if not q:
            continue
        for tool_name in order:
            t = by_name.get(tool_name)
            if t is None:
                continue
            content = _invoke_search_tool(t, q)
            n += 1
            rows.append(
                {
                    "id": f"s{n}",
                    "tool": tool_name,
                    "content": content[:MAX_SNIPPET_PER_SOURCE],
                }
            )

    if not rows:
        return [
            {
                "id": "s1",
                "tool": "retrieval_fallback",
                "content": "No search tools were available or every query string was empty.",
            }
        ]

    summary = (
        "Note: The model returned invalid tool-call JSON (common if the Ollama model is not "
        "strong at tool use). Search tools were run directly for: "
        + "; ".join(flat[:5])
    )
    note_row = {
        "id": "note-fallback",
        "tool": "retrieval_note",
        "content": summary[:MAX_SNIPPET_PER_SOURCE],
    }
    return [note_row] + rows


class ResearchState(TypedDict, total=False):
    """Shared state for the research pipeline."""

    user_query: str
    max_hops: NotRequired[int]
    hop_count: NotRequired[int]
    rag_snippets: NotRequired[str]
    sources: Annotated[list[dict[str, Any]], operator.add]
    analysis: NotRequired[str]
    insights: NotRequired[str]
    next_queries: NotRequired[list[str]]
    pending_subqueries: NotRequired[list[str]]
    report: NotRequired[str]


VERBATIM_EVIDENCE_TOOLS = frozenset(
    {"uploaded_pdf", "wikipedia_search", "arxiv_search", "tavily_search"}
)

META_SOURCE_TOOLS = frozenset({"retrieval_note", "retrieval_fallback"})


def partition_sources_for_display(
    sources: list[dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split sources for the UI: evidence excerpts vs pipeline metadata."""
    verbatim: list[dict[str, Any]] = []
    meta: list[dict[str, Any]] = []
    for s in sources or []:
        if not isinstance(s, dict):
            continue
        tool = str(s.get("tool") or "").strip()
        if tool in META_SOURCE_TOOLS:
            meta.append(s)
        else:
            verbatim.append(s)
    return verbatim, meta


def _rag_snippets_to_pdf_sources(rag_snippets: str) -> list[dict[str, Any]]:
    """Turn UI-built RAG text into source rows so PDFs appear alongside tool sources."""
    if not rag_snippets or not rag_snippets.strip():
        return []
    chunks = [c.strip() for c in rag_snippets.split("\n\n---\n\n") if c.strip()]
    if not chunks:
        chunks = [rag_snippets.strip()]
    out: list[dict[str, Any]] = []
    for i, ch in enumerate(chunks[:12]):
        out.append(
            {
                "id": f"pdf-{i + 1}",
                "tool": "uploaded_pdf",
                "content": ch[:MAX_SNIPPET_PER_SOURCE],
            }
        )
    return out


def _tool_messages_to_sources(messages: list) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    n = 0
    for msg in messages:
        if isinstance(msg, ToolMessage) and msg.name:
            n += 1
            content = (msg.content or "")[:MAX_SNIPPET_PER_SOURCE]
            out.append(
                {
                    "id": f"s{n}",
                    "tool": msg.name,
                    "content": content,
                }
            )
    return out


def _format_sources_for_llm(sources: list[dict[str, Any]], rag_snippets: str) -> str:
    parts: list[str] = []
    if rag_snippets and rag_snippets.strip():
        parts.append(
            "=== User-uploaded document context (RAG) ===\n"
            + rag_snippets.strip()[:MAX_SOURCE_CHARS]
        )
    total = len(parts[0]) if parts else 0
    for s in sources:
        t = s.get("tool")
        if t == "uploaded_pdf":
            continue
        if t in META_SOURCE_TOOLS:
            continue
        block = f"\n--- Source {s.get('id', '?')} via {s.get('tool', '?')} ---\n{s.get('content', '')}"
        if total + len(block) > MAX_SOURCE_CHARS:
            parts.append("\n... [truncated additional sources]")
            break
        parts.append(block)
        total += len(block)
    return "\n".join(parts) if parts else "(No retrieved sources yet.)"


def _parse_next_queries(text: str) -> list[str]:
    """Parse a trailing JSON object {"next_queries": [...]} from model output."""
    try:
        m = re.search(r"\{[\s\S]*\"next_queries\"[\s\S]*\}\s*$", text.strip())
        if not m:
            return []
        obj = json.loads(m.group(0))
        nq = obj.get("next_queries") or []
        if isinstance(nq, list):
            return [str(x).strip() for x in nq if str(x).strip()][:5]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def _strip_json_trailer(text: str) -> str:
    """Remove trailing JSON block from insights display text."""
    m = re.search(r"\n*\{[\s\S]*\"next_queries\"[\s\S]*\}\s*$", text.strip())
    if m:
        return text[: m.start()].strip()
    return text.strip()


RETRIEVAL_SYSTEM = """You are the Contextual Retriever Agent.

The user message may start with "Excerpts from user-uploaded PDFs". Those excerpts are the user's own documents—treat them as first-class evidence for the question. Compare and combine them with external tools where useful.

You have search tools: use them to add definitions, papers, or news. Wikipedia for encyclopedic facts, arxiv for research papers, tavily for current events when available.

If PDF excerpts already answer much of the question, still run tools when they add authoritative external context (e.g. standard definitions, related work). When done, reply with a brief 1–2 sentence summary of what you found (tools will have run already).

Anti-hallucination: Never fabricate tool results or URLs. Your closing summary must only paraphrase what the tools actually returned (including NO_RESULTS/ERROR lines). Do not fill gaps with guessed facts.

Tool-calling discipline: When you call a tool, arguments must be valid JSON only (e.g. {"query": "your search text"}). Do not put reasoning, planning, or long prose where a tool call is expected—Ollama will fail to parse it."""


def build_research_graph(
    llm: BaseChatModel,
    tools: list,
    *,
    retrieval_llm: BaseChatModel | None = None,
    strict_grounding: bool = True,
) -> Any:
    """
    Compile the research pipeline. If retrieval_llm is None, uses `llm` for retrieval agent.

    If strict_grounding is True, analyze/insights/report skip the LLM when there is no usable
    evidence, avoiding invented summaries.
    """
    r_llm = retrieval_llm or llm
    retrieval_agent = create_agent(r_llm, tools, system_prompt=RETRIEVAL_SYSTEM)

    def seed_pdf_sources(state: ResearchState) -> dict[str, Any]:
        """LangGraph node: register uploaded PDF chunks as sources before tool retrieval."""
        pdf_src = _rag_snippets_to_pdf_sources(state.get("rag_snippets") or "")
        if not pdf_src:
            return {}
        return {"sources": pdf_src}

    def retrieve(state: ResearchState) -> dict[str, Any]:
        hop = int(state.get("hop_count") or 0)
        pending = state.get("pending_subqueries") or []
        user_q = state.get("user_query") or ""
        rag = (state.get("rag_snippets") or "").strip()
        rag_prefix = ""
        if rag:
            rag_prefix = (
                "=== Excerpts from user-uploaded PDFs (primary user-provided evidence) ===\n"
                f"{rag[:12000]}\n"
                "=== End PDF excerpts ===\n\n"
            )
        if pending:
            qtext = (
                rag_prefix
                + "Run targeted searches for these sub-questions (use the best tool for each):\n"
                + "\n".join(f"- {q}" for q in pending)
            )
        else:
            qtext = (
                rag_prefix
                + f"Research question:\n{user_q}\n\n"
                + "Gather relevant information: prioritize the PDF excerpts above when they apply, "
                + "and use tools to complement with external sources."
            )

        try:
            result = retrieval_agent.invoke({"messages": [HumanMessage(content=qtext)]})
            messages = result.get("messages") or []
            new_sources = _tool_messages_to_sources(messages)
        except Exception as e:
            if not _is_tool_call_parse_error(e):
                raise
            qs = [str(q).strip() for q in (pending or [user_q]) if str(q).strip()][:5]
            if not qs:
                qs = [user_q.strip()] if user_q.strip() else []
            new_sources = _direct_retrieval_sources(tools, qs)

        updates: dict[str, Any] = {
            "sources": new_sources,
            "hop_count": hop + 1,
            "pending_subqueries": [],
        }
        return updates

    def analyze(state: ResearchState) -> dict[str, Any]:
        sources = state.get("sources") or []
        rag = state.get("rag_snippets") or ""
        bundle = _format_sources_for_llm(sources, rag)
        if strict_grounding and not _evidence_usable(sources, rag):
            return {"analysis": INSUFFICIENT_EVIDENCE_ANALYSIS}
        prompt = f"""You are the Critical Analysis Agent.

Research question:
{state.get("user_query", "")}

Evidence bundle:
{bundle}

{GROUNDING_RULES}

Tasks:
1) Summarize only claims that are explicitly supported by the evidence above; cite Source ids when possible.
2) Note any contradictions or tensions between sources.
3) Comment briefly on limitations (single-source claims, missing angles, etc.).

Write clear markdown sections: ## Summary, ## Contradictions, ## Limitations."""
        out = llm.invoke([HumanMessage(content=prompt)])
        content = out.content if isinstance(out.content, str) else str(out.content)
        return {"analysis": content}

    def insights(state: ResearchState) -> dict[str, Any]:
        sources = state.get("sources") or []
        rag = state.get("rag_snippets") or ""
        bundle = _format_sources_for_llm(sources, rag)
        if strict_grounding and not _evidence_usable(sources, rag):
            text = INSUFFICIENT_EVIDENCE_INSIGHTS
            nq = _parse_next_queries(text)
            display = _strip_json_trailer(text)
            return {
                "insights": display,
                "next_queries": nq,
                "pending_subqueries": nq,
            }
        prompt = f"""You are the Insight Generation Agent.

Research question:
{state.get("user_query", "")}

Prior analysis:
{state.get("analysis", "")}

Evidence bundle (abbreviated):
{bundle[:8000]}

{GROUNDING_RULES}

Tasks:
1) Propose 2–4 testable hypotheses or trends grounded only in the evidence (mark uncertainty clearly).
2) List 2–5 concrete follow-up search queries that would reduce uncertainty (or empty list if none needed).
3) End your response with ONLY a JSON object on the last line, no markdown fences, like:
{{"next_queries": ["query one", "query two"]}}

Use [] for next_queries if no further retrieval is needed."""
        out = llm.invoke([HumanMessage(content=prompt)])
        text = out.content if isinstance(out.content, str) else str(out.content)
        nq = _parse_next_queries(text)
        display = _strip_json_trailer(text)
        return {
            "insights": display,
            "next_queries": nq,
            "pending_subqueries": nq,
        }

    def report(state: ResearchState) -> dict[str, Any]:
        sources = state.get("sources") or []
        rag = state.get("rag_snippets") or ""
        bundle = _format_sources_for_llm(sources, rag)
        if strict_grounding and not _evidence_usable(sources, rag):
            return {"report": INSUFFICIENT_EVIDENCE_REPORT}
        prompt = f"""You are the Report Builder Agent.

Compile a professional markdown report for the user.

Research question:
{state.get("user_query", "")}

Critical analysis:
{state.get("analysis", "")}

Insights:
{state.get("insights", "")}

Source excerpts (reference by Source id when citing):
{bundle[:12000]}

{GROUNDING_RULES}

Produce sections:
# Executive overview
# Key findings
# Evidence and citations (every factual bullet should tie to a Source id or uploaded PDF context; omit claims you cannot cite)
# Contradictions and caveats
# Hypotheses and open questions
# Suggested next steps"""
        out = llm.invoke([HumanMessage(content=prompt)])
        content = out.content if isinstance(out.content, str) else str(out.content)
        return {"report": content}

    def route_after_insights(state: ResearchState) -> Literal["retrieve", "report"]:
        nq = state.get("next_queries") or []
        hops = int(state.get("hop_count") or 0)
        max_h = int(state.get("max_hops") or 2)
        if nq and hops < max_h:
            return "retrieve"
        return "report"

    workflow = StateGraph(ResearchState)
    workflow.add_node("seed_pdf", seed_pdf_sources)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("analyze", analyze)
    workflow.add_node("insights", insights)
    workflow.add_node("report", report)

    workflow.add_edge(START, "seed_pdf")
    workflow.add_edge("seed_pdf", "retrieve")
    workflow.add_edge("retrieve", "analyze")
    workflow.add_edge("analyze", "insights")
    workflow.add_conditional_edges(
        "insights", route_after_insights, {"retrieve": "retrieve", "report": "report"}
    )
    workflow.add_edge("report", END)

    return workflow.compile()


def _initial_state(user_query: str, max_hops: int, rag_snippets: str) -> ResearchState:
    initial: ResearchState = {
        "user_query": user_query,
        "max_hops": max_hops,
        "hop_count": 0,
    }
    if rag_snippets:
        initial["rag_snippets"] = rag_snippets
    return initial


def run_investigation(
    graph: Any,
    *,
    user_query: str,
    max_hops: int = 2,
    rag_snippets: str = "",
) -> ResearchState:
    """Single invoke; returns final state dict."""
    return graph.invoke(_initial_state(user_query, max_hops, rag_snippets))


def stream_investigation(
    graph: Any,
    *,
    user_query: str,
    max_hops: int = 2,
    rag_snippets: str = "",
):
    """Yields stream chunks (stream_mode='updates') for UI progress."""
    yield from graph.stream(
        _initial_state(user_query, max_hops, rag_snippets), stream_mode="updates"
    )


def build_retrieval_tools(tavily_api_key: str | None):
    """
    LangChain tools for the Contextual Retriever agent (no Streamlit dependencies).
    """
    from langchain_core.tools import tool
    from tavily import TavilyClient
    import wikipedia
    import arxiv

    @tool
    def wikipedia_search(query: str) -> str:
        """Search Wikipedia for encyclopedic information: people, places, history, science concepts."""
        try:
            wikipedia.set_lang("en")
            search_results = wikipedia.search(query, results=3)
            if not search_results:
                search_results = wikipedia.search(
                    " ".join(query.split()[:3]), results=3
                )
            if not search_results:
                return "NO_RESULTS: No Wikipedia articles found."
            for article_name in search_results:
                try:
                    page = wikipedia.page(article_name)
                    summary = wikipedia.summary(article_name, sentences=4)
                    return f"Wikipedia: {page.title}\n\n{summary}\n\nSource: {page.url}"
                except wikipedia.exceptions.DisambiguationError as e:
                    if e.options:
                        try:
                            page = wikipedia.page(e.options[0])
                            summary = wikipedia.summary(e.options[0], sentences=4)
                            return f"Wikipedia: {page.title}\n\n{summary}\n\nSource: {page.url}"
                        except Exception:
                            continue
                except wikipedia.exceptions.PageError:
                    continue
            return "NO_RESULTS: Wikipedia pages not accessible."
        except Exception as e:
            return f"ERROR: {str(e)}"

    @tool
    def arxiv_search(query: str) -> str:
        """Search ArXiv for academic papers and technical research."""
        try:
            client = arxiv.Client()
            search = arxiv.Search(
                query=query, max_results=5, sort_by=arxiv.SortCriterion.Relevance
            )
            results_list = list(client.results(search))
            if not results_list:
                simplified = " ".join(query.replace('"', "").split()[:5])
                search = arxiv.Search(
                    query=simplified,
                    max_results=5,
                    sort_by=arxiv.SortCriterion.Relevance,
                )
                results_list = list(client.results(search))
            if not results_list:
                return "NO_RESULTS: No papers found on ArXiv."
            formatted = []
            for i, result in enumerate(results_list, 1):
                authors = ", ".join([a.name for a in result.authors[:3]])
                formatted.append(
                    f"{i}. {result.title}\nAuthors: {authors}\n"
                    f"Published: {result.published.strftime('%Y-%m-%d')}\n"
                    f"Abstract: {result.summary[:300]}...\n"
                )
            return "\n".join(formatted)
        except Exception as e:
            return f"ERROR: {str(e)}"

    tools: list = [wikipedia_search, arxiv_search]
    key = (tavily_api_key or "").strip()
    if key:
        tavily_client = TavilyClient(api_key=key)

        @tool
        def tavily_search(query: str) -> str:
            """Search the web for current events, news, weather, or time-sensitive information."""
            try:
                response = tavily_client.search(query)
                results = response.get("results", [])
                if not results:
                    return "NO_RESULTS: No search results found."
                formatted_results = []
                for i, result in enumerate(results[:5], 1):
                    title = result.get("title", "No title")
                    content = result.get("content", "No content")
                    url = result.get("url", "No URL")
                    formatted_results.append(f"{i}. {title}\n{content}\n")
                return "\n".join(formatted_results)
            except Exception as e:
                return f"ERROR: {str(e)}"

        tools = [tavily_search, wikipedia_search, arxiv_search]
    return tools
