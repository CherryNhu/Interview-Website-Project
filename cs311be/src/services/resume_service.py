import os
import json
import re
from fastapi import UploadFile, HTTPException
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader

from src.prompts.prompt import RESUME_DETAILS_EXTRACTOR, JOB_DETAILS_EXTRACTOR
from src.schemas.resume_schemas import ResumeSchema, JobDetails
from src.engines.llm_engine import LLMEngine

class ResumeService:
    def __init__(self):
        self.parser = LlamaParse(
            api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
            result_type="text",
            language="vi",
            fast_mode=True,
            continuous_mode=False,
            parsing_instruction="Extract personal information, work experience, education, projects, certifications, achievements, and skills from the CV."
        )
        self.llm_engine = LLMEngine()

    async def extract_cv(self, file: UploadFile) -> dict:
        """Extract content from CV file (PDF or DOCX) using ResumeFlow schema."""
        try:
            # Save temp file
            file_path = f"temp/{file.filename}"
            os.makedirs("temp", exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(await file.read())

            # Parse document
            if not file_path.lower().endswith(('.pdf', '.docx')):
                raise ValueError("Only PDF and DOCX files are supported")

            file_extractor = {".pdf": self.parser, ".docx": self.parser}
            reader = SimpleDirectoryReader(
                input_files=[file_path],
                file_extractor=file_extractor
            )
            documents = await reader.aload_data()

            # Extract and clean text
            resume_text = "\n".join(doc.text for doc in documents)

            # Build prompt manually
            resume_schema = ResumeSchema.schema()
            prompt = RESUME_DETAILS_EXTRACTOR.format(
                resume_text=resume_text,
                format_instructions=json.dumps(resume_schema, indent=2, ensure_ascii=False)
            )

            # Call LLM to parse into JSON
            response = await self.llm_engine.call_llm(
                prompt=prompt,
                response_format={"type": "json_object"}
            )

            # Parse JSON response
            try:
                resume_json = json.loads(response)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code block
                json_match = re.search(r'```json\n([\s\S]*?)\n```', response)
                if json_match:
                    resume_json = json.loads(json_match.group(1))
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to parse LLM response as JSON"
                    )

            # Validate JSON with Pydantic
            resume_data = ResumeSchema(**resume_json)

            # Cleanup temp file
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

    async def extract_job_details(self, job_description: str) -> dict:
        """Extract job details from text using ResumeFlow schema."""
        try:
            # Build prompt manually
            job_schema = JobDetails.schema()
            prompt = JOB_DETAILS_EXTRACTOR.format(
                job_description=job_description,
                format_instructions=json.dumps(job_schema, indent=2, ensure_ascii=False)
            )

            # Call LLM to parse into JSON
            response = await self.llm_engine.call_llm(
                prompt=prompt,
                response_format={"type": "json_object"}
            )

            # Parse JSON response
            try:
                job_json = json.loads(response)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code block
                json_match = re.search(r'```json\n([\s\S]*?)\n```', response)
                if json_match:
                    job_json = json.loads(json_match.group(1))
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to parse LLM response as JSON"
                    )

            # Validate JSON with Pydantic
            job_data = JobDetails(**job_json)

            return job_data.dict()

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing job description: {str(e)}"
            )