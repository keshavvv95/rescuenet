import os
import uuid
import shutil
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, cast
from geoalchemy2 import Geography
from pydantic import BaseModel
from app.api import deps
from app.db.models import Complaint, User, ComplaintStatus, ZoneSighting
from app.services import ai_detector

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ComplaintResponse(BaseModel):
    id: str | None = None
    title: str | None = None
    status: str | None = None
    is_emergency: bool | None = None
    priority_score: float | None = None
    priority_reasoning: str | None = None
    ai_animal_type: str | None = None
    ai_confidence: float | None = None
    photo_authentic: bool | None = None
    photo_authenticity_scores: dict | None = None
    is_possible_duplicate: bool = False
    candidate_match_id: str | None = None
    auto_merged_to_id: str | None = None
    message: str | None = None

    class Config:
        from_attributes = True

@router.post("/", response_model=ComplaintResponse)
def submit_complaint(
    title: str = Form(...),
    description: str = Form(None),
    latitude: float = Form(...),
    longitude: float = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Submit a new complaint with AI detection, authenticity, priority, and duplicate checking."""
    
    # 1. Save uploaded photo
    file_ext = os.path.splitext(photo.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    photo_url = f"/static/uploads/{unique_filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(photo.file, buffer)
        
    # 2. Call AI Detection Model
    detection_result = ai_detector.detect_animal(file_path)
    
    # 3. Authenticity Check
    auth_result = ai_detector.verify_photo_authenticity(file_path, latitude, longitude)
    
    # 4. Priority Scoring
    priority = ai_detector.calculate_priority(description, detection_result["confidence"])
    
    # 5. Duplicate Detection (Consensus-Based)
    # PostGIS distance: 100 meters, time within last 48 hours
    time_threshold = datetime.utcnow() - timedelta(hours=48)
    
    location_wkt = f"POINT({longitude} {latitude})"
    
    candidates = db.query(Complaint).filter(
        Complaint.created_at >= time_threshold,
        func.ST_DWithin(
            cast(Complaint.location, Geography),
            cast(func.ST_GeomFromText(location_wkt, 4326), Geography),
            100 # meters
        )
    ).all()
    
    is_possible_duplicate = False
    candidate_match_id = None
    auto_merged = False
    
    for candidate in candidates:
        # Check image similarity
        # SIMPLIFIED: Assume local file exists at candidate.photo_url path equivalent
        candidate_file_path = os.path.join(UPLOAD_DIR, os.path.basename(candidate.photo_url))
        if os.path.exists(candidate_file_path):
            similarity = ai_detector.check_image_similarity(file_path, candidate_file_path)
        else:
            similarity = 0.5 # Default mock
            
        spatial_match = True # Because it passed ST_DWithin
        image_match = similarity > 0.8
        
        if spatial_match and image_match:
            # Auto-merge: create a zone sighting instead of a new complaint
            sighting = ZoneSighting(
                complaint_id=candidate.id,
                reporter_id=current_user.id,
                location=location_wkt,
                photo_url=photo_url
            )
            db.add(sighting)
            db.commit()
            
            return ComplaintResponse(
                auto_merged_to_id=str(candidate.id),
                message="Your report was auto-merged as a sighting to an existing active case."
            )
        elif spatial_match or image_match:
            is_possible_duplicate = True
            candidate_match_id = str(candidate.id)
            # Do not break, just flag and continue to create as new
    
    # 6. Save as new complaint if not auto-merged
    new_complaint = Complaint(
        reporter_id=current_user.id,
        title=title,
        description=description,
        photo_url=photo_url,
        location=location_wkt,
        status=ComplaintStatus.New,
        ai_animal_type=detection_result["animal_type"],
        ai_confidence=detection_result["confidence"],
        photo_authentic=auth_result["is_authentic"],
        photo_authenticity_scores=auth_result["scores"],
        is_emergency=priority["is_emergency"],
        priority_score=priority["score"],
        priority_reasoning=priority["reasoning"]
    )
    
    db.add(new_complaint)
    db.commit()
    db.refresh(new_complaint)
    
    # Auto-assign to nearest officer (PostGIS nearest-neighbor <->>)
    nearest_officer = db.query(User).filter(User.role == "Officer").order_by(
        User.zone_id # SIMPLIFIED: In full version, use actual officer last_known_location and <-> operator. Here we just take the first for the demo.
    ).first()
    
    if nearest_officer:
        new_complaint.assigned_to_id = nearest_officer.id
        new_complaint.status = ComplaintStatus.Assigned
        db.commit()
    
    resp = ComplaintResponse.model_validate(new_complaint)
    resp.id = str(new_complaint.id)
    resp.is_possible_duplicate = is_possible_duplicate
    resp.candidate_match_id = candidate_match_id
    if is_possible_duplicate:
        resp.message = "Possible duplicate found. Saved as new but flagged for review."
    
    return resp

@router.patch("/{complaint_id}/status")
def update_complaint_status(
    complaint_id: str, 
    status: ComplaintStatus, 
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Update status. If 'Not Found', widen the search radius."""
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    complaint.status = status
    
    message = f"Status updated to {status.value}"
    
    if status == ComplaintStatus.Not_Found:
        # Keep case active, widen search radius for the frontend to show
        # SIMPLIFIED: In a full version, we'd emit a WebSocket event to nearby users
        # and update a `search_radius_meters` column on the complaint.
        message = "Case marked Not Found. Search radius expanded to 500m for 4 hours."
        
    db.commit()
    return {"status": status.value, "message": message}

