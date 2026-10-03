from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    Citizen = "Citizen"
    Officer = "Officer"
    NGO_Admin = "NGO Admin"
    Volunteer = "Volunteer"
    Super_Admin = "Super Admin"

class ComplaintStatus(str, enum.Enum):
    New = "New"
    Assigned = "Assigned"
    In_Progress = "In Progress"
    Searching = "Searching"
    Not_Found = "Not Found"
    Closed = "Closed"

class CommunityZone(Base):
    __tablename__ = "community_zones"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    polygon_area = Column(Geometry('POLYGON', srid=4326), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String)
    role = Column(Enum(UserRole), default=UserRole.Citizen, nullable=False)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("community_zones.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title = Column(String)
    description = Column(String)
    photo_url = Column(String)
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.New, nullable=False)
    is_emergency = Column(Boolean, default=False)
    priority_score = Column(Float)
    priority_reasoning = Column(String)
    ai_animal_type = Column(String)
    ai_confidence = Column(Float)
    photo_authentic = Column(Boolean)
    photo_authenticity_scores = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class ZoneSighting(Base):
    __tablename__ = "zone_sightings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id"), nullable=False)
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    photo_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
