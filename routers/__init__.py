from .projects import router as projects_router
from .debug import router as debug_router
from .history import router as history_router

__all__ = [
    "projects_router",
    "debug_router", 
    "history_router"
]