from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class StartMockRequest(BaseModel):
    session_id: str
    cv_text: str
    jd_text: str
    role: Optional[str] = None

class StartMockResponse(BaseModel):
    session_id: str
    first_question: str

class MockTurnRequest(BaseModel):
    session_id: str
    user_answer: str

class MockTurnResponse(BaseModel):
    session_id: str
    timestamp: datetime
    reasoning_summary: str
    next_question: str
    followups: List[str] = []