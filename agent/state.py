from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class AgentState:
    """Defines the state of the conversation."""
    user_message: str = ""
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    intent: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    api_response: Optional[Dict[str, Any]] = None
    agent_response: str = ""
    needs_clarification: bool = False
    clarification_message: str = ""
    
    # Keeps track of confirmed details for a booking operation
    booking_context: Dict[str, Any] = field(default_factory=dict)