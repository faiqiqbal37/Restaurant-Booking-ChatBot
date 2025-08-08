from agent.graph import build_graph
from agent.state import AgentState

def run_cli():
    """Starts the terminal-based chat interface."""
    app = build_graph()
    
    # Initialize the state using your dataclass
    # This object will be updated and reused in each loop iteration.
    current_state = AgentState()
    
    print("Restaurant Booking Agent (CLI) is ready. Type 'quit' to exit.")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'quit':
            break
            
        # Update the state with the new user message for this turn
        current_state.user_message = user_input
        
        # Invoke the graph. It takes the state dataclass, runs, and returns a dictionary.
        final_state_dict = app.invoke(current_state)
        
        # FIX: Access the result using dictionary keys, not attributes.
        agent_response_text = final_state_dict.get('agent_response', "Sorry, I encountered an issue and couldn't respond.")
        print(f"Agent: {agent_response_text}")
        
        # Update the conversation history in our state object for the next turn
        current_state.conversation_history = final_state_dict.get('conversation_history', [])
        
        # Also update the booking context to remember details across turns
        current_state.booking_context = final_state_dict.get('booking_context', {})
        
        # Reset parts of the state for the next turn
        current_state.user_message = ""
        current_state.api_response = None
        current_state.agent_response = ""

if __name__ == "__main__":
    run_cli()