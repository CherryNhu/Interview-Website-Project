from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict, Any

class InputChatbotMessage(BaseModel):
    room_id: str
    query: str

class ResponseChat(BaseModel):
    """
    A model for representing a chat response.
    """
    response: str
    #is_outdomain: bool

class ChatbotMessage(BaseModel):
    session_id: str
    chat_message: str
    answer: str
    datetime: datetime

class ResumeData(BaseModel):
    session_id: str
    resume_data: Dict[str, Any]
    datetime: datetime

class JobData(BaseModel):
    session_id: str
    job_data: Dict[str, Any]
    datetime: datetime

class SessionContext(BaseModel):
    session_id: str
    resume_data: Optional[Dict[str, Any]] = None
    job_data: Optional[Dict[str, Any]] = None

