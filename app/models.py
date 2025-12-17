# app/models.py
from pydantic import BaseModel
from typing import Optional, List, Dict,Any

class ChatRequest(BaseModel):
    session_id: Optional[str] = None   # keep session-level conv memory if you want
    text: str
    
class ChatResponse(BaseModel):
    reply: str
    retrieved_docs: Optional[List[Dict[str, Any]]] = None
    last_tool: Optional[Dict[str, Any]] = None
    elapsed_ms: Optional[int] = None