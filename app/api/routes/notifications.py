from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.db.models import Notification, User
from pydantic import BaseModel

router = APIRouter()

class NotificationResponse(BaseModel):
    id: str
    type: str
    message: str
    is_read: bool

@router.get("/", response_model=list[NotificationResponse])
def get_notifications(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Get user's notifications."""
    notifs = db.query(Notification).filter(Notification.user_id == current_user.id).all()
    return [{"id": str(n.id), "type": n.type, "message": n.message, "is_read": n.is_read} for n in notifs]

@router.post("/{notification_id}/read")
def mark_read(
    notification_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Mark notification as read."""
    notif = db.query(Notification).filter(
        Notification.id == notification_id, 
        Notification.user_id == current_user.id
    ).first()
    
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notif.is_read = True
    db.commit()
    return {"status": "success"}

def send_notification(db: Session, user_id: str, notif_type: str, message: str, email: bool = False, push: bool = False):
    """
    Utility function to send notifications.
    SIMPLIFIED: push notification interface abstraction.
    """
    n = Notification(user_id=user_id, type=notif_type, message=message)
    db.add(n)
    db.commit()
    
    if email:
        # SIMPLIFIED: SMTP call would go here
        print(f"Mock: Sending email to {user_id}")
    
    if push:
        # SIMPLIFIED: Firebase/Twilio abstraction call
        print(f"Mock: Sending push notification to {user_id}")
