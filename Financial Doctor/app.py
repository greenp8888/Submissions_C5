"""
FinanceDoctor — Streamlit Application (Layer 4)
=================================================
Main UI with three tabs: Chat, Dashboard, Data Explorer.
Sidebar for API keys, model selection, and document upload.
"""

import streamlit as st
import pandas as pd
from langchain_core.messages import AIMessage, HumanMessage

from config import AVAILABLE_MODELS, AGENT_METADATA
from document_parser import parse_document
from rag_pipeline import RAGPipeline
from graph import build_graph
from dashboard import (
    detect_columns,
    render_summary_cards,
    render_spending_breakdown,
    render_monthly_trends,
    render_debt_analysis,
    render_savings_tracker,
    render_top_expenses,
)


# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="FinanceDoctor — Chanakya AI",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────

st.markdown("""
<style>
    /* ---------- Global ---------- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .stApp { font-family: 'Inter', sans-serif; }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown label {
        color: #e0e0ff !important;
    }

    /* ---------- Header ---------- */
    .hero-title {
        background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.4rem;
        font-weight: 700;
        margin-bottom: 0;
        text-align: center;
    }
    .hero-subtitle {
        color: #9ca3af;
        text-align: center;
        font-size: 1rem;
        margin-top: 0.25rem;
        margin-bottom: 1.5rem;
    }

    /* ---------- Chat Messages ---------- */
    .stChatMessage {
        border-radius: 12px !important;
        margin-bottom: 0.75rem !important;
    }

    /* ---------- Route Badges ---------- */
    .route-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    .route-debt {
        background: linear-gradient(135deg, #ff416c, #ff4b2b);
        color: white;
    }
    .route-savings {
        background: linear-gradient(135deg, #11998e, #38ef7d);
        color: white;
    }
    .route-budget {
        background: linear-gradient(135deg, #2563eb, #3b82f6);
        color: white;
    }
    .route-action {
        background: linear-gradient(135deg, #f7971e, #ffd200);
        color: #1a1a2e;
    }

    /* ---------- Sidebar Branding ---------- */
    .sidebar-brand {
        text-align: center;
        padding: 1.5rem 0 1rem 0;
    }
    .sidebar-brand-icon { font-size: 3rem; margin-bottom: 0.25rem; }
    .sidebar-brand-name {
        font-size: 1.3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #f7971e, #ffd200);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* ---------- Metrics ---------- */
    .metric-row { display: flex; gap: 12px; margin: 12px 0; }
    .metric-card {
        flex: 1;
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #2d2d44;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
    }
    .metric-value { font-size: 1.4rem; font-weight: 700; color: #ffd200; }
    .metric-label {
        font-size: 0.72rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* ---------- Status bar ---------- */
    .status-bar {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #2d2d44;
        border-radius: 10px;
        padding: 12px 18px;
        margin: 12px 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .status-dot {
        width: 10px; height: 10px; border-radius: 50%;
        display: inline-block;
    }
    .status-dot.active { background: #38ef7d; box-shadow: 0 0 6px #38ef7d; }
    .status-dot.inactive { background: #ff6b6b; }

    /* ---------- Tab styling ---------- */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────

defaults = {
    "messages": [],
    "financial_data_md": "",
    "financial_df": None,
    "graph": None,
    "rag_pipeline": None,
    "current_model": "",
    "data_ingested": False,
    "chunk_count": 0,
    "doc_source": "",
    "processed_files": set(),
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-icon">🪙</div>
        <div class="sidebar-brand-name">FinanceDoctor</div>
        <p style="color:#9ca3af; font-size:0.8rem; margin-top:4px;">Powered by Chanakya-AI</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── API Keys ──────────────────────────────
    st.markdown("### 🔑 API Configuration")
    openrouter_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        placeholder="sk-or-v1-...",
        help="Get your key from https://openrouter.ai/keys",
    )
    tavily_key = st.text_input(
        "Tavily API Key",
        type="password",
        placeholder="tvly-...",
        help="Get your key from https://tavily.com",
    )
    llamaparse_key = st.text_input(
        "LlamaParse API Key (optional)",
        type="password",
        placeholder="llx-...",
        help="For PDF parsing. Get from https://cloud.llamaindex.ai — PyPDF2 used as fallback",
    )

    st.markdown("---")

    # ── Model Selector ────────────────────────
    st.markdown("### 🤖 Model Selection")
    selected_model_label = st.selectbox(
        "Choose LLM",
        options=list(AVAILABLE_MODELS.keys()),
        index=0,
        help="🆓 = Free on OpenRouter, 💰 = Paid",
    )
    selected_model = AVAILABLE_MODELS[selected_model_label]
    st.caption(f"`{selected_model}`")

    st.markdown("---")

    # ── File Upload ───────────────────────────
    st.markdown("### 📁 Upload Financial Data")
    uploaded_files = st.file_uploader(
        "Bank statement, expenses, loans...",
        type=["csv", "xlsx", "xls", "pdf"],
        help="Supported: CSV, Excel (.xlsx), PDF",
        accept_multiple_files=True,
    )

    if uploaded_files:
        # Process button
        if st.button("🚀 Process Document(s)", use_container_width=True, type="primary"):
            new_files = [f for f in uploaded_files if f.name not in st.session_state.processed_files]
            
            if not new_files:
                st.info("All uploaded files have already been processed.")
            else:
                for uploaded_file in new_files:
                    with st.spinner(f"📄 Parsing {uploaded_file.name}..."):
                        try:
                            text, df = parse_document(
                                uploaded_file,
                                uploaded_file.name,
                                llamaparse_key=llamaparse_key,
                            )
                            # Append Text
                            if text:
                                header = f"\n\n--- Source: {uploaded_file.name} ---\n\n"
                                st.session_state.financial_data_md += header + text
                            
                            # Concat DataFrame
                            if df is not None:
                                if st.session_state.financial_df is None:
                                    st.session_state.financial_df = df
                                else:
                                    st.session_state.financial_df = pd.concat(
                                        [st.session_state.financial_df, df], 
                                        ignore_index=True
                                    )
                        except Exception as e:
                            st.error(f"❌ Parsing failed for {uploaded_file.name}: {e}")
                            continue

                    with st.spinner(f"🧠 Chunking & embedding {uploaded_file.name}..."):
                        try:
                            # Initialize RAG pipeline
                            if st.session_state.rag_pipeline is None:
                                st.session_state.rag_pipeline = RAGPipeline()

                            added_chunks = st.session_state.rag_pipeline.ingest(
                                text, source=uploaded_file.name
                            )
                            st.session_state.chunk_count += added_chunks
                        except Exception as e:
                            st.error(f"❌ RAG pipeline error for {uploaded_file.name}: {e}")
                            continue
                    
                    st.session_state.processed_files.add(uploaded_file.name)

                st.session_state.data_ingested = True
                st.session_state.doc_source = ", ".join(sorted(list(st.session_state.processed_files)))

                # Rebuild graph with RAG pipeline
                if openrouter_key and tavily_key:
                    with st.spinner("🔧 Building AI graph..."):
                        st.session_state.graph = build_graph(
                            openrouter_key, tavily_key, selected_model,
                            rag_pipeline=st.session_state.rag_pipeline,
                        )
                        st.session_state.current_model = selected_model

                rows = len(st.session_state.financial_df) if st.session_state.financial_df is not None else 0
                st.success(
                    f"✅ Processed New Files!\n"
                    f"- **{rows} total rows** loaded\n"
                    f"- **{st.session_state.chunk_count} total chunks** embedded\n"
                    f"- Stored in LanceDB"
                )
                st.rerun()

    # Show ingestion status
    if st.session_state.data_ingested:
        if st.button("🗑️ Clear Data", use_container_width=True, type="secondary"):
            if st.session_state.rag_pipeline:
                 st.session_state.rag_pipeline.clear()
            for key in ["financial_data_md", "current_model", "doc_source"]:
                 st.session_state[key] = ""
            st.session_state["financial_df"] = None
            st.session_state["graph"] = None
            st.session_state["rag_pipeline"] = None
            st.session_state["data_ingested"] = False
            st.session_state["chunk_count"] = 0
            st.session_state["processed_files"] = set()
            st.rerun()

        st.markdown(f"""
        <div class="status-bar">
            <span class="status-dot active"></span>
            <span style="color: #e0e0ff; font-size: 0.85rem;">
                <strong>{st.session_state.doc_source}</strong><br/>
                {st.session_state.chunk_count} chunks in vector store
            </span>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.financial_df is not None:
            with st.expander("Preview Data", expanded=False):
                st.dataframe(
                    st.session_state.financial_df.head(10).astype(str),
                    use_container_width=True,
                )

    st.markdown("---")

    # ── Build Graph (if keys present but graph not built) ──
    if openrouter_key and tavily_key:
        need_rebuild = (
            st.session_state.graph is None
            or st.session_state.current_model != selected_model
        )
        if need_rebuild:
            with st.spinner("🔧 Building AI graph..."):
                st.session_state.graph = build_graph(
                    openrouter_key, tavily_key, selected_model,
                    rag_pipeline=st.session_state.rag_pipeline,
                )
                st.session_state.current_model = selected_model
            st.success("✅ AI Graph ready!")

        # Agent status display
        st.markdown("""
        <div class="metric-row">
            <div class="metric-card">
                <div class="metric-value">5</div>
                <div class="metric-label">Nodes</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">4</div>
                <div class="metric-label">Agents</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Show agent list
        with st.expander("🤖 Active Agents", expanded=False):
            for agent_id, meta in AGENT_METADATA.items():
                st.markdown(
                    f"**{meta['label']}** — {meta['description']}"
                )
    else:
        st.warning("⚠️ Enter OpenRouter + Tavily API keys to activate AI.")

    # Clear chat
    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown(
        "<p style='color:#555; text-align:center; font-size:0.7rem;'>"
        "FinanceDoctor v2.0 • LangGraph + LanceDB + Streamlit<br>"
        "Not financial advice. Consult a SEBI-registered advisor.</p>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# MAIN AREA — HEADER
# ─────────────────────────────────────────────

st.markdown('<p class="hero-title">🪙 FinanceDoctor</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-subtitle">'
    'Your AI-powered Chanakya for Indian Personal Finance — '
    'Debt, Budget, Savings & Action Plans'
    '</p>',
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────
# TABS: Chat | Dashboard | Data
# ─────────────────────────────────────────────

tab_chat, tab_dashboard, tab_data = st.tabs(["💬 Chat", "📊 Dashboard", "📁 Data Explorer"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1: CHAT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_chat:
    # Info bar
    if st.session_state.data_ingested:
        st.info(
            f"📊 **{st.session_state.doc_source}** loaded — "
            f"{st.session_state.chunk_count} chunks in vector store. "
            "The AI will search your data via RAG for every response.",
            icon="✅",
        )
    else:
        st.info(
            "💡 **Tip:** Upload a financial document (CSV, Excel, PDF) in the sidebar "
            "for personalized analysis powered by RAG.",
            icon="📎",
        )

    # Chat history
    for msg in st.session_state.messages:
        role = msg["role"]
        with st.chat_message(role, avatar="🧑‍💻" if role == "user" else "🪙"):
            if "route" in msg and msg["route"]:
                meta = AGENT_METADATA.get(msg["route"], {})
                badge_class = meta.get("badge_class", "route-budget")
                label = meta.get("label", msg["route"])
                st.markdown(
                    f'<span class="route-badge {badge_class}">{label}</span>',
                    unsafe_allow_html=True,
                )
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask Chanakya-AI about your finances..."):
        if not st.session_state.graph:
            st.error("⚠️ Please enter your API keys in the sidebar first.")
            st.stop()

        # Display user message
        st.session_state.messages.append({"role": "user", "content": prompt, "route": ""})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        # Build LangChain message history
        lc_messages = []
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            else:
                lc_messages.append(AIMessage(content=msg["content"]))

        # Invoke the graph
        with st.chat_message("assistant", avatar="🪙"):
            with st.spinner("🧠 Chanakya-AI is thinking..."):
                try:
                    # Build data summary for the agents
                    data_summary = ""
                    if st.session_state.financial_data_md:
                        # Truncate to avoid massive prompts
                        md = st.session_state.financial_data_md
                        data_summary = md[:3000] if len(md) > 3000 else md

                    result = st.session_state.graph.invoke({
                        "messages": lc_messages,
                        "financial_data_summary": data_summary,
                        "route_decision": "",
                    })

                    route = result.get("route_decision", "budget_advisor")
                    ai_msgs = [
                        m for m in result["messages"]
                        if isinstance(m, AIMessage) and m.content
                    ]
                    response_text = (
                        ai_msgs[-1].content if ai_msgs
                        else "I could not generate a response. Please try again."
                    )

                    # Show route badge
                    meta = AGENT_METADATA.get(route, {})
                    badge_class = meta.get("badge_class", "route-budget")
                    label = meta.get("label", route)
                    st.markdown(
                        f'<span class="route-badge {badge_class}">{label}</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(response_text)

                    # Save to session
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "route": route,
                    })

                except Exception as e:
                    error_msg = f"❌ **Error:** {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "route": "",
                    })


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2: DASHBOARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_dashboard:
    df = st.session_state.financial_df

    if df is None:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px;">
            <div style="font-size: 4rem; margin-bottom: 16px;">📊</div>
            <h3 style="color: #e0e0ff;">No Data Yet</h3>
            <p style="color: #9ca3af;">
                Upload a bank statement or financial CSV/Excel in the sidebar<br/>
                to see interactive charts and analysis here.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        col_map = detect_columns(df)

        # Summary cards
        render_summary_cards(df, col_map)

        st.markdown("---")

        # Two-column layout: Spending + Debt
        col_left, col_right = st.columns(2)

        with col_left:
            render_spending_breakdown(df, col_map)

        with col_right:
            render_savings_tracker(df, col_map)

        st.markdown("---")

        # Full-width monthly trends
        render_monthly_trends(df, col_map)

        st.markdown("---")

        # Debt analysis + Top expenses
        col_debt, col_top = st.columns(2)

        with col_debt:
            render_debt_analysis(df, col_map)

        with col_top:
            render_top_expenses(df, col_map)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3: DATA EXPLORER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_data:
    df = st.session_state.financial_df

    if df is None:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px;">
            <div style="font-size: 4rem; margin-bottom: 16px;">📁</div>
            <h3 style="color: #e0e0ff;">No Data Loaded</h3>
            <p style="color: #9ca3af;">Upload a document in the sidebar to explore your data.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"### 📁 Data from: `{st.session_state.doc_source}`")
        st.markdown(f"**{len(df)} rows** × **{len(df.columns)} columns**")

        # Column info
        with st.expander("📋 Column Summary", expanded=False):
            col_info = pd.DataFrame({
                "Column": df.columns,
                "Type": df.dtypes.astype(str).values,
                "Non-Null": df.notnull().sum().values,
                "Sample": [str(df[c].iloc[0]) if len(df) > 0 else "" for c in df.columns],
            })
            st.dataframe(col_info.astype(str), use_container_width=True, hide_index=True)

        # Filters
        col_map = detect_columns(df)
        cat_col = col_map.get("category")
        type_col = col_map.get("type")

        filter_cols = st.columns(3)
        filtered_df = df.copy()

        with filter_cols[0]:
            if cat_col and cat_col in df.columns:
                cats = ["All"] + sorted(df[cat_col].dropna().unique().tolist())
                sel_cat = st.selectbox("Filter by Category", cats)
                if sel_cat != "All":
                    filtered_df = filtered_df[filtered_df[cat_col] == sel_cat]

        with filter_cols[1]:
            if type_col and type_col in df.columns:
                types = ["All"] + sorted(df[type_col].dropna().unique().tolist())
                sel_type = st.selectbox("Filter by Type", types)
                if sel_type != "All":
                    filtered_df = filtered_df[filtered_df[type_col] == sel_type]

        with filter_cols[2]:
            st.markdown(f"**Showing:** {len(filtered_df)} of {len(df)} rows")

        # Data table
        st.dataframe(filtered_df.astype(str), use_container_width=True, hide_index=True, height=500)

        # Download button
        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Filtered Data (CSV)",
            csv_data,
            file_name="filtered_financial_data.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # RAG chunks info
        if st.session_state.data_ingested:
            st.markdown("---")
            st.markdown("### 🧠 RAG Vector Store Info")
            st.markdown(f"""
            <div class="status-bar">
                <span class="status-dot active"></span>
                <span style="color: #e0e0ff;">
                    <strong>LanceDB</strong> — {st.session_state.chunk_count} chunks stored |
                    Embedding model: <code>all-MiniLM-L6-v2</code> (384-dim)
                </span>
            </div>
            """, unsafe_allow_html=True)

            # Test RAG search
            rag_query = st.text_input(
                "🔍 Test RAG Search",
                placeholder="e.g., 'home loan EMI' or 'grocery spending'",
            )
            if rag_query and st.session_state.rag_pipeline:
                results = st.session_state.rag_pipeline.query(rag_query, top_k=3)
                if results:
                    for i, chunk in enumerate(results, 1):
                        st.markdown(f"**Chunk {i}:**")
                        st.code(chunk, language=None)
                else:
                    st.warning("No results found.")
