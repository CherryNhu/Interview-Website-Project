from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional

class Media(BaseModel):
    linkedin: Optional[str] = Field(description="LinkedIn profile URL")
    github: Optional[str] = Field(description="GitHub profile URL")
    medium: Optional[str] = Field(description="Medium profile URL")
    devpost: Optional[str] = Field(description="Devpost profile URL")

class Experience(BaseModel):
    role: Optional[str] = Field(description="The job title or position held. e.g. Software Engineer, Machine Learning Engineer.")
    company: Optional[str] = Field(description="The name of the company or organization.")
    location: Optional[str] = Field(description="The location of the company or organization. e.g. San Francisco, USA.")
    from_date: Optional[str] = Field(description="The start date of the employment period. e.g., Aug 2023")
    to_date: Optional[str] = Field(description="The end date of the employment period. e.g., Nov 2025")
    description: List[Optional[str]] = Field(description="A list of 3 bullet points describing the work experience, tailored to match job requirements. Each bullet point should follow the 'Did X by doing Y, achieved Z' format, quantify impact, implicitly use STAR methodology, use strong action verbs, and be highly relevant to the specific job. Ensure clarity, active voice, and impeccable grammar.")

class Experiences(BaseModel):
    work_experience: List[Experience] = Field(description="Work experiences, including job title, company, location, dates, and description.")

class Education(BaseModel):
    degree: Optional[str] = Field(description="The degree or qualification obtained and The major or field of study. e.g., Bachelor of Science in Computer Science.")
    university: Optional[str] = Field(description="The name of the institution where the degree was obtained with location. e.g. Arizona State University, Tempe, USA")
    from_date: Optional[str] = Field(description="The start date of the education period. e.g., Aug 2023")
    to_date: Optional[str] = Field(description="The end date of the education period. e.g., May 2025")
    courses: List[Optional[str]] = Field(description="Relevant courses or subjects studied during the education period. e.g. [Data Structures, Algorithms, Machine Learning]")

class Educations(BaseModel):
    education: List[Education] = Field(description="Educational qualifications, including degree, institution, dates, and relevant courses.")

class Link(BaseModel):
    name: Optional[str] = Field(description="The name or title of the link.")
    link: Optional[str] = Field(description="The URL of the link.")

class Project(BaseModel):
    name: Optional[str] = Field(description="The name or title of the project.")
    type: Optional[str] = Field(description="The type or category of the project, such as hackathon, publication, professional, and academic.")
    link: Optional[str] = Field(description="A link to the project repository or demo.")
    resources: Optional[List[Link]] = Field(description="Additional resources related to the project, such as documentation, slides, or videos.")
    from_date: Optional[str] = Field(description="The start date of the project. e.g. Aug 2023")
    to_date: Optional[str] = Field(description="The end date of the project. e.g. Nov 2023")
    description: List[Optional[str]] = Field(description="A list of 3 bullet points describing the project experience, tailored to match job requirements. Each bullet point should follow the 'Did X by doing Y, achieved Z' format, quantify impact, implicitly use STAR methodology, use strong action verbs, and be highly relevant to the specific job. Ensure clarity, active voice, and impeccable grammar.")

class Projects(BaseModel):
    projects: List[Project] = Field(description="Project experiences, including project name, type, link, resources, dates, and description.")

class Certification(BaseModel):
    name: Optional[str] = Field(description="The name of the certification.")
    by: Optional[str] = Field(description="The organization or institution that issued the certification.")
    link: Optional[str] = Field(description="A link to verify the certification.")

class Certifications(BaseModel):
    certifications: List[Certification] = Field(description="job relevant certifications that you have earned, including the name, issuing organization, and a link to verify the certification.")

class Achievements(BaseModel):
    achievements: List[Optional[str]] = Field(description="job relevant key accomplishments, awards, or recognitions that demonstrate your skills and abilities.")

class SkillSection(BaseModel):
    name: Optional[str] = Field(description="name or title of the skill group and competencies relevant to the job, such as programming languages, data science, tools & technologies, cloud & DevOps, full stack, or soft skills.")
    skills: List[Optional[str]] = Field(description="Specific skills or competencies within the skill group, such as Python, JavaScript, C#, SQL in programming languages.")

class SkillSections(BaseModel):
    skill_section: List[SkillSection] = Field(description="Skill sections, each containing a group of skills and competencies relevant to the job.")

class ResumeSchema(BaseModel):
    name: Optional[str] = Field(description="The full name of the candidate.")
    summary: Optional[str] = Field(description="A brief summary or objective statement highlighting key skills, experience, and career goals.")
    phone: Optional[str] = Field(description="The contact phone number of the candidate.")
    email: Optional[str] = Field(description="The contact email address of the candidate.")
    title: Optional[str] = Field(description="The professional title or headline of the candidate, e.g., Software Engineer, Data Scientist.")
    location: Optional[str] = Field(description="The current location of the candidate, e.g., City")
    media: Media = Field(description="Links to professional social media profiles, such as LinkedIn, GitHub, or personal website.")
    work_experience: List[Experience] = Field(description="Work experiences, including job title, company, location, dates, and description.")
    education: List[Education] = Field(description="Educational qualifications, including degree, institution, dates, and relevant courses.")
    skill_section: List[SkillSection] = Field(description="Skill sections, each containing a group of skills and competencies relevant to the job.")
    projects: List[Project] = Field(description="Project experiences, including project name, type, link, resources, dates, and description.")
    certifications: List[Certification] = Field(description="job relevant certifications that you have earned, including the name, issuing organization, and a link to verify the certification.")
    achievements: List[Optional[str]] = Field(description="job relevant key accomplishments, awards, or recognitions that demonstrate your skills and abilities.")

class Achievement(BaseModel):
    title: str  # Title of the achievement (e.g., "Best Developer Award")
    description: Optional[str]  # Description of the achievement
    date: Optional[str] = None  # Date of the achievement
    issuer: Optional[str] = None  # Organization or entity that issued the achievement
    
class SkillGroup(BaseModel):
    group_name: str = Field(description="The name of the skill group, e.g., 'Frontend Development', 'Data Science', 'Cloud & DevOps'.")
    requirements: List[Optional[str]] = Field(description="A list of specific skills or competencies required within the skill group, e.g., ['Minimum 3 years of software engineering experience building web frontend', 'Good understanding of web frontend architecture.',...] for Frontend Development.")

class SkillGroupV2(BaseModel):
    group_name: str
    languages: List[str] = []
    work_experience: List[str] = []  # Changed to List[str]
    projects: List[str] = []  # Changed to List[str]
    certifications: List[Certification] = []
    achievements: List[Achievement] = []

class JobDetails(BaseModel):
    job_title: Optional[str] = Field(description="The specific role, its level, and scope within the organization.")
    job_purpose: Optional[str] = Field(description="A high-level overview of the role and why it exists in the organization.")
    keywords: List[Optional[str]] = Field(description="Key expertise, skills, and requirements the job demands.")
    job_duties_and_responsibilities: List[Optional[str]] = Field(description="Focus on essential functions, their frequency and importance, level of decision-making, areas of accountability, and any supervisory responsibilities.")
    required_qualifications: List[Optional[str]] = Field(description="Including education, minimum experience, specific knowledge, skills, abilities, and any required licenses or certifications.")
    preferred_qualifications: List[Optional[str]] = Field(description="Additional 'nice-to-have' qualifications that could set a candidate apart.")
    company_name: Optional[str] = Field(description="The name of the hiring organization.")
    company_details: Optional[str] = Field(description="Overview, mission, values, or way of working that could be relevant for tailoring a resume or cover letter.")
    
class JobDetailsV2(BaseModel):
    required_skills: List[SkillGroup] = []  # List of skill groups
class PersonalInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None  # Professional title, e.g., "Software Engineer"
    location: Optional[str] = None  # Location, e.g., "Hanoi, Vietnam"

class MissingInfoItem(BaseModel):
    field: str  = Field(description="The specific field or section that needs additional information (e.g., 'Front End Development Skills', 'Mobile Development skills').")
    suggestion: str  = Field(description="A clear and concise suggestion on what information needs to be added (e.g., 'Include specific front-end technologies like React, Angular, or Vue.js along with your proficiency level, related projects, and work experience to demonstrate your expertise in front-end development.').")
class CVCommentSchema(BaseModel):
    advantages: List[Optional[str]] = Field(description="List of strengths or positive aspects of the resume to the job description.")
    disadvantages: List[Optional[str]] = Field(description="List of weaknesses or negative aspects of the resume to the job description.")
    missing_information: List[MissingInfoItem] = Field(description="List of missing information items with suggestions for improvement.")
    

class AlignmentScoreSchema(BaseModel):
    satisfied_requirements: List[str] = Field(description="List of requirements that the resume explicitly meets for the skill group.")
    unsatisfied_requirements: List[str] = Field(description="List of requirements that the resume does not meet or where evidence is insufficient for the skill group.")

class GroupAlignmentScore(BaseModel):
    group_name: str = Field(description="Name of the skill group being evaluated")
    satisfied_requirements: List[str] = Field(description="List of requirements that the resume explicitly meets for this skill group.")
    unsatisfied_requirements: List[str] = Field(description="List of requirements that the resume does not meet or where evidence is insufficient for this skill group.")

class MultipleAlignmentScoreSchema(BaseModel):
    alignment_scores: List[GroupAlignmentScore] = Field(description="List of alignment scores for all skill groups")