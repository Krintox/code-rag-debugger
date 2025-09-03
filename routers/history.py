from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from models import schemas, crud
from services.auth_service import get_current_active_user  # <-- your authentication dependency

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/commits/{commit_hash}", response_model=schemas.Commit)
def read_commit(
    commit_hash: str,
    project_id: int,
    current_user: schemas.User = Depends(get_current_active_user)  # <-- auth here
):
    """Get a specific commit"""
    commit = crud.commit.get_by_hash(hash=commit_hash, project_id=project_id)
    if commit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commit not found"
        )
    return commit


@router.post("/feedback", response_model=schemas.Feedback)
def create_feedback(
    feedback: schemas.FeedbackCreate,
    current_user: schemas.User = Depends(get_current_active_user)  # <-- auth here
):
    """Submit feedback on a debug response"""
    db_feedback = crud.feedback.create(feedback.model_dump())
    return db_feedback


@router.get("/feedback/{debug_query_id}", response_model=List[schemas.Feedback])
def read_feedback(
    debug_query_id: int,
    current_user: schemas.User = Depends(get_current_active_user)  # <-- auth here
):
    """Get feedback for a specific debug query"""
    feedback = crud.feedback.get_by_debug_query(debug_query_id=debug_query_id)
    return feedback
