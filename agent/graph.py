from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import classify_intent, process_parameters, execute_api_call, generate_response

def should_continue(state: AgentState) -> str:
    """Router to decide the next step."""
    if state.needs_clarification:
        return "generate_response"
    if state.intent and state.intent != "general_inquiry":
        return "execute_api_call"
    return "generate_response"

def after_api_call(state: AgentState) -> str:
    """Router after an API call to decide if we need more info or can generate a final response."""
    if state.needs_clarification:
        return "generate_response"
    return "generate_response"
    
def build_graph():
    """Builds the LangGraph workflow."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("process_parameters", process_parameters)
    workflow.add_node("execute_api_call", execute_api_call)
    workflow.add_node("generate_response", generate_response)

    # Define edges
    workflow.set_entry_point("classify_intent")
    workflow.add_edge("classify_intent", "process_parameters")
    
    # FIX: Changed to add_conditional_edges (plural)
    workflow.add_conditional_edges(
        "process_parameters",
        should_continue,
        {
            "execute_api_call": "execute_api_call",
            "generate_response": "generate_response"
        }
    )
    # FIX: Changed to add_conditional_edges (plural)
    workflow.add_conditional_edges(
        "execute_api_call",
        after_api_call,
        {
            "generate_response": "generate_response"
        }
    )
    workflow.add_edge("generate_response", END)

    return workflow.compile()