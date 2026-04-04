## Langraph Introductory Code



# Step 1: Define the Graph State
from typing import Dict, TypedDict, Optional
from langgraph.graph import StateGraph, END

#States, #Nodes, #Edges
'''
State

step 0: {question:null, classification:null, response:null}
Pressed button - step 1: {question:"Hi, how are you?", classification:null, response:null}
# Now first node is executed
step 2: {question:"Hi, how are you?", classification:"greeting", response:null}
step 3: {question:"how are you?", classification:"greeting", response:"Hello! How can I help you today?'"}
'''


#states defination Step 1
class OutskillClass(TypedDict):
    question: Optional[str]
    classification: Optional[str]
    response: Optional[str]


# Step 2: Create the Graph Canvas
workflow = StateGraph(OutskillClass)

#helper function to classify input
def classify(question: str) -> str:
    print("In classify " + question)
    greetings = ["hello", "hi", "hey"]
    if any(word in question.lower() for word in greetings):
        return "greeting"
    return "search"

# Step 3: Define Nodes

def classify_input_node(state):
    question = state.get('question', '').strip() #Hi, How are you?
    classification = classify(question) #greteeting
    print(classification)
    return {"classification": classification}

def handle_greeting_node(state):
    return {"response": "Hello! How can I help you today?"}

def handle_search_node(state):
    question = state.get('question', '').strip()
    search_result = f"Paras this is a serach result for the '{question}'"
    return {"response": search_result}

# Step 4: Add Nodes to the Graph
workflow.add_node("classify_input", classify_input_node)
workflow.add_node("handle_greeting", handle_greeting_node)
workflow.add_node("handle_search", handle_search_node)

# Decide which node to go to
def decide_next_node(state):
    return "handle_greeting" if state.get('classification') == "greeting" else "handle_search"



# Step 5: Set Entry and End Points
workflow.set_entry_point("classify_input")

workflow.add_conditional_edges(
    "classify_input",
    decide_next_node,
    {
        "handle_greeting": "handle_greeting",
        "handle_search": "handle_search"
    }
)

workflow.add_edge("handle_greeting", END)
workflow.add_edge("handle_search", END)

# Step 6: Compile the graph
app = workflow.compile()

inputs = {"question": "how are you?"}
result = app.invoke(inputs) # Runs the graph with the given inputs
print(result)
