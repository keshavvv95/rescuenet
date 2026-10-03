import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal, engine
from app.db.models import Base, User, CommunityZone, Complaint, ComplaintStatus, UserRole
from app.core.security import get_password_hash
import uuid

def seed():
    # Caution: This will drop and recreate all tables. Requires PostGIS enabled on DB.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # 1. Create Zone
    zone = CommunityZone(
        name="Downtown District",
        polygon_area="POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))" # Dummy coordinate box
    )
    db.add(zone)
    db.commit()
    db.refresh(zone)
    
    # 2. Create Users
    citizen = User(
        email="citizen@rescuenet.test",
        password_hash=get_password_hash("password123"),
        full_name="John Doe",
        role=UserRole.Citizen,
        zone_id=zone.id
    )
    officer = User(
        email="officer@rescuenet.test",
        password_hash=get_password_hash("password123"),
        full_name="Officer Jane",
        role=UserRole.Officer,
        zone_id=zone.id
    )
    db.add_all([citizen, officer])
    db.commit()
    db.refresh(citizen)
    db.refresh(officer)
    
    # 3. Create a Complaint
    complaint = Complaint(
        reporter_id=citizen.id,
        assigned_to_id=officer.id,
        title="Injured Stray Dog",
        description="Dog hit by vehicle, bleeding.",
        photo_url="/static/uploads/dummy.jpg",
        location="POINT(0.5 0.5)",
        status=ComplaintStatus.Assigned,
        is_emergency=True,
        priority_score=100.0,
        priority_reasoning="Emergency keyword detected: 'bleeding'; 'hit by vehicle'",
        ai_animal_type="Dog",
        ai_confidence=0.92,
        photo_authentic=True
    )
    db.add(complaint)
    db.commit()
    
    print("Seed data loaded successfully!")
    db.close()

if __name__ == "__main__":
    seed()
