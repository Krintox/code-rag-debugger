from sqlalchemy import Column, Integer, Boolean, String, DateTime, ForeignKey
from datetime import datetime
from .database import Base

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    debug_query_id = Column(Integer, index=True, nullable=False)
    helpful = Column(Boolean, default=False)
    comments = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
