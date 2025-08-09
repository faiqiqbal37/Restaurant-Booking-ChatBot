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
    # Try to find JSON between curly braces
    match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Fallback: try to extract just the content between first { and last }
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass
    
    return None

def classify_intent(state: AgentState) -> AgentState:
    print("--- Node: Classify Intent ---")
    
    # Build conversation context string
    context_str = ""
    for msg in state.conversation_history[-4:]:  # Last 4 messages for better context
        context_str += f"{msg['role'].title()}: {msg['content']}\n"
    
    # Check if we're continuing an existing booking conversation
    # FIXED: Only consider it continuing if we're actually in a booking flow AND user isn't asking for something else
    continuing_booking = bool(
        state.booking_context and 
        any(state.booking_context.values()) and
        not any(keyword in state.user_message.lower() 
               for keyword in ['cancel', 'check my booking', 'modify', 'change', 
                              'available', 'availability', 'check availability', 'what times'])
    )
    
    print(f"Continuing booking: {continuing_booking}")
    print(f"Current booking context: {state.booking_context}")
    
    prompt = INTENT_CLASSIFICATION_PROMPT.format(
        conversation_history=context_str,
        user_message=state.user_message,
        current_booking_context=json.dumps(state.booking_context, indent=2)
    )
    
    try:
        response_text = llm.invoke(prompt).content
        print(f"Raw LLM response: {response_text}")  # Debug output
        
        parsed_response = extract_json(response_text)
        
        if parsed_response:
            # FIXED: Let the LLM's intent classification take precedence
            # Only override if we're truly continuing a booking AND the intent makes sense in that context
            llm_intent = parsed_response.get("intent", "general_inquiry")
            
            if continuing_booking and llm_intent in ['make_booking', 'general_inquiry']:
                # Only keep make_booking if the LLM also thinks it's booking-related
                state.intent = "make_booking"
            else:
                # Trust the LLM's classification for all other cases
                state.intent = llm_intent
            
            # Clean and validate parameters
            raw_params = parsed_response.get("parameters", {})
            state.parameters = {}
            
            # Extract and validate each parameter
            for key, value in raw_params.items():
                if value is not None and str(value).strip() not in ["", "null", "None"]:
                    # Special handling for party_size - convert to int
                    if key == "party_size":
                        try:
                            # Handle written numbers
                            number_words = {
                                'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                                'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
                            }
                            value_str = str(value).lower().strip()
                            if value_str in number_words:
                                state.parameters[key] = number_words[value_str]
                            else:
                                # Try to extract number from text like "for 4 people" or "4"
                                number_match = re.search(r'\d+', str(value))
                                if number_match:
                                    state.parameters[key] = int(number_match.group())
                                else:
                                    state.parameters[key] = int(value)
                        except (ValueError, TypeError):
                            print(f"Could not parse party_size: {value}")
                            continue  # Skip invalid party sizes
                    else:
                        state.parameters[key] = str(value).strip()
            
            state.needs_clarification = parsed_response.get("needs_clarification", False)
            state.clarification_message = parsed_response.get("clarification_message", "")
            
            print(f"Classified intent: {state.intent}")
            print(f"Extracted parameters: {state.parameters}")
        else:
            print("Failed to parse JSON response, using fallback")
            # FIXED: For fallback, don't assume continuing booking
            # Try to determine intent from keywords in the user message
            user_msg_lower = state.user_message.lower()
            
            if any(word in user_msg_lower for word in ['available', 'availability', 'check availability', 'what times', 'free tables']):
                state.intent = "check_availability"
            elif any(word in user_msg_lower for word in ['book', 'reserve', 'table', 'reservation']) and continuing_booking:
                state.intent = "make_booking"
            elif any(word in user_msg_lower for word in ['cancel']) and 'booking' in user_msg_lower:
                state.intent = "cancel_booking"
            elif continuing_booking:
                state.intent = "make_booking"
            else:
                state.intent = "general_inquiry"
                
            state.needs_clarification = True
            state.clarification_message = "I'm sorry, I had trouble understanding that. Could you please rephrase your request?"
            
    except Exception as e:
        print(f"Error in intent classification: {e}")
        # FIXED: Same logic for error handling
        user_msg_lower = state.user_message.lower()
        
        if any(word in user_msg_lower for word in ['available', 'availability', 'check availability', 'what times', 'free tables']):
            state.intent = "check_availability"
        elif continuing_booking:
            state.intent = "make_booking"
        else:
            state.intent = "general_inquiry"
            
        state.needs_clarification = True
        state.clarification_message = "I encountered an error processing your request. Could you please try again?"
    
    return state
    
def process_parameters(state: AgentState) -> AgentState:
    print("--- Node: Process Parameters ---")
    print(f"Current booking context: {state.booking_context}")
    print(f"New parameters: {state.parameters}")
    
    # Update booking context with new valid parameters
    if state.parameters:
        for key, value in state.parameters.items():
            if value is not None and str(value).strip() not in ["", "null", "None"]:
                print(f"Adding {key}: {value} to booking context")
                state.booking_context[key] = value
    
    print(f"Updated booking context: {state.booking_context}")
    
    # Process and validate date
    if state.booking_context.get('date'):
        raw_date = state.booking_context['date']
        parsed_date = parse_natural_date(raw_date)
        if parsed_date:
            state.booking_context['date'] = parsed_date
            print(f"Parsed date: {parsed_date}")
        else:
            state.needs_clarification = True
            state.clarification_message = f"I couldn't understand the date '{raw_date}'. Could you provide it in YYYY-MM-DD format or use terms like 'today', 'tomorrow', or 'next Friday'?"
            return state
    
    # Validate time format if provided
    if state.booking_context.get('time'):
        time_str = str(state.booking_context['time'])
        # Check if time is in valid format
        time_pattern1 = re.compile(r'^\d{1,2}:\d{2}$')
        time_pattern2 = re.compile(r'^\d{1,2}(am|pm)$', re.IGNORECASE)
        
        if not time_pattern1.match(time_str) and not time_pattern2.match(time_str):
            # Try to convert common formats
            converted_time = convert_time_format(time_str)
            if converted_time:
                state.booking_context['time'] = converted_time
                print(f"Converted time: {converted_time}")
            else:
                state.needs_clarification = True
                state.clarification_message = f"I couldn't understand the time '{time_str}'. Could you provide it in HH:MM format (like 19:30) or with AM/PM (like 7:30 PM)?"
                return state
    
    # Check if we have required parameters for the intent
    state = check_required_parameters(state)
    
    return state

def convert_time_format(time_str: str) -> str:
    """Convert various time formats to HH:MM format."""
    time_str = time_str.lower().strip()
    
    # Handle formats like "7pm", "7:30pm", "19:30"
    if 'pm' in time_str:
        time_part = time_str.replace('pm', '').strip()
        if ':' in time_part:
            hour, minute = time_part.split(':')
        else:
            hour, minute = time_part, '00'
        
        try:
            hour = int(hour)
            if hour < 12:
                hour += 12
            return f"{hour:02d}:{minute}"
        except ValueError:
            return ""
    
    elif 'am' in time_str:
        time_part = time_str.replace('am', '').strip()
        if ':' in time_part:
            hour, minute = time_part.split(':')
        else:
            hour, minute = time_part, '00'
        
        try:
            hour = int(hour)
            if hour == 12:
                hour = 0
            return f"{hour:02d}:{minute}"
        except ValueError:
            return ""
    
    # Handle formats like "7", "7:30" (assume 24-hour if no AM/PM)
    elif ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 2:
            try:
                hour = int(parts[0])
                minute = int(parts[1])
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return f"{hour:02d}:{minute:02d}"
            except ValueError:
                pass
    
    return ""

def check_required_parameters(state: AgentState) -> AgentState:
    """Check if we have all required parameters for the current intent."""
    intent = state.intent
    context = state.booking_context
    
    print(f"Checking required parameters for intent: {intent}")
    print(f"Available context: {context}")
    
    missing_params = []
    
    if intent == "check_availability":
        if not context.get("date"):
            missing_params.append("date")
        if not context.get("party_size"):
            missing_params.append("number of people")
    
    elif intent == "make_booking":
        # Check each required parameter individually
        required_fields = {
            "date": "date",
            "time": "time", 
            "party_size": "number of people",
            "customer_name": "your name",
            "phone": "phone number"
        }
        
        for field, description in required_fields.items():
            if not context.get(field):
                missing_params.append(description)
                print(f"Missing required field: {field} ({description})")
    
    elif intent in ["check_booking", "cancel_booking", "modify_booking"]:
        if not context.get("booking_reference"):
            missing_params.append("booking reference")
    
    print(f"Missing parameters: {missing_params}")
    
    if missing_params:
        state.needs_clarification = True
        if len(missing_params) == 1:
            state.clarification_message = f"I need your {missing_params[0]} to complete the booking. Could you please provide it?"
        else:
            # Only ask for the first missing item to avoid overwhelming the user
            state.clarification_message = f"I need your {missing_params[0]} to continue. Could you please provide it?"
    else:
        print("All required parameters are available!")
        state.needs_clarification = False
        state.clarification_message = ""
    
    return state

def execute_api_call(state: AgentState) -> AgentState:
    print(f"--- Node: Execute API Call for intent '{state.intent}' ---")
    intent = state.intent
    context = state.booking_context
    
    try:
        if intent == "check_availability":
            state.api_response = api_client.check_availability(
                context["date"], 
                int(context["party_size"])
            )
        
        elif intent == "make_booking":
            # Split customer name into first and last name
            full_name = context["customer_name"].strip().split()
            first_name = full_name[0]
            surname = full_name[-1] if len(full_name) > 1 else "Guest"
            
            # Generate email (in production, you'd ask for this)
            email = f"{first_name.lower()}.{surname.lower()}@example.com"
            
            state.api_response = api_client.create_booking(
                context["date"],
                context["time"], 
                int(context["party_size"]),
                first_name,
                surname,
                email,
                context["phone"]
            )
        
        elif intent == "check_booking":
            state.api_response = api_client.get_booking_details(context["booking_reference"])
        
        elif intent == "cancel_booking":
            state.api_response = api_client.cancel_booking(context["booking_reference"])
        
        elif intent == "modify_booking":
            # For modify_booking, we need the booking reference and at least one field to modify
            booking_ref = context["booking_reference"]
            new_date = context.get("new_date")
            new_time = context.get("new_time") 
            new_party_size = context.get("new_party_size")
            
            if new_date or new_time or new_party_size:
                state.api_response = api_client.update_booking(
                    booking_ref, new_date, new_time, 
                    int(new_party_size) if new_party_size else None
                )
            else:
                state.needs_clarification = True
                state.clarification_message = "What would you like to change about your booking? You can modify the date, time, or party size."
                return state
    
    except Exception as e:
        print(f"API call error: {e}")
        state.api_response = {
            "status": 500,
            "error": f"Sorry, I encountered an error while processing your request: {str(e)}"
        }
    
    return state

def generate_response(state: AgentState) -> AgentState:
    print("--- Node: Generate Response ---")
    
    # If we need clarification, return the clarification message
    if state.needs_clarification and state.clarification_message:
        state.agent_response = state.clarification_message
        # Add this exchange to conversation history
        state.conversation_history.append({"role": "user", "content": state.user_message})
        state.conversation_history.append({"role": "assistant", "content": state.agent_response})
        return state
    
    # Generate response based on API result
    try:
        prompt = RESPONSE_GENERATION_PROMPT.format(
            intent=state.intent,
            parameters=json.dumps(state.parameters, indent=2),
            api_response=json.dumps(state.api_response, indent=2) if state.api_response else "No API call was made",
            booking_context=json.dumps(state.booking_context, indent=2)
        )
        
        # Use regular LLM without JSON formatting for natural response
        response_llm = ChatOllama(model="llama3.2")
        state.agent_response = response_llm.invoke(prompt).content
        
    except Exception as e:
        print(f"Response generation error: {e}")
        state.agent_response = "I apologize, but I encountered an error while generating my response. Please try again."
    
    # Add this exchange to conversation history
    state.conversation_history.append({"role": "user", "content": state.user_message})
    state.conversation_history.append({"role": "assistant", "content": state.agent_response})
    
    return state