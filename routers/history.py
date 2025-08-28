from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from models import schemas
from models import crud

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/commits/{commit_hash}", response_model=schemas.Commit)
def read_commit(commit_hash: str, project_id: int):
    """Get a specific commit"""
    commit = crud.commit.get_by_hash(hash=commit_hash, project_id=project_id)
    if commit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commit not found"
        )
    return commit

@router.post("/feedback", response_model=schemas.Feedback)
def create_feedback(feedback: schemas.FeedbackCreate):
    """Submit feedback on a debug response"""
    db_feedback = crud.feedback.create(feedback.model_dump())
    return db_feedback

@router.get("/feedback/{debug_query_id}", response_model=List[schemas.Feedback])
def read_feedback(debug_query_id: int):
    """Get feedback for a specific debug query"""
    feedback = crud.feedback.get_by_debug_query(debug_query_id=debug_query_id)
    return feedback