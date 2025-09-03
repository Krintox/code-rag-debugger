# File: routers/profile.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from models import schemas, crud
from models.user import User, UserSettings
from services.auth_service import get_current_active_user

router = APIRouter(prefix="/profile", tags=["profile"])
logger = logging.getLogger(__name__)

@router.get("/settings", response_model=UserSettings)
async def get_user_settings(
    current_user: User = Depends(get_current_active_user)
):
    """Get user settings"""
    # TODO: Persist user-specific settings in DB
    return UserSettings()

@router.put("/settings", response_model=UserSettings)
async def update_user_settings(
    settings: UserSettings,
    current_user: User = Depends(get_current_active_user)
):
    """Update user settings"""
    # TODO: Save settings to DB
    return settings

@router.get("/notifications", response_model=List[schemas.Notification])
async def get_user_notifications(
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    unread_only: bool = False
):
    """Get notifications for the authenticated user"""
    notifications = crud.notification.get_user_notifications(
        user_id=current_user.id, skip=skip, limit=limit, unread_only=unread_only
    )
    return notifications

@router.post("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Mark a single notification as read"""
    result = crud.notification.mark_as_read(notification_id, current_user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return {"message": "Notification marked as read"}

@router.post("/notifications/read-all")
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_active_user)
):
    """Mark all notifications as read for the authenticated user"""
    success = crud.notification.mark_all_as_read(current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read"
        )
    return {"message": "All notifications marked as read"}
