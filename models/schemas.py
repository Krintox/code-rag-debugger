from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from .symbol import Symbol, Reference, SymbolChunk, SymbolEmbeddingMetadata, IndexingJob, ReferencePack
from models.user import User

# Project schemas
class ProjectBase(BaseModel):
    name: str
    git_url: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Commit schemas
class CommitBase(BaseModel):
    hash: str
    author: str
    message: str
    timestamp: Optional[datetime] = None
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
    use_reference_pack: bool = True  # New parameter

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
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Reference schemas - moved to avoid circular imports
class DebugReferenceRequest(BaseModel):
    project_id: int
    error_snippet: str
    file_path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    token_budget: int = 4000
    ranking_params: Optional[Dict[str, float]] = None

# Forward references for symbol-related schemas
class SymbolSearchResult(BaseModel):
    symbol: 'Symbol'  # Forward reference
    similarity: float
    metadata: Dict[str, Any]

class ReferenceWithSymbol(BaseModel):
    reference: 'Reference'  # Forward reference
    depth: int
    symbol: 'Symbol'  # Forward reference
    
class ReferencePack(BaseModel):
    symbol: Symbol
    references: List[Reference]
    ranking_params: Optional[Dict[str, float]] = None
    token_budget: Optional[int] = None

class NotificationBase(BaseModel):
    message: str
    type: str = "info"  # could be "info", "warning", "error", etc.
    read: bool = False

class NotificationCreate(NotificationBase):
    user_id: int

class Notification(NotificationBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Import symbol models here to avoid circular imports
from .symbol import Symbol, Reference

# Update the forward references with actual classes
SymbolSearchResult.update_forward_refs()
ReferenceWithSymbol.update_forward_refs()