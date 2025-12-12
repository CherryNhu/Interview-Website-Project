from pydantic import BaseModel
from typing import List, Optional

class Experience(BaseModel):
    company: str
    position: str
    start_date: str
    end_date: str
    description: str

class Education(BaseModel):
    institution: str
    degree: str
    major: str
    start_date: str
    end_date: str

class Project(BaseModel):
    name: str
    description: str
    role: str
    technologies: List[str]

class Certification(BaseModel):
    name: str
    issuer: str
    date: str

class Achievement(BaseModel):
    title: str
    description: str
    date: str

class SkillSection(BaseModel):
    category: str
    skills: List[str]

class ResumeSchema(BaseModel):
    personal_info: dict
    work_experience: List[Experience]
    education: List[Education]
    projects: List[Project]
    certifications: List[Certification]
    achievements: List[Achievement]
    skill_section: List[SkillSection]

class JobDetails(BaseModel):
    job_title: str
    company_name: str
    location: str
    job_type: str
    experience_level: str
    skills_required: List[str]
    description: str
    url: Optional[str] = None