"""
agents/analyst.py — Critical Analyst Node

The skeptic. Reads raw retrieved data and:
- Filters noise and irrelevant content
- Flags contradictions between sources
- Assesses source quality (peer-reviewed vs. blog post vs. AI answer)
- Synthesizes validated, trustworthy facts

Analogy: Think PolitiFact + Nature peer reviewer rolled into one.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from core.state import ResearchState


ANALYST_SYSTEM_PROMPT = """You are a Critical Research Analyst with expertise in information verification and source evaluation.

Your analysis must follow this EXACT structure with these headers:

## Validated Facts
List facts that are confirmed by multiple independent sources or come from authoritative sources (peer-reviewed papers, official statistics, established institutions). For each fact, cite which source(s) confirm it.

## Contradictions & Conflicts
Explicitly flag any contradictions between sources. Format: "Source A claims [X], but Source B states [Y]. Likely explanation: [Z]."
If no contradictions, state "No significant contradictions found."

## Source Quality Assessment
Rate each source type present:
- Peer-reviewed papers: HIGH credibility
- Official statistics/government data: HIGH credibility  
- Established news outlets: MEDIUM credibility
- AI-synthesized answers (Tavily): MEDIUM credibility (use as starting point)
- Blogs/forums: LOW credibility

## Information Gaps
What critical information is MISSING that would strengthen this research? What questions remain unanswered?

## Discarded Information
What did you filter out and why? (e.g., "Discarded 2 sources as promotional content with no verifiable claims.")

Be brutally honest. A weak evidence base is better acknowledged than dressed up."""


def analyst_node(state: ResearchState, llm: ChatOpenAI) -> ResearchState:
    """
    Analyst node: synthesizes raw docs into validated, contradiction-flagged facts.

    Args:
        state: ResearchState with raw_documents populated
        llm  : Initialized LLM

    Returns:
        Updated state with analyzed_facts populated
    """
    print(f"[Analyst] Analyzing {len(state['raw_documents'])} documents...")

    # Format docs for the prompt — include tool_used for source quality context
    formatted_docs = ""
    for i, doc in enumerate(state["raw_documents"]):
        formatted_docs += (
            f"\n--- Document {i+1} ---\n"
            f"Source: {doc.get('source', 'Unknown')}\n"
            f"Retrieved via: {doc.get('tool_used', 'unknown tool')}\n"
            f"Related to: {doc.get('sub_query', 'N/A')}\n"
            f"Content: {doc.get('content', '')[:1500]}\n"
        )

    user_prompt = f"""Original Research Question: {state['user_query']}

Raw Retrieved Documents ({len(state['raw_documents'])} total):
{formatted_docs}

Provide your critical analysis following the required structure."""

    try:
        response = llm.invoke([
            SystemMessage(content=ANALYST_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])

        print(f"[Analyst] Analysis complete ({len(response.content)} chars).")
        return {
            **state,
            "analyzed_facts": response.content,
            "current_agent": "Critical Analyst ✅",
        }

    except Exception as e:
        error_msg = f"Analyst node failed: {str(e)}"
        print(f"[Analyst] ERROR: {error_msg}")
        return {
            **state,
            "analyzed_facts": f"Analysis failed: {error_msg}",
            "current_agent": "Critical Analyst ❌",
            "error": error_msg,
        }