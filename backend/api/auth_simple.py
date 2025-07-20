from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
import os

router = APIRouter()

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# In-memory storage for demo purposes
users_db = {}

# Schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserResponse(BaseModel):
    email: EmailStr
    username: str
    id: str
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    # Check if user exists
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user_id = f"user-{len(users_db) + 1}"
    users_db[user.email] = {
        "id": user_id,
        "email": user.email,
        "username": user.username,
        "password": get_password_hash(user.password),
        "created_at": datetime.utcnow()
    }
    
    return UserResponse(
        id=user_id,
        email=user.email,
        username=user.username,
        created_at=users_db[user.email]["created_at"]
    )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Find user
    user = users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token", response_model=Token)
async def token(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"Login attempt with username: {form_data.username}")
    print(f"Current users in DB: {list(users_db.keys())}")
    
    # Find user by email first, then by username
    user = users_db.get(form_data.username)
    
    # If not found by email, search by username
    if not user:
        for email, user_data in users_db.items():
            if user_data["username"] == form_data.username:
                user = user_data
                break
    
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = users_db.get(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        username=user["username"],
        created_at=user["created_at"]
    )