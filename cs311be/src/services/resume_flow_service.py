import os
import json
import re
from fastapi import UploadFile, HTTPException
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader
from src.prompts.resume_flow_prompt import RESUME_DETAILS_EXTRACTOR, JOB_DETAILS_EXTRACTOR, JOB_DETAILS_EXTRACTOR_V2,ADD_MISSING_INFORMATION_PROMPT,RESUME_GENERATOR, CALCULATE_MULTIPLE_ALIGNMENT_SCORE_PROMPT, RESUME_IMPROVEMENT_ANALYSIS_PROMPT,GIVE_CV_COMMENT_PROMPT,RESUME_WRITER_PERSONA, EXPERIENCE, SKILLS, PROJECTS, EDUCATIONS, CERTIFICATIONS, ACHIEVEMENTS
from src.schemas.resume_flow_schemas import ResumeSchema, JobDetails, JobDetailsV2, CVCommentSchema, AlignmentScoreSchema, MultipleAlignmentScoreSchema
from src.engines.resume_flow_llm_engine import LLMEngineResumeFlow
from typing import List, Dict, Optional
from src.schemas.resume_flow_schemas import Experiences, SkillSections, Projects, Educations, Certifications, Achievements
from src.utils.text_utils import clean_string, extract_resume_text, calculate_cosine_similarity
from src.utils.latex_ops import latex_to_pdf
import time
import asyncio

class ResumeFlowService:
    def __init__(self):
        self.parser = LlamaParse(
            api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
            result_type="text",
            language="vi",
            fast_mode=True,
            continuous_mode=False,
        )
        self.llm_engine = LLMEngineResumeFlow(system_prompt=RESUME_WRITER_PERSONA)

    async def extract_cv(self, file: UploadFile) -> dict:
        """Extract content from CV file (PDF or DOCX) using ResumeFlow schema."""
        try:
            file_path = f"temp/{file.filename}"
            os.makedirs("temp", exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(await file.read())

            if not file_path.lower().endswith(('.pdf', '.docx')):
                raise ValueError("Only PDF and DOCX files are supported")

            file_extractor = {".pdf": self.parser, ".docx": self.parser}
            reader = SimpleDirectoryReader(
                input_files=[file_path],
                file_extractor=file_extractor
            )
            documents = await reader.aload_data()
            resume_text = "\n".join(doc.text for doc in documents)
            resume_schema = ResumeSchema.schema()
            prompt = RESUME_DETAILS_EXTRACTOR.format(
                resume_text=resume_text,
                format_instructions=json.dumps(resume_schema, indent=2, ensure_ascii=False)
            )
            response = await self.llm_engine.call_llm(
                prompt=prompt,
                response_format={"type": "json_object"},
                use_mini=True
            )
            try:
                resume_json = json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'```json\n([\s\S]*?)\n```', response)
                if json_match:
                    resume_json = json.loads(json_match.group(1))
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to parse LLM response as JSON"
                    )
            resume_data = ResumeSchema(**resume_json)
            os.remove(file_path)
            return resume_data.dict()
        except Exception as e:
            if 'file_path' in locals():
                try:
                    os.remove(file_path)
                except:
                    pass
            raise HTTPException(
                status_code=500,
                detail=f"Error processing CV: {str(e)}"
            )
    async def extract_job_details(self, job_description: Optional[str] = None, file: Optional[UploadFile] = None) -> dict:
        """Extract job details from text or file (PDF, DOCX, TXT) using ResumeFlow schema."""
        try:
            if file and file.filename:  # Kiểm tra file có hợp lệ không
                file_path = f"temp/{file.filename}"
                os.makedirs("temp", exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(await file.read())

                if not file_path.lower().endswith(('.pdf', '.docx', '.txt')):
                    raise ValueError("Only PDF, DOCX, and TXT files are supported")

                if file_path.lower().endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        job_description = f.read()
                else:
                    file_extractor = {".pdf": self.parser, ".docx": self.parser}
                    reader = SimpleDirectoryReader(
                        input_files=[file_path],
                        file_extractor=file_extractor
                    )
                    documents = await reader.aload_data()
                    job_description = "\n".join(doc.text for doc in documents)
                os.remove(file_path)
            elif not job_description:
                raise ValueError("Either job_description or a valid file must be provided")

            if not job_description:
                raise ValueError("Job description is empty after processing")

            job_schema = JobDetails.schema()
            prompt = JOB_DETAILS_EXTRACTOR.format(
                job_description=job_description,
                format_instructions=json.dumps(job_schema, indent=2, ensure_ascii=False),
            )
            response = await self.llm_engine.call_llm(
                prompt=prompt,
                response_format={"type": "json_object"},
                use_mini=True
            )
            try:
                job_json = json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'```json\n([\s\S]*?)\n```', response)
                if json_match:
                    job_json = json.loads(json_match.group(1))
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to parse LLM response as JSON"
                    )
            job_data = JobDetails(**job_json)
            return job_data.dict()
        except Exception as e:
            if 'file_path' in locals():
                try:
                    os.remove(file_path)
                except:
                    pass
            raise HTTPException(
                status_code=500,
                detail=f"Error processing job description: {str(e)}"
            )

    async def extract_job_details_v2(self, job_description: Optional[str] = None, file: Optional[UploadFile] = None) -> dict:
        """Extract job details from text or file (PDF, DOCX, TXT) using ResumeFlow schema with grouped skills."""
        try:
            if file and file.filename:  # Kiểm tra file có hợp lệ không
                file_path = f"temp/{file.filename}"
                os.makedirs("temp", exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(await file.read())

                if not file_path.lower().endswith(('.pdf', '.docx', '.txt')):
                    raise ValueError("Only PDF, DOCX, and TXT files are supported")

                if file_path.lower().endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        job_description = f.read()
                else:
                    file_extractor = {".pdf": self.parser, ".docx": self.parser}
                    reader = SimpleDirectoryReader(
                        input_files=[file_path],
                        file_extractor=file_extractor
                    )
                    documents = await reader.aload_data()
                    job_description = "\n".join(doc.text for doc in documents)
                os.remove(file_path)
            elif not job_description:
                raise ValueError("Either job_description or a valid file must be provided")

            if not job_description:
                raise ValueError("Job description is empty after processing")

            job_schema = JobDetailsV2.schema()
            prompt = JOB_DETAILS_EXTRACTOR_V2.format(
                job_description=job_description,
                format_instructions=json.dumps(job_schema, indent=2, ensure_ascii=False)
            )
            response = await self.llm_engine.call_llm(
                prompt=prompt,
                response_format={"type": "json_object"}
            )
            try:
                job_json = json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'```json\n([\s\S]*?)\n```', response)
                if json_match:
                    job_json = json.loads(json_match.group(1))
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to parse LLM response as JSON"
                    )
            job_data = JobDetailsV2(**job_json)
            return job_data.dict()
        except Exception as e:
            if 'file_path' in locals():
                try:
                    os.remove(file_path)
                except:
                    pass
            raise HTTPException(
                status_code=500,
                detail=f"Error processing job description: {str(e)}"
            )
            
    async def extract_job_details_v12(self, job_description: str = None, file: UploadFile = None) -> dict:
        """Extract job details from text or file (PDF or DOCX) using ResumeFlow schema with grouped skills."""
        try:
            if file:
                file_path = f"temp/{file.filename}"
                os.makedirs("temp", exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(await file.read())
                if not file_path.lower().endswith(('.pdf', '.docx')):
                    raise ValueError("Only PDF and DOCX files are supported")

                file_extractor = {".pdf": self.parser, ".docx": self.parser}
                reader = SimpleDirectoryReader(
                    input_files=[file_path],
                    file_extractor=file_extractor
                )
                documents = await reader.aload_data()
                job_description = "\n".join(doc.text for doc in documents)
                os.remove(file_path)
            elif not job_description:
                raise ValueError("Either job_description or file must be provided")
            
            # Chuẩn bị schemas và prompts
            job_schema = JobDetails.schema()
            job_schema2 = JobDetailsV2.schema()
            
            prompt1 = JOB_DETAILS_EXTRACTOR.format(
                job_description=job_description,
                format_instructions=json.dumps(job_schema, indent=2, ensure_ascii=False)
            )
            
            prompt2 = JOB_DETAILS_EXTRACTOR_V2.format(
                job_description=job_description,
                format_instructions=json.dumps(job_schema2, indent=2, ensure_ascii=False)
            )
            
            # Chạy song song 2 LLM calls
            response1, response2 = await asyncio.gather(
                self.llm_engine.call_llm(
                    prompt=prompt1,
                    response_format={"type": "json_object"},
                    use_mini=True
                ),
                self.llm_engine.call_llm(
                    prompt=prompt2,
                    response_format={"type": "json_object"}
                )
            )
            
            # Xử lý response 1
            try:
                job_json = json.loads(response1)
            except json.JSONDecodeError:
                json_match = re.search(r'```json\n([\s\S]*?)\n```', response1)
                if json_match:
                    job_json = json.loads(json_match.group(1))
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to parse LLM response as JSON"
                    )
            
            # Xử lý response 2
            try:
                job_json2 = json.loads(response2)
            except json.JSONDecodeError:
                json_match2 = re.search(r'```json\n([\s\S]*?)\n```', response2)
                if json_match2:
                    job_json2 = json.loads(json_match2.group(1))
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to parse LLM response as JSON"
                    )
            
            job_data = JobDetails(**job_json)
            job_data2 = JobDetailsV2(**job_json2)
            return job_data.dict(), job_data2.dict()
        
        except Exception as e:
            if 'file_path' in locals():
                try:
                    os.remove(file_path)
                except:
                    pass
            raise HTTPException(
                status_code=500,
                detail=f"Error processing job description: {str(e)}"
            )

    async def calculate_alignment_score(self, resume_json: dict, job_json: dict, job_json_v2: dict) -> dict:
        """Calculate alignment scores for all skill groups between resume and job description in a single LLM call."""
        try:
            # Validate inputs using schemas
            resume_data = ResumeSchema(**resume_json)
            job_data = JobDetails(**job_json)
            job_data_v2 = JobDetailsV2(**job_json_v2)

            # Prepare all skill groups data for single LLM call
            all_skill_groups = []
            for group in job_data_v2.required_skills:
                group_name = group.group_name
                requirements = [req for req in group.requirements if req]
                if requirements:  # Only include groups with requirements
                    all_skill_groups.append({
                        "group_name": group_name,
                        "requirements": requirements
                    })

            # If no groups have requirements, return empty result
            if not all_skill_groups:
                return {}

            # Create prompt with all skill groups
            prompt = CALCULATE_MULTIPLE_ALIGNMENT_SCORE_PROMPT.format(
                all_skill_groups=json.dumps(all_skill_groups, indent=2, ensure_ascii=False),
                resume_json=json.dumps(resume_data.dict(), indent=2, ensure_ascii=False),
                job_json=json.dumps(job_data.dict(), indent=2, ensure_ascii=False),
                format_instructions=json.dumps(MultipleAlignmentScoreSchema.schema(), indent=2, ensure_ascii=False)
            )

            # Single LLM call for all groups
            response = await self.llm_engine.call_llm(
                prompt=prompt,
                response_format={"type": "json_object"}
            )

            try:
                response_json = json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'```json\n([\s\S]*?)\n```', response)
                if json_match:
                    response_json = json.loads(json_match.group(1))
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to parse LLM response as JSON"
                    )

            # Validate against MultipleAlignmentScoreSchema
            validated_response = MultipleAlignmentScoreSchema(**response_json)

            # Convert to the expected output format
            result = {}
            for group_score in validated_response.alignment_scores:
                result[group_score.group_name] = {
                    "satisfied_requirements": group_score.satisfied_requirements,
                    "unsatisfied_requirements": group_score.unsatisfied_requirements
                }

            # Add empty results for groups that weren't processed (no requirements)
            for group in job_data_v2.required_skills:
                if group.group_name not in result:
                    result[group.group_name] = {
                        "satisfied_requirements": [],
                        "unsatisfied_requirements": []
                    }

            return result

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error calculating alignment score: {str(e)}"
            )
    async def add_missing_information(self, resume_data: dict, missing_information: List[dict]) -> dict:
        """Add missing information to resume data based on evaluate_cv output."""
        try:
            # Step 1: Preprocess missing_information
            processed_missing_info = []
            for item in missing_information:
                if item.get("data"):  # Only include items with non-empty data
                    processed_item = {
                        "field": item["field"],
                        "data": item["data"]
                    }
                    processed_missing_info.append(processed_item)

            # Step 2: Create prompt with explicit schema instructions
            prompt = ADD_MISSING_INFORMATION_PROMPT.format(
                resume_schema=json.dumps(ResumeSchema.schema(), indent=2, ensure_ascii=False),
                resume_data=json.dumps(resume_data, indent=2, ensure_ascii=False),
                missing_information=json.dumps(processed_missing_info, indent=2, ensure_ascii=False)
            )

            # Step 3: Call LLM to merge the information
            response = await self.llm_engine.call_llm(
                prompt=prompt,
                response_format={"type": "json_object"}
            )

            # Step 4: Parse and validate response
            try:
                updated_resume_json = json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'```json\n([\s\S]*?)\n```', response)
                if json_match:
                    updated_resume_json = json.loads(json_match.group(1))
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to parse LLM response as JSON"
                    )

            # Step 5: Validate with ResumeSchema
            updated_resume_data = ResumeSchema(**updated_resume_json)
            return updated_resume_data.dict()

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error adding missing information to resume: {str(e)}"
            )
    async def create_resume(self, resume_data: dict, job_data: dict) -> dict:
        """Generate a new resume based on user resume data and job description using ResumeFlow logic."""
        try:
            # Step 1: Validate inputs using schemas
            try:
                resume_data = ResumeSchema(**resume_data)
                job_data = JobDetails(**job_data)
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid resume_data or job_data: {str(e)}"
                )

            # Step 2: Initialize result dictionary with default empty sections
            resume_details = {
                "personal": {
                    "name": resume_data.name,
                    "email": resume_data.email,
                    "phone": resume_data.phone,
                    "title": resume_data.title,
                    "location": resume_data.location,
                    "github": resume_data.media.github,
                    "linkedin": resume_data.media.linkedin
                }
            }

            # Step 3: Define section mapping
            section_mapping = {
                "work_experience": {"prompt": EXPERIENCE, "schema": Experiences},
                "skill_section": {"prompt": SKILLS, "schema": SkillSections},
                "projects": {"prompt": PROJECTS, "schema": Projects},
                "education": {"prompt": EDUCATIONS, "schema": Educations},
                "certifications": {"prompt": CERTIFICATIONS, "schema": Certifications},
                "achievements": {"prompt": ACHIEVEMENTS, "schema": Achievements},
            }

            resume_data_dict = resume_data.dict()
            
            # Step 4: Process sections concurrently
            async def process_section(section, config):
                """Process a single section and return the result."""
                if section == "achievements":
                    # Special handling for achievements section
                    combined_achievements_data = {
                        "projects": resume_data_dict.get("projects", []),
                        "work_experience": resume_data_dict.get("work_experience", []),
                        "achievements": resume_data_dict.get("achievements", [])
                    }
                    
                    prompt = config["prompt"].format(
                        section_data=json.dumps(combined_achievements_data, indent=2, ensure_ascii=False),
                        job_description=json.dumps(job_data.dict(), indent=2, ensure_ascii=False),
                        format_instructions=json.dumps(config["schema"].schema(), indent=2, ensure_ascii=False)
                    )
                else:
                    # Normal handling for other sections
                    prompt = config["prompt"].format(
                        section_data=json.dumps(resume_data_dict[section], indent=2, ensure_ascii=False),
                        job_description=json.dumps(job_data.dict(), indent=2, ensure_ascii=False),
                        format_instructions=json.dumps(config["schema"].schema(), indent=2, ensure_ascii=False)
                    )
                
                response = await self.llm_engine.call_llm(
                    prompt=prompt,
                    response_format={"type": "json_object"}
                )
                
                try:
                    response_json = json.loads(response)
                except json.JSONDecodeError:
                    json_match = re.search(r'```json\n([\s\S]*?)\n```', response)
                    if json_match:
                        response_json = json.loads(json_match.group(1))
                    else:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to parse LLM response for {section} as JSON"
                        )
                
                return section, response_json

            # Process all sections concurrently using asyncio.gather
            tasks = [process_section(section, config) for section, config in section_mapping.items()]
            results = await asyncio.gather(*tasks)
            
            # Build resume_details from results
            for section, response_json in results:
                if section == "achievements":
                    print(f"Achievements response: {response_json}")
                    achievements = response_json.get(section, [])
                    resume_details[section] = achievements
                    print(f"Final achievements: {resume_details[section]}")
                elif section == "skill_section":
                    resume_details[section] = [item for item in response_json.get(section, []) if item.get("skills")]
                else:
                    resume_details[section] = response_json.get(section, [])

            # Step 5: Add keywords from job_data
            resume_details["keywords"] = ", ".join(job_data.keywords) if job_data.keywords else ""

            # Step 6: Save resume as JSON
            os.makedirs("temp", exist_ok=True)
            company_name = clean_string(job_data.company_name or "Unknown")
            job_title = clean_string(job_data.job_title or "Unknown")[:20]
            timestamp = int(time.time())  # Add timestamp for uniqueness
            doc_name = f"{company_name}_{job_title}_resume_{timestamp}"
            json_path = f"temp/{doc_name}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(resume_details, f, indent=2, ensure_ascii=False)

            # Step 7: Convert to PDF using LaTeX
            pdf_path = f"temp/{doc_name}.pdf"
            resume_latex = latex_to_pdf(resume_details, pdf_path)

            # Step 8: Return JSON and PDF path
            return {
                "resume_data": resume_details,
                "pdf_path": pdf_path
            }

        except Exception as e:
            # Clean up temporary files
            for file in [json_path, pdf_path] if 'json_path' in locals() and 'pdf_path' in locals() else []:
                try:
                    os.remove(file)
                except:
                    pass
            raise HTTPException(
                status_code=500,
                detail=f"Error generating resume: {str(e)}"
            )
    async def give_cv_comment_from_data(self, resume_data: dict, job_data: dict, alignment_scores: dict) -> dict:
        """Provide comments on the resume based on pre-extracted job and resume data and alignment scores."""
        try:
            prompt = GIVE_CV_COMMENT_PROMPT.format(
                resume_json=json.dumps(resume_data, indent=2, ensure_ascii=False),
                job_json=json.dumps(job_data, indent=2, ensure_ascii=False),
                alignment_scores=json.dumps(alignment_scores, indent=2, ensure_ascii=False),
                format_instructions=json.dumps(CVCommentSchema.schema(), indent=2, ensure_ascii=False)
            )
            response = await self.llm_engine.call_llm(
                prompt=prompt,
                response_format={"type": "json_object"}
            )
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'```json\n([\s\S]*?)\n```', response)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to parse LLM response as JSON"
                    )
            result = CVCommentSchema(**result).dict()
            result["missing_information"] = [
                {**item, "data": ""} for item in result["missing_information"]
            ]
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating CV comment from data: {str(e)}")

    async def calculate_content_preservation(self, resume_data_1: dict, resume_data_2: dict) -> float:
        """
        Calculate content preservation between two resume data using embedding similarity.
        
        Args:
            resume_data_1 (dict): First resume data from extract_cv output
            resume_data_2 (dict): Second resume data from extract_cv output
            
        Returns:
            float: Cosine similarity score between 0 and 1
        """
        try:
            # Extract text content from both resume data
            text_1 = extract_resume_text(resume_data_1)
            text_2 = extract_resume_text(resume_data_2)
            
            # Validate extracted text
            if not text_1.strip() or not text_2.strip():
                raise ValueError("One or both resume texts are empty after extraction")
            
            # Get embeddings for both texts
            embedding_1 = await self.llm_engine.get_embedding(text_1)
            embedding_2 = await self.llm_engine.get_embedding(text_2)
            
            # Calculate cosine similarity
            similarity = calculate_cosine_similarity(embedding_1, embedding_2)
            
            return round(similarity, 4)
            
        except Exception as e:
            print(f"Error in calculate_content_preservation: {str(e)}")
            raise Exception(f"Failed to calculate content preservation: {str(e)}")


    async def analyze_resume_improvements(self, original_resume_data: dict, enhanced_resume_data: dict) -> dict:
        """
        Analyze improvements between original and enhanced resume data.
        
        Args:
            original_resume_data (dict): Original resume data from extract_cv output
            enhanced_resume_data (dict): Enhanced resume data from extract_cv output
            
        Returns:
            dict: Dictionary containing original_summary, enhanced_summary, and improvements list
        """
        try:
            # Validate inputs using ResumeSchema
            try:
                original_resume = ResumeSchema(**original_resume_data)
                enhanced_resume = ResumeSchema(**enhanced_resume_data)
            except ValueError as e:
                raise ValueError(f"Invalid resume data format: {str(e)}")
            
            # Create prompt for LLM analysis
            prompt = RESUME_IMPROVEMENT_ANALYSIS_PROMPT.format(
                original_resume_data=json.dumps(original_resume.dict(), indent=2, ensure_ascii=False),
                enhanced_resume_data=json.dumps(enhanced_resume.dict(), indent=2, ensure_ascii=False)
            )
            
            # Call LLM to analyze improvements
            response = await self.llm_engine.call_llm(
                prompt=prompt,
                response_format={"type": "json_object"}
            )
            
            # Parse LLM response
            try:
                response_json = json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'```json\n([\s\S]*?)\n```', response)
                if json_match:
                    response_json = json.loads(json_match.group(1))
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to parse LLM response as JSON"
                    )
            
            # Extract data from response
            original_summary = response_json.get("original_summary", "Professional with relevant experience and skills.")
            enhanced_summary = response_json.get("enhanced_summary", "Enhanced professional with improved positioning and impact.")
            improvements = response_json.get("improvements", [])
            
            # Validate that we have a list of strings for improvements
            if not isinstance(improvements, list):
                improvements = ["Resume has been updated with enhanced formatting and structure"]
            
            # Ensure all items are strings
            improvements = [str(item) for item in improvements if item]
            
            # Ensure we have at least some improvements
            if not improvements:
                improvements = ["Resume has been updated with enhanced formatting and structure"]
            
            return {
                "original_summary": str(original_summary),
                "enhanced_summary": str(enhanced_summary),
                "improvements": improvements
            }
            
        except Exception as e:
            print(f"Error in analyze_resume_improvements: {str(e)}")
            # Return fallback response if LLM fails
            return {
                "original_summary": "Professional with relevant experience and skills.",
                "enhanced_summary": "Enhanced professional with improved positioning and targeted expertise.",
                "improvements": [
                    "Resume structure has been optimized for better readability",
                    "Content has been enhanced for improved professional presentation",
                    "Formatting has been updated to meet current industry standards"
                ]
            }
