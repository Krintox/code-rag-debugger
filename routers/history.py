from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models.database import get_db
from models import schemas
from models import crud

router = APIRouter(prefix="/history", tags=["history"])

@router.get("/commits/{commit_hash}", response_model=schemas.Commit)
def read_commit(commit_hash: str, project_id: int, db: Session = Depends(get_db)):
    """Get a specific commit"""
    commit = crud.commit.get_by_hash(db, hash=commit_hash, project_id=project_id)
    if commit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commit not found"
        )
    return commit

@router.post("/feedback", response_model=schemas.Feedback)
def create_feedback(feedback: schemas.FeedbackCreate, db: Session = Depends(get_db)):
    """Submit feedback on a debug response"""
    # In a real implementation, you would validate that the debug_query_id exists
    db_feedback = crud.feedback.create(db, obj_in=feedback)
    return db_feedback

@router.get("/feedback/{debug_query_id}", response_model=List[schemas.Feedback])
def read_feedback(debug_query_id: int, db: Session = Depends(get_db)):
    """Get feedback for a specific debug query"""
    feedback = crud.feedback.get_by_debug_query(db, debug_query_id=debug_query_id)
    return feedback