from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class Feedback(BaseModel):
    id: Optional[int] = None
    debug_query_id: int
    helpful: bool = False
    comments: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True