import streamlit as st
import json
from agent.graph import build_graph
from agent.state import AgentState

# Page configuration
st.set_page_config(
    page_title="TheHungryUnicorn Booking Agent", 
    layout="wide",
    page_icon="🍴"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .booking-context {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #1f77b4;
        margin: 10px 0;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
        margin: 10px 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
        margin: 10px 0;
    }
    .help-text {
        font-size: 0.9em;
        color: #6c757d;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🍴 TheHungryUnicorn Restaurant Booking Agent")
st.markdown("---")

# Sidebar with help information
with st.sidebar:
    st.header("🔧 Features")
    st.markdown("""
    **I can help you with:**
    - 📅 Check table availability
    - 🍽️ Make new bookings
    - 👀 View existing bookings
    - ✏️ Modify reservations
    - ❌ Cancel bookings
    - ❓ General restaurant questions
    

    """)
    
    # Debug section (expandable)
    with st.expander("🐛 Debug Info"):
        if "state" in st.session_state:
            st.json(st.session_state.state.booking_context)
            st.text(f"Intent: {getattr(st.session_state.state, 'intent', 'None')}")
            st.text(f"Messages: {len(st.session_state.state.conversation_history)}")

# Initialize graph and session state
if "app" not in st.session_state:
    with st.spinner("Initializing booking agent..."):
        st.session_state.app = build_graph()
    st.success("✅ Booking agent ready!")

if "state" not in st.session_state:
    st.session_state.state = AgentState()

if "show_context" not in st.session_state:
    st.session_state.show_context = True

# # Show current booking context if active
# if (st.session_state.state.booking_context and 
#     st.session_state.show_context and
#     any(st.session_state.state.booking_context.values())):
    
#     st.markdown("### 📋 Current Booking Information")
    
#     context = st.session_state.state.booking_context
#     context_display = []
    
#     if context.get('date'):
#         context_display.append(f"**Date:** {context['date']}")
#     if context.get('time'):
#         context_display.append(f"**Time:** {context['time']}")
#     if context.get('party_size'):
#         context_display.append(f"**Party Size:** {context['party_size']} people")
#     if context.get('customer_name'):
#         context_display.append(f"**Name:** {context['customer_name']}")
#     if context.get('phone'):
#         context_display.append(f"**Phone:** {context['phone']}")
#     if context.get('booking_reference'):
#         context_display.append(f"**Reference:** {context['booking_reference']}")
    
#     if context_display:
#         st.markdown('<div class="booking-context">', unsafe_allow_html=True)
#         st.markdown(" | ".join(context_display))
        
#         col1, col2 = st.columns([1, 4])
#         with col1:
#             if st.button("Clear Context", key="clear_context"):
#                 st.session_state.state.booking_context = {}
#                 st.rerun()
#         with col2:
#             st.session_state.show_context = st.checkbox(
#                 "Show booking context", 
#                 value=st.session_state.show_context
#             )
        
#         st.markdown('</div>', unsafe_allow_html=True)

# Main chat interface
st.markdown("### 💬 Chat")

# Display conversation history
chat_container = st.container()
with chat_container:
    for i, msg in enumerate(st.session_state.state.conversation_history):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Handle user input
if prompt := st.chat_input("Type your message here... (e.g., 'Book a table for 4 tomorrow at 7pm')"):
    
    # Validate input
    if not prompt.strip():
        st.error("Please enter a message!")
        st.stop()
    
    # Clear previous transient state
    st.session_state.state.clear_transient_state()
    
    # Set the new user message
    st.session_state.state.user_message = prompt
    
    # Add user message to display
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Process through the agent
    with st.chat_message("assistant"):
        with st.spinner("Processing your request..."):
            try:
                # Invoke the graph
                final_state_dict = st.session_state.app.invoke(st.session_state.state)
                
                # Extract response
                agent_response = final_state_dict.get(
                    'agent_response', 
                    "I apologize, but I encountered an issue processing your request."
                )
                
                # Display response
                st.markdown(agent_response)
                
                # Update persistent state
                st.session_state.state.conversation_history = final_state_dict.get(
                    'conversation_history', 
                    st.session_state.state.conversation_history
                )
                st.session_state.state.booking_context = final_state_dict.get(
                    'booking_context', 
                    st.session_state.state.booking_context
                )
                st.session_state.state.intent = final_state_dict.get('intent')
                
                # Show success/error indicators based on API response
                api_response = final_state_dict.get('api_response')
                if api_response:
                    status = api_response.get('status', 0)
                    if status == 200 or status == 201:
                        # Successful API call
                        if 'booking created' in agent_response.lower() or 'confirmed' in agent_response.lower():
                            st.markdown('<div class="success-message">✅ Booking operation completed successfully!</div>', 
                                      unsafe_allow_html=True)
                        elif 'cancelled' in agent_response.lower():
                            st.markdown('<div class="success-message">✅ Cancellation completed successfully!</div>', 
                                      unsafe_allow_html=True)
                    elif status >= 400:
                        # API error
                        st.markdown('<div class="error-message">⚠️ There was an issue with your request. Please check the details above.</div>', 
                                  unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.markdown("Please try again or contact the restaurant directly.")
    
    # Force refresh to show updated context
    st.rerun()

# Footer with additional controls
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🔄 Reset Conversation", help="Clear all conversation history"):
        st.session_state.state = AgentState()
        st.rerun()

with col2:
    if st.button("📞 Contact Restaurant", help="Get restaurant contact information"):
        st.info("📍 TheHungryUnicorn Restaurant\n📞 Phone: Call for direct bookings\n🌐 Visit our website for more information")

with col3:
    if st.button("❓ Help", help="Show usage examples"):
        st.info("""
        **Example requests:**
        
        🍽️ **Making a booking:**
        - "Book a table for 4 people tomorrow at 7:30pm, name is John Smith, phone 123-456-7890"
        - "I'd like to make a reservation for next Friday evening"
        
        📅 **Checking availability:**
        - "What times are available this weekend for 2 people?"
        - "Do you have any tables free on December 25th?"
        
        👀 **Managing bookings:**
        - "Check my booking ABC123"
        - "Cancel my reservation for tomorrow"
        - "Change my booking from 6pm to 8pm"
        """)

with col4:
    # Export conversation
    if st.session_state.state.conversation_history:
        conversation_text = "\n\n".join([
            f"{msg['role'].title()}: {msg['content']}" 
            for msg in st.session_state.state.conversation_history
        ])
        st.download_button(
            "💾 Export Chat", 
            data=conversation_text,
            file_name="booking_conversation.txt",
            mime="text/plain",
            help="Download conversation history"
        )

# Help text at bottom
st.markdown('<p class="help-text">💡 Tip: Be specific with your requests. Include date, time, party size, and contact details for bookings.</p>', 
            unsafe_allow_html=True)