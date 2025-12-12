import os
from src.services.resume_flow_service import ResumeFlowService
from src.engines.llm_engine import LLMEngine
from src.engines.resume_flow_llm_engine import LLMEngineResumeFlow
from src.engines.chatbot_agent import Agent
from src.services.chatbot_message import ChatbotMessageManagement
from src.services.resume_service import ResumeService
from src.storage.resume_storage import ResumeJobStorage

class Service():
    def __init__(self):
        self.llm_engine = LLMEngine()
        self.resume_flow_llm_engine = LLMEngineResumeFlow()
        self.chatbot = Agent()
        self.chatbot_mess_mgmt = ChatbotMessageManagement()
        self.resume_service = ResumeService()
        self.resume_flow_service = ResumeFlowService()
        self.resume_job_storage = ResumeJobStorage()
        
