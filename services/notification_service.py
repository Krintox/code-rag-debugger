# File: services/notification_service.py
from typing import List, Dict, Any
from models import crud
from services.email_service import email_service
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        pass

    def create_notification(
        self, 
        user_id: int, 
        type: str, 
        title: str, 
        message: str, 
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Create a new notification for a user"""
        try:
            notification_data = {
                "user_id": user_id,
                "type": type,
                "title": title,
                "message": message,
                "metadata": metadata or {}
            }
            
            result = crud.notification.create(notification_data)
            return result is not None
            
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            return False

    def send_email_notification(
        self, 
        user_email: str, 
        user_id: int, 
        type: str, 
        title: str, 
        message: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Send email notification and create in-app notification"""
        # Create in-app notification
        self.create_notification(user_id, type, title, message, metadata)
        
        # Send email if it's an important notification
        if type in ["error", "warning"]:
            return email_service.send_project_notification(
                user_email, 
                "System Notification", 
                f"{title}: {message}"
            )
        
        return True

    def get_user_notifications(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100, 
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get user notifications"""
        return crud.notification.get_user_notifications(
            user_id, skip, limit, unread_only
        )

    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        result = crud.notification.mark_as_read(notification_id, user_id)
        return result is not None

    def mark_all_as_read(self, user_id: int) -> bool:
        """Mark all notifications as read"""
        return crud.notification.mark_all_as_read(user_id)

notification_service = NotificationService()