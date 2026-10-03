from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.db.models import Volunteer, Ngo, User, UserRole
from pydantic import BaseModel
from typing import List

router = APIRouter()

class VolunteerProfileCreate(BaseModel):
    availability: str
    skill_tags: List[str]

class NgoProfileCreate(BaseModel):
    name: str
    description: str
    capacity: int

@router.post("/volunteers")
def create_volunteer_profile(
    profile: VolunteerProfileCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Create volunteer profile."""
    vol = Volunteer(user_id=current_user.id, availability=profile.availability, skill_tags=profile.skill_tags)
    db.add(vol)
    db.commit()
    db.refresh(vol)
    return {"id": str(vol.id), "status": "success"}

@router.post("/ngos")
def create_ngo_profile(
    profile: NgoProfileCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Create NGO profile."""
    ngo = Ngo(user_id=current_user.id, name=profile.name, description=profile.description, capacity=profile.capacity)
    db.add(ngo)
    db.commit()
    db.refresh(ngo)
    return {"id": str(ngo.id), "status": "success"}

@router.get("/ngos")
def list_ngos(db: Session = Depends(deps.get_db)):
    """List verified NGOs."""
    ngos = db.query(Ngo).filter(Ngo.verification_status == "Verified").all()
    return [{"id": str(n.id), "name": n.name, "capacity": n.capacity} for n in ngos]
