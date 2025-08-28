from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
from .commit import Commit

class Project(BaseModel):
    id: Optional[int] = None
    name: str
    git_url: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    commits: List[Commit] = []

    class Config:
        from_attributes = True