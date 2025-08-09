from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import classify_intent, process_parameters, execute_api_call, generate_response

def should_continue_after_parameters(state: AgentState) -> str:
    """Router to decide the next step after parameter processing."""
    print(f"Router: intent={state.intent}, needs_clarification={state.needs_clarification}")
    
    # If we need clarification, go straight to response generation
    if state.needs_clarification:
        return "generate_response"
    
    # If it's a general inquiry, no API call needed
    if state.intent == "general_inquiry":
        return "generate_response"
    
    # For all other intents that require API calls
    if state.intent in ["check_availability", "make_booking", "check_booking", 
                       "cancel_booking", "modify_booking"]:
        return "execute_api_call"
    
    # Default to response generation
    return "generate_response"

def after_api_call(state: AgentState) -> str:
    """Router after an API call - always go to response generation."""
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
    
    # Always go from intent classification to parameter processing
    workflow.add_edge("classify_intent", "process_parameters")
    
    # Conditional routing after parameter processing
    workflow.add_conditional_edges(
        "process_parameters",
        should_continue_after_parameters,
        {
            "execute_api_call": "execute_api_call",
            "generate_response": "generate_response"
        }
    )
    
    # After API call, always generate response
    workflow.add_conditional_edges(
        "execute_api_call",
        after_api_call,
        {
            "generate_response": "generate_response"
        }
    )
    
    # End after generating response
    workflow.add_edge("generate_response", END)

    return workflow.compile()