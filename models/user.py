# File: models/user.py
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    READER = "reader"
    GUEST = "guest"

class SubscriptionPlan(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None

class User(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    role: UserRole
    subscription_plan: SubscriptionPlan
    subscription_expires_at: Optional[datetime] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

class TokenData(BaseModel):
    user_id: Optional[str] = None  # Change from int to str
    email: Optional[str] = None

class SubscriptionCreate(BaseModel):
    plan: SubscriptionPlan
    payment_method_id: Optional[str] = None

class SubscriptionUpdate(BaseModel):
    plan: Optional[SubscriptionPlan] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None

class NotificationPreferences(BaseModel):
    email_notifications: bool = True
    push_notifications: bool = True
    project_updates: bool = True
    security_alerts: bool = True
    newsletter: bool = False

class UserSettings(BaseModel):
    theme: str = "light"
    language: str = "en"
    timezone: str = "UTC"
    notification_preferences: NotificationPreferences