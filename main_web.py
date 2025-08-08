import streamlit as st
from agent.graph import build_graph
from agent.state import AgentState

st.set_page_config(page_title="Booking Agent (Ollama)", layout="wide")
st.title("Restaurant Booking Conversational Agent")

# Initialize graph and session state
if "app" not in st.session_state:
    st.session_state.app = build_graph()
if "state" not in st.session_state:
    st.session_state.state = AgentState()

# Display conversation history
for msg in st.session_state.state.conversation_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle user input
if prompt := st.chat_input("I'd like to book a table for 2 tomorrow..."):
    # Get the current state from session_state
    current_state = st.session_state.state
    current_state.user_message = prompt
    current_state.conversation_history.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # Invoke agent
    with st.spinner("Thinking..."):
        # The invoke method returns a dictionary-like object
        final_state_dict = st.session_state.app.invoke(current_state)

    # --- FIX APPLIED HERE ---
    # Access the agent_response using dictionary keys
    agent_response = final_state_dict.get('agent_response', "Sorry, something went wrong.")
    
    with st.chat_message("assistant"):
        st.markdown(agent_response)
    
    # Update the state object for the next turn
    st.session_state.state.conversation_history.append({"role": "assistant", "content": agent_response})
    st.session_state.state.booking_context = final_state_dict.get('booking_context', {})
    
    # Reset transient fields
    st.session_state.state.agent_response = ""
    st.session_state.state.api_response = None
    st.session_state.state.user_message = ""