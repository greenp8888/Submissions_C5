"""
research_engine.py
Orchestrates all specialized agents: Retriever, Critical Analysis,
Insight Generation, Fact-Check, and Report Builder.

Python 3.14+ compatible:
  - No 'from __future__ import annotations' (PEP 563 was withdrawn; PEP 649
    is the 3.14 default — annotations are evaluated lazily at use-site, so
    the __future__ shim is both unnecessary and potentially misleading).
  - Built-in generic aliases (list, dict) used directly in annotations.
  - X | Y union syntax used directly (valid since 3.10, no shim needed).
  - No mutable default arguments.
  - typing.Any retained (still the correct spelling for untyped positions).

Concurrency model (Agent 1):
  - The main query is decomposed into 3 angle-based sub-queries.
  - All sub-queries are submitted to Tavily simultaneously via
    ThreadPoolExecutor, alongside all PDF extractions.
  - Results are merged and deduplicated by URL before the LLM synthesis step.
  - Wall-clock time for Agent 1 drops from O(N) to O(1) relative to the
    number of searches, bounded only by the slowest individual request.
"""

import re
import concurrent.futures
from typing import Any

import requests

# ── Local HuggingFace RAG (optional — degrades gracefully if not installed) ──
from rag import RAGIndex, build_rag_index, RAG_AVAILABLE, DEFAULT_EMBED_MODEL

# ── Optional PDF support ──────────────────────────────────────────────────────
try:
    import pypdf
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Maximum worker threads for concurrent I/O.  Tavily + PDF tasks are all
# network/disk-bound so a generous thread count is safe.
_MAX_WORKERS = 10


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _llm(
    messages: list[dict[str, str]],
    openrouter_key: str,
    model: str,
    max_tokens: int = 1500,
    system: str | None = None,
) -> str:
    """Call OpenRouter /chat/completions and return the assistant text."""
    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system:
        payload["messages"] = [{"role": "system", "content": system}] + messages

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://deep-research-assistant.app",
            "X-Title": "DeepResearch Assistant",
        },
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def _tavily_search(query: str, tavily_key: str, max_results: int = 7) -> list[dict[str, Any]]:
    """
    Search Tavily for a single query and return a list of result dicts.
    Tavily's synthesised answer (if present) is prepended as a pseudo-result
    so downstream agents can reference it.
    """
    resp = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": tavily_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": False,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    results: list[dict[str, Any]] = data.get("results", [])
    if data.get("answer"):
        results.insert(0, {
            "title": f"Tavily Answer — {query[:60]}",
            "url": f"tavily://answer/{query[:40].replace(' ', '-')}",
            "content": data["answer"],
            "score": 1.0,
        })
    return results


def _tavily_search_concurrent(
    queries: list[str],
    tavily_key: str,
    max_results_per_query: int = 7,
) -> list[dict[str, Any]]:
    """
    Fire all *queries* against Tavily simultaneously using a thread pool.

    Returns a deduplicated, score-sorted list of results.  URLs that appear
    in more than one query's results are kept only once (highest-score copy).

    Args:
        queries:               List of search strings to run in parallel.
        tavily_key:            Tavily API key.
        max_results_per_query: Max results requested per individual query.

    Returns:
        Merged, deduplicated list sorted by score descending.
    """
    all_results: list[dict[str, Any]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
        future_to_query = {
            pool.submit(_tavily_search, q, tavily_key, max_results_per_query): q
            for q in queries
        }
        for future in concurrent.futures.as_completed(future_to_query):
            query = future_to_query[future]
            try:
                results = future.result()
                # Tag each result with which sub-query produced it
                for r in results:
                    r.setdefault("_source_query", query)
                all_results.extend(results)
            except Exception as exc:
                # Partial failure: record a placeholder so the digest mentions
                # the failed sub-query rather than silently dropping it.
                all_results.append({
                    "title": f"[Search failed] {query[:80]}",
                    "url": "tavily://error",
                    "content": f"Search error for query '{query}': {exc}",
                    "score": 0.0,
                    "_source_query": query,
                })

    # Deduplicate by URL, keeping the highest-score entry for each URL.
    seen: dict[str, dict[str, Any]] = {}
    for r in all_results:
        url = r.get("url", "")
        if url not in seen or r.get("score", 0) > seen[url].get("score", 0):
            seen[url] = r

    return sorted(seen.values(), key=lambda r: r.get("score", 0), reverse=True)


def _build_sub_queries(query: str, extra_context: str) -> list[str]:
    """
    Decompose the user query into 3 complementary search angles:
      1. The query as-is (or with extra context appended).
      2. A "latest research / recent developments" variant.
      3. A "criticism / challenges / limitations" variant.

    Running these concurrently gives broader coverage than a single search
    without requiring an extra LLM call to plan the queries.
    """
    base = f"{query}. {extra_context[:200]}" if extra_context else query
    return [
        base,
        f"{query} latest research recent developments 2024 2025",
        f"{query} challenges limitations criticism controversies",
    ]


def _extract_pdf_text(file_obj: Any) -> str:
    """Extract text from a PDF file-like object using pypdf."""
    if not PDF_SUPPORT:
        return "[PDF support unavailable — install pypdf]"
    try:
        reader = pypdf.PdfReader(file_obj)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)[:8000]  # cap to avoid context overflow
    except Exception as exc:
        return f"[Error reading PDF: {exc}]"


def _extract_pdfs_concurrent(pdf_files: list[Any]) -> list[str]:
    """
    Extract text from all PDFs simultaneously via a thread pool.

    Each PDF is opened in its own thread.  The GIL is not a bottleneck here
    because pypdf spends most of its time in I/O and byte-decoding.

    Returns a list of non-empty extracted text strings, one per PDF.
    """
    if not pdf_files:
        return []

    results: list[str] = []

    def _extract_one(pdf: Any) -> str | None:
        text = _extract_pdf_text(pdf)
        name = getattr(pdf, "name", "document")
        if text.strip():
            return f"[PDF: {name}]\n{text}"
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
        futures = [pool.submit(_extract_one, pdf) for pdf in pdf_files]
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                if result:
                    results.append(result)
            except Exception as exc:
                results.append(f"[PDF extraction error: {exc}]")

    return results


def _count_re(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, re.IGNORECASE | re.MULTILINE))


# ─────────────────────────────────────────────────────────────────────────────
# ResearchEngine
# ─────────────────────────────────────────────────────────────────────────────

class ResearchEngine:
    def __init__(
        self,
        openrouter_key: str,
        tavily_key: str,
        model: str = "anthropic/claude-sonnet-4.5",
        max_results: int = 7,
        max_tokens: int = 1500,
        embed_model: str = DEFAULT_EMBED_MODEL,
        use_local_rag: bool = True,
    ):
        self.or_key = openrouter_key
        self.tv_key = tavily_key
        self.model  = model
        self.max_results   = max_results
        self.max_tokens    = max_tokens
        self.embed_model   = embed_model
        self.use_local_rag = use_local_rag and RAG_AVAILABLE
        # RAG index is built lazily in run_retriever once PDFs are extracted.
        self._rag_index: RAGIndex | None = None

    # ── Shared LLM call ──────────────────────────────────────────────────────
    def _call(self, system: str, user: str, max_tokens: int | None = None) -> str:
        return _llm(
            messages=[{"role": "user", "content": user}],
            openrouter_key=self.or_key,
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            system=system,
        )

    # =========================================================================
    # AGENT 1 — Contextual Retriever
    # =========================================================================
    def run_retriever(
        self,
        query: str,
        extra_context: str = "",
        pdf_files: list[Any] | None = None,
    ) -> dict[str, Any]:
        """
        Fetches web results via Tavily and extracts PDF text concurrently,
        then uses the LLM to produce a structured evidence digest.

        Concurrency strategy
        --------------------
        Three complementary Tavily sub-queries (base, recent-developments,
        criticisms) and all PDF extractions are submitted to a shared
        ThreadPoolExecutor simultaneously.  Results arrive as each future
        completes; the slowest individual request determines the wall-clock
        wait, not the sum of all requests.

          Before:  N serial requests  → total ≈ N × avg_latency
          After:   N parallel requests → total ≈ max(individual latencies)
        """
        pdf_files = pdf_files or []

        # 1a. Decompose query into 3 complementary search angles
        sub_queries = _build_sub_queries(query, extra_context)

        # 1b. Fire all Tavily searches AND all PDF extractions concurrently
        #     in a single shared thread pool.
        raw_web: list[dict[str, Any]] = []
        pdf_texts: list[str] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
            # Submit all Tavily sub-queries
            search_futures: dict[concurrent.futures.Future[list[dict[str, Any]]], str] = {
                pool.submit(_tavily_search, q, self.tv_key, self.max_results): q
                for q in sub_queries
            }
            # Submit all PDF extractions alongside the searches
            pdf_futures: dict[concurrent.futures.Future[str], Any] = {
                pool.submit(_extract_pdf_text, pdf): pdf
                for pdf in pdf_files
            }

            # Collect Tavily results as they arrive
            for future in concurrent.futures.as_completed(search_futures):
                sq = search_futures[future]
                try:
                    results = future.result()
                    for r in results:
                        r.setdefault("_source_query", sq)
                    raw_web.extend(results)
                except Exception as exc:
                    raw_web.append({
                        "title": f"[Search failed] {sq[:80]}",
                        "url": "tavily://error",
                        "content": f"Search error for '{sq}': {exc}",
                        "score": 0.0,
                        "_source_query": sq,
                    })

            # Collect PDF results as they arrive
            for future in concurrent.futures.as_completed(pdf_futures):
                pdf = pdf_futures[future]
                try:
                    text = future.result()
                    name = getattr(pdf, "name", "document")
                    if text.strip():
                        pdf_texts.append(f"[PDF: {name}]\n{text}")
                except Exception as exc:
                    pdf_texts.append(f"[PDF extraction error: {exc}]")

        # Deduplicate web results by URL, keeping the highest-score copy
        seen: dict[str, dict[str, Any]] = {}
        for r in raw_web:
            url = r.get("url", "")
            if url not in seen or r.get("score", 0) > seen[url].get("score", 0):
                seen[url] = r
        web_results = sorted(seen.values(), key=lambda r: r.get("score", 0), reverse=True)

        # 1c. Build local RAG index from PDF chunks (if enabled + PDFs present)
        rag_context = ""
        rag_chunk_count = 0
        if self.use_local_rag and pdf_texts:
            try:
                self._rag_index = build_rag_index(
                    pdf_texts,
                    model_name=self.embed_model,
                    chunk_size=400,
                    overlap=80,
                )
                if self._rag_index and not self._rag_index.is_empty():
                    rag_chunk_count = self._rag_index.chunk_count
                    rag_context = self._rag_index.format_context(
                        query_text=query,
                        top_k=6,
                        max_chars=3500,
                    )
            except Exception as exc:
                rag_context = f"[RAG indexing error: {exc}]"

        # 1d. Build context blob for LLM
        web_blob = "\n\n---\n\n".join(
            f"SOURCE [{i+1}]: {r.get('title','')}\nURL: {r.get('url','')}\n{r.get('content','')[:600]}"
            for i, r in enumerate(web_results)
        )
        # Use semantic RAG chunks when available; fall back to full PDF text
        if rag_context:
            pdf_section = rag_context
        elif pdf_texts:
            pdf_section = "\n\n---\n\n".join(pdf_texts)
        else:
            pdf_section = "No PDFs provided."

        system_prompt = (
            "You are the Contextual Retriever Agent in a multi-agent research system. "
            "Your role: synthesize raw retrieved evidence into a clean, structured evidence digest. "
            "Preserve source attribution. Be factual and exhaustive."
        )
        user_prompt = f"""Research Query: {query}

=== WEB SOURCES ===
{web_blob}

=== PDF CONTEXT ({"semantic RAG — top chunks by similarity" if rag_context else "full text"}) ===
{pdf_section}

Task: Produce a structured Evidence Digest with:
1. A 200-word summary of the overall landscape
2. Key facts and data points (bulleted, with source numbers)
3. A source list with credibility notes (peer-reviewed / news / grey literature / unknown)

Format clearly with markdown headings."""

        digest = self._call(system_prompt, user_prompt, max_tokens=2000)

        return {
            "digest":          digest,
            "web_results":     web_results,
            "pdf_texts":       pdf_texts,
            "web_count":       len(web_results),
            "pdf_count":       len(pdf_texts),
            "rag_chunk_count": rag_chunk_count,
            "rag_model":       self.embed_model if (self.use_local_rag and pdf_texts) else None,
            "raw_query":       query,
        }

    # =========================================================================
    # AGENT 2 — Critical Analysis
    # =========================================================================
    def run_analysis(self, query: str, retrieval: dict[str, Any]) -> dict[str, Any]:
        """
        Cross-references evidence, identifies contradictions, validates sources.
        """
        system_prompt = (
            "You are the Critical Analysis Agent. Your job: evaluate the evidence digest, "
            "spot contradictions, assess source credibility, and highlight knowledge gaps. "
            "Be precise — quote or paraphrase specific conflicting claims."
        )
        user_prompt = f"""Research Query: {query}

=== EVIDENCE DIGEST ===
{retrieval['digest']}

Tasks:
1. **Contradictions & Inconsistencies** — List each conflict between sources. State which sources disagree and on what.
2. **Source Credibility Assessment** — Rate each source: High / Medium / Low credibility with one-line rationale.
3. **Knowledge Gaps** — What important questions remain unanswered by the evidence?
4. **Consensus View** — What does the weight of evidence suggest?

Use markdown. Be critical and specific."""

        analysis_text = self._call(system_prompt, user_prompt, max_tokens=2000)

        contradiction_count = max(
            _count_re(r"contradiction|conflict|disagree|inconsisten", analysis_text), 1
        )
        source_count = retrieval["web_count"] + retrieval["pdf_count"]

        return {
            "text": analysis_text,
            "contradiction_count": contradiction_count,
            "source_count": source_count,
        }

    # =========================================================================
    # AGENT 3 — Insight Generation
    # =========================================================================
    def run_insights(self, query: str, retrieval: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
        """
        Applies reasoning chains to generate hypotheses and spot emerging trends.
        """
        system_prompt = (
            "You are the Insight Generation Agent. Armed with evidence and critical analysis, "
            "your role is to reason forward: generate testable hypotheses, identify emerging trends, "
            "and surface non-obvious patterns. Think like a scientist and a strategist."
        )
        user_prompt = f"""Research Query: {query}

=== EVIDENCE DIGEST ===
{retrieval['digest'][:1500]}

=== CRITICAL ANALYSIS ===
{analysis['text'][:1500]}

Tasks:
1. **Emerging Trends** — Identify 3-5 trends visible in the evidence. For each: name, description, supporting evidence, confidence level (High/Medium/Low).
2. **Hypotheses** — Propose 3-5 testable hypotheses that follow from the data. Format: IF [condition] THEN [outcome] BECAUSE [mechanism].
3. **Reasoning Chain** — For your top hypothesis, show explicit step-by-step reasoning from evidence to conclusion.
4. **Contrarian View** — What if the consensus is wrong? Propose an alternative interpretation.

Use markdown."""

        insight_text = self._call(system_prompt, user_prompt, max_tokens=2000)

        hypothesis_count = max(_count_re(r"hypothesis|hypothes", insight_text), 1)
        trend_count      = max(_count_re(r"trend", insight_text), 1)

        return {
            "text": insight_text,
            "hypothesis_count": min(hypothesis_count, 5),
            "trend_count":      min(trend_count, 5),
        }

    # =========================================================================
    # AGENT 4 — Fact-Check
    # =========================================================================
    def run_factcheck(self, query: str, analysis: dict[str, Any], insights: dict[str, Any]) -> dict[str, Any]:
        """
        Extracts key claims and assesses their verifiability.
        """
        system_prompt = (
            "You are the Fact-Check Agent. Extract the most important factual claims from "
            "the analysis and insights, then evaluate each for: verifiability, evidence strength, "
            "and risk of misinformation. Flag anything that needs corroboration."
        )
        user_prompt = f"""Research Query: {query}

=== CRITICAL ANALYSIS ===
{analysis['text'][:1200]}

=== INSIGHTS ===
{insights['text'][:1200]}

Tasks:
1. **Claim Extraction** — List 5-8 specific factual claims made in the above.
2. **Verification Status** — For each claim: Verified ✅ / Unverified ⚠️ / Disputed ❌, with reasoning.
3. **Risk Flags** — Note any claims that could be misleading or that require expert validation.
4. **Overall Reliability Score** — Rate the body of evidence: Strong / Moderate / Weak, with justification.

Use a table or structured list. Be concise."""

        factcheck_text = self._call(system_prompt, user_prompt, max_tokens=1500)

        verified_count = _count_re(r"verified|✅", factcheck_text)
        flagged_count  = _count_re(r"unverified|disputed|⚠️|❌|flag", factcheck_text)

        return {
            "text": factcheck_text,
            "verified_count": max(verified_count, 1),
            "flagged_count":  max(flagged_count, 0),
        }

    # =========================================================================
    # AGENT 5 — Report Builder
    # =========================================================================
    def run_report_builder(
        self,
        query: str,
        retrieval: dict[str, Any],
        analysis: dict[str, Any],
        insights: dict[str, Any],
        factcheck: dict[str, Any],
    ) -> str:
        """
        Compiles all agent outputs into a polished, structured research report.
        """
        system_prompt = (
            "You are the Report Builder Agent — the final stage of a multi-agent research pipeline. "
            "Your job is to compile all agent outputs into a single, authoritative, well-structured "
            "research report in markdown. Write for an intelligent but non-specialist audience. "
            "The report must be comprehensive, readable, and actionable."
        )

        source_list = "\n".join(
            f"- [{r.get('title','Untitled')}]({r.get('url','#')}) (score: {r.get('score', 'n/a')})"
            for r in retrieval["web_results"][:10]
        )

        user_prompt = f"""Research Query: **{query}**

=== EVIDENCE DIGEST (Retriever Agent) ===
{retrieval['digest']}

=== CRITICAL ANALYSIS (Analysis Agent) ===
{analysis['text']}

=== INSIGHTS & HYPOTHESES (Insight Agent) ===
{insights['text']}

=== FACT-CHECK (Fact-Check Agent) ===
{factcheck['text']}

=== SOURCE LIST ===
{source_list}

Compile a full research report with these exact sections:

# [Descriptive Report Title]

## Executive Summary
(150-200 words covering the core findings and their significance)

## Methodology
(Brief description of sources consulted, agents used, and analysis approach)

## Key Findings
(The most important substantive findings, with evidence citations)

## Contradictions & Debates
(Where sources disagree — what is contested and why it matters)

## Source Credibility Analysis
(Assessment of the evidence base quality)

## Emerging Trends
(Forward-looking patterns identified in the evidence)

## Hypotheses & Implications
(Testable hypotheses and their strategic/practical implications)

## Fact-Check Summary
(Key claims, their verification status, and reliability assessment)

## Knowledge Gaps & Future Research
(What remains unknown; recommended next investigative steps)

## References
(Formatted source list)

---
*Report generated by DeepResearch Multi-Agent System*

Write the full report now. Use markdown formatting throughout."""

        report = self._call(system_prompt, user_prompt, max_tokens=4096)
        return report