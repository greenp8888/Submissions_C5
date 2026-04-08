from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.config import CHUNK_SIZE, CHUNK_OVERLAP, MAX_RETRIEVAL_K, EMBEDDING_MODEL


def create_vector_store_from_pdfs(file_paths: list[str]) -> FAISS:
    """Create a FAISS vector store from a list of PDF file paths."""
    all_docs = []
    for file_path in file_paths:
        loader = PyPDFLoader(file_path)
        all_docs.extend(loader.load())

    if not all_docs:
        raise ValueError("No documents loaded from PDFs")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    texts = splitter.split_documents(all_docs)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return FAISS.from_documents(texts, embeddings)


def create_retriever(vector_store: FAISS, k: int = MAX_RETRIEVAL_K):
    """Create a retriever from a FAISS vector store."""
    return vector_store.as_retriever(search_kwargs={"k": k})


def get_relevant_snippets(
    retriever, query: str, max_snippets: int = 6, max_chars: int = 1500
) -> str:
    """Get relevant text snippets from the retriever for a given query."""
    if not retriever or not query.strip():
        return ""

    try:
        if hasattr(retriever, "invoke"):
            docs = retriever.invoke(query)
        else:
            docs = retriever.get_relevant_documents(query)

        return "\n\n---\n\n".join(
            (d.page_content or "")[:max_chars] for d in (docs or [])[:max_snippets]
        )
    except Exception:
        return ""
