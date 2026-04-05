import os
import pytest
from unittest.mock import patch
from langchain_core.documents import Document

import tools.vector_store
from tools.vector_store import ingest_pdf_to_chroma, chroma_local_search

@pytest.fixture
def mock_chroma_env(monkeypatch, tmp_path):
    """Overrides the persistent directory to use a temporary location for tests."""
    monkeypatch.setattr(tools.vector_store, "CHROMA_PERSIST_DIR", str(tmp_path / "chroma_db"))

def test_ingest_pdf_to_chroma(mock_chroma_env):
    """Validates the PDF ingestion wrapper independently."""
    class MockUploadedFile:
        def __init__(self, name, content):
            self.name = name
            self.content = content
        def getvalue(self):
            return self.content.encode('utf-8')
    
    fake_file = MockUploadedFile("test_doc.pdf", "Dummy PDF content bytes.")

    with patch("tools.vector_store.PyPDFLoader") as MockLoader:
        mock_instance = MockLoader.return_value
        mock_instance.load.return_value = [
            Document(
                page_content="This is a test document concerning the global economy. Another sentence for good measure.", 
                metadata={"source": "test_doc.pdf", "page": 1}
            )
        ]
        
        result = ingest_pdf_to_chroma(fake_file)
        assert result["status"] == "success"
        assert result["chunk_count"] > 0

def test_chroma_local_search(mock_chroma_env):
    """Validates the chroma_local_search tool correctly looks up similarities."""
    # Searching an empty store
    results_empty = chroma_local_search.invoke({"query": "economy"})
    assert any("No documents in local store" in r["content"] for r in results_empty)
    
    # Adding data to store
    class MockUploadedFile:
        def __init__(self, name, content):
            self.name = name
            self.content = content
        def getvalue(self):
            return self.content.encode('utf-8')
    
    fake_file = MockUploadedFile("test_doc.pdf", "Dummy PDF content bytes.")
    with patch("tools.vector_store.PyPDFLoader") as MockLoader:
        mock_instance = MockLoader.return_value
        mock_instance.load.return_value = [
            Document(
                page_content="The quick brown fox jumps over the lazy dog.", 
                metadata={"source": "test_doc.pdf", "page": 1}
            )
        ]
        ingest_pdf_to_chroma(fake_file)
        
    # Searching populated store
    results_populated = chroma_local_search.invoke({"query": "fox"})
    assert len(results_populated) > 0
    assert any("fox" in r["content"].lower() for r in results_populated)
