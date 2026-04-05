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
"""

import re
from typing import Any

import requests

# ── Optional PDF support ──────────────────────────────────────────────────────
try:
    import pypdf
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


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
    """Search Tavily and return a list of result dicts."""
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
    results = data.get("results", [])
    # Attach Tavily's synthesized answer as first pseudo-result
    if data.get("answer"):
        results.insert(0, {
            "title": "Tavily Synthesized Answer",
            "url": "tavily://answer",
            "content": data["answer"],
            "score": 1.0,
        })
    return results


def _extract_pdf_text(file_obj) -> str:
    """Extract text from a PDF file-like object using pypdf."""
    if not PDF_SUPPORT:
        return "[PDF support unavailable — install pypdf]"
    try:
        reader = pypdf.PdfReader(file_obj)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)[:8000]  # cap to avoid context overflow
    except Exception as exc:
        return f"[Error reading PDF: {exc}]"


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
    ):
        self.or_key = openrouter_key
        self.tv_key = tavily_key
        self.model  = model
        self.max_results = max_results
        self.max_tokens  = max_tokens

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
        Fetches web results via Tavily, extracts PDF text, then uses the LLM
        to produce a structured evidence digest.
        """
        pdf_files = pdf_files or []

        # 1a. Web search
        search_query = query
        if extra_context:
            search_query = f"{query}. Context: {extra_context[:300]}"
        web_results = _tavily_search(search_query, self.tv_key, self.max_results)

        # 1b. PDF extraction
        pdf_texts: list[str] = []
        for pdf in pdf_files:
            text = _extract_pdf_text(pdf)
            if text.strip():
                pdf_texts.append(f"[PDF: {getattr(pdf, 'name', 'document')}]\n{text}")

        # 1c. Build context blob for LLM
        web_blob = "\n\n---\n\n".join(
            f"SOURCE [{i+1}]: {r.get('title','')}\nURL: {r.get('url','')}\n{r.get('content','')[:600]}"
            for i, r in enumerate(web_results)
        )
        pdf_blob = "\n\n---\n\n".join(pdf_texts) if pdf_texts else "No PDFs provided."

        system_prompt = (
            "You are the Contextual Retriever Agent in a multi-agent research system. "
            "Your role: synthesize raw retrieved evidence into a clean, structured evidence digest. "
            "Preserve source attribution. Be factual and exhaustive."
        )
        user_prompt = f"""Research Query: {query}

=== WEB SOURCES ===
{web_blob}

=== PDF DOCUMENTS ===
{pdf_blob}

Task: Produce a structured Evidence Digest with:
1. A 200-word summary of the overall landscape
2. Key facts and data points (bulleted, with source numbers)
3. A source list with credibility notes (peer-reviewed / news / grey literature / unknown)

Format clearly with markdown headings."""

        digest = self._call(system_prompt, user_prompt, max_tokens=2000)

        return {
            "digest": digest,
            "web_results": web_results,
            "pdf_texts": pdf_texts,
            "web_count": len(web_results),
            "pdf_count": len(pdf_texts),
            "raw_query": query,
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
