# 🧪 Testing Guide

This document outlines the automated testing strategy for the **Autonomous Research Assistant**. The test suite validates the core functionality, UI components, and knowledge base integrations without incurring live API costs.

## 🛠️ Testing Methodology

The project uses `pytest` as the primary test runner and leverages the `streamlit.testing` framework to simulate user interactions and interface rendering. Mocking is heavily utilized to isolate components from external network requests (e.g., OpenRouter, Tavily).

## 🚀 Running the Tests

To run the full test suite locally, ensure you have the virtual environment installed with `uv`, then execute:

```bash
uv run pytest tests/ -v
```

This will run all test files located in the `tests/` directory and output the results.

## 🗂️ Test Categories

### 1. Application flow and UI Tests (`test_app.py`)
These tests validate the Streamlit application logic and state management using `streamlit.testing.v1.AppTest`.
- **API Key Gate**: Verifies that the application successfully blocks access when the required `.env` variables or input credentials are missing, and ensures the correct prompts are rendered.
- **UI Unlocking**: Simulates a user entering dummy credentials into the sidebar and submitting them to verify the main research interface unlocks seamlessly.
- **Model Selection**: Ensures the sidebar component properly manages LLM selections.
- **Mocked Research Pipeline Result**: Injects raw pipeline outputs directly into the component's `session_state` to ensure that results, timing metrics, chunk processing info, and markdown generation are handled by the UI properly without triggering the actual LangGraph multi-agent execution pipeline.

### 2. Vector Store and Ingestion Tests (`test_vector_store.py`)
These unit tests focus on the local RAG capability, using `pytest.MonkeyPatch` and `unittest.mock.patch` to avoid persisting test data into the real ChromeDB cache.
- **PDF Ingestion Check** (`test_ingest_pdf_to_chroma`): Validates that a mocked file upload process correctly triggers `PyPDFLoader`, splits documents into chunks, and correctly logs the success status.
- **Query Resolution Check** (`test_chroma_local_search`): Verifies the localized LangChain tool returns proper empty warnings for non-matching sources and returns accurate chunk responses when documents match the query terms.

## 🛡️ Continuous Validation
We enforce correct API key isolation and robust garbage collection during these test executions to prevent "ResourceWarnings" from leaking an open async loop, ensuring complete production readiness.
