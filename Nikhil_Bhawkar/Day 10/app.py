import streamlit as st
import os
import tempfile

from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langgraph.prebuilt import create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langchain_community.utilities.arxiv import ArxivAPIWrapper

# UI Configuration
st.set_page_config(page_title="Modern Agentic RAG", layout="wide")

with st.sidebar:
    st.header("Infrastructure")
    open_key = st.text_input("OpenRouter API Key", type="password")
    tavily_key = st.text_input("Tavily API Key", type="password")
    pdf_file = st.file_uploader("Upload PDF", type="pdf")

# Vectorization
@st.cache_resource
def index_pdf(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.getvalue())
        path = tmp.name
    try:
        loader = PyPDFLoader(path)
        chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150).split_documents(loader.load())
        return FAISS.from_documents(chunks, HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2"))
    finally:
        os.remove(path)

if pdf_file and "vs" not in st.session_state:
    with st.spinner("⏳ Vectorizing..."):
        st.session_state.vs = index_pdf(pdf_file)

# Core Execution Logic
st.title("Architected Agentic RAG")
query = st.text_input("Query:")

if query:
    if not (open_key and tavily_key):
        st.error("Missing Keys.")
        st.stop()

    with st.spinner("🤖 Executing Workflow..."):
        os.environ["TAVILY_API_KEY"] = tavily_key
        
        # Modern Model Config
        llm = ChatOpenAI(
            model="openai/gpt-4o-mini",
            api_key=open_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0
        )
        
        final_out = ""
        source_tag = ""
        hit_pdf = False

        # STEP 1: LCEL RAG
        if "vs" in st.session_state:
            retriever = st.session_state.vs.as_retriever(search_kwargs={"k": 3})
            
            # Pure LCEL Chain
            rag_chain = (
                RunnableParallel({
                    "context": retriever | (lambda docs: "\n\n".join(d.page_content for d in docs)),
                    "input": RunnablePassthrough()
                })
                | ChatPromptTemplate.from_template("Answer using context. If missing, say 'NOT_FOUND'.\nContext: {context}\nQuestion: {input}")
                | llm
                | StrOutputParser()
            )

            res = rag_chain.invoke(query)
            if "NOT_FOUND" not in res:
                final_out, source_tag, hit_pdf = res, "PDF Context", True

        # STEP 2: LangGraph Agent Fallback
        if not hit_pdf:
            tools = [
                WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()),
                ArxivQueryRun(api_wrapper=ArxivAPIWrapper()),
                TavilySearchResults(max_results=3)
            ]
            
            # Create agent
            graph_agent = create_react_agent(llm, tools)
            
            try:
                # LangGraph expects and returns a list of messages (State)
                result = graph_agent.invoke({"messages": [("human", query)]})
                # The last message in the graph is the final AI output
                final_out = result["messages"][-1].content
                source_tag = "LangGraph Agent (Web)"
            except Exception as e:
                final_out, source_tag = f"Workflow Error: {e}", "System"

        # Rendering
        st.markdown(f"**Result ({source_tag})**")
        st.info(final_out)