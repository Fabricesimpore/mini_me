from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    cognitive_profile = Column(JSON, nullable=True)
    privacy_settings = Column(JSON, nullable=True)

    def __init__(self, email, name, password_hash, cognitive_profile=None, privacy_settings=None):
        self.email = email
        self.name = name
        self.password_hash = password_hash
        self.cognitive_profile = cognitive_profile
        self.privacy_settings = privacy_settings
