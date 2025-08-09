from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class AgentState:
    """Defines the state of the conversation with improved tracking."""
    user_message: str = ""
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    intent: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    api_response: Optional[Dict[str, Any]] = None
    agent_response: str = ""
    needs_clarification: bool = False
    clarification_message: str = ""
    
    # Persistent context for booking operations across turns
    booking_context: Dict[str, Any] = field(default_factory=dict)
    
    # Track the current operation state
    current_operation: Optional[str] = None  # "booking", "checking", "cancelling", etc.
    
    def clear_transient_state(self):
        """Clear state that shouldn't persist between turns."""
        self.user_message = ""
        self.api_response = None
        self.agent_response = ""
        self.needs_clarification = False
        self.clarification_message = ""
        self.parameters = {}
        
    def clear_booking_context(self):
        """Clear booking context when starting a new booking process."""
        # Only clear if we're not in the middle of an operation
        if not self.needs_clarification:
            self.booking_context = {}
            print("Booking context cleared")
    
    def preserve_booking_reference(self):
        """Preserve only the booking reference when clearing context."""
        if self.booking_context.get('booking_reference'):
            booking_ref = self.booking_context['booking_reference']
            self.booking_context = {'booking_reference': booking_ref}
            print(f"Preserved booking reference: {booking_ref}")
        
    def add_to_history(self, role: str, content: str):
        """Helper method to add messages to conversation history."""
        self.conversation_history.append({"role": role, "content": content})
        
        # Keep only last 10 exchanges to manage context size
        if len(self.conversation_history) > 20:  # 20 = 10 exchanges * 2 messages each
            self.conversation_history = self.conversation_history[-20:]
    
    def get_context_summary(self) -> str:
        """Get a summary of current booking context for debugging."""
        return f"Current context: {self.booking_context}"
    
    def has_active_booking(self) -> bool:
        """Check if there's an active booking reference in context."""
        return bool(self.booking_context.get('booking_reference'))
    
    def is_booking_complete(self) -> bool:
        """Check if a booking has all required information."""
        required_fields = ["date", "time", "party_size", "customer_name", "phone"]
        return all(self.booking_context.get(field) for field in required_fields)
    
    def get_missing_booking_fields(self) -> List[str]:
        """Get list of missing required booking fields."""
        required_fields = {
            "date": "date",
            "time": "time", 
            "party_size": "number of people",
            "customer_name": "your name",
            "phone": "phone number"
        }
        
        missing = []
        for field, description in required_fields.items():
            if not self.booking_context.get(field):
                missing.append(description)
        
        return missing