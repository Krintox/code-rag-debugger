from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models.database import get_db
from models import schemas
from models import crud
from services.git_service import git_service
from services.embedding_service import embedding_service

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project and clone its repository"""
    # Check if project already exists
    db_project = crud.project.get_by_name(db, name=project.name)
    if db_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project with this name already exists"
        )
    
    # Clone or update the repository
    try:
        repo_path = git_service.clone_or_update_repo(project.git_url, project.name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to clone repository: {str(e)}"
        )
    
    # Get commit history
    try:
        commits = git_service.get_commit_history(repo_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get commit history: {str(e)}"
        )
    
    # Create project in database
    db_project = crud.project.create(db, obj_in=project)
    
    # Add commits to database
    for commit_data in commits:
        commit_create = schemas.CommitCreate(
            **commit_data,
            project_id=db_project.id
        )
        crud.commit.create(db, obj_in=commit_create)
    
    # Index commits in vector database
    try:
        embedding_service.index_commit_history(db_project.id, commits)
    except Exception as e:
        # Don't fail the request if indexing fails, just log it
        print(f"Failed to index commits: {e}")
    
    return db_project

@router.get("/", response_model=List[schemas.Project])
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all projects"""
    projects = crud.project.get_multi(db, skip=skip, limit=limit)
    return projects

@router.get("/{project_id}", response_model=schemas.Project)
def read_project(project_id: int, db: Session = Depends(get_db)):
    """Get a specific project"""
    db_project = crud.project.get(db, id=project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return db_project

@router.get("/{project_id}/commits", response_model=List[schemas.Commit])
def read_project_commits(project_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get commits for a specific project"""
    # Verify project exists
    db_project = crud.project.get(db, id=project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    commits = crud.commit.get_by_project(db, project_id=project_id, skip=skip, limit=limit)
    return commits

@router.post("/{project_id}/refresh")
def refresh_project(project_id: int, db: Session = Depends(get_db)):
    """Refresh a project's data from git"""
    db_project = crud.project.get(db, id=project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update the repository
    try:
        repo_path = git_service.clone_or_update_repo(db_project.git_url, db_project.name)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update repository: {str(e)}"
        )
    
    # Get updated commit history
    try:
        commits = git_service.get_commit_history(repo_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get commit history: {str(e)}"
        )
    
    # Update commits in database (simplified - in production, you'd need to handle updates)
    # For now, we'll just reindex
    
    # Reindex commits in vector database
    try:
        embedding_service.index_commit_history(db_project.id, commits)
        return {"message": "Project refreshed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to refresh project: {str(e)}"
        )