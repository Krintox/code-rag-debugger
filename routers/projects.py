from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List
import logging

from models import schemas
from models import crud
from services.git_service import git_service
from services.embedding_service import embedding_service
from models.database import get_db

router = APIRouter(prefix="/projects", tags=["projects"])
logger = logging.getLogger(__name__)

# --- CORS Preflight Handlers ---
@router.options("/")
async def options_projects():
    return Response(headers={
        "Access-Control-Allow-Origin": "http://localhost:3000",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    })

@router.options("/{project_id}")
async def options_project(project_id: int):
    return Response(headers={
        "Access-Control-Allow-Origin": "http://localhost:3000",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    })

@router.options("/{project_id}/refresh")
async def options_refresh(project_id: int):
    return Response(headers={
        "Access-Control-Allow-Origin": "http://localhost:3000",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    })

@router.options("/{project_id}/commits")
async def options_commits(project_id: int):
    return Response(headers={
        "Access-Control-Allow-Origin": "http://localhost:3000",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    })

# --- Existing Endpoints ---
@router.post("/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate):
    """Create a new project and clone its repository"""
    try:
        # Test database connection first
        get_db()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )
    
    # Check if project already exists
    db_project = crud.project.get_by_name(name=project.name)
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
    project_data = project.model_dump()
    db_project = crud.project.create(project_data)
    
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project in database"
        )
    
    # Add commits to database
    successful_commits = 0
    for commit_data in commits:
        if isinstance(commit_data["files_changed"], str):
            try:
                if commit_data["files_changed"].startswith('{') and commit_data["files_changed"].endswith('}'):
                    files_str = commit_data["files_changed"][1:-1]
                    commit_data["files_changed"] = [f.strip() for f in files_str.split(',') if f.strip()]
                else:
                    commit_data["files_changed"] = [commit_data["files_changed"]]
            except:
                commit_data["files_changed"] = []
        
        commit_data["project_id"] = db_project["id"]
        result = crud.commit.create_commit(commit_data)
        if result:
            successful_commits += 1
    
    logger.info(f"Created project with {successful_commits}/{len(commits)} commits")
    
    # Index commits in vector database
    try:
        embedding_service.index_commit_history(db_project["id"], commits)
    except Exception as e:
        logger.error(f"Failed to index commits: {e}")
    
    return db_project

@router.get("/", response_model=List[schemas.Project])
def read_projects(skip: int = 0, limit: int = 100):
    """Get all projects"""
    projects = crud.project.get_multi(skip=skip, limit=limit)
    return projects

@router.get("/{project_id}", response_model=schemas.Project)
def read_project(project_id: int):
    """Get a specific project"""
    db_project = crud.project.get(project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return db_project

@router.get("/{project_id}/commits", response_model=List[schemas.Commit])
def read_project_commits(project_id: int, skip: int = 0, limit: int = 100):
    """Get commits for a specific project"""
    db_project = crud.project.get(project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    commits = crud.commit.get_by_project(project_id=project_id, skip=skip, limit=limit)
    return commits

@router.post("/{project_id}/refresh")
def refresh_project(project_id: int):
    """Refresh a project's data from git"""
    db_project = crud.project.get(project_id)
    if db_project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    try:
        repo_path = git_service.clone_or_update_repo(db_project["git_url"], db_project["name"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update repository: {str(e)}"
        )
    
    try:
        commits = git_service.get_commit_history(repo_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get commit history: {str(e)}"
        )
    
    try:
        embedding_service.index_commit_history(db_project["id"], commits)
        return {"message": "Project refreshed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to refresh project: {str(e)}"
        )
