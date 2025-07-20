from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class BehavioralData(Base):
    __tablename__ = 'behavioral_data'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    behavior_type = Column(String, nullable=False)
    data = Column(JSONB, default=dict)
    source = Column(String, nullable=True) 