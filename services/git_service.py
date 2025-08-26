import git
import os
from typing import List, Dict, Any
from datetime import datetime
from config import settings
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class GitService:
    def __init__(self):
        self.repo_base_path = Path(settings.REPOSITORY_BASE_PATH)
        self.repo_base_path.mkdir(exist_ok=True)

    def clone_or_update_repo(self, git_url: str, project_name: str) -> str:
        """Clone or update a git repository"""
        repo_path = self.repo_base_path / project_name
        
        try:
            if repo_path.exists():
                # Update existing repository
                repo = git.Repo(repo_path)
                origin = repo.remotes.origin
                origin.pull()
                logger.info(f"Updated repository: {project_name}")
            else:
                # Clone new repository
                repo = git.Repo.clone_from(git_url, repo_path)
                logger.info(f"Cloned repository: {project_name}")
                
            return str(repo_path)
        except git.exc.GitCommandError as e:
            logger.error(f"Git operation failed for {project_name}: {e}")
            raise Exception(f"Failed to clone or update repository: {e}")

    def get_commit_history(self, repo_path: str, max_commits: int = None) -> List[Dict[str, Any]]:
        """Get commit history from a repository"""
        if max_commits is None:
            max_commits = settings.MAX_COMMIT_HISTORY
            
        try:
            repo = git.Repo(repo_path)
            commits = []
            
            for commit in repo.iter_commits(max_count=max_commits):
                # Get files changed in this commit as a proper list
                files_changed = []
                try:
                    # Get the diff for this commit and extract file paths
                    if commit.parents:
                        # Compare with parent commit
                        parent = commit.parents[0]
                        diff = parent.diff(commit)
                        files_changed = [d.a_path for d in diff if d.a_path]
                    else:
                        # Initial commit - get all files in the tree
                        files_changed = [item.path for item in commit.tree.traverse() if isinstance(item, git.Blob)]
                except (IndexError, AttributeError, Exception) as e:
                    logger.warning(f"Could not get files changed for commit {commit.hexsha}: {e}")
                    # Fallback: try to get files from stats
                    try:
                        files_changed = list(commit.stats.files.keys())
                    except:
                        files_changed = []
                
                commits.append({
                    "hash": commit.hexsha,
                    "author": str(commit.author),
                    "message": commit.message.strip(),
                    "timestamp": datetime.fromtimestamp(commit.committed_date),
                    "files_changed": files_changed  # This should be a list, not a string
                })
                
            return commits
        except git.exc.InvalidGitRepositoryError:
            logger.error(f"Invalid git repository: {repo_path}")
            raise Exception(f"Path is not a valid git repository: {repo_path}")

    def get_file_content(self, repo_path: str, file_path: str, commit_hash: str = None) -> str:
        """Get content of a file at a specific commit"""
        try:
            repo = git.Repo(repo_path)
            
            if commit_hash:
                # Get file content at specific commit
                commit = repo.commit(commit_hash)
                return commit.tree[file_path].data_stream.read().decode('utf-8')
            else:
                # Get current file content
                file_path_obj = Path(repo_path) / file_path
                with open(file_path_obj, 'r', encoding='utf-8') as f:
                    return f.read()
                    
        except (KeyError, FileNotFoundError):
            logger.error(f"File not found: {file_path} at commit {commit_hash}")
            raise Exception(f"File not found: {file_path}")
        except git.exc.BadName:
            logger.error(f"Invalid commit hash: {commit_hash}")
            raise Exception(f"Invalid commit hash: {commit_hash}")

    def get_diff(self, repo_path: str, commit_hash: str) -> str:
        """Get the diff for a specific commit"""
        try:
            repo = git.Repo(repo_path)
            commit = repo.commit(commit_hash)
            
            if commit.parents:
                # Compare with parent commit
                parent = commit.parents[0]
                return repo.git.diff(parent.hexsha, commit.hexsha)
            else:
                # Initial commit - show all files
                return repo.git.show(commit.hexsha)
                
        except git.exc.BadName:
            logger.error(f"Invalid commit hash: {commit_hash}")
            raise Exception(f"Invalid commit hash: {commit_hash}")

git_service = GitService()