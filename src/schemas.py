from typing import Optional, Literal, Dict, Any
from langgraph.graph import MessagesState

class State(MessagesState):
    email_input: str
    classification_decision: Literal["ignore", "respond", "notify"]
    proposal: Optional[Dict[str, Any]] = None

