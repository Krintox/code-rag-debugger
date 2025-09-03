from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request, Response
from fastapi.security import OAuth2PasswordBearer
from models.user import User, UserInDB, TokenData, UserRole
from models import crud
from config import settings
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class AuthService:
    def __init__(self):
        pass

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    async def get_current_user(self, request: Request) -> UserInDB:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
        
        # Try to get token from cookie first
        token = request.cookies.get("access_token")
        
        # If not in cookie, try Authorization header
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            raise credentials_exception
        
        try:
            # Decode the token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            
            if user_id is None:
                raise credentials_exception
            
            # Convert to int and get user
            user_id_int = int(user_id)
            user = crud.user.get(user_id_int)
            
            if user is None:
                raise credentials_exception
            
            return user
            
        except (JWTError, ValueError) as e:
            logger.error(f"JWT or conversion error: {str(e)}")
            raise credentials_exception
        except Exception as e:
            logger.error(f"Unexpected error in get_current_user: {str(e)}")
            raise credentials_exception
    
    async def get_current_active_user(self, current_user: UserInDB) -> UserInDB:
        if not current_user["is_active"]:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user

    async def get_current_user_from_token(self, token: str) -> Optional[User]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            user = crud.user.get(int(user_id))
            return user
        except JWTError:
            return None

    def require_role(self, roles: List[UserRole]):
        async def role_checker(current_user: UserInDB = Depends(get_current_user_dependency)):
            if current_user["role"] not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return current_user
        return role_checker

    def require_subscription(self, plans: List[str]):
        async def subscription_checker(current_user: UserInDB = Depends(get_current_user_dependency)):
            if current_user["subscription_plan"] not in plans:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Subscription required"
                )
            return current_user
        return subscription_checker

# Create auth_service instance
auth_service = AuthService()

# Create dependency functions
async def get_current_user_dependency(request: Request):
    return await auth_service.get_current_user(request)

async def get_current_active_user_dependency(
    current_user: UserInDB = Depends(get_current_user_dependency)
):
    return await auth_service.get_current_active_user(current_user)

# Export helpers at module level so routers can import them directly
get_current_user = get_current_user_dependency
get_current_active_user = get_current_active_user_dependency
require_role = auth_service.require_role
require_subscription = auth_service.require_subscription
get_current_user_from_token = auth_service.get_current_user_from_token