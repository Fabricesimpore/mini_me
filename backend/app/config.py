from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use SQLite for local development
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Settings for authentication
class Settings:
    SECRET_KEY = "your-secret-key"  # Change this in production!
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60

settings = Settings()
