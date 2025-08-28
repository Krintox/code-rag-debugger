from fastapi import APIRouter, Depends, HTTPException, status
from models.database import get_db
from models import schemas
from models import crud
from services.rag_service import rag_service

router = APIRouter(prefix="/debug", tags=["debug"])

@router.post("/", response_model=schemas.DebugResponse)
def debug_code(query: schemas.DebugQuery):
    """Debug a code error using RAG"""
    # Verify project exists
    db_project = crud.project.get(query.project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Generate debug response using RAG
    result = rag_service.generate_debug_response(
        query.project_id,
        query.error_message,
        query.code_snippet,
        query.file_path,
        query.additional_context
    )
    
    return result

@router.post("/rag", response_model=schemas.RAGResponse)
def rag_query(query: schemas.RAGQuery):
    """Perform a general RAG query on project data"""
    # Verify project exists
    db_project = crud.project.get(query.project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # This would use the retrieval service to get results
    # For now, return a placeholder response
    return {
        "results": [],
        "answer": "This feature is not fully implemented yet."
    }