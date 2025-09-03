# File: routers/debug.py
from fastapi import APIRouter, Depends, HTTPException, status
from models.database import get_db
from models import schemas, crud
from services.rag_service import rag_service
from services.auth_service import get_current_active_user  # <-- import the right one
from models.user import UserInDB  # use your DB model, not schemas.User

router = APIRouter(prefix="/debug", tags=["debug"])


@router.post("/", response_model=schemas.DebugResponse)
def debug_code(
    query: schemas.DebugQuery,
    current_user: UserInDB = Depends(get_current_active_user),  # <-- fixed
    db=Depends(get_db)
):
    """Debug a code error using RAG"""
    # Verify project exists & belongs to current user
    db_project = crud.project.get(query.project_id)
    if db_project is None or db_project["owner_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    # Generate debug response using RAG
    result = rag_service.generate_debug_response(
        query.project_id,
        query.error_message,
        query.code_snippet,
        query.file_path,
        query.additional_context,
        query.use_reference_pack
    )

    return result


@router.post("/rag", response_model=schemas.RAGResponse)
def rag_query(
    query: schemas.RAGQuery,
    current_user: UserInDB = Depends(get_current_active_user),  # <-- fixed
    db=Depends(get_db)
):
    """Perform a general RAG query on project data"""
    # Verify project exists & belongs to current user
    db_project = crud.project.get(query.project_id)
    if db_project is None or db_project["owner_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    # Placeholder response
    return {
        "results": [],
        "answer": "This feature is not fully implemented yet."
    }
