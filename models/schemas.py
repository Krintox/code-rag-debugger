from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# Remove the import from . import crud since it causes circular import
# Project schemas
class ProjectBase(BaseModel):
    name: str
    git_url: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Commit schemas
class CommitBase(BaseModel):
    hash: str
    author: str
    message: str
    timestamp: datetime
    files_changed: List[str]

class CommitCreate(CommitBase):
    project_id: int

class Commit(CommitBase):
    id: int
    project_id: int
    
    class Config:
        from_attributes = True

# Debug query schemas
class DebugQuery(BaseModel):
    error_message: str
    code_snippet: Optional[str] = None
    file_path: Optional[str] = None
    additional_context: Optional[str] = None
    project_id: int

class DebugContext(BaseModel):
    commit: Optional[Commit] = None
    similar_errors: List[Any] = []
    documentation: List[str] = []
    code_suggestions: List[str] = []

class DebugResponse(BaseModel):
    solution: str
    context: DebugContext
    confidence: float

# RAG schemas
class RAGQuery(BaseModel):
    query: str
    project_id: int
    max_results: int = 5

class RAGResult(BaseModel):
    content: str
    source: str
    similarity: float

class RAGResponse(BaseModel):
    results: List[RAGResult]
    answer: str

# User feedback schemas
class FeedbackBase(BaseModel):
    debug_query_id: int
    helpful: bool
    comments: Optional[str] = None

class FeedbackCreate(FeedbackBase):
    pass

class Feedback(FeedbackBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True