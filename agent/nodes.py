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
    if state.parameters.get('date'):
        parsed_date = parse_natural_date(state.parameters['date'])
        state.parameters['date'] = parsed_date
        if not parsed_date:
            state.needs_clarification = True
            state.clarification_message = "I couldn't understand that date. Could you provide it in YYYY-MM-DD format?"
    
    # Update booking context with any newly provided, valid parameters
    state.booking_context.update({k: v for k, v in state.parameters.items() if v is not None})
    return state
    
def execute_api_call(state: AgentState) -> AgentState:
    print(f"--- Node: Execute API Call for intent '{state.intent}' ---")
    intent = state.intent
    params = state.booking_context # Use the full context
    
    if intent == "check_availability":
        if params.get("date") and params.get("party_size"):
            state.api_response = api_client.check_availability(params["date"], params["party_size"])
        else:
            state.needs_clarification = True
    elif intent == "make_booking":
        required = ["date", "time", "party_size", "customer_name", "phone"]
        if all(params.get(k) for k in required):
            state.api_response = api_client.create_booking(
                params["date"], params["time"], params["party_size"],
                params["customer_name"], params["surname"], # Assuming name is first name
                params["email"], params["phone"]
            )
        else:
            state.needs_clarification = True
    elif intent == "check_booking":
        if params.get("booking_reference"):
            state.api_response = api_client.get_booking_details(params["booking_reference"])
        else:
            state.needs_clarification = True
    elif intent == "cancel_booking":
        if params.get("booking_reference"):
            state.api_response = api_client.cancel_booking(params["booking_reference"])
        else:
            state.needs_clarification = True
    # Add other intents like modify_booking here
            
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