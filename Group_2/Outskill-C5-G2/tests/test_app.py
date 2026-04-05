import os
import pytest
from streamlit.testing.v1 import AppTest

def test_app_loads_api_gate():
    """Verify that when no keys are provided, the API key gate renders."""
    at = AppTest.from_file("app.py", default_timeout=30)
    
    # Overwrite the environment keys to empty strings so load_dotenv doesn't load real ones
    with pytest.MonkeyPatch.context() as m:
        m.setenv("OPENROUTER_API_KEY", "")
        m.setenv("TAVILY_API_KEY", "")
        at.run()
        
        assert not at.exception
        
        assert "**API Keys Required**" in at.warning[0].value
        
        # Verify gate inputs
        text_inputs = [ti.label for ti in at.text_input]
        assert "🔑 OpenRouter API Key" in text_inputs
        assert "🔑 Tavily Search API Key" in text_inputs
        
        # Verify Save button
        buttons = [btn.label for btn in at.button]
        assert "💾 Save Keys & Continue" in buttons

def test_ui_unlocks_with_keys():
    """Verify that when the API key gate receives keys, it unlocks the main UI."""
    at = AppTest.from_file("app.py", default_timeout=30)
    
    # Overwrite the environment keys to empty strings so load_dotenv doesn't load real ones
    with pytest.MonkeyPatch.context() as m:
        m.setenv("OPENROUTER_API_KEY", "")
        m.setenv("TAVILY_API_KEY", "")
        at.run()
        
        # Simulate entering keys in the sidebar
        at.text_input(key="openrouter_key").input("sk-or-v1-dummy").run()
        at.text_input(key="tavily_key").input("tvly-dummy").run()
        
        assert not at.exception
        
        # Verify standard dashboard elements load
        markdown_vals = [md.value for md in at.markdown]
        assert any("### 🎯 Research Question" in md for md in markdown_vals)

def test_sidebar_model_selection():
    """Verify the sidebar correctly handles model selection."""
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    
    model_selectbox = None
    for sb in at.selectbox:
        if sb.label == "LLM via OpenRouter":
            model_selectbox = sb
            break
            
    assert model_selectbox is not None
    # Change index and run
    if len(model_selectbox.options) > 1:
        model_selectbox.set_value(model_selectbox.options[1]).run()
        assert not at.exception

def test_mocked_research_pipeline_results():
    """Simulate a successful research pipeline run to verify the UI renders the results."""
    at = AppTest.from_file("app.py", default_timeout=30)
    
    # We will inject a dummy pipeline result into session_state before running
    # This bypasses the need for API keys / LLM execution
    dummy_result = {
        "final_report": "# Dummy Final Report\n\nThis is a mock report.",
        "raw_documents": [
            {"source": "mock_source_1", "content": "Mock content 1", "tool_used": "tavily_web_search", "sub_query": "mock query"}
        ],
        "routing_plan": [
            {"sub_query": "mock query", "tools": ["tavily_web_search"], "rationale": "Mock rationale"}
        ],
        "current_agent": "reporter",
        "error": None
    }
    
    at.session_state["pipeline_result"] = dummy_result
    at.session_state["last_query"] = "mock user question"
    at.session_state["pipeline_elapsed"] = 10.5
    at.session_state["openrouter_key"] = "mock_or_key"
    at.session_state["tavily_key"] = "mock_tvly_key"
    
    at.run()
    
    assert not at.exception
    
    # Check metrics existence
    metric_labels = [m.label for m in at.metric]
    assert "⏱️ Total Time" in metric_labels
    assert "📄 Doc Chunks" in metric_labels
    
    # Elements like download buttons might not be cleanly exposed in all versions of AppTest.
    # We verify the most critical parts: metrics and markdown presence.

    markdown_vals = [md.value for md in at.markdown]
    assert any("📋 Research Report" in md for md in markdown_vals)
    assert any("Dummy Final Report" in md for md in markdown_vals)
