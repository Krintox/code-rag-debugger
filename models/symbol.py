from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class SymbolType(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    CONSTANT = "constant"
    VARIABLE = "variable"
    MODULE = "module"
    IMPORT = "import"

class ReferenceType(str, Enum):
    CALL = "call"
    IMPORT = "import"
    INHERITANCE = "inheritance"
    USAGE = "usage"
    IMPLEMENTATION = "implementation"

class SymbolBase(BaseModel):
    project_id: int
    symbol_name: str
    symbol_type: SymbolType
    language: str
    file_path: str
    start_line: int
    end_line: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    commit_hash: Optional[str] = None
    token_count_estimate: int = 0
    usage_count: int = 0
    centrality_score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SymbolCreate(SymbolBase):
    pass

class Symbol(SymbolBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SymbolChunk(BaseModel):
    id: Optional[int] = None
    symbol_id: int
    chunk_index: int
    content: str
    start_line: int
    end_line: int
    embedding_vector_id: Optional[str] = None
    token_count: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Reference(BaseModel):
    id: Optional[int] = None
    from_symbol_id: int
    to_symbol_id: int
    reference_type: ReferenceType
    file_path: str
    line: int
    context_snippet: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SymbolEmbeddingMetadata(BaseModel):
    id: Optional[int] = None
    symbol_id: int
    pinecone_id: str
    namespace: str
    embedding_dim: int
    last_upserted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class IndexingJob(BaseModel):
    id: Optional[int] = None
    project_id: int
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    stats: Dict[str, Any] = Field(default_factory=dict)
    last_error: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ReferencePack(BaseModel):
    symbol: Symbol
    definition: str
    references: List[Dict[str, Any]]
    callers: List[Dict[str, Any]]
    callees: List[Dict[str, Any]]
    imports: List[Dict[str, Any]]
    tests: List[Dict[str, Any]]
    historical_fixes: List[Dict[str, Any]]
    token_count: int
    reasoning: str

    class Config:
        from_attributes = True