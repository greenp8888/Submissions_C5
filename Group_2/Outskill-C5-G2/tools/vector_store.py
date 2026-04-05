"""
tools/vector_store.py — ChromaDB Local Vector Store Tool + Ingestion Pipeline

USE THIS TOOL FOR:
- Searching content from PDFs the user has uploaded
- Internal/private documents not on the web or ArXiv
- Company reports, custom research papers, proprietary data

ChromaDB is 100% free and runs locally. No API key needed.
Data persists to disk at ./chroma_db/ between sessions.

Analogy: This is your team's private filing cabinet. Only contains
what you've explicitly put in it. If it's empty, it returns nothing useful.
"""

import os
import tempfile
from typing import List, Dict
from langchain_core.tools import tool
from langchain_community.document_loaders import PyPDFLoader
#from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings


# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"   # 33M params, fast, free, local
CHROMA_PERSIST_DIR = "./chroma_db"
CHROMA_COLLECTION_NAME = "research_docs"


def get_embeddings() -> FastEmbedEmbeddings:
    """Returns a local FastEmbed embedding model. No API key. No cost."""
    return FastEmbedEmbeddings(model_name=EMBED_MODEL_NAME)


def get_vector_store() -> Chroma:
    """
    Returns a persistent ChromaDB instance.
    Creates the collection if it doesn't exist yet.
    """
    return Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=CHROMA_PERSIST_DIR,
    )


# ─────────────────────────────────────────────
# PDF INGESTION PIPELINE
# ─────────────────────────────────────────────
def ingest_pdf_to_chroma(uploaded_file) -> Dict[str, str]:
    """
    End-to-end PDF ingestion: bytes → chunks → embeddings → ChromaDB.

    Pipeline:
        Streamlit UploadedFile
            → Temp file on disk (PyPDFLoader needs a path)
            → PyPDFLoader extracts text per page
            → RecursiveCharacterTextSplitter chunks it (512 tokens, 50 overlap)
            → FastEmbed converts chunks to vectors (locally)
            → ChromaDB stores vectors + text + metadata

    Args:
        uploaded_file: Streamlit UploadedFile object

    Returns:
        Dict with 'status' ("success"/"error") and 'message'
    """
    tmp_path = None
    try:
        # Write bytes to temp file — PyPDFLoader needs a real path
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        loader = PyPDFLoader(tmp_path)
        pages = loader.load()

        if not pages:
            return {"status": "error", "message": "PDF is empty or could not be read."}

        # Chunk — 512 chars with 50-char overlap for context continuity
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " ", ""],
        )
        chunks = splitter.split_documents(pages)

        # Tag each chunk with source filename for citation later
        for chunk in chunks:
            chunk.metadata["source"] = uploaded_file.name

        # Embed locally and store in ChromaDB
        vector_store = get_vector_store()
        vector_store.add_documents(chunks)

        return {
            "status": "success",
            "message": f"✅ '{uploaded_file.name}' — {len(chunks)} chunks stored in ChromaDB.",
            "chunk_count": len(chunks),
        }

    except Exception as e:
        return {"status": "error", "message": f"❌ Ingestion failed: {str(e)}"}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ─────────────────────────────────────────────
# CHROMADB SEARCH TOOL
# ─────────────────────────────────────────────
@tool
def chroma_local_search(query: str) -> List[Dict[str, str]]:
    """
    Search the local ChromaDB vector store for relevant chunks from uploaded documents.
    
    Best for: User-uploaded PDFs, private documents, internal reports.
    NOT for: Real-time info (use tavily_web_search) or academic papers (use arxiv_search).
    Returns empty/unhelpful results if no PDFs have been uploaded yet.
    
    Args:
        query: Natural language search query
    
    Returns:
        List of dicts with 'source' (filename) and 'content' (matching chunk text)
    """
    try:
        vector_store = get_vector_store()

        # Check if collection has anything — avoid wasted embedding call
        if vector_store._collection.count() == 0:
            return [{
                "source": "ChromaDB (empty)",
                "content": "No documents in local store. Upload PDFs in the sidebar first.",
            }]

        docs = vector_store.similarity_search(query, k=4)

        return [
            {
                "source": doc.metadata.get("source", "Local Document"),
                "content": doc.page_content,
            }
            for doc in docs
        ] or [{"source": "ChromaDB", "content": "No relevant chunks found for this query."}]

    except Exception as e:
        return [{"source": "error", "content": f"ChromaDB search failed: {str(e)}"}]