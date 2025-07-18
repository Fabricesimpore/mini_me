from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import SessionLocal
from sqlalchemy.orm import Session
from fastapi import Depends
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from sqlalchemy.exc import IntegrityError
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status
from backend.app.services.auth import decode_access_token
from backend.app.models.user import User  # Add this import for type hints
from backend.app.models.user import Base
from backend.app.config import engine
from fastapi import Body
from pydantic import BaseModel
from typing import Optional, Dict, Any

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal Cognitive Clone API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/db-health")
def db_health(db: Session = Depends(get_db)):
    try:
        # Simple query to test DB connection
        db.execute(text("SELECT 1"))
        return {"db_status": "ok"}
    except Exception as e:
        return {"db_status": "error", "detail": str(e)}

@app.get("/")
async def root():
    return {"message": "Personal Cognitive Clone API"}

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    from backend.app.services.auth import get_password_hash
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, name=user.name, password_hash=hashed_password)
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
        return {"id": new_user.id, "email": new_user.email, "name": new_user.name}
    except IntegrityError:
        db.rollback()
        return {"error": "User with this email already exists."}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    from backend.app.services.auth import verify_password, create_access_token
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        return {"error": "Incorrect email or password"}
    access_token = create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_exception
    email = payload["sub"]
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

@app.get("/me")
def read_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "created_at": str(current_user.created_at)
    }

class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None

@app.put("/me")
def update_me(update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    updated = False
    if update.name is not None:
        current_user.name = update.name
        updated = True
    if update.email is not None:
        current_user.email = update.email
        updated = True
    if updated:
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "created_at": str(current_user.created_at)
    }

class CognitiveProfileModel(BaseModel):
    communication_style: Optional[Dict[str, Any]] = None
    decision_patterns: Optional[Dict[str, Any]] = None
    value_system: Optional[Dict[str, Any]] = None

@app.post("/users/{user_id}/cognitive-profile")
def create_cognitive_profile(user_id: int, profile: CognitiveProfileModel, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.cognitive_profile is not None:
        raise HTTPException(status_code=400, detail="Cognitive profile already exists")
    user.cognitive_profile = profile.dict()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.cognitive_profile

@app.get("/users/{user_id}/cognitive-profile")
def get_cognitive_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.cognitive_profile is None:
        raise HTTPException(status_code=404, detail="Cognitive profile not found")
    return user.cognitive_profile

@app.put("/users/{user_id}/cognitive-profile")
def update_cognitive_profile(user_id: int, profile: CognitiveProfileModel, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.cognitive_profile is None:
        raise HTTPException(status_code=404, detail="Cognitive profile not found")
    user.cognitive_profile = profile.dict()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.cognitive_profile

@app.delete("/users/{user_id}/cognitive-profile")
def delete_cognitive_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.cognitive_profile is None:
        raise HTTPException(status_code=404, detail="Cognitive profile not found")
    user.cognitive_profile = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"detail": "Cognitive profile deleted"}
