# File: routers/references.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
import logging

from models import schemas, crud
from models.user import User
from workers.reference_indexer import reference_indexer
from services.reference_service import reference_service
from services.auth_service import get_current_active_user

router = APIRouter(prefix="/references", tags=["references"])
logger = logging.getLogger(__name__)

@router.post("/projects/{project_id}/index")
async def index_project_references(
    project_id: int, 
    background_tasks: BackgroundTasks,
    force_full_reindex: bool = False,
    current_user: User = Depends(get_current_active_user)
):
    """Trigger reference indexing for a project"""
    db_project = crud.project.get(project_id)
    if db_project is None or db_project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    
    # Run indexing in background
    background_tasks.add_task(
        reference_indexer.index_project_symbols,
        project_id,
        None,
        None,
        force_full_reindex
    )
    
    return {"message": "Reference indexing started in background"}

@router.get("/projects/{project_id}/symbols", response_model=List[schemas.Symbol])
def get_project_symbols(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    symbol_type: Optional[str] = None,
    file_path: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get symbols for a project with optional filtering"""
    db_project = crud.project.get(project_id)
    if db_project is None or db_project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    
    symbols = crud.symbol.get_by_project(project_id, skip, limit)
    
    # Apply filters
    if symbol_type:
        symbols = [s for s in symbols if s['symbol_type'] == symbol_type]
    if file_path:
        symbols = [s for s in symbols if s['file_path'] == file_path]
    
    return symbols

@router.get("/symbols/{symbol_id}/references", response_model=List[schemas.Reference])
def get_symbol_references(
    symbol_id: int,
    max_depth: int = 1,
    max_references: int = 50,
    current_user: User = Depends(get_current_active_user)
):
    """Get references for a specific symbol"""
    symbol = crud.symbol.get(symbol_id)
    if symbol is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symbol not found"
        )
    
    # Ensure user has access to the project the symbol belongs to
    db_project = crud.project.get(symbol["project_id"])
    if db_project is None or db_project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    references = reference_service.get_symbol_references(symbol_id, max_depth, max_references)
    return references

@router.post("/debug/reference-pack", response_model=schemas.ReferencePack)
def get_debug_reference_pack(
    request: schemas.DebugReferenceRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Get a reference pack for debugging"""
    # Ensure user has access to the project
    db_project = crud.project.get(request.project_id)
    if db_project is None or db_project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )

    try:
        # Resolve snippet to symbol
        symbol_id = reference_service.resolve_snippet_to_symbol(
            request.project_id,
            request.file_path,
            request.error_snippet,
            (request.start_line, request.end_line) if request.start_line and request.end_line else None
        )
        
        if not symbol_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Could not resolve symbol from the provided snippet"
            )
        
        # Build reference pack
        reference_pack = reference_service.build_reference_pack(
            symbol_id,
            request.token_budget,
            request.ranking_params
        )
        
        return reference_pack
        
    except Exception as e:
        logger.error(f"Failed to build reference pack: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build reference pack: {str(e)}"
        )

@router.get("/projects/{project_id}/indexing-jobs", response_model=List[schemas.IndexingJob])
def get_indexing_jobs(
    project_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Get indexing jobs for a project"""
    db_project = crud.project.get(project_id)
    if db_project is None or db_project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or access denied"
        )
    
    jobs = crud.indexing_job.get_by_project(project_id)
    return jobs
