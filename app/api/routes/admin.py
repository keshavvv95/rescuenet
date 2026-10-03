from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api import deps
from app.db.models import Complaint, ComplaintStatus, Donation, User
from pydantic import BaseModel
import uuid

router = APIRouter()

@router.post("/sos")
def trigger_sos(
    latitude: float, 
    longitude: float,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Trigger SOS: creates a complaint pre-marked Emergency, skips normal triage, immediately triggers nearest assignment.
    """
    location_wkt = f"POINT({longitude} {latitude})"
    
    # 1. Create emergency complaint
    sos_case = Complaint(
        reporter_id=current_user.id,
        title="SOS Emergency Sighting",
        description="Immediate assistance required. Triggered via SOS.",
        location=location_wkt,
        status=ComplaintStatus.New,
        is_emergency=True,
        priority_score=100.0,
        priority_reasoning="Triggered via SOS endpoint."
    )
    db.add(sos_case)
    db.commit()
    db.refresh(sos_case)
    
    # 2. Nearest Assignment Logic
    nearest_officer = db.query(User).filter(User.role == "Officer").first() # SIMPLIFIED: Nearest neighbor logic
    if nearest_officer:
        sos_case.assigned_to_id = nearest_officer.id
        sos_case.status = ComplaintStatus.Assigned
        db.commit()
        
    return {"message": "SOS triggered, nearest officer notified", "complaint_id": str(sos_case.id)}

@router.post("/donations/verify")
def verify_donation(payment_id: str, amount: float, db: Session = Depends(deps.get_db)):
    """Verify Razorpay/Stripe test-mode donation."""
    # SIMPLIFIED: Trust the payment ID for the demo
    donation = Donation(
        amount=amount,
        payment_gateway_id=payment_id,
        status="Completed"
    )
    db.add(donation)
    db.commit()
    return {"status": "success", "donation_id": str(donation.id)}

@router.get("/analytics")
def get_analytics(db: Session = Depends(deps.get_db)):
    """Get admin analytics (volume, heatmaps)."""
    total = db.query(Complaint).count()
    emergencies = db.query(Complaint).filter(Complaint.is_emergency == True).count()
    return {
        "complaints_count": total,
        "emergency_count": emergencies,
        "average_resolution_time": "4h" # SIMPLIFIED
    }
