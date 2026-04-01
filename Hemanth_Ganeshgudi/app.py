import streamlit as st
import os
import tempfile

# ─────────────────────────────────────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Agentic RAG System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #6C63FF, #3ECFCF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        color: #888;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    .badge-pdf {
        background-color: #d4edda;
        color: #155724;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .badge-agent {
        background-color: #cce5ff;
        color: #004085;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .source-chunk {
        background: #f8f9fa;
        border-left: 3px solid #6C63FF;
        padding: 8px 12px;
        border-radius: 4px;
        margin: 6px 0;
        font-size: 0.85rem;
    }
    .stAlert {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
for key, default in {
    "vectorstore": None,
    "messages": [],
    "pdf_names": [],
    "embeddings": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔑 API Keys")
    openai_key  = st.text_input("OpenAI API Key",  type="password", placeholder="sk-...")
    tavily_key  = st.text_input("Tavily API Key",  type="password", placeholder="tvly-...")

    if openai_key:
        os.environ["OPENAI_API_KEY"]  = openai_key
    if tavily_key:
        os.environ["TAVILY_API_KEY"]  = tavily_key

    st.markdown("---")
    st.markdown("## ⚙️ Settings")
    faiss_threshold = st.slider(
        "PDF Relevance Threshold (L2 distance)",
        min_value=0.1, max_value=2.0, value=1.0, step=0.05,
        help=(
            "FAISS L2 distance — **lower = more similar**. "
            "If the best-matching chunk has a distance ABOVE this value, "
            "the question is routed to the ReAct agent instead."
        ),
    )
    top_k = st.slider("Chunks retrieved from PDF", min_value=1, max_value=8, value=4)

    st.markdown("---")
    st.markdown("## 📖 How it works")
    st.markdown("""
1. Enter your **API keys** above  
2. **Upload** one or more PDFs  
3. **Ask** any question  

The system:
- 🔍 First searches your **PDFs** (FAISS + GPT-4o)  
- If the answer isn't found it falls back to the  
  **ReAct Agent** which picks from:  
  &nbsp;&nbsp;🌐 **Wikipedia** — encyclopaedic knowledge  
  &nbsp;&nbsp;🔎 **Tavily** — live web search  
  &nbsp;&nbsp;📄 **arXiv** — academic papers  
""")

    st.markdown("---")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
    if st.button("🗂️ Clear All (PDFs + Chat)"):
        st.session_state.messages   = []
        st.session_state.vectorstore = None
        st.session_state.pdf_names   = []
        st.session_state.embeddings  = None
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">🤖 Agentic RAG System</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Upload PDFs → ask questions → auto-escalates to Wikipedia / Tavily / arXiv when needed</p>',
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
#  PDF UPLOAD & INDEXING
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### 📂 Upload Documents")
uploaded_files = st.file_uploader(
    "Drop one or more PDF files here",
    type=["pdf"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

def index_pdfs(files, api_key):
    """Load PDFs, chunk, embed, and store in FAISS."""
    from langchain_community.document_loaders import PyPDFLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS

    all_docs = []
    for f in files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(f.read())
            tmp_path = tmp.name
        loader = PyPDFLoader(tmp_path)
        all_docs.extend(loader.load())
        os.unlink(tmp_path)

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(all_docs)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore, embeddings, len(chunks)


if uploaded_files:
    if not openai_key:
        st.warning("⚠️ Enter your OpenAI API Key in the sidebar to index PDFs.")
    else:
        new_names = [f.name for f in uploaded_files if f.name not in st.session_state.pdf_names]
        if new_names:
            with st.spinner(f"Embedding {len(uploaded_files)} PDF(s) into FAISS …"):
                try:
                    vs, emb, n_chunks = index_pdfs(uploaded_files, openai_key)
                    st.session_state.vectorstore = vs
                    st.session_state.embeddings  = emb
                    st.session_state.pdf_names   = [f.name for f in uploaded_files]
                    st.success(f"✅ {len(uploaded_files)} PDF(s) indexed → **{n_chunks}** chunks stored in FAISS")
                except Exception as e:
                    st.error(f"❌ Indexing failed: {e}")

if st.session_state.pdf_names:
    with st.expander(f"📚 {len(st.session_state.pdf_names)} document(s) indexed", expanded=False):
        for name in st.session_state.pdf_names:
            st.markdown(f"&nbsp;&nbsp;📄 `{name}`", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  CORE LOGIC
# ─────────────────────────────────────────────────────────────────────────────

def build_react_agent(oai_key: str, tvly_key: str):
    """Build a ReAct agent with Wikipedia, Tavily, and arXiv tools."""
    from langchain_openai import ChatOpenAI
    from langchain_community.tools   import WikipediaQueryRun, ArxivQueryRun
    from langchain_community.utilities import WikipediaAPIWrapper, ArxivAPIWrapper
    from langchain_community.tools.tavily_search import TavilySearchResults
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain import hub

    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=oai_key)

    # ── Tool 1: Wikipedia ──────────────────────────────────────────────────
    wiki_wrapper = WikipediaAPIWrapper(top_k_results=3, doc_content_chars_max=2000)
    wiki_tool    = WikipediaQueryRun(api_wrapper=wiki_wrapper)
    wiki_tool.name        = "wikipedia"
    wiki_tool.description = (
        "Search Wikipedia for encyclopaedic knowledge, definitions, historical events, "
        "and general background information. Input: a concise search query."
    )

    # ── Tool 2: Tavily (live web search) ───────────────────────────────────
    tavily_tool = TavilySearchResults(
        max_results=5,
        tavily_api_key=tvly_key,
    )
    tavily_tool.name        = "tavily_search"
    tavily_tool.description = (
        "Search the internet for current events, latest news, recent data, "
        "or anything that requires up-to-date information beyond Wikipedia. "
        "Input: a natural-language search query."
    )

    # ── Tool 3: arXiv ─────────────────────────────────────────────────────
    arxiv_wrapper = ArxivAPIWrapper(top_k_results=3, doc_content_chars_max=2000)
    arxiv_tool    = ArxivQueryRun(api_wrapper=arxiv_wrapper)
    arxiv_tool.name        = "arxiv"
    arxiv_tool.description = (
        "Search arXiv for peer-reviewed academic papers, scientific research, "
        "technical reports, and cutting-edge studies in any STEM field. "
        "Input: a topic or keyword query."
    )

    tools  = [wiki_tool, tavily_tool, arxiv_tool]
    prompt = hub.pull("hwchase17/react")

    agent          = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=6,
    )
    return agent_executor


def rag_answer(question: str, vectorstore, top_k: int, threshold: float, oai_key: str):
    """Retrieve from FAISS and generate an answer with GPT-4o."""
    from langchain_openai import ChatOpenAI
    from langchain.chains import RetrievalQA

    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=oai_key)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type="stuff",
    )
    result = qa_chain.invoke({"query": question})
    return result["result"], result["source_documents"]


UNCERTAIN_PHRASES = [
    "i don't know", "not mentioned", "not found in",
    "no information", "cannot find", "not provided",
    "does not contain", "not discuss", "not covered",
    "i cannot answer", "no relevant", "outside the scope",
]

def route_and_answer(question: str, threshold: float, top_k: int):
    """
    Decision logic:
      1. If no vectorstore → go straight to agent.
      2. Compute FAISS L2 scores; if best > threshold → agent.
      3. Generate RAG answer; if answer signals uncertainty → agent.
      4. Otherwise return RAG answer.
    """
    oai_key  = os.environ.get("OPENAI_API_KEY", "")
    tvly_key = os.environ.get("TAVILY_API_KEY", "")

    # ── No PDF indexed ─────────────────────────────────────────────────────
    if st.session_state.vectorstore is None:
        agent     = build_react_agent(oai_key, tvly_key)
        result    = agent.invoke({"input": question})
        return result["output"], "agent", [], "No PDF uploaded — used agent directly."

    vs = st.session_state.vectorstore

    # ── Score-based routing ────────────────────────────────────────────────
    docs_scores = vs.similarity_search_with_score(question, k=top_k)
    if not docs_scores:
        agent  = build_react_agent(oai_key, tvly_key)
        result = agent.invoke({"input": question})
        return result["output"], "agent", [], "No matching chunks found in PDF."

    best_score = docs_scores[0][1]  # L2 distance (lower = more similar)

    if best_score > threshold:
        agent  = build_react_agent(oai_key, tvly_key)
        result = agent.invoke({"input": question})
        reason = (
            f"Best PDF similarity score ({best_score:.3f}) exceeded threshold ({threshold:.2f}) "
            "→ routed to ReAct agent."
        )
        return result["output"], "agent", [], reason

    # ── RAG answer ─────────────────────────────────────────────────────────
    answer, source_docs = rag_answer(question, vs, top_k, threshold, oai_key)

    if any(p in answer.lower() for p in UNCERTAIN_PHRASES):
        agent  = build_react_agent(oai_key, tvly_key)
        result = agent.invoke({"input": question})
        reason = "RAG answer indicated uncertainty → escalated to ReAct agent."
        return result["output"], "agent", [], reason

    return answer, "pdf", docs_scores[:3], f"Best chunk distance: {best_score:.3f} (≤ {threshold:.2f})"


# ─────────────────────────────────────────────────────────────────────────────
#  CHAT UI
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 💬 Chat")

# Render history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            src = msg.get("source", "")
            if src == "pdf":
                st.markdown('<span class="badge-pdf">📄 Answered from PDF</span>', unsafe_allow_html=True)
            elif src == "agent":
                st.markdown('<span class="badge-agent">🤖 ReAct Agent (Wikipedia · Tavily · arXiv)</span>', unsafe_allow_html=True)
            if msg.get("routing_reason"):
                st.caption(f"⚙️ {msg['routing_reason']}")
            if msg.get("chunks"):
                with st.expander("📎 Source chunks from PDF"):
                    for doc, score in msg["chunks"]:
                        st.markdown(
                            f'<div class="source-chunk"><b>Page {doc.metadata.get("page", "?")} '
                            f'— L2 score: {score:.4f}</b><br>{doc.page_content[:350]}…</div>',
                            unsafe_allow_html=True,
                        )

# Input
if prompt := st.chat_input("Ask anything about your PDFs or any topic …"):
    if not openai_key:
        st.error("❌ Please enter your OpenAI API Key in the sidebar first.")
    elif not tavily_key:
        st.error("❌ Please enter your Tavily API Key in the sidebar first.")
    else:
        # User bubble
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Assistant bubble
        with st.chat_message("assistant"):
            with st.spinner("Thinking …"):
                try:
                    answer, source, chunks, routing_reason = route_and_answer(
                        prompt, faiss_threshold, top_k
                    )
                    st.markdown(answer)
                    if source == "pdf":
                        st.markdown('<span class="badge-pdf">📄 Answered from PDF</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="badge-agent">🤖 ReAct Agent (Wikipedia · Tavily · arXiv)</span>', unsafe_allow_html=True)
                    st.caption(f"⚙️ {routing_reason}")

                    if source == "pdf" and chunks:
                        with st.expander("📎 Source chunks from PDF"):
                            for doc, score in chunks:
                                st.markdown(
                                    f'<div class="source-chunk"><b>Page {doc.metadata.get("page", "?")} '
                                    f'— L2 score: {score:.4f}</b><br>{doc.page_content[:350]}…</div>',
                                    unsafe_allow_html=True,
                                )

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "source": source,
                        "chunks": chunks if source == "pdf" else [],
                        "routing_reason": routing_reason,
                    })

                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    st.info("💡 Check that both API keys are valid and that you have internet access.")
