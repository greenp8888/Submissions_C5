# MISSION
You are an elite Python Architect and LangGraph expert. Your task is to build "Chanakya-AI", a personalized Financial Coach application. We have a strict 12-hour deadline. You must prioritize clean, working, functional code over complex, scalable abstractions.

# TECH STACK
- Frontend: Streamlit
- Orchestration: LangGraph & LangChain
- LLM: OpenRouter (anthropic/claude-3.5-sonnet)
- Tools: Tavily API (for live internet search)
- Data Processing: Pandas

# ARCHITECTURE RULES (STRICT STRICT STRICT)
1. NO VECTOR DATABASES. Do not use Chroma, Pinecone, or LangChain vector stores. We are using "In-Context RAG".
2. You will read an uploaded CSV file using Pandas, convert it to a Markdown string, and pass it directly into the LangGraph state.
3. Use a simple "Router-Worker" LangGraph pattern to prevent infinite loops. 

# LANGGRAPH GRAPH SPECIFICATION
Define a `TypedDict` state with: `messages` (list), `financial_data` (string), and `route_decision` (string).
Nodes required:
1. `Supervisor_Node`: Looks at the user query and decides whether to route to 'debt_agent' or 'budget_agent'.
2. `Debt_Agent_Node`: Analyzes debt. MUST be equipped with the Tavily Tool.
3. `Budget_Agent_Node`: Analyzes spending and savings. MUST be equipped with the Tavily Tool.

# SYSTEM PROMPTS & INDIAN CONTEXT
You must hardcode these instructions into the System Prompts for the Debt and Budget agents:
"You are Chanakya-AI, a strict, SEBI-registered style Financial Coach in India. 
- Always output currency in Indian Rupees (₹) and use the Indian numbering system (Lakhs, Crores).
- You understand Indian tax regimes (80C, 80D, 24b).
- Prioritize clearing high-interest unsecured debt (Credit Cards at 36%+ APR or Personal Loans at 15%) before investing.
- Compare savings rates against Indian benchmarks like PPF (7.1%), Bank FDs, and the Nifty 50.
- If asked about current rates, use the Tavily search tool appending 'India 2026' to the query."

# STREAMLIT UI SPECIFICATION
- Build a clean chat interface using `st.chat_message`.
- Add a sidebar with:
  1. A file uploader restricted to CSVs.
  2. Text inputs for API Keys (OpenRouter API Key, Tavily API Key).
- When a CSV is uploaded, extract it to a markdown string and hold it in the session state to be passed to the LangGraph invocation.

# DELIVERABLES
Generate the complete implementation plan and write the following files:
1. `requirements.txt`
2. `graph.py` (Contains the LangGraph nodes, edges, state, and compilation)
3. `app.py` (Contains the Streamlit UI and invokes the graph)

Execute the code generation immediately after confirming this plan. Do not ask for permission to proceed with writing the code.