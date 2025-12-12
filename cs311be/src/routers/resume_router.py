from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import FileResponse, StreamingResponse
from src.services.service import Service
from src.routers.dependencies import get_service
from pydantic import BaseModel
from typing import List, Dict, Optional
from src.utils.text_utils import clean_string, generate_simple_report_pdf
from src.utils.latex_ops import encode_tex_file
import time
import json
import os
import io
import asyncio

class ReviewRequest(BaseModel):
    resume_json: dict
    job_json: dict

class ExtractCVV2Request(BaseModel):
    required_skills: List[dict]  # Danh sách required_skills từ extract-job-v2

class GiveCVCommentRequest(BaseModel):
    alignment_scores: dict  # Alignment scores từ calculate-alignment-score

class AddMissingInformationRequest(BaseModel):
    resume_data: dict  # Đầu ra của extract_cv
    missing_information: List[dict]  # Đầu ra của evaluate_cv với trường data đã điền

class GenerateCVRequest(BaseModel):
    job_data: dict  # Đầu ra của extract-job-v2
    resume_data: dict  # Đầu ra của add-missing-information

class AnalyzeImprovementsRequest(BaseModel):
    original_resume_data: dict  # Đầu ra của extract_cv (resume gốc)
    enhanced_resume_data: dict  # Đầu ra của extract_cv (resume đã nâng cấp)

class GenerateReportRequest(BaseModel):
    alignment_scores: dict  # Alignment scores từ evaluate-cv
    cv_comment: dict  # CV comment từ evaluate-cv
    resume_data: dict  # Resume data để lấy tên ứng viên
    job_data: dict  # Job data để lấy thông tin công việc

resume_router = APIRouter(
    prefix="/resume-flow",
    tags=["Resume Flow"]
)

@resume_router.post("/extract-cv/")
async def extract_cv(
    file: UploadFile = File(...),
    service: Service = Depends(get_service)
):
    """Extract content from CV file (PDF or DOCX) using ResumeFlow schema."""
    try:
        return {"resume_data": await service.resume_flow_service.extract_cv(file)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@resume_router.post("/extract-job-v1/")
async def extract_job_v2(
    job_description: str = Form(...),
    service: Service = Depends(get_service)
):
    """Extract job details from text using ResumeFlow schema with grouped skills."""
    try:
        job_data = await service.resume_flow_service.extract_job_details(job_description, None)
        return job_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
@resume_router.post("/extract-job-v2/")
async def extract_job_v2(
    job_description: str = Form(...),
    service: Service = Depends(get_service)
):
    """Extract job details from text using ResumeFlow schema with grouped skills."""
    try:
        job_data = await service.resume_flow_service.extract_job_details_v2(job_description, None)
        return job_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@resume_router.post("/calculate-content-preservation/")
async def calculate_content_preservation(
    resume_data_1: Dict,
    resume_data_2: Dict,
    service: Service = Depends(get_service)
):
    """Calculate content preservation between two resume data using embedding similarity."""
    try:
        similarity_score = await service.resume_flow_service.calculate_content_preservation(
            resume_data_1,
            resume_data_2
        )
        return {
            "content_preservation_score": similarity_score,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating content preservation: {str(e)}")

@resume_router.post("/analyze-resume-improvements/")
async def analyze_resume_improvements(
    request: AnalyzeImprovementsRequest,
    service: Service = Depends(get_service)
):
    """Analyze improvements between original and enhanced resume data."""
    try:
        analysis_result = await service.resume_flow_service.analyze_resume_improvements(
            request.original_resume_data,
            request.enhanced_resume_data
        )
        return {
            "original_summary": analysis_result["original_summary"],
            "enhanced_summary": analysis_result["enhanced_summary"],
            "improvements": analysis_result["improvements"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing resume improvements: {str(e)}")

@resume_router.post("/calculate-alignment-score/")
async def calculate_alignment_score(
    resume_file: UploadFile = File(...),
    job_data: str = Form(...),
    job_data_v2: str = Form(...),
    service: Service = Depends(get_service)
):
    """Calculate alignment scores between resume and job description, returning only similarity scores."""
    try:

        job_data_dict = json.loads(job_data)
        job_data_v2_dict = json.loads(job_data_v2)
        
        resume_data = await service.resume_flow_service.extract_cv(resume_file)
        return {"alignment_score": await service.resume_flow_service.calculate_alignment_score(
            resume_data, 
            job_data_dict,
            job_data_v2_dict
        ),
                "resume_data": resume_data
                }
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=422, 
            detail=f"Invalid JSON in job_data or job_data_v2: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating alignment score: {str(e)}")
    
@resume_router.post("/evaluate-cv/")
async def evaluate_cv(
    job_description: str = Form(...),
    resume_file: UploadFile = File(...),
    service: Service = Depends(get_service)
):
    """Evaluate Ascertain resume against job description, returning alignment scores and review comments."""
    try:
        # ✅ Thực hiện song song job extraction và resume extraction
        job_task = service.resume_flow_service.extract_job_details_v12(job_description, None)
        resume_task = service.resume_flow_service.extract_cv(resume_file)
        
        # Chờ cả 2 task hoàn thành
        (job_data, job_data_v2), resume_data = await asyncio.gather(job_task, resume_task)

        alignment_scores = await service.resume_flow_service.calculate_alignment_score(resume_data, job_data,job_data_v2)
        
        cv_comment = await service.resume_flow_service.give_cv_comment_from_data(
            resume_data=resume_data,
            job_data=job_data,
            alignment_scores=alignment_scores
        )
        
        # Step 5: Combine results
        return {
            "resume_data": resume_data,
            "job_data": job_data,
            "job_data_v2": job_data_v2,
            "alignment_scores": alignment_scores,
            "cv_comment": cv_comment
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating CV: {str(e)}")
    
@resume_router.post("/add-missing-information/")
async def add_missing_information(
    request: AddMissingInformationRequest,
    service: Service = Depends(get_service)
):
    """Add missing information to resume data based on evaluate_cv output."""
    try:
        return {
            "updated_resume_data": await service.resume_flow_service.add_missing_information(
                request.resume_data,
                request.missing_information
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@resume_router.post("/create-resume")
async def create_resume(resume_data: Dict, job_data: Dict,service: Service = Depends(get_service)
):
    """Generate a new resume based on user resume data and job description."""
    try:
        result = await service.resume_flow_service.create_resume(resume_data, job_data)
        return {
            "resume_data": result["resume_data"],
            "pdf_path": FileResponse(
                result["pdf_path"],
                media_type="application/pdf",
                filename=os.path.basename(result["pdf_path"])
            )
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in router generating resume: {str(e)}"
        )

@resume_router.post("/add-data-and-create-resume")
async def create_resume_enhanced(resume_data: dict, missing_information: List[dict], job_data: Dict, service: Service = Depends(get_service)):
    try:
        new_resume_data = await service.resume_flow_service.add_missing_information(
            resume_data,
            missing_information
        )
        result = await service.resume_flow_service.create_resume(new_resume_data, job_data)
        
        # Generate Overleaf link
        overleaf_link = None
        pdf_path = result.get("pdf_path")
        
        if pdf_path and os.path.exists(pdf_path):
            tex_content = encode_tex_file(pdf_path)
            if tex_content:
                overleaf_link = f"data:application/zip;base64,{tex_content}"
        
        # Store PDF path temporarily for download
        pdf_filename = os.path.basename(pdf_path)
        
        # ✅ MOVE FILES TO TEMP DIRECTORY FOR DOWNLOAD
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_pdf_path = os.path.join(temp_dir, pdf_filename)
        temp_tex_path = os.path.join(temp_dir, pdf_filename.replace('.pdf', '.tex'))
        
        # Move files to temp directory
        if os.path.exists(pdf_path):
            os.rename(pdf_path, temp_pdf_path)
            
        tex_original_path = pdf_path.replace('.pdf', '.tex')
        if os.path.exists(tex_original_path):
            os.rename(tex_original_path, temp_tex_path)
        
        # ✅ CLEANUP ANY REMAINING JSON FILES IN ORIGINAL LOCATION
        json_original_path = pdf_path.replace('.pdf', '.json')
        if os.path.exists(json_original_path):
            try:
                os.remove(json_original_path)
            except Exception as e:
                print(f"Warning: Could not cleanup original JSON file: {e}")
        
        # Return metadata with Overleaf link
        return {
            "success": True,
            "new_resume_data": new_resume_data,
            "message": "Resume created successfully",
            "overleaf_link": overleaf_link,
            "pdf_filename": pdf_filename,
            "download_url": f"/resume-flow/download-pdf/{pdf_filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@resume_router.get("/download-pdf/{filename}")
async def download_pdf(filename: str):
    """Download PDF file using StreamingResponse."""
    try:
        # Construct file path (assuming files are stored in temp directory)
        file_path = os.path.join("temp", filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Read PDF file content
        with open(file_path, "rb") as pdf_file:
            pdf_content = pdf_file.read()
        
        # ✅ XÓA TẤT CẢ CÁC FILE LIÊN QUAN NGAY SAU KHI ĐỌC XONG
        try:
            # Remove PDF file
            os.remove(file_path)
            # print(f"Cleaned up PDF: {file_path}")
            
            # Remove corresponding TEX file if exists
            tex_path = file_path.replace('.pdf', '.tex')
            if os.path.exists(tex_path):
                os.remove(tex_path)
                # print(f"Cleaned up TEX: {tex_path}")
            
            # Remove corresponding JSON file if exists
            json_path = file_path.replace('.pdf', '.json')
            if os.path.exists(json_path):
                os.remove(json_path)
                # print(f"Cleaned up JSON: {json_path}")
                
        except Exception as cleanup_error:
            print(f"Warning: Could not cleanup files: {cleanup_error}")
        
        # Return PDF file using StreamingResponse
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@resume_router.post("/generate-report-pdf/")
async def generate_report_pdf(
    request: GenerateReportRequest,
    service: Service = Depends(get_service)
):
    """Generate PDF report from alignment scores and CV comments."""
    try:
        # ✅ Validate input data
        if not request.alignment_scores:
            raise HTTPException(status_code=400, detail="Alignment scores are required")
        if not request.cv_comment:
            raise HTTPException(status_code=400, detail="CV comment is required")
        if not request.resume_data:
            raise HTTPException(status_code=400, detail="Resume data is required")
        if not request.job_data:
            raise HTTPException(status_code=400, detail="Job data is required")
        
        # Create report content
        report_content = {
            "candidate_name": request.resume_data.get("name", "Unknown Candidate"),
            "job_title": request.job_data.get("job_title", "Unknown Position"),
            "company_name": request.job_data.get("company_name", "Unknown Company"),
            "alignment_scores": request.alignment_scores,
            "cv_comment": request.cv_comment,
            "generated_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Generate simple report PDF
        report_pdf_path = await generate_simple_report_pdf(report_content)
        
        # Read PDF content
        with open(report_pdf_path, "rb") as pdf_file:
            pdf_content = pdf_file.read()
        
        # Cleanup
        try:
            os.remove(report_pdf_path)
        except Exception as cleanup_error:
            print(f"Warning: Could not cleanup report file: {cleanup_error}")
        
        # Return PDF
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=resume_analysis_report.pdf"
            }
        )
    except Exception as e:
        print(f"Error generating report PDF: {str(e)}")
        # ✅ Return a more user-friendly error response
        raise HTTPException(
            status_code=500, 
            detail=f"Unable to generate report PDF. Please try again later. Error: {str(e)}"
        )