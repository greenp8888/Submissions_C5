# LLM Configuration & Prompting Patterns

## The OpenRouter Abstraction Layer

The system uses a unified `llm` object initialized in `core/state.py`. This object is configured to use the `OpenRouter` provider, which acts as a proxy to access various commercial and open-source models (e.g., GPT-4o, Claude 3.5, Llama 3.3) via a single API key.

### Key Configuration Parameters

| Parameter | Location | Purpose |
|-----------|----------|---------|
| `model` | `core/state.py` | The specific model ID string (e.g., `openai/gpt-4o-mini`). |
| `temperature` | `core/state.py` | Controls randomness. Set to `0.0` for deterministic, research-grade output. |
| `max_tokens` | `core/state.py` | Limits response length to prevent rambling and ensure concise, actionable intelligence. |
| `base_url` | `core/state.py` | Points to `https://openrouter.ai/api/v1`. |
| `api_key` | `.env` | Loaded from `OPENROUTER_API_KEY`. |

---

## Prompting Patterns Used

### 1. The "Decision Matrix" Pattern (Planner)

The Planner agent uses a **fixed, hard-coded decision matrix** rather than asking the LLM which tool to use. This ensures deterministic routing and prevents the LLM from hallucinating tool names.

**Implementation:**
```python
# In agents/planner.py
DECISION_MATRIX = {
    "academic": ["arxiv_search", "chroma_local"],
    "current_events": ["tavily_web_search"],
    "general": ["tavily_web_search", "chroma_local"],
    "default": ["tavily_web_search"]
}

def planner_node(state: ResearchState, llm):
    # LLM reads this matrix and maps the query to a category
    category = llm.invoke(...)
    tools = DECISION_MATRIX.get(category, DECISION_MATRIX["default"])
    # ... generate sub-queries ...
```

### 2. The "Structured Output" Pattern (All Agents)

To ensure the LLM returns JSON-compatible data instead of prose, we use the `langchain_core.output_parsers.StrOutputParser` combined with strict system prompts.

**Implementation:**
```python
# In agents/analyst.py
SYSTEM_PROMPT = """
You are an analyst. Return ONLY a JSON object with keys: 'verified_facts', 'contradictions', 'confidence_score'.
Do NOT include markdown formatting or explanations."""

# In core/graph.py
chain = (prompt | llm | StrOutputParser())
```

### 3. The "Explicit Chain-of-Thought" Pattern (Insight Generator)

The Insight Generator is the only node allowed to perform "creative" reasoning. It is explicitly instructed to use a step-by-step logical flow to prevent leaps in logic.

**Implementation:**
```python
# In agents/insight.py
SYSTEM_PROMPT = """
Follow these steps:
1. OBSERVATION: What does the data explicitly state?
2. CONSEQUENCE: What logically follows from this observation?
3. HYPOTHESIS: What is the strategic implication?
4. RISK: What could invalidate this hypothesis?
Return ONLY the final hypothesis."""
```

### 4. The "APA Citation" Pattern (Reporter)

The Reporter is strictly forbidden from generating generic citations. It must extract the Title and URL directly from the retrieved documents.

**Implementation:**
```python
# In agents/reporter.py
SYSTEM_PROMPT = """
For each fact, append the citation in this exact format:
- [Title](URL)

Example: "The study found X. [Quantum Physics Explained](https://arxiv.org/abs/2401.0001)"
"""
```

---

## 🔧 Model Selection Strategy

The system is designed to be flexible. Here is the recommended model selection for balancing cost and performance:

| Agent | Recommended Model | Rationale |
|-------|-------------------|-----------|
| **Planner** | `openai/gpt-4o-mini` | Fast, cheap, and excellent at following structured logic. |
| **Retriever** | `openai/gpt-4o-mini` | Needs to parse JSON quickly; speed matters more than reasoning here. |
| **Analyst** | `openai/gpt-4o-mini` | Good at filtering and classification tasks. |
| **Insight Generator** | `openai/gpt-4o` or `anthropic/claude-3-5-sonnet` | Requires deep reasoning; worth the cost for better hypothesis generation. |
| **Reporter** | `openai/gpt-4o-mini` | Simple formatting task; no need for a powerful model. |

**Note:** The `model` variable in `core/state.py` can be changed globally to switch providers (e.g., from OpenAI to Anthropic) by simply updating the model string.
