import os
import uuid
import shutil
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, cast
from geoalchemy2 import Geography
from app.api import deps
from app.db.models import User, ZoneSighting, Complaint, ComplaintStatus
from pydantic import BaseModel
from typing import List

router = APIRouter()
UPLOAD_DIR = "uploads"

class SightingResponse(BaseModel):
    id: str
    complaint_id: str
    message: str

@router.post("/sightings", response_model=SightingResponse)
def create_sighting(
    latitude: float = Form(...),
    longitude: float = Form(...),
    photo: UploadFile = File(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Post a live sighting update in a zone. Auto-links to the nearest active case by proximity + time.
    """
    location_wkt = f"POINT({longitude} {latitude})"
    time_threshold = datetime.utcnow() - timedelta(hours=48)
    
    # Find nearest active complaint within 500m
    nearest_complaint = db.query(Complaint).filter(
        Complaint.status.in_([ComplaintStatus.Searching, ComplaintStatus.Not_Found, ComplaintStatus.In_Progress, ComplaintStatus.Assigned]),
        Complaint.created_at >= time_threshold,
        func.ST_DWithin(
            cast(Complaint.location, Geography),
            cast(func.ST_GeomFromText(location_wkt, 4326), Geography),
            500
        )
    ).order_by(
        func.ST_Distance(
            cast(Complaint.location, Geography),
            cast(func.ST_GeomFromText(location_wkt, 4326), Geography)
        )
    ).first()
    
    if not nearest_complaint:
        raise HTTPException(status_code=404, detail="No active cases found nearby to link this sighting to.")

    photo_url = None
    if photo:
        file_ext = os.path.splitext(photo.filename)[1]
        unique_filename = f"sighting_{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(photo.file, buffer)
        photo_url = f"/static/uploads/{unique_filename}"
        
    sighting = ZoneSighting(
        complaint_id=nearest_complaint.id,
        reporter_id=current_user.id,
        location=location_wkt,
        photo_url=photo_url
    )
    db.add(sighting)
    db.commit()
    db.refresh(sighting)
    
    return SightingResponse(
        id=str(sighting.id),
        complaint_id=str(nearest_complaint.id),
        message="Sighting created and auto-linked to nearby active case."
    )

@router.get("/feed")
def get_zone_feed(zone_id: str, db: Session = Depends(deps.get_db)):
    """General zone feed for informal posts."""
    posts = db.query(CommunityPost).filter(CommunityPost.zone_id == zone_id).order_by(CommunityPost.created_at.desc()).all()
    # Simplified mapping
    return [{"id": str(p.id), "content": p.content, "photo_url": p.photo_url} for p in posts]

@router.post("/sightings/{sighting_id}/upvote")
def upvote_sighting(sighting_id: str, db: Session = Depends(deps.get_db)):
    """Upvote/confirm endpoint for sighting updates."""
    # SIMPLIFIED: Just returning success. In full version, create an Upvote record in DB.
    return {"status": "success", "message": "Sighting confirmed by user."}
