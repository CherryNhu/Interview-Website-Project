from io import BytesIO
import os
from fastapi import APIRouter, Depends, FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
import base64
from pymongo import MongoClient
import gridfs
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import pytz

# Định nghĩa timezone
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')

def get_vn_time():
    """Get current time in Vietnam timezone"""
    return datetime.now(vn_tz).replace(tzinfo=None)
from pydantic import BaseModel, EmailStr
from bson import ObjectId
import secrets
import emails

db_router = APIRouter(
    prefix="/db",
    tags=["Database Operations"]
)

# Email configuration
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
BASE_URL = os.getenv("FRONTEND_URL")

# Kết nối MongoDB
uri = os.getenv("USERDB_URI")
userdb_cluster_name = os.getenv("USERDB_CLUSTER_NAME")
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")
userdb_name = os.getenv("USERDB_NAME")
client = MongoClient(uri)
db = client[userdb_cluster_name]
fs = gridfs.GridFS(db)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
users_collection = db[userdb_name]
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        exp = payload.get("exp")
        
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        # Kiểm tra token có hết hạn không
        if exp and get_vn_time().timestamp() > exp:
            raise HTTPException(status_code=401, detail="Token has expired")
            
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
def generate_verification_token() -> str:
    """Generate a random verification token"""
    return secrets.token_urlsafe(32)

async def send_verification_email(email: str, token: str):
    """Send verification email to user"""
    verification_url = f"{BASE_URL}/verify-account?token={token}"
    
    message = emails.html(
        html=f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Verify Your Email</h2>
            <p>Hello,</p>
            <p>Thank you for registering. Please click the button below to verify your email:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_url}" 
                   style="background: linear-gradient(135deg, #3b82f6, #8b5cf6);
                          color: white; 
                          padding: 14px 25px; 
                          text-decoration: none; 
                          border-radius: 12px; 
                          display: inline-block;
                          font-weight: bold;">
                    Verify Email
                </a>
            </div>
            <p>This link will expire in 2 minutes.</p>
            <p>Best regards,<br>CVision Team</p>
        </div>
        """,
        subject="Verify Your Email - CVision",
        mail_from=("CVision", EMAIL_USERNAME),
        mail_to=email
    )
    
    response = message.send(
        smtp={
            "host": EMAIL_HOST,
            "port": EMAIL_PORT,
            "ssl": False,
            "tls": True,
            "user": EMAIL_USERNAME,
            "password": EMAIL_PASSWORD
        }
    )
    return response.status_code == 250

class RegisterUserRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
class LoginUserRequest(BaseModel):
    email: str
    password: str

@db_router.post("/login/")
async def login_user(request: LoginUserRequest):
    try:
        # Tìm người dùng theo email
        user = users_collection.find_one({"email": request.email})
        if not user:
            raise HTTPException(status_code=400, detail="The email or password you entered is incorrect")

        # Kiểm tra mật khẩu
        if not pwd_context.verify(request.password, user["password"]):
            raise HTTPException(status_code=400, detail="The email or password you entered is incorrect")

        # Kiểm tra xác thực email
        if not user.get("is_verified", False):
            raise HTTPException(status_code=403, detail="Please verify your email before signing in")

        # Tạo JWT token
        token_data = {
            "sub": user["email"],
            "exp": get_vn_time() + timedelta(hours=24)  # Token hết hạn sau 24 giờ
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        # Trả về token và thông tin người dùng
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": str(user["_id"]),  # Convert ObjectId to string
                "full_name": user["full_name"],
                "email": user["email"],
                "resume_id": str(user.get("resume_id")) if user.get("resume_id") else None,  # Convert if exists
                "avatar_id": str(user.get("avatar_id")) if user.get("avatar_id") else None,  # Convert if exists
                "jd_id": str(user.get("jd_id")) if user.get("jd_id") else None  # Convert if exists
            }
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again later")



@db_router.post("/register/")
async def register_user(request: RegisterUserRequest, background_tasks: BackgroundTasks):
    try:
        # Check if email already exists
        existing_user = users_collection.find_one({"email": request.email})
        if existing_user:
            if existing_user.get("is_verified", False):
                raise HTTPException(status_code=400, detail="Email already registered")
            else:
                # If user exists but not verified, delete old record
                users_collection.delete_one({"_id": existing_user["_id"]})

        # Generate verification token
        verification_token = generate_verification_token()
        token_expires = get_vn_time() + timedelta(minutes=2)

        # Hash password
        hashed_password = pwd_context.hash(request.password)

        # Create new user
        user = {
            "full_name": request.full_name,
            "email": request.email,
            "password": hashed_password,
            "is_verified": False,
            "verification_token": verification_token,
            "token_expires_at": token_expires,
            "created_at": get_vn_time()
        }
        result = users_collection.insert_one(user)

        # Send verification email in background
        background_tasks.add_task(send_verification_email, request.email, verification_token)

        return {
            "message": "Registration successful! Please check your email to verify your account.",
            "user_id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while registering user")

@db_router.get("/verify-email")
async def verify_email(token: str):
    """Verify email using token"""
    try:
        # Find user with token
        user = users_collection.find_one({"verification_token": token})
        
        if not user:
            raise HTTPException(
                status_code=400, 
                detail="Invalid verification token"
            )

        # If already verified, just return success
        if user.get("is_verified", False):
            return {"message": "Email already verified!"}
            
        # Check if token has expired
        if user.get("token_expires_at", get_vn_time()) < get_vn_time():
            raise HTTPException(
                status_code=400,
                detail="Verification token has expired"
            )
        
        # Update verification status
        users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "is_verified": True,
                    "verified_at": get_vn_time()
                },
                "$unset": {
                    "verification_token": "",
                    "token_expires_at": ""
                }
            }
        )
        
        return {"message": "Email verified successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while verifying email")

@db_router.post("/resend-verification")
async def resend_verification_email(email: str = Form(...)):
    """Resend verification email"""
    try:
        # Find user regardless of verification status
        user = users_collection.find_one({"email": email})
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        if user.get("is_verified", False):
            raise HTTPException(
                status_code=400,
                detail="Email is already verified"
            )
        
        # Generate new token
        new_token = generate_verification_token()
        token_expires = get_vn_time() + timedelta(hours=24)
        
        # Update token and expiry
        users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "verification_token": new_token,
                    "token_expires_at": token_expires
                }
            }
        )
        
        # Send new verification email
        success = await send_verification_email(email, new_token)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to send verification email. Please try again later."
            )
        
        return {"message": "Verification email has been resent!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while resending verification email")

@db_router.get("/dashboard/")
async def get_dashboard(current_user: str = Depends(get_current_user)):
    # Check if user is verified
    user = users_collection.find_one({"email": current_user})
    if not user.get("is_verified", False):
        raise HTTPException(status_code=403, detail="Please verify your email first")
    
    return {"message": f"Welcome to your dashboard, {current_user}!"}

@db_router.post("/upload-resume/")
async def upload_resume(user_id: str = Form(...), file: UploadFile = File(...)):
    try:
        # Kiểm tra loại file (chỉ cho phép PDF hoặc DOCX)
        if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and DOCX are allowed.")
        
        # Chuyển user_id thành ObjectId
        user_object_id = ObjectId(user_id)
        
        # Lấy thông tin user để kiểm tra resume cũ
        user = users_collection.find_one({"_id": user_object_id})
        if user and "resume_id" in user:
            # Xóa resume cũ từ GridFS
            try:
                fs.delete(user["resume_id"])
            except gridfs.errors.NoFile:
                # Bỏ qua nếu file không tồn tại
                pass
        
        # Lưu file mới vào GridFS
        file_id = fs.put(await file.read(), filename=file.filename, content_type=file.content_type)
        
        # Lưu file_id vào MongoDB
        users_collection.update_one(
            {"_id": user_object_id},  # Sử dụng ObjectId
            {"$set": {"resume_id": file_id}},
            upsert=True
        )
        
        return {"message": "Resume uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while uploading resume")


@db_router.post("/submit-jd/")
async def submit_jd(user_id: str = Form(...), jd_text: str = Form(...)):
    try:
        # Convert user_id to ObjectId
        user_object_id = ObjectId(user_id)

        # Save JD text in MongoDB
        users_collection.update_one(
            {"_id": user_object_id},
            {"$set": {"jd_text": jd_text}},
            upsert=True
        )

        return {"message": "Job description submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while submitting job description")

@db_router.post("/upload-avatar/")
async def upload_avatar(user_id: str = Form(...), file: UploadFile = File(...)):
    try:
        # Kiểm tra loại file (chỉ cho phép ảnh)
        if file.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG and PNG are allowed.")
        
        # Lưu file vào GridFS
        file_id = fs.put(await file.read(), filename=file.filename, content_type=file.content_type)
        
        # Chuyển user_id thành ObjectId
        user_object_id = ObjectId(user_id)
        
        # Lưu file_id vào MongoDB
        users_collection.update_one(
            {"_id": user_object_id},  # Sử dụng ObjectId
            {"$set": {"avatar_id": file_id}},
            upsert=True
        )
        
        return {"message": "Avatar uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while uploading avatar")

@db_router.get("/download-resume/{user_id}")
async def download_resume(user_id: str):
    try:
        # Lấy file_id từ MongoDB
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user or "resume_id" not in user:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Chuyển đổi resume_id từ chuỗi sang ObjectId
        resume_id = ObjectId(user["resume_id"])
        
        # Lấy file từ GridFS
        file = fs.get(resume_id)
        
        # Trả về file
        return StreamingResponse(
            BytesIO(file.read()),
            media_type=file.content_type,
            headers={
                "Content-Disposition": f"attachment; filename={file.filename}"
            }
        )
    except gridfs.errors.NoFile:
        raise HTTPException(status_code=404, detail="File not found in GridFS")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while downloading resume")

@db_router.get("/download-jd/{user_id}")
async def download_jd(user_id: str):
    try:

        # Lấy file_id từ MongoDB
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user or "jd_id" not in user:
            raise HTTPException(status_code=404, detail="JD not found")

        # Chuyển đổi jd_id từ chuỗi sang ObjectId
        jd_id = ObjectId(user["jd_id"])

        # Lấy file từ GridFS
        file = fs.get(jd_id)

        # Trả về file
        return StreamingResponse(
            BytesIO(file.read()),
            media_type=file.content_type,
            headers={
                "Content-Disposition": f"attachment; filename={file.filename}"
            }
        )
    except gridfs.errors.NoFile:
        raise HTTPException(status_code=404, detail="File not found in GridFS")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while downloading job description")


@db_router.get("/download-avatar/{user_id}")
async def download_avatar(user_id: str):

    try:
        # Lấy file_id từ MongoDB
        user = users_collection.find_one({"_id": user_id})
        if not user or "avatar_id" not in user:
            raise HTTPException(status_code=404, detail="Avatar not found")
        
        # Chuyển đổi avatar_id từ chuỗi sang ObjectId
        avatar_id = ObjectId(user["avatar_id"])
        
        # Lấy file từ GridFS
        file = fs.get(avatar_id)
        
        # Trả về file ảnh
        return StreamingResponse(
            BytesIO(file.read()),
            media_type=file.content_type
        )
    except gridfs.errors.NoFile:
        raise HTTPException(status_code=404, detail="File not found in GridFS")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while downloading avatar")

@db_router.get("/view-resume/{user_id}")
async def view_resume(user_id: str):
    try:
        # Lấy file_id từ MongoDB
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user or "resume_id" not in user:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Chuyển đổi resume_id từ chuỗi sang ObjectId
        resume_id = ObjectId(user["resume_id"])
        
        # Lấy file từ GridFS
        file = fs.get(resume_id)
        
        # Xác định loại file
        is_pdf = file.content_type == "application/pdf"
        
        # Nếu là PDF, trả về base64 để hiển thị
        # Nếu là DOCX, trả về binary để download
        if is_pdf:
            file_content = base64.b64encode(file.read()).decode("utf-8")
            return {
                "filename": file.filename,
                "content_type": file.content_type,
                "file_content": file_content,
                "is_pdf": True
            }
        else:
            return {
                "filename": file.filename,
                "content_type": file.content_type,
                "is_pdf": False
            }
    except gridfs.errors.NoFile:
        raise HTTPException(status_code=404, detail="File not found in GridFS")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while viewing resume")

@db_router.post("/save-analysis-result/")
async def save_analysis_result(user_id: str = Form(...), score: str = Form(...), report: UploadFile = File(...)):
    try:
        # Kiểm tra loại file (chỉ cho phép PDF)
        if report.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Invalid file type. Only PDF is allowed.")

        # Lưu file report vào GridFS
        report_id = fs.put(await report.read(), filename=report.filename, content_type=report.content_type)

        # Tạo đối tượng resume-analysis-result
        analysis_result = {
            "user_id": ObjectId(user_id),
            "score": score,
            "report_id": report_id,
            "created_at": get_vn_time()
        }

        # Lưu vào MongoDB
        db["resume_analysis_results"].insert_one(analysis_result)

        return {"message": "Analysis result saved successfully", "report_id": str(report_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while saving analysis result")

@db_router.post("/save-improvement-results/")
async def save_improvement_results(user_id: str = Form(...), score: str = Form(...), resume: UploadFile = File(...)):
    try:
        # Kiểm tra loại file (chỉ cho phép PDF)
        if resume.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Invalid file type. Only PDF is allowed.")

        # Lưu file resume vào GridFS
        new_resume_id = fs.put(await resume.read(), filename=resume.filename, content_type=resume.content_type)

        # Tạo đối tượng resume-improvement-result
        improvement_result = {
            "user_id": ObjectId(user_id),
            "score": score,
            "new_resume_id": new_resume_id,
            "created_at": get_vn_time()
        }

        # Lưu vào MongoDB
        result = db["resume_improvement_results"].insert_one(improvement_result)

        return {
            "message": "Improvement result saved successfully", 
            "id": str(result.inserted_id),
            "new_resume_id": str(new_resume_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while saving improvement result")

@db_router.get("/get-history/{user_id}")
async def get_history(user_id: str):
    try:
        # Chuyển user_id thành ObjectId
        user_object_id = ObjectId(user_id)
        
        # Lấy tất cả kết quả phân tích resume
        analysis_results = list(db["resume_analysis_results"].find(
            {"user_id": user_object_id},
            {"_id": 1, "score": 1, "report_id": 1, "created_at": 1}
        ).sort("created_at", -1))  # Sắp xếp theo thời gian mới nhất
        
        # Lấy tất cả kết quả cải thiện resume
        improvement_results = list(db["resume_improvement_results"].find(
            {"user_id": user_object_id},
            {"_id": 1, "score": 1, "new_resume_id": 1, "created_at": 1}
        ).sort("created_at", -1))  # Sắp xếp theo thời gian mới nhất

        # Lấy tất cả interview sessions của user (hỗ trợ cả ObjectId và string user_id)
        all_interview_sessions = list(db["interview_sessions"].find(
            {"$or": [
                {"user_id": user_object_id},
                {"user_id": str(user_object_id)}
            ]},
            {"_id": 1, "session_id": 1, "status": 1, "created_at": 1, "source": 1}
        ).sort("created_at", -1))  # Sắp xếp theo thời gian mới nhất

        # Tính toán thống kê interview
        total_interviews = len(all_interview_sessions)
        completed_interviews = len([s for s in all_interview_sessions if s.get("status") == "completed"])
        interview_completion_rate = (completed_interviews / total_interviews * 100) if total_interviews > 0 else 0
        
        print(total_interviews)             
        # Lấy chỉ các interview đã completed để hiển thị trong history
        interview_results = [s for s in all_interview_sessions if s.get("status") == "completed"]
        
        for result in interview_results:
            result["_id"] = str(result.get("_id"))
            if "session_id" in result and result["session_id"] is not None:
                result["session_id"] = str(result["session_id"])
            result["created_at"] = result["created_at"].isoformat()
            result["source"] = result["source"]
            

        # Chuyển ObjectId thành string để có thể serialize
        for result in analysis_results:
            result["_id"] = str(result["_id"])
            result["report_id"] = str(result["report_id"])
            result["created_at"] = result["created_at"].isoformat()

        for result in improvement_results:
            result["_id"] = str(result["_id"])
            result["new_resume_id"] = str(result["new_resume_id"])
            result["created_at"] = result["created_at"].isoformat()
        return {
            "analysis_results": analysis_results,
            "improvement_results": improvement_results,
            "interview_results": interview_results,
            "interview_stats": {
                "total_interviews": total_interviews,
                "completed_interviews": completed_interviews,
                "completion_rate": round(interview_completion_rate, 1)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching history")

@db_router.get("/download-history-file/{file_id}")
async def download_history_file(file_id: str):
    try:
        # Lấy file từ GridFS
        file = fs.get(ObjectId(file_id))
        
        # Trả về file
        return StreamingResponse(
            BytesIO(file.read()),
            media_type=file.content_type,
            headers={
                "Content-Disposition": f"attachment; filename={file.filename}"
            }
        )
    except gridfs.errors.NoFile:
        raise HTTPException(status_code=404, detail="File not found in GridFS")
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while downloading file")

@db_router.get("/user-files/{user_id}")
async def get_user_files(user_id: str):
    try:
        # Fetch user from MongoDB
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Return resume_id and jd_text
        return {
            "resume_id": str(user.get("resume_id")) if user.get("resume_id") else None,
            "jd_text": user.get("jd_text")if user.get("resume_id") else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching user files")