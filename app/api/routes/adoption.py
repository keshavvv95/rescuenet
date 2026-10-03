import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.db.models import AdoptionListing, AdoptionApplication, User, UserRole
from pydantic import BaseModel
from typing import List

router = APIRouter()

class AdoptionListingCreate(BaseModel):
    animal_name: str
    species: str
    breed: str | None = None
    age_months: int | None = None
    description: str

class ApplicationCreate(BaseModel):
    message: str

@router.post("/listings")
def create_listing(
    listing: AdoptionListingCreate, 
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.NGO_Admin, UserRole.Super_Admin]))
):
    """Create an adoption listing (NGOs only)."""
    db_listing = AdoptionListing(**listing.model_dump())
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    return {"id": str(db_listing.id), "status": db_listing.status}

@router.post("/listings/{listing_id}/apply")
def apply_for_adoption(
    listing_id: str, 
    app_data: ApplicationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Submit an adoption application."""
    listing = db.query(AdoptionListing).filter(AdoptionListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
        
    application = AdoptionApplication(
        listing_id=listing.id,
        applicant_id=current_user.id,
        message=app_data.message
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return {"id": str(application.id), "status": application.status}
