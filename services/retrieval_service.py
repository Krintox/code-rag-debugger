from typing import List, Dict, Any
from .embedding_service import embedding_service
from .git_service import git_service
import logging

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self):
        pass

    def retrieve_similar_errors(self, project_id: int, error_message: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve similar errors from the project's history"""
        try:
            # Query the commit collection for similar errors
            collection_name = f"project_{project_id}_commits"
            results = embedding_service.query_collection(
                collection_name, 
                error_message, 
                n_results
            )
            
            # Filter for commits that might contain error fixes
            error_commits = []
            for result in results:
                if any(keyword in result["content"].lower() for keyword in ["fix", "error", "bug", "issue"]):
                    error_commits.append({
                        "commit": result["metadata"],
                        "similarity": 1 - result["distance"],  # Convert distance to similarity
                        "content": result["content"]
                    })
            
            return error_commits
            
        except Exception as e:
            logger.error(f"Failed to retrieve similar errors: {e}")
            return []

    def retrieve_relevant_documentation(self, project_id: int, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Retrieve relevant documentation for a query"""
        # This would query a documentation collection
        # For now, return empty list as placeholder
        return []

    def get_commit_context(self, project_id: int, commit_hash: str) -> Dict[str, Any]:
        """Get detailed context for a specific commit"""
        try:
            # Get project to find repo path
            # This would require database access which we'll handle in the router
            # For now, return basic info
            return {
                "hash": commit_hash,
                "details": f"Commit {commit_hash} details would be retrieved here"
            }
        except Exception as e:
            logger.error(f"Failed to get commit context: {e}")
            return {}

    def get_code_suggestions(self, project_id: int, error_message: str, code_snippet: str = None) -> List[str]:
        """Get code suggestions based on error and context"""
        # This would use more advanced retrieval and potentially pattern matching
        # For now, return placeholder
        return [
            "Check for null references in your code",
            "Verify input parameters are valid",
            "Ensure all resources are properly disposed"
        ]

retrieval_service = RetrievalService()