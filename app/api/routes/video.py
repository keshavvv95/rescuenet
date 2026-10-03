import os
import uuid
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.db.models import Complaint
from app.services import ai_detector
from pydantic import BaseModel

router = APIRouter()
UPLOAD_DIR = "uploads"

class VideoVerificationResponse(BaseModel):
    match: bool
    confidence: float
    explanation: str

@router.post("/verify", response_model=VideoVerificationResponse)
def verify_on_site(
    complaint_id: str = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(deps.get_db)
):
    """
    On-site live video / photo verification assistant.
    SIMPLIFIED: Uses single-shot photo comparison instead of continuous streaming.
    """
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    original_photo_path = os.path.join(UPLOAD_DIR, os.path.basename(complaint.photo_url))
    if not os.path.exists(original_photo_path):
        raise HTTPException(status_code=404, detail="Original photo not found on server")

    # Save new photo
    file_ext = os.path.splitext(photo.filename)[1]
    unique_filename = f"verify_{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)
        
    # Call AI verification
    result = ai_detector.verify_animal_match(
        original_image_path=original_photo_path,
        new_image_path=file_path,
        original_description=complaint.description or ""
    )
    
    return VideoVerificationResponse(**result)

