# Path: agent/nodes.py

import json
import re
from langchain_community.chat_models import ChatOllama
from agent.state import AgentState
from agent.prompts import INTENT_CLASSIFICATION_PROMPT, RESPONSE_GENERATION_PROMPT
from api.client import BookingAPIClient
from utils.parsers import parse_natural_date

# Initialize components
llm = ChatOllama(model="llama3.2", format="json")
api_client = BookingAPIClient()

def extract_json(text: str):
    """Extracts the first valid JSON object from a string."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None

def classify_intent(state: AgentState) -> AgentState:
    print("--- Node: Classify Intent ---")
    # Clean previous clarification state to avoid confusion
    state.needs_clarification = False
    state.clarification_message = ""
    
    prompt = INTENT_CLASSIFICATION_PROMPT.format(
        conversation_history=state.conversation_history,
        user_message=state.user_message
    )
    response_text = llm.invoke(prompt).content
    parsed_response = extract_json(response_text)
    
    if parsed_response:
        state.intent = parsed_response.get("intent")
        state.parameters = parsed_response.get("parameters", {})
        state.needs_clarification = parsed_response.get("needs_clarification", False)
        state.clarification_message = parsed_response.get("clarification_message", "")
    else:
        state.intent = "general_inquiry"
        state.agent_response = "I'm sorry, I had trouble understanding that. Could you please rephrase?"
    return state

def process_parameters(state: AgentState) -> AgentState:
    print("--- Node: Process Parameters ---")
    # Update booking context with any newly provided, valid parameters
    if state.parameters:
        state.booking_context.update({k: v for k, v in state.parameters.items() if v is not None})

    # Standardize the date if it exists in the context
    if state.booking_context.get('date'):
        parsed_date = parse_natural_date(state.booking_context['date'])
        state.booking_context['date'] = parsed_date
        # If parsing fails, we now know we need to ask for clarification
        if not parsed_date:
            state.needs_clarification = True
            state.clarification_message = "I couldn't understand that date. Could you provide it in YYYY-MM-DD format, please?"
    
    return state
    
def execute_api_call(state: AgentState) -> AgentState:
    print(f"--- Node: Execute API Call for intent '{state.intent}' ---")
    intent = state.intent
    context = state.booking_context
    
    if intent == "check_availability":
        if context.get("date") and context.get("party_size"):
            state.api_response = api_client.check_availability(context["date"], context["party_size"])
        else:
            state.needs_clarification = True # Set flag if data is missing
    
    elif intent == "make_booking":
        # --- LOGIC FLAW FIX: Explicitly check for all required params ---
        required_keys = ["date", "time", "party_size", "customer_name", "phone"]
        if all(context.get(k) for k in required_keys):
            # --- KEYERROR FIX: Split customer_name into first and last names ---
            full_name = context["customer_name"].split()
            first_name = full_name[0]
            surname = full_name[-1] if len(full_name) > 1 else "Guest" # Fallback for single names
            
            # Assuming email is not gathered for simplicity, using a placeholder
            email = f"{first_name.lower()}.{surname.lower()}@example.com"

            state.api_response = api_client.create_booking(
                context["date"], context["time"], context["party_size"],
                first_name, surname, email, context["phone"]
            )
        else:
            state.needs_clarification = True # Set flag if data is missing

    elif intent == "check_booking":
        if context.get("booking_reference"):
            state.api_response = api_client.get_booking_details(context["booking_reference"])
        else:
            state.needs_clarification = True

    elif intent == "cancel_booking":
        if context.get("booking_reference"):
            state.api_response = api_client.cancel_booking(context["booking_reference"])
        else:
            state.needs_clarification = True
            
    return state

def generate_response(state: AgentState) -> AgentState:
    print("--- Node: Generate Response ---")
    if state.needs_clarification and state.clarification_message:
        state.agent_response = state.clarification_message
        return state

    prompt = RESPONSE_GENERATION_PROMPT.format(
        intent=state.intent,
        parameters=state.parameters,
        api_response=state.api_response
    )
    # Use a different LLM config for natural language generation
    response_llm = ChatOllama(model="llama3.2")
    state.agent_response = response_llm.invoke(prompt).content
    return state