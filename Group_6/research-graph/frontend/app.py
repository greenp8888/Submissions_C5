import os
import sys
import shutil
import tempfile
import logging

logging.getLogger("transformers").setLevel(logging.ERROR)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from configs.llm import (
    LLM_PROVIDER,
    OLLAMA_CONFIG,
    OPENROUTER_CONFIG,
    RAG_CONFIG,
)
from agents.research_graph import (
    VERBATIM_EVIDENCE_TOOLS,
    build_research_graph,
    build_retrieval_tools,
    partition_sources_for_display,
    run_investigation,
    stream_investigation,
)

EMBEDDING_MODEL = RAG_CONFIG["embedding_model"]


def get_llm():
    """Create LLM instance based on configuration."""
    if LLM_PROVIDER == "openrouter":
        from langchain_openai import ChatOpenAI

        if not OPENROUTER_CONFIG["api_key"]:
            raise ValueError("OPENROUTER_API_KEY is not set in .env file")

        return ChatOpenAI(
            model=OPENROUTER_CONFIG["model"],
            api_key=OPENROUTER_CONFIG["api_key"],
            base_url="https://openrouter.ai/api/v1",
            temperature=OPENROUTER_CONFIG["temperature"],
            top_p=OPENROUTER_CONFIG["top_p"],
            max_tokens=4096,
            default_headers={
                "HTTP-Referer": "https://localhost",
                "X-Title": "Research Graph",
            },
        )
    else:
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=OLLAMA_CONFIG["model"],
            base_url=OLLAMA_CONFIG["base_url"],
            temperature=OLLAMA_CONFIG["temperature"],
            top_p=OLLAMA_CONFIG["top_p"],
        )


def _merge_stream_chunk(accumulated: dict, step: dict) -> dict:
    """Merge LangGraph stream_mode='updates' chunks into one view of final fields."""
    for _node_name, update in step.items():
        if not isinstance(update, dict):
            continue
        for k, v in update.items():
            if k == "sources" and isinstance(v, list):
                accumulated.setdefault("sources", []).extend(v)
            else:
                accumulated[k] = v
    return accumulated


def _rag_snippets_from_retriever(retriever, query: str) -> str:
    if not retriever or not query.strip():
        return ""
    try:
        if hasattr(retriever, "invoke"):
            docs = retriever.invoke(query)
        else:
            docs = retriever.get_relevant_documents(query)
        return "\n\n---\n\n".join(
            (d.page_content or "")[:1500] for d in (docs or [])[:6]
        )
    except Exception:
        return ""


st.set_page_config(page_title="Research Assistant", layout="wide")
st.title("Multi-source research assistant")
st.caption(
    "Contextual Retriever → Critical Analysis → Insight Generation → Report Builder "
    f"(LangGraph). Provider: **{LLM_PROVIDER.upper()}**."
)

st.sidebar.header("Retrieval")
st.sidebar.caption(
    "Uploaded PDFs are embedded and matched to your question; excerpts are injected into "
    "the retriever step and listed as **uploaded_pdf** sources."
)
tavily_key = st.sidebar.text_input(
    "Tavily API Key (optional)",
    type="password",
    help="Optional live web search for the retriever agent.",
)
max_hops = st.sidebar.slider("Max retrieval hops", min_value=1, max_value=4, value=2)

st.sidebar.header("Grounding & sampling")
strict_grounding = st.sidebar.checkbox(
    "Strict grounding",
    value=True,
    help="If there is no usable PDF text or tool results, skip analyze/insights/report LLM calls and return a clear 'insufficient evidence' message instead of guessing.",
)
llm_temperature = st.sidebar.slider(
    "LLM temperature",
    min_value=0.0,
    max_value=1.0,
    value=0.1,
    step=0.05,
    help="Lower = less paraphrase drift and hallucination risk for factual tasks.",
)
llm_top_p = st.sidebar.slider(
    "Top-p",
    min_value=0.1,
    max_value=1.0,
    value=0.9,
    step=0.05,
)

st.sidebar.header("Run mode")
use_stream = st.sidebar.checkbox("Stream step updates", value=True)

st.sidebar.markdown(
    """
**Pipeline**
1. **Retrieve** — Wikipedia, ArXiv, optional Tavily (+ PDF snippets)
2. **Analyze** — summary, contradictions, limitations
3. **Insights** — hypotheses; may trigger another retrieve hop
4. **Report** — structured markdown
"""
)

retriever = None

try:
    st.sidebar.info(f"LLM Provider: **{LLM_PROVIDER.upper()}**")

    tavily_key_stripped = (tavily_key or "").strip()
    if tavily_key_stripped:
        os.environ["TAVILY_API_KEY"] = tavily_key_stripped

    tools = build_retrieval_tools(tavily_key_stripped or None)
    llm = get_llm()
    graph = build_research_graph(llm, tools, strict_grounding=strict_grounding)

    uploaded_files = st.file_uploader(
        "Upload PDFs for extra context (optional)",
        type=["pdf"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        try:
            all_docs = []
            temp_dir = tempfile.mkdtemp()
            for uploaded_file in uploaded_files:
                file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                loader = PyPDFLoader(file_path)
                all_docs.extend(loader.load())
            if all_docs:
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000, chunk_overlap=200
                )
                texts = splitter.split_documents(all_docs)
                embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
                db = FAISS.from_documents(texts, embeddings)
                retriever = db.as_retriever(search_kwargs={"k": 5})
                st.success(
                    f"{len(uploaded_files)} PDF(s) indexed for context snippets."
                )
            shutil.rmtree(temp_dir)
        except Exception as e:
            st.error(f"Error processing PDFs: {str(e)}")

    query = st.text_input(
        "Research question", placeholder="e.g. Compare recent LLM efficiency techniques"
    )

    if st.button("Run investigation", type="primary"):
        if not query.strip():
            st.warning("Enter a research question.")
        else:
            q = query.strip()
            rag_snippets = _rag_snippets_from_retriever(retriever, q)

            if use_stream:
                progress = st.status("Running research graph…", expanded=True)
                accumulated: dict = {}
                try:
                    for step in stream_investigation(
                        graph,
                        user_query=q,
                        max_hops=max_hops,
                        rag_snippets=rag_snippets,
                    ):
                        for node_name, update in step.items():
                            progress.write(f"**{node_name}**")
                            if isinstance(update, dict):
                                for k in update:
                                    if k == "messages":
                                        continue
                                    val = update[k]
                                    if isinstance(val, str) and len(val) > 500:
                                        progress.caption(f"· {k}: ({len(val)} chars)")
                                    elif isinstance(val, list):
                                        progress.caption(f"· {k}: {len(val)} items")
                                    else:
                                        progress.caption(f"· {k}: {val!r}")
                        _merge_stream_chunk(accumulated, step)
                    progress.update(label="Done", state="complete")
                    st.session_state["last_research"] = accumulated
                except Exception as e:
                    progress.update(label="Failed", state="error")
                    st.error(f"LLM Error: {str(e)}")
            else:
                with st.spinner("Running full pipeline…"):
                    try:
                        st.session_state["last_research"] = run_investigation(
                            graph,
                            user_query=q,
                            max_hops=max_hops,
                            rag_snippets=rag_snippets,
                        )
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    result = st.session_state.get("last_research")
    if result:
        st.divider()
        st.subheader("Report")
        st.caption(
            "Verify important claims against the source excerpts below. Models can misread or overgeneralize evidence."
        )
        st.markdown(result.get("report") or "_No report yet._")
        with st.expander("Critical analysis"):
            st.markdown(result.get("analysis") or "_N/A_")
        with st.expander("Insights"):
            st.markdown(result.get("insights") or "_N/A_")
        with st.expander("Retrieved source excerpts"):
            sources = result.get("sources") or []
            verbatim, meta = partition_sources_for_display(sources)
            st.caption(
                "Only the **Evidence excerpts** block below is verbatim text from your PDFs or "
                "search APIs. It is **not** rewritten by the report model—use it to fact-check the report. "
                "Excerpts are shown as plain text so wiki/markdown in the raw API response is not styled like a polished answer."
            )
            if meta:
                st.markdown(
                    "**Pipeline notes** *(not third-party evidence; do not cite as a source)*"
                )
                for s in meta:
                    st.info((s.get("content") or "").strip() or "(empty)")
            if not verbatim:
                st.caption(
                    "No API or PDF excerpts on record (check Ollama/tool calling, network, or upload PDFs)."
                )
            else:
                st.markdown("**Evidence excerpts** *(verbatim)*")
                for s in verbatim:
                    tool = str(s.get("tool") or "?")
                    sid = str(s.get("id") or "?")
                    prov = (
                        "search / PDF API"
                        if tool in VERBATIM_EVIDENCE_TOOLS
                        else "retrieval"
                    )
                    st.markdown(f"**{sid}** — `{tool}` — _{prov}_")
                    body = (s.get("content") or "").strip()
                    if body:
                        st.text(body)
                    else:
                        st.caption("(empty content)")

except Exception as e:
    st.error(f"Initialization error: {str(e)}")
