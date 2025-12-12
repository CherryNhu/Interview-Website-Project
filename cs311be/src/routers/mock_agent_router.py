from fastapi import APIRouter, HTTPException
from datetime import datetime
from src.schemas.mock_agent import StartMockRequest, StartMockResponse, MockTurnRequest, MockTurnResponse
from src.services.mock_agent_service import MockAgentService

router = APIRouter(prefix="/mock", tags=["mock-agent"])
_service = MockAgentService()

@router.post("/start", response_model=StartMockResponse)
def start_mock(payload: StartMockRequest):
    try:
        first_q = _service.start_session(payload.session_id, payload.cv_text, payload.jd_text, payload.role)
        return StartMockResponse(session_id=payload.session_id, first_question=first_q)
    except HTTPException as he:
        raise he
    except Exception as e:
        print("start_mock error:", e)
        raise HTTPException(status_code=500, detail=f"start_mock failed: {e}")

@router.post("/turn", response_model=MockTurnResponse)
def mock_turn(payload: MockTurnRequest):
    try:
        data = _service.process_turn(payload.session_id, payload.user_answer)
        return MockTurnResponse(
            session_id=payload.session_id,
            timestamp=datetime.utcnow(),
            reasoning_summary=data["reasoning_summary"],
            next_question=data["next_question"],
            followups=data.get("followups", []),
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        print("mock_turn error:", e)
        raise HTTPException(status_code=500, detail=f"mock_turn failed: {e}")