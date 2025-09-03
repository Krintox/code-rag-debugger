from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
import logging
from datetime import datetime, timedelta
from jose import jwt, JWTError

from models import crud
from models.user import User, UserCreate, Token, UserUpdate, SubscriptionCreate
from services.auth_service import auth_service, get_current_active_user, get_current_user_from_token
from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

@router.post("/register", response_model=User)
async def register_user(
    user_in: UserCreate, 
    background_tasks: BackgroundTasks
):
    """Register a new user"""
    if crud.user.get_by_email(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if crud.user.get_by_username(user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    user_data = user_in.model_dump()
    user_data["role"] = "developer"
    user_data["subscription_plan"] = "free"
    
    db_user = crud.user.create_user(user_data)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    return db_user

@router.post("/login", response_model=Token)
async def login_user(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """Login user and set cookies"""
    try:
        user = crud.user.get_by_email(form_data.username) or crud.user.get_by_username(form_data.username)
        
        if not user:
            logger.error(f"User not found: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        
        if not auth_service.verify_password(form_data.password, user["hashed_password"]):
            logger.error(f"Invalid password for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        
        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        access_token = auth_service.create_access_token(data={"sub": str(user["id"])})
        refresh_token = auth_service.create_refresh_token(data={"sub": str(user["id"])})
        
        # Set cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
            secure=False,
            samesite="lax"
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token
        }
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.post("/logout")
async def logout_user(response: Response):
    """Logout user by clearing cookies"""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}

@router.post("/refresh", response_model=Token)
async def refresh_token(request: Request, response: Response):
    """Refresh access token using refresh token from cookie"""
    try:
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No refresh token provided"
            )
        
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user = crud.user.get(int(user_id))
        if not user or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        access_token = auth_service.create_access_token(data={"sub": str(user["id"])})
        new_refresh_token = auth_service.create_refresh_token(data={"sub": str(user["id"])})
        
        # Update cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            secure=False,
            samesite="lax"
        )
        
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
            secure=False,
            samesite="lax"
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": new_refresh_token
        }
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.get("/me", response_model=User)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@router.put("/me", response_model=User)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update current user information"""
    updated_user = crud.user.update_user(current_user["id"], user_update.model_dump(exclude_unset=True))
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )
    return updated_user

@router.post("/me/subscription", response_model=User)
async def update_subscription(
    subscription: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Update user subscription"""
    expires_at = datetime.now() + timedelta(days=30)
    
    updated_user = crud.user.update_subscription(
        current_user["id"], 
        subscription.plan, 
        expires_at
    )
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subscription"
        )
    
    return updated_user

@router.post("/forgot-password")
async def forgot_password(email: str, background_tasks: BackgroundTasks):
    """Send password reset email"""
    user = crud.user.get_by_email(email)
    if user:
        reset_token = auth_service.create_access_token(
            data={"sub": str(user["id"]), "purpose": "password_reset"},
            expires_delta=timedelta(hours=1)
        )
        # Email service implementation would go here
    
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/reset-password")
async def reset_password(token: str, new_password: str):
    """Reset user password"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("purpose") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token purpose"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )
        
        hashed_password = auth_service.get_password_hash(new_password)
        updated_user = crud.user.update_user(int(user_id), {"hashed_password": hashed_password})
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        return {"message": "Password updated successfully"}
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

# Debug endpoints
@router.get("/debug/user/{user_id}")
async def debug_user(user_id: int):
    """Debug endpoint to check user retrieval"""
    user = crud.user.get(user_id)
    return {
        "user_id": user_id,
        "user_exists": user is not None,
        "user_data": user
    }

@router.get("/debug-token")
async def debug_token(request: Request):
    """Debug endpoint to check token validation"""
    try:
        token = request.cookies.get("access_token")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            return {"error": "No token provided"}
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        
        return {
            "token": token,
            "payload": payload,
            "user_id": user_id,
            "user_id_type": type(user_id).__name__ if user_id else None,
            "user_exists": bool(crud.user.get(int(user_id))) if user_id else False
        }
    except Exception as e:
        return {"error": str(e)}