from src.storage.mongodb import CRUDDocuments
from src.schemas.chatbot import ResumeData, JobData, SessionContext
from datetime import datetime

class CRUDResumeData(CRUDDocuments):
    def __init__(self):
        super().__init__()
        self.collection = self.connection.db.resume_data

class CRUDJobData(CRUDDocuments):
    def __init__(self):
        super().__init__()
        self.collection = self.connection.db.job_data

class ResumeJobStorage:
    def __init__(self):
        self.resume_storage = CRUDResumeData()
        self.job_storage = CRUDJobData()
    
    def save_resume_data(self, session_id: str, resume_data: dict):
        """Save resume data for a session"""
        resume_record = ResumeData(
            session_id=session_id,
            resume_data=resume_data,
            datetime=datetime.now()
        )
        return self.resume_storage.insert_one_doc(resume_record.model_dump())
    
    def save_job_data(self, session_id: str, job_data: dict):
        """Save job data for a session"""
        job_record = JobData(
            session_id=session_id,
            job_data=job_data,
            datetime=datetime.now()
        )
        return self.job_storage.insert_one_doc(job_record.model_dump())
    
    def get_session_context(self, session_id: str) -> SessionContext:
        """Get both resume and job data for a session"""
        resume_doc = self.resume_storage.find_one_doc({"session_id": session_id})
        job_doc = self.job_storage.find_one_doc({"session_id": session_id})
        
        return SessionContext(
            session_id=session_id,
            resume_data=resume_doc.get("resume_data") if resume_doc else None,
            job_data=job_doc.get("job_data") if job_doc else None
        )
    
    def get_resume_data(self, session_id: str) -> dict:
        """Get resume data for a session"""
        doc = self.resume_storage.find_one_doc({"session_id": session_id})
        return doc.get("resume_data") if doc else None
    
    def get_job_data(self, session_id: str) -> dict:
        """Get job data for a session"""
        doc = self.job_storage.find_one_doc({"session_id": session_id})
        return doc.get("job_data") if doc else None
    
    def get_session_metadata(self, session_id: str) -> dict:
        """Get session metadata including creation date and duration"""
        # Get resume data creation date
        resume_doc = self.resume_storage.find_one_doc({"session_id": session_id})
        job_doc = self.job_storage.find_one_doc({"session_id": session_id})
        
        # Use the earliest creation date
        created_at = None
        if resume_doc and resume_doc.get("datetime"):
            created_at = resume_doc["datetime"]
        elif job_doc and job_doc.get("datetime"):
            created_at = job_doc["datetime"]
        
        # Check for session metadata record
        session_metadata = None
        if resume_doc and resume_doc.get("session_type"):
            session_metadata = resume_doc
        
        return {
            "created_at": created_at,
            "duration": "25 min",  # Default duration, could be calculated from chat history
            "session_type": session_metadata.get("session_type") if session_metadata else "mock_interview",
            "status": session_metadata.get("status") if session_metadata else "active"
        }
    
    def initialize_session_metadata(self, session_id: str):
        """Initialize session metadata if not already exists"""
        # Check if session metadata already exists
        existing_resume = self.resume_storage.find_one_doc({"session_id": session_id})
        existing_job = self.job_storage.find_one_doc({"session_id": session_id})
        
        # If no metadata exists, create a basic session record
        if not existing_resume and not existing_job:
            # Create a minimal session record to track session start time
            session_record = {
                "session_id": session_id,
                "session_type": "mock_interview",
                "created_at": datetime.now(),
                "status": "active"
            }
            # Store in resume collection as a session tracker
            self.resume_storage.insert_one_doc(session_record)