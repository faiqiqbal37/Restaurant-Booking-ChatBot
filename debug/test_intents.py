# Path: debug/test_intents.py

import json
import sys
import os

# Add parent directory to path to import agent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.nodes import classify_intent_with_rules, extract_parameters_with_rules, extract_json
from agent.state import AgentState
from langchain_community.chat_models import ChatOllama

def test_intent_classification():
    """Test intent classification with various examples."""
    
    test_cases = [
        # Check booking cases
        {
            "message": "Check my booking ABC123",
            "expected": "check_booking",
            "description": "Check existing booking with reference"
        },
        {
            "message": "What time is my reservation?",
            "expected": "check_booking", 
            "description": "Check existing booking without reference"
        },
        {
            "message": "Can you tell me the details of my booking?",
            "expected": "check_booking",
            "description": "Check booking details"
        },
        
        # Check availability cases
        {
            "message": "What times are available for Friday?",
            "expected": "check_availability",
            "description": "Check available times"
        },
        {
            "message": "Do you have any tables free this weekend?",
            "expected": "check_availability", 
            "description": "Check weekend availability"
        },
        {
            "message": "Are you open tomorrow for dinner?",
            "expected": "check_availability",
            "description": "Check if open tomorrow"
        },
        
        # Make booking cases
        {
            "message": "Book a table for 4 people tomorrow at 7pm",
            "expected": "make_booking",
            "description": "Complete booking request"
        },
        {
            "message": "I'd like to make a reservation",
            "expected": "make_booking",
            "description": "General booking intent"
        },
        {
            "message": "Reserve a table for tonight",
            "expected": "make_booking",
            "description": "Booking for tonight"
        },
        
        # Cancel booking cases
        {
            "message": "Cancel my booking ABC123",
            "expected": "cancel_booking",
            "description": "Cancel with reference"
        },
        {
            "message": "I need to cancel my reservation for tomorrow",
            "expected": "cancel_booking",
            "description": "Cancel without reference"
        },
        {
            "message": "Delete my booking please",
            "expected": "cancel_booking",
            "description": "Delete booking"
        },
        
        # Modify booking cases
        {
            "message": "Change my booking from 6pm to 8pm",
            "expected": "modify_booking",
            "description": "Change time"
        },
        {
            "message": "Reschedule my reservation to next week",
            "expected": "modify_booking", 
            "description": "Reschedule booking"
        },
        {
            "message": "Update my booking for 6 people instead of 4",
            "expected": "modify_booking",
            "description": "Change party size"
        }
    ]
    
    print("🧪 Testing Intent Classification")
    print("=" * 50)
    
    correct = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        message = test_case["message"]
        expected = test_case["expected"]
        description = test_case["description"]
        
        # Test rule-based classification
        result = classify_intent_with_rules(message, {})
        predicted = result["intent"]
        confidence = result["confidence"]
        
        status = "✅" if predicted == expected else "❌"
        print(f"{i:2d}. {status} {description}")
        print(f"    Message: '{message}'")
        print(f"    Expected: {expected}, Got: {predicted} (confidence: {confidence:.2f})")
        
        if predicted == expected:
            correct += 1
        else:
            print(f"    ⚠️  MISMATCH! Expected {expected}, got {predicted}")
        
        print()
    
    accuracy = (correct / total) * 100
    print(f"📊 Accuracy: {correct}/{total} ({accuracy:.1f}%)")
    
    return accuracy

def test_parameter_extraction():
    """Test parameter extraction functionality."""
    
    test_cases = [
        {
            "message": "Book a table for 4 people tomorrow at 7pm, my name is John Smith, phone 123-456-7890",
            "expected": {
                "party_size": 4,
                "customer_name": "John Smith", 
                "phone": "123-456-7890"
            }
        },
        {
            "message": "Check my booking ABC123",
            "expected": {
                "booking_reference": "ABC123"
            }
        },
        {
            "message": "Cancel reservation REF456",
            "expected": {
                "booking_reference": "REF456"
            }
        },
        {
            "message": "Table for two people please",
            "expected": {
                "party_size": 2
            }
        }
    ]
    
    print("\n🔍 Testing Parameter Extraction")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        message = test_case["message"]
        expected = test_case["expected"]
        
        extracted = extract_parameters_with_rules(message)
        
        print(f"{i}. Message: '{message}'")
        print(f"   Expected: {expected}")
        print(f"   Extracted: {extracted}")
        
        # Check if all expected parameters were found
        matches = 0
        for key, value in expected.items():
            if key in extracted and extracted[key] == value:
                matches += 1
        
        if matches == len(expected):
            print("   ✅ All parameters extracted correctly")
        else:
            print(f"   ❌ Only {matches}/{len(expected)} parameters correct")
        
        print()

def test_conversation_flow():
    """Test a complete conversation flow."""
    
    print("\n🗣️ Testing Conversation Flow")
    print("=" * 50)
    
    # Initialize state
    state = AgentState()
    
    conversation_steps = [
        {
            "user": "I'd like to book a table",
            "expected_intent": "make_booking",
            "should_ask_for": ["date", "time", "party_size", "name", "phone"]
        },
        {
            "user": "For tomorrow at 7pm",
            "expected_intent": "make_booking", 
            "should_ask_for": ["party_size", "name", "phone"]
        },
        {
            "user": "For 4 people",
            "expected_intent": "make_booking",
            "should_ask_for": ["name", "phone"]
        },
        {
            "user": "My name is John Smith, phone 123-456-7890",
            "expected_intent": "make_booking",
            "should_ask_for": []
        }
    ]
    
    for i, step in enumerate(conversation_steps, 1):
        user_input = step["user"]
        expected_intent = step["expected_intent"]
        
        print(f"Step {i}: User says '{user_input}'")
        
        # Simulate classification
        result = classify_intent_with_rules(user_input, state.booking_context)
        predicted_intent = result["intent"]
        
        print(f"         Predicted intent: {predicted_intent}")
        print(f"         Expected intent: {expected_intent}")
        
        if predicted_intent == expected_intent:
            print("         ✅ Intent correct")
        else:
            print("         ❌ Intent incorrect")
        
        # Extract parameters and update context
        params = extract_parameters_with_rules(user_input)
        state.booking_context.update(params)
        
        print(f"         Updated context: {state.booking_context}")
        print()

def debug_json_parsing():
    """Test JSON parsing with problematic responses."""
    
    print("\n🔧 Testing JSON Parsing")
    print("=" * 50)
    
    test_responses = [
        # Good JSON
        '{"intent": "make_booking", "confidence": 0.9}',
        
        # JSON with trailing comma
        '{"intent": "make_booking", "confidence": 0.9,}',
        
        # JSON with markdown
        '```json\n{"intent": "make_booking", "confidence": 0.9}\n```',
        
        # JSON with extra text
        'Here is the classification: {"intent": "make_booking", "confidence": 0.9} - this should work',
        
        # Malformed JSON
        '{"intent": "make_booking", "confidence": 0.9, "parameters": {date": "2024-12-25"}}',
    ]
    
    for i, response in enumerate(test_responses, 1):
        print(f"Test {i}: {response[:50]}...")
        result = extract_json(response)
        if result:
            print(f"         ✅ Parsed: {result}")
        else:
            print(f"         ❌ Failed to parse")
        print()

def interactive_test():
    """Interactive testing mode."""
    
    print("\n🎮 Interactive Testing Mode")
    print("=" * 50)
    print("Enter messages to test intent classification (type 'quit' to exit):")
    
    context = {}
    
    while True:
        user_input = input("\nUser: ").strip()
        if user_input.lower() == 'quit':
            break
        
        # Test rule-based classification
        result = classify_intent_with_rules(user_input, context)
        params = extract_parameters_with_rules(user_input)
        
        print(f"Intent: {result['intent']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Parameters: {params}")
        print(f"Reason: {result.get('reason', 'N/A')}")
        
        # Update context for next iteration
        context.update(params)
        print(f"Updated context: {context}")

if __name__ == "__main__":
    print("🚀 Restaurant Booking Agent - Debug Suite")
    print("=" * 60)
    
    # Run all tests
    test_intent_classification()
    test_parameter_extraction()
    test_conversation_flow()
    debug_json_parsing()
    
    # Ask if user wants interactive mode
    print("\nWould you like to run interactive tests? (y/n): ", end="")
    if input().lower().startswith('y'):
        interactive_test()
    
    print("\n✨ Debug suite completed!")