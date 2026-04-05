"""Tests for Contextual Retriever Agent."""
import pytest
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from state import create_initial_state
from agents.retriever import retrieve_sources, _dedup_sources, _generate_source_id


class TestGenerateSourceId:
    def test_format(self):
        assert _generate_source_id("arxiv", 0) == "arxiv-001"
        assert _generate_source_id("web", 9) == "web-010"
        assert _generate_source_id("wiki", 99) == "wiki-100"


class TestDedupSources:
    def test_dedup_by_url(self):
        sources = [
            {"title": "Paper A", "url": "https://arxiv.org/abs/123"},
            {"title": "Paper B", "url": "https://arxiv.org/abs/123"},
            {"title": "Paper C", "url": "https://arxiv.org/abs/456"},
        ]
        result = _dedup_sources(sources)
        assert len(result) == 2

    def test_dedup_by_title(self):
        sources = [
            {"title": "Quantum Error Correction", "url": "https://a.com"},
            {"title": "quantum error correction", "url": "https://b.com"},
            {"title": "Different Paper", "url": "https://c.com"},
        ]
        result = _dedup_sources(sources)
        assert len(result) == 2

    def test_no_dedup_needed(self):
        sources = [
            {"title": "A", "url": "https://a.com"},
            {"title": "B", "url": "https://b.com"},
        ]
        result = _dedup_sources(sources)
        assert len(result) == 2

    def test_empty_input(self):
        assert _dedup_sources([]) == []


class TestRetrieveSources:
    def test_no_sub_questions(self):
        state = create_initial_state("test query")
        result = retrieve_sources(state)
        assert result["sources"] == []
        assert "No sub-questions" in result["retrieval_summary"]

    @patch("agents.retriever.search_news")
    @patch("agents.retriever.search_web")
    @patch("agents.retriever.search_wikipedia")
    @patch("agents.retriever.search_arxiv")
    def test_successful_retrieval(self, mock_arxiv, mock_wiki, mock_web, mock_news):
        # Setup mocks
        mock_arxiv.invoke.return_value = [
            {"title": "QEC Paper", "summary": "About QEC", "authors": "Author A",
             "url": "https://arxiv.org/abs/1", "published": "2024-01-01", "categories": ["quant-ph"]}
        ]
        mock_wiki.invoke.return_value = [
            {"title": "Quantum Computing", "summary": "Overview...", "content": "Full content...",
             "url": "https://en.wikipedia.org/wiki/Quantum_computing"}
        ]
        mock_web.invoke.return_value = [
            {"title": "QEC Breakthrough", "content": "Recent news...",
             "url": "https://news.com/qec", "score": 0.9}
        ]
        mock_news.invoke.return_value = [
            {"title": "Google QEC", "content": "Google announced...",
             "url": "https://news.com/google", "score": 0.85}
        ]

        state = create_initial_state("quantum error correction")
        state["sub_questions"] = [
            {"id": 1, "question": "What is QEC?", "search_keywords": ["quantum error correction"],
             "priority": 1, "reasoning": "Core question"},
        ]

        result = retrieve_sources(state)

        assert len(result["sources"]) >= 3  # arxiv + wiki + web + news
        assert result["retrieval_round"] == 1
        assert "Retrieved" in result["retrieval_summary"]

        # Verify source types
        types = {s["source_type"] for s in result["sources"]}
        assert "ARXIV" in types
        assert "WIKIPEDIA" in types
        assert "WEB" in types

    @patch("agents.retriever.search_news")
    @patch("agents.retriever.search_web")
    @patch("agents.retriever.search_wikipedia")
    @patch("agents.retriever.search_arxiv")
    def test_handles_tool_errors(self, mock_arxiv, mock_wiki, mock_web, mock_news):
        """Pipeline should continue even if some tools fail."""
        mock_arxiv.invoke.side_effect = Exception("ArXiv down")
        mock_wiki.invoke.return_value = [{"error": "disambiguation"}]
        mock_web.invoke.return_value = [
            {"title": "Result", "content": "Content", "url": "https://r.com", "score": 0.8}
        ]
        mock_news.invoke.return_value = []

        state = create_initial_state("test")
        state["sub_questions"] = [
            {"id": 1, "question": "Test?", "search_keywords": ["test"], "priority": 1, "reasoning": "test"},
        ]

        result = retrieve_sources(state)

        # Should still return web results despite arxiv + wiki failures
        assert len(result["sources"]) >= 1
        assert result["sources"][0]["source_type"] == "WEB"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
