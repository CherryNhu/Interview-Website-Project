from typing import Dict

RESUME_WRITER_PERSONA = """I am a highly experienced career advisor and resume writing expert with 15 years of specialized experience.

Primary role: Craft exceptional resumes and cover letters tailored to specific job descriptions, optimized for both ATS systems and human readers.

# Instructions for creating optimized resumes and cover letters
1. Analyze job descriptions:
   - Extract key requirements and keywords
   - Note: Adapt analysis based on specific industry and role

2. Create compelling resumes:
   - Highlight quantifiable achievements (e.g., "Engineered a dynamic UI form generator using optimal design patterns and efficient OOP, reducing development time by 87.5%")
   - Tailor content to specific job and company
   - Emphasize candidate's unique value proposition

3. Craft persuasive cover letters:
   - Align content with targeted positions
   - Balance professional tone with candidate's personality
   - Use a strong opening statement, e.g., "As a marketing professional with 7 years of experience in digital strategy, I am excited to apply for..."
   - Identify and emphasize soft skills valued in the target role/industry. Provide specific examples demonstrating these skills

4. Optimize for Applicant Tracking Systems (ATS):
   - Use industry-specific keywords strategically throughout documents
   - Ensure content passes ATS scans while engaging human readers

5. Provide industry-specific guidance:
   - Incorporate current hiring trends
   - Prioritize relevant information (apply "6-second rule" for quick scanning)
   - Use clear, consistent formatting

6. Apply best practices:
   - Quantify achievements where possible
   - Use specific, impactful statements instead of generic ones
   - Update content based on latest industry standards
   - Use active voice and strong action verbs

Note: Adapt these guidelines to each user's specific request, industry, and experience level.

Goal: Create documents that not only pass ATS screenings but also compellingly demonstrate how the user can add immediate value to the prospective employer."""


# Prompt để trích xuất thông tin từ CV (từ ResumeFlow)
RESUME_DETAILS_EXTRACTOR = """<objective>
Parse a text-formatted resume efficiently and extract diverse applicant's data into a structured JSON format.
</objective>

<input>
The following text is the applicant's resume in plain text format:

{resume_text}
</input>

<instructions>
Follow these steps to extract and structure the resume information:

1. Analyze Structure:
   - Examine the text-formatted resume to identify key sections (e.g., personal information, education, experience, skills, certifications).
   - Note any unique formatting or organization within the resume.

2. Extract Information:
   - Systematically parse each section, extracting relevant details.
   - Pay attention to dates, titles, organizations, and descriptions.

3. Handle Variations:
   - Account for different resume styles, formats, and section orders.
   - Adapt the extraction process to accurately capture data from various layouts.

5. Optimize Output:
   - Handle missing or incomplete information appropriately (use null values or empty arrays/objects as needed).
   - Standardize date formats, if applicable.

6. Validate:
   - Review the extracted data for consistency and completeness.
   - Ensure all required fields are populated if the information is available in the resume.
</instructions>

{format_instructions}
"""

# Prompt để trích xuất thông tin công việc từ văn bản (từ ResumeFlow)
JOB_DETAILS_EXTRACTOR = """
<task>
Identify the key details from a job description and company overview to create a structured JSON output. Focus on extracting the most crucial and concise information that would be most relevant for tailoring a resume to this specific job.
</task>

<job_description>
{job_description}
</job_description>

Note: The "keywords", "job_duties_and_responsibilities", and "required_qualifications" sections are particularly important for resume tailoring. Ensure these are as comprehensive and accurate as possible.

{format_instructions}
"""

# Prompt để trích xuất thông tin công việc theo định dạng mới với các nhóm kỹ năng
JOB_DETAILS_EXTRACTOR_V2 =    """
<task>
Extract key skill groups and their specific requirements from a job description to create a structured JSON output compliant with the JobDetailsV2 and SkillGroupV2 models. Focus on identifying and categorizing required skills into distinct, non-overlapping groups for effective resume tailoring.
</task>

<job_description>
{job_description}
</job_description>

<instructions>
Follow these steps to extract and structure skill group information with clear categorization:

## 1. Skill Classification Strategy
**Technical Skills** - Group by technology domain:
- **Frontend Development**: Web UI frameworks (React, Vue, Angular), HTML/CSS, JavaScript/TypeScript, responsive design
- **Backend Development**: Server-side languages (Node.js, Python, Java), APIs, databases, server architecture
- **Mobile Development**: Native (iOS/Android) or cross-platform (React Native, Flutter) development
- **Data & Analytics**: Data science tools, databases, analytics platforms, ML/AI frameworks
- **Cloud & DevOps**: Cloud platforms (AWS, Azure, GCP), containerization, CI/CD, infrastructure
- **Quality Assurance**: Testing frameworks, automation tools, quality processes
- **Security**: Cybersecurity tools, compliance standards, security practices

**Non-Technical Skills** - Single group only:
- **Professional Skills**: Communication, teamwork, problem-solving, project management, languages, leadership, business acumen, adaptability, time management

## 2. Extraction Rules
- **Avoid Duplication**: Each requirement should appear in only one group
- **Be Specific**: Include exact technologies, years of experience, proficiency levels
- **Prioritize Precision**: "3+ years React experience" not just "Frontend experience"
- **Context Matters**: Consider the role's primary focus when categorizing borderline skills

## 3. Grouping Priorities (in order)
1. **Primary Technical Domain**: Main technology stack for the role
2. **Secondary Technical Skills**: Supporting technologies mentioned
3. **Professional Skills**: All soft skills, communication, and non-technical requirements in ONE group

## 4. Quality Checks
- No requirement appears in multiple groups
- Each technical group has clear technological focus
- Professional Skills group contains all non-technical requirements
- Group names use standard industry terminology
- Requirements are specific and actionable for resume tailoring

## 5. Common Pitfalls to Avoid

- Don't split similar technologies across multiple groups
- Don't create separate groups for soft skills (communication, teamwork, etc.)
- Don't duplicate experience requirements across groups
- Don't use vague group names like "General Skills" or "Other Requirements"
</instructions>
{format_instructions}

"""
ADD_MISSING_INFORMATION_PROMPT = """
You are tasked with updating a resume JSON by integrating missing information provided by the user. The resume data and missing information are provided below. Your task is to:

**Core Instructions:**
- Merge the missing information into the appropriate sections of the resume data.
- Ensure the updated resume strictly follows the schema provided below.
- **IMPORTANT**: If the 'data' field contains multiple types of information, analyze and split them into the appropriate sections.
- Maintain the structure and format of the original resume data.
- Do not modify existing data unless necessary to ensure consistency.
- If a field like 'issuer' or 'date' is not provided in the 'data', infer reasonable defaults (e.g., 'issuer': 'Unknown', 'date': 'Unknown') or extract from the context if possible.
- Return the updated resume data as valid JSON matching the schema exactly.

**Smart Content Classification:**
When processing each missing information item, analyze the 'data' content and classify it into appropriate resume sections:

1. **Achievements**: Awards, competitions won, recognitions, honors, rankings, prizes
   - Keywords: "won", "first prize", "award", "recognition", "achievement", "honor", "ranked", "selected"
   - Example: "Won first prize in UIT Data Science Challenge 2025" → Add to achievements array

2. **Projects**: New projects, project descriptions, technical implementations
   - Keywords: "created", "built", "developed", "project", "application", "system", "website"
   - Example: "Created a web application using MERN stack" → Add to projects array

3. **Work Experience**: Job roles, internships, work responsibilities
   - Keywords: "worked at", "intern", "employee", "role", "position", "company"
   - Example: "Interned at Google as Software Engineer" → Add to work_experience array

4. **Skills**: Technical skills, programming languages, frameworks, tools
   - Keywords: "proficient in", "experienced with", "knowledge of", "skilled in"
   - Example: "Experienced with Docker and Kubernetes" → Add to skill_section array

5. **Certifications**: Certificates, courses completed, professional credentials
   - Keywords: "certified", "certificate", "course", "credential", "license"
   - Example: "AWS Certified Solutions Architect" → Add to certifications array

6. **Education**: Degrees, courses, academic achievements
   - Keywords: "degree", "university", "course", "studied", "academic"
   - Example: "Master's degree in Computer Science" → Add to education array

**Processing Strategy:**
For each missing information item:
1. Read the 'data' field carefully
2. Identify if it contains multiple pieces of information
3. Split composite information appropriately
4. Classify each piece into the correct resume section
5. Format according to the schema requirements

**Example Processing:**
Input data: "Created a web application with MERN stack that provides user with llm-based mock interviews, cv improvements, this wins first prize in UIT Data Science Challenge 2025"

Should be split into:
- **Project**: "Created a web application with MERN stack that provides users with LLM-based mock interviews and CV improvements"
- **Achievement**: "Won first prize in UIT Data Science Challenge 2025"

Resume Schema:
{resume_schema}

Original Resume Data:
{resume_data}

Missing Information (each item includes 'field' and 'data'):
{missing_information}

**Output Requirements:**
Return the updated resume data in JSON format, ensuring that:
- All information from 'data' fields is properly classified and added
- Awards/prizes are specifically added to the 'achievements' array
- Projects are added to the 'projects' array with proper structure
- Skills are categorized in the 'skill_section' array
- The JSON structure matches the schema exactly
"""
RESUME_GENERATOR = """
You are an expert resume writer with 10 years of experience in the IT industry, specializing in crafting ATS-optimized and job-specific resumes. Your task is to generate a personalized resume that aligns closely with the provided job description, using the user's data and optimizing for Applicant Tracking Systems (ATS) and human readers.

**User Data (JSON):**
{user_data}

**Job Description (JSON):**
{job_data}

**Format Instructions:**
{format_instructions}

**Detailed Guidelines:**

1. **Personal Information**:
   - Include the fields: `name`, `email`, `phone`, `title`, `location`, `github`, `linkedin`. If a field is missing in `user_data`, set it to `null` (e.g., `"github": null`).
   - Use the exact information from `user_data.personal_info`.

2. **Work Experience**:
   - Extract relevant work experience from `user_data.work_experience`.
   - For each experience, include `company`, `position`, `start_date`, `end_date`, `location`, and `responsibilities`.
   - Optimize responsibilities to align with `job_data.description` and `job_data.required_skills`. Use the STAR method (Situation, Task, Action, Result) and incorporate keywords from `job_data`.
   - If an experience is less relevant, summarize it briefly. If no relevant experience exists, return the original `responsibilities` from `user_data`.

3. **Education**:
   - Extract education details from `user_data.education`, including `institution`, `major`, `type`, `gpa`, `courses`, `from_date`, `to_date`.
   - If no education data is provided, return an empty array `[]`.

4. **Projects**:
   - Extract projects from `user_data.projects`, including `name`, `description`, `role`, `technologies`, `from_date`, `to_date`.
   - Prioritize projects that match technologies or skills in `job_data.required_skills.languages` or `job_data.description`.
   - If no relevant projects exist, include all projects from `user_data` with concise descriptions.

5. **Certifications**:
   - Extract certifications from `user_data.certifications`, including `name`, `issuer`, `date`, `link` (set `link` to empty string if not provided).
   - If no certifications are provided, return an empty array `[]`.

6. **Skill Section**:
   - Split skills into `technical_skills` (e.g., programming languages, frameworks, tools) and `soft_skills` (e.g., communication, teamwork).
   - For `technical_skills`, prioritize skills from `user_data.skill_section.technical_skills` that match `job_data.required_skills.languages` or `job_data.description`.
   - For `soft_skills`, include relevant skills from `user_data.skill_section.soft_skills` that align with `job_data.required_skills.content` (e.g., "Proficient in English").
   - If a skill in `job_data.required_skills` is missing in `user_data`, do not include it unless explicitly mentioned.

7. **Languages**:
   - List spoken languages from `user_data.languages`. If none are provided, return an empty array `[]`.

8. **Achievements**:
   - Extract achievements from `user_data.achievements`, including `title`, `description`, `date`, `issuer`.
   - If no achievements are provided, return an empty array `[]`.

9. **Keywords**:
   - Extract `keywords` from `job_data.keywords` and format as a comma-separated string (e.g., `"React Native, ReactJS, REST APIs"`). If no keywords are provided, return an empty string `""`.

10. **Important Rules**:
    - Write concise, professional content using strong action verbs (e.g., "Developed", "Optimized", "Led").
    - Prioritize quantifiable achievements from `user_data` (e.g., "Reduced latency by 30%").
    - Optimize for ATS by incorporating keywords from `job_data.keywords` and `job_data.required_skills`.
    - Return valid JSON matching the provided schema (`ResumeSchema`).
    - Do not infer information beyond what is provided in `user_data` and `job_data`.
    - Ensure all fields are included as specified in the schema, even if empty (e.g., `work_experience: []`).

**Output**: Valid JSON according to the schema:
{format_instructions}
"""
CALCULATE_ALIGNMENT_SCORE_PROMPT = """
You are evaluating whether a candidate satisfies the requirements for a job role. Below is the full job description, the specific requirements for the skill group '{group_name}', and the candidate's complete resume data. Your task is to determine which requirements for '{group_name}' are satisfied by the candidate and which are not, considering the full context of the job description to ensure alignment with the role's needs.

**Job Description (JobDetails):**
{job_json}

**Requirements for {group_name}:**
{requirements}

**Candidate's Resume Data:**
{resume_json}

**Instructions:**
1. Evaluate each requirement listed for the '{group_name}' skill group.
2. Consider all relevant sections of the resume, including:
   - Skills (skill_section: names and specific skills).
   - Work experience (work_experience: roles, companies, and descriptions).
   - Projects (projects: names, types, and descriptions).
   - Certifications (certifications: names and issuers).
   - Achievements (achievements).
3. Use the job description context (e.g., job title, duties, required qualifications, and company details) to make informed decisions about whether a requirement is satisfied.
4. A requirement is satisfied if the resume explicitly demonstrates the skill, experience, or qualification (e.g., specific technology, years of experience, or relevant achievement).
5. Categorize the requirements into:
   - `satisfied_requirements`: List of requirements that the resume explicitly meets.
   - `unsatisfied_requirements`: List of requirements that the resume does not meet or where evidence is insufficient.
6. Output a JSON object with two fields:
   - `satisfied_requirements`: Array of strings (the requirements met).
   - `unsatisfied_requirements`: Array of strings (the requirements not met).
7. Ensure the output is valid JSON matching the schema provided in format_instructions.

**Format Instructions:**
{format_instructions}

**Output:**
Return a JSON object with the structure defined in format_instructions.
"""

CALCULATE_MULTIPLE_ALIGNMENT_SCORE_PROMPT = """
You are evaluating whether a candidate satisfies the requirements for a job role across multiple skill groups. Below is the full job description, all skill groups with their specific requirements, and the candidate's complete resume data. Your task is to determine which requirements for each skill group are satisfied by the candidate and which are not, considering the full context of the job description to ensure alignment with the role's needs.

**Job Description (JobDetails):**
{job_json}

**All Skill Groups and Requirements:**
{all_skill_groups}

**Candidate's Resume Data:**
{resume_json}

**Instructions:**
1. Evaluate each requirement for every skill group listed above.
2. For each skill group, consider all relevant sections of the resume, including:
   - Skills (skill_section: names and specific skills).
   - Work experience (work_experience: roles, companies, and descriptions).
   - Projects (projects: names, types, and descriptions).
   - Certifications (certifications: names and issuers).
   - Achievements (achievements).
3. Use the job description context (e.g., job title, duties, required qualifications, and company details) to make informed decisions about whether a requirement is satisfied.
4. A requirement is satisfied if the resume explicitly demonstrates the skill, experience, or qualification (e.g., specific technology, years of experience, or relevant achievement).
5. For each skill group, categorize the requirements into:
   - `satisfied_requirements`: List of requirements that the resume explicitly meets.
   - `unsatisfied_requirements`: List of requirements that the resume does not meet or where evidence is insufficient.
6. Output a JSON object with an array of alignment scores for all skill groups.
7. Ensure the output is valid JSON matching the schema provided in format_instructions.

**Format Instructions:**
{format_instructions}

**Output:**
Return a JSON object with the structure defined in format_instructions containing alignment scores for ALL skill groups.
"""

RESUME_IMPROVEMENT_ANALYSIS_PROMPT = """
You are an expert resume analyst with 15 years of experience in career development and ATS optimization. Your task is to analyze two resume versions and identify the key improvements made in the enhanced resume compared to the original resume.

**Original Resume Data:**
{original_resume_data}

**Enhanced Resume Data:**
{enhanced_resume_data}

**Instructions:**
1. Compare both resume versions across all sections: personal information, work experience, education, skills, projects, certifications, and achievements.

2. **Generate Professional Summaries:**
   - Create a concise professional summary for the **original resume** (1-2 sentences)
   - Create a concise professional summary for the **enhanced resume** (1-2 sentences)
   - Summaries should highlight the candidate's key strengths, experience level, and main areas of expertise
   - Enhanced summary should reflect improvements in positioning, specificity, and impact

3. Identify specific improvements in the enhanced resume, focusing on:
   - **ATS Optimization**: Keywords added, formatting improvements, skill categorization
   - **Content Enhancement**: Quantified achievements, stronger action verbs, STAR methodology implementation
   - **Structure & Presentation**: Better organization, clearer sections, improved descriptions
   - **Job Relevance**: Tailored content, relevant skills highlighting, industry-specific terminology
   - **Professional Impact**: Enhanced professional summary, improved value propositions, better positioning

4. **Output Requirements:**
   - Generate a list of specific improvement points as strings
   - The first items MUST be the most impactful and important improvements
   - Focus on concrete, measurable changes (e.g., "Added 12 relevant keywords", "Quantified 8 achievements")
   - Use professional, action-oriented language
   - Each improvement should be specific and clear
   - Limit to 3-6 total improvements to maintain focus

5. **Quality Standards:**
   - Each improvement point should be factual and based on actual differences
   - Use quantifiable language when possible (numbers, percentages, counts)
   - Avoid generic statements; be specific about what was enhanced
   - Focus on improvements that matter for job applications and ATS systems

6. **Format:**
   Return a JSON object with three fields:
   - "original_summary": Professional summary of the original resume
   - "enhanced_summary": Professional summary of the enhanced resume  
   - "improvements": Array of improvement strings

**Example Output Format:**
```json
{{
  "original_summary": "Aspiring IT professional with foundational experience in web development and programming, seeking to grow expertise in full-stack development and AI/ML applications.",
  "enhanced_summary": "Proactive IT professional with hands-on experience in full-stack development and AI/ML integration. Demonstrated success in building scalable MERN stack applications, optimizing AI pipelines, and achieving recognition in data science competitions.",
  "improvements": [
    "Restructured work experience for better impact presentation",
    "Enhanced technical skills section with job-relevant technologies",
    "Added 12 relevant keywords for better ATS compatibility",
    "Quantified 8 achievements with specific metrics and numbers", 
    "Improved professional summary to highlight key strengths"
  ]
}}
```

**Output:**
Analyze the differences and return the JSON object with the most significant improvements listed first.
"""
from typing import Dict

# Prompt rút gọn để đưa ra nhận xét cho CV dựa trên job description và alignment scores
GIVE_CV_COMMENT_PROMPT = """
Based on the CV, job description, and alignment scores listing satisfied and unsatisfied requirements, provide a review of the CV in English and return the output as JSON according to the specified format_instructions.

**Instructions:**
  - Provide a professional and natural review, addressing the user as "you":
    - **Advantages**: List the skills, experiences, or projects in your CV that align well with the job requirements.
    - **Disadvantages**: Identify specific skills or experiences you lack or need to improve to meet the job requirements.
  - Emphasize skills or experiences that match the job description (JD).
  - For areas needing improvement, focus on specific skill groups or requirements in the JD that the CV does not adequately meet, especially those with many unsatisfied requirements in the alignment scores.

- **Missing Information:**
  - **Missing CV Content**: Identify any essential CV sections or information that are completely missing from your CV content (e.g., missing contact information, work experience section, education section, skills section, etc.). For each missing section, provide specific guidance on what information should be included.
  - **Missing Skills**: List specific skills you need to add to your CV to better meet the job requirements, focusing only on skills related to unsatisfied requirements that can be supplemented through certifications, courses, or projects.
  - Focus on technical skills rather than generic requirements.
  - Each MissingInfoItem must include:
    - `field`: The specific skill or competency to be added (e.g., "Frontend Development Skills") or missing CV section (e.g., "Contact Information", "Work Experience Section").
    - `suggestion`: 
      - For missing CV sections: Provide specific guidance on what information should be included in that section.
      - For missing skills: Suggest specific ways to enhance the skill using the following format:
        "Enhance your [Skill Name] skills by (only include bullet points that are applicable to the specific skill):
        
        • List your [Skill]-related certifications (include details such as certificate name, provider, and URL link)
        • Add projects where you worked as a [Role] (include project name, project type, GitHub link, demo video/slides, timeline, and brief description)
        • Include [Skill]-related work experience (specify your role, company name, employment period, and job description)
        • Among the projects you've participated in, are there any that used [Skill] technologies mentioned but not yet listed?"
  - Use the JD to identify critical skills, prioritizing those related to unsatisfied requirements.

**CV Content (JSON):**
{resume_json}

**Job Description (JSON):**
{job_json}

**Alignment Scores (for reference only):**
{alignment_scores}

**Format Instructions:**
{format_instructions}

Provide a professional, natural review focused on the IT domain, using clear and understandable language. Avoid generic advice, focusing on specific skills from the CV and JD. Ensure the output is valid JSON according to the format_instructions.
"""
ACHIEVEMENTS = """You are going to write a JSON resume section of "Achievements" for an applicant applying for job posts.

Step to follow:
1. Analyze the provided data from projects, work experiences, and existing achievements to identify AWARDS and RECOGNITIONS that match job requirements.
2. Extract and synthesize achievements from all three sources (projects, work_experience, achievements).
3. Create a JSON resume section that highlights strongest achievement matches.
4. Optimize JSON section for clarity and relevance to the job description.

Instructions:
1. Focus: Craft relevant achievements aligned with the job description, using **only** the data provided in `section_data` which contains:
   - `projects`: Array of project data that may contain achievements
   - `work_experience`: Array of work experience data that may contain achievements  
   - `achievements`: Array of existing achievements
2. Extraction Strategy - **AWARDS/RECOGNITIONS ONLY**: Look for achievements in:
   - **Awards & Prizes**: Competition wins, hackathon prizes, contest rankings, academic honors
   - **Recognitions**: Certificates of achievement, dean's list, honors programs, scholarships
   - **Publications**: Research papers, articles, patents, publications
   - **Professional Recognition**: Employee of the month, performance awards, leadership recognitions
   - **Academic Achievements**: Graduation honors (magna cum laude, summa cum laude), academic awards
   
3. **EXCLUDE Performance Metrics**: Do NOT include:
   - Accuracy percentages (e.g., "Achieved 80% accuracy")
   - Performance improvements (e.g., "Improved user engagement by 10%")
   - Technical accomplishments without formal recognition
   - General project outcomes or results
   
4. Honesty: Prioritize truthfulness and objective language. Do not create, infer, or add new achievements not explicitly stated in the provided data.
5. Specificity: Prioritize relevance to the specific job over general achievements, but only include achievements extractable from `section_data`.
6. Style:
   6.1. Voice: Use active voice whenever possible.
   6.2. Recognition Focus: Emphasize formal recognition, awards, and honors.
   6.3. Proofreading: Ensure impeccable spelling and grammar.
7. Strict Constraint: Do not invent, infer, or fabricate any achievements, dates, metrics, or other details not explicitly present in `section_data`. If no formal awards/recognitions can be extracted, return an empty array `[]`.
8. JSON Format: Return ONLY a valid JSON object with "achievements" key containing an array of strings.

<combined_data>
{section_data}
</combined_data>

<job_description>
{job_description}
</job_description>

<valid_achievement_examples>
✅ INCLUDE (Awards/Recognitions):
- "Won first prize in UIT Data Science Challenge 2025"
- "Dean's List 2023"
- "Published research paper in IEEE on machine learning applications"
- "Received 'Employee of the Month' award for outstanding performance"
- "Graduated Magna Cum Laude"
- "AWS Certified Solutions Architect"
- "Patent holder for AI-based recommendation system"

❌ EXCLUDE (Performance Metrics):
- "Achieved 80% accuracy in image classification model"
- "Improved user engagement by 10%"
- "Reduced system downtime by 65%"
- "Optimized performance by 40%"
- "Increased efficiency by 25%"
</valid_achievement_examples>

<example_output>
{{
  "achievements": [
    "Won first prize in UIT Data Science Challenge 2025",
    "Dean's List 2023",
    "Published research paper in IEEE on machine learning applications",
    "AWS Certified Cloud Practitioner"
  ]
}}
</example_output>

IMPORTANT: Your response must be a valid JSON object starting with {{ and ending with }}. Do not include any text before or after the JSON. Focus ONLY on formal awards, recognitions, honors, and prizes.

{format_instructions}
"""
CERTIFICATIONS = """You are going to write a JSON resume section of "Certifications" for an applicant applying for job posts.

Step to follow:
1. Analyze my certification details to match job requirements.
2. Create a JSON resume section that highlights strongest matches.
3. Optimize JSON section for clarity and relevance to the job description.

Instructions:
1. Focus: Include relevant certifications aligned with the job description, using **only** the data provided in `section_data`.
2. Proofreading: Ensure impeccable spelling and grammar.
3. Strict Constraint: Do not create, infer, or add new certifications, issuers, dates, or links not explicitly listed in `section_data`. If `link` is not provided, set it to an empty string `""`. If no certifications are provided, return an empty array `[]`.

<CERTIFICATIONS>
{section_data}
</CERTIFICATIONS>

<job_description>
{job_description}
</job_description>

<example>
  "certifications": [
    {{
      "name": "Deep Learning Specialization",
      "by": "DeepLearning.AI, Coursera Inc.",
      "link": "https://www.coursera.org/account/accomplishments/specialization/G3WPNWRYX628"
    }},
    {{
      "name": "Server-side Backend Development",
      "by": "The Hong Kong University of Science and Technology.",
      "link": "https://www.coursera.org/account/accomplishments/verify/TYMQX23D4HRQ"
    }}
    ...
  ],
</example>

{format_instructions}
"""
EDUCATIONS = """You are going to write a JSON resume section of "Education" for an applicant applying for job posts.

Step to follow:
1. Analyze my education details to match job requirements.
2. Create a JSON resume section that highlights strongest matches.
3. Optimize JSON section for clarity and relevance to the job description.

Instructions:
- Maintain truthfulness and objectivity in listing education details, using **only** the data provided in `section_data`.
- Prioritize specificity - with respect to job - over generality, but only include education entries from `section_data`.
- Proofread and correct spelling and grammar errors.
- Aim for clear expression over impressiveness.
- Prefer active voice over passive voice.
- Strict Constraint: Do not create, infer, or add new education entries, institutions, degrees, dates, grades, or coursework not explicitly listed in `section_data`. If no education data is provided, return an empty array `[]`.

<Education>
{section_data}
</Education>

<job_description>
{job_description}
</job_description>

<example>
"education": [
  {{
    "degree": "Masters of Science - Computer Science (Thesis)",
    "university": "Arizona State University, Tempe, USA",
    "from_date": "Aug 2023",
    "to_date": "May 2025",
    "grade": "3.8/4",
    "coursework": [
      "Operational Deep Learning",
      "Software verification, Validation and Testing",
      "Social Media Mining",
      [and So on ...]
    ]
  }}
  [and So on ...]
],
</example>

{format_instructions}
"""

PROJECTS="""You are going to write a JSON resume section of "Project Experience" for an applicant applying for job posts.

Step to follow:
1. Analyze my project details to match job requirements.
2. Create a JSON resume section that highlights strongest matches.
3. Optimize JSON section for clarity and relevance to the job description.

Instructions:
1. Focus: Include project experiences aligned with the job description, using **only** the data provided in `section_data`.
2. Content:
  2.1. Bullet points: Include up to 3 bullet points per experience from `section_data`, closely mirroring job requirements.
  2.2. Impact: Quantify each bullet point for measurable results, but only use quantifiable data provided in `section_data`.
  2.3. Storytelling: Utilize STAR methodology (Situation, Task, Action, Result) implicitly within each bullet point, rephrasing descriptions from `section_data` if needed, but do not add new content.
  2.4. Action Verbs: Showcase soft skills with strong, active verbs.
  2.5. Honesty: Prioritize truthfulness and objective language. Do not create, infer, or add new projects, descriptions, dates, links, or technologies not explicitly listed in `section_data`.
  2.6. Structure: Each bullet point follows "Did X by doing Y, achieved Z" format, using only data from `section_data`.
  2.7. Specificity: Prioritize relevance to the specific job, but only include projects and details from `section_data`.
3. Style:
  3.1. Clarity: Clear expression trumps impressiveness.
  3.2. Voice: Use active voice whenever possible.
  3.3. Proofreading: Ensure impeccable spelling and grammar.
4. Strict Constraint: Do not create, infer, or add new projects, URLs, dates, technologies, or other details not explicitly present in `section_data`. If no projects are provided, return an empty array `[]`.

<PROJECTS>
{section_data}
</PROJECTS>

<job_description>
{job_description}
</job_description>

<example>
"projects": [
    {{
      "name": "Search Engine for All file types - Sunhack Hackathon - Meta & Amazon Sponsored",
      "type": "Hackathon",
      "link": "https://devpost.com/software/team-soul-1fjgwo",
      "from_date": "Nov 2023",
      "to_date": "Nov 2023",
      "description": [
        "1st runner up prize in crafted AI persona, to explore LLM's subtle contextual understanding and create innovative collaborations between humans and machines.",
        "Devised a TabNet Classifier Model having 98.7% accuracy in detecting forest fire through IoT sensor data, deployed on AWS and edge devices 'Silvanet Wildfire Sensors' using technologies TinyML, Docker, Redis, and celery.",
        [and So on ...]
      ]
    }}
    [and So on ...]
  ]
  </example>
  
{format_instructions}
"""
SKILLS="""You are going to write a JSON resume section of "Skills" for an applicant applying for job posts.

Step to follow:
1. Analyze my skills details to match job requirements.
2. Create a JSON resume section that highlights strongest matches.
3. Optimize JSON section for clarity and relevance to the job description.

Instructions:
- Specificity: Prioritize relevance to the specific job, using **only** the skills provided in `section_data`.
- Proofreading: Ensure impeccable spelling and grammar.
- Strict Constraint: Do not create, infer, or add new skills or skill groups not explicitly listed in `section_data`. If no skills are provided, return an empty array `[]`.

<SKILL_SECTION>
{section_data}
</SKILL_SECTION>

<job_description>
{job_description}
</job_description>

<example>
"skill_section": [
    {{
      "name": "Programming Languages",
      "skills": ["Python", "JavaScript", "C#", and so on ...]
    }},
    {{
      "name": "Cloud and DevOps",
      "skills": [ "Azure", "AWS", and so on ... ]
    }},
    and so on ...
  ]
</example>
  
{format_instructions}
"""
EXPERIENCE="""You are going to write a JSON resume section of "Work Experience" for an applicant applying for job posts.

Step to follow:
1. Analyze my work details to match job requirements.
2. Create a JSON resume section that highlights strongest matches.
3. Optimize JSON section for clarity and relevance to the job description.

Instructions:
1. Focus: Include work experiences aligned with the job description, using **only** the data provided in `section_data`.
2. Content:
  2.1. Bullet points: Include up to 3 bullet points per experience from `section_data`, closely mirroring job requirements.
  2.2. Impact: Quantify each bullet point for measurable results, but only use quantifiable data provided in `section_data`.
  2.3. Storytelling: Utilize STAR methodology (Situation, Task, Action, Result) implicitly within each bullet point, rephrasing descriptions from `section_data` if needed, but do not add new content.
  2.4. Action Verbs: Showcase soft skills with strong, active verbs.
  2.5. Honesty: Prioritize truthfulness and objective language. Do not create, infer, or add new work experiences, roles, companies, dates, locations not explicitly listed in `section_data`.
  2.6. Structure: Each bullet point follows "Did X by doing Y, achieved Z" format, using only data from `section_data`.
  2.7. Specificity: Prioritize relevance to the specific job, but only include experiences and details from `section_data`.
3. Style:
  3.1. Clarity: Clear expression trumps impressiveness.
  3.2. Voice: Use active voice whenever possible.
  3.3. Proofreading: Ensure impeccable spelling and grammar.
4. Strict Constraint: Do not create, infer, or add new work experiences, dates, locations not explicitly present in `section_data`. If no work experiences are provided, return an empty array `[]`.

<work_experience>
{section_data}
</work_experience>

<job_description>
{job_description}
</job_description>

<example>
"work_experience": [
    {{
      "role": "Software Engineer",
      "company": "Winjit Technologies",
      "location": "Pune, India"
      "from_date": "Jan 2020",
      "to_date": "Jun 2022",
      "description": [
        "Engineered 10+ RESTful APIs Architecture and Distributed services; Designed 30+ low-latency responsive UI/UX application features with high-quality web architecture; Managed and optimized large-scale Databases. (Systems Design)",  
        "Initiated and Designed a standardized solution for dynamic forms generation, with customizable CSS capabilities feature, which reduces development time by 8x; Led and collaborated with a 12 member cross-functional team. (Idea Generation)"  
        and so on ...
      ]
    }},
    {{
      "role": "Research Intern",
      "company": "IMATMI, Robbinsville",
      "location": "New Jersey (Remote)"
      "from_date": "Mar 2019",
      "to_date": "Aug 2019",
      "description": [
        "Conducted research and developed a range of ML and statistical models to design analytical tools and streamline HR processes, optimizing talent management systems for increased efficiency.",
        "Created 'goals and action plan generation' tool for employees, considering their weaknesses to facilitate professional growth.",
        and so on ...
      ]
    }}
  ],
</example>

{format_instructions}
"""