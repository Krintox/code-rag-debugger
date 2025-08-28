from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Project(BaseModel):
    id: Optional[int] = None
    name: str
    git_url: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Commit(BaseModel):
    id: Optional[int] = None
    hash: str
    author: str
    message: str
    timestamp: datetime
    files_changed: List[str]
    project_id: int

    class Config:
        from_attributes = True

class Feedback(BaseModel):
    id: Optional[int] = None
    debug_query_id: int
    helpful: bool
    comments: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True