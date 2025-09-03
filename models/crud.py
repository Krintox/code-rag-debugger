from typing import Type, TypeVar, List, Optional, Dict, Any
from models.database import get_db
from supabase import Client
import logging
from datetime import datetime  # needed for update_subscription
from services.auth_service import auth_service  # uncomment and adjust based on your project
from models.enums import SubscriptionPlan  # uncomment if you have SubscriptionPlan enum

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType")


class CRUDBase:
    def __init__(self, table_name: str):
        self.table_name = table_name

    def get(self, id: int) -> Optional[Dict[str, Any]]:
        try:
            supabase = get_db()
            result = supabase.table(self.table_name).select("*").eq("id", id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting record from {self.table_name}: {e}")
            return None

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            supabase = get_db()
            result = supabase.table(self.table_name).select("*").range(skip, skip + limit - 1).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting multiple records from {self.table_name}: {e}")
            return []

    def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            supabase = get_db()
            result = supabase.table(self.table_name).insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating record in {self.table_name}: {e}")
            return None

    def update(self, id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            supabase = get_db()
            result = supabase.table(self.table_name).update(data).eq("id", id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating record in {self.table_name}: {e}")
            return None

    def remove(self, id: int) -> Optional[Dict[str, Any]]:
        try:
            supabase = get_db()
            result = supabase.table(self.table_name).delete().eq("id", id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error deleting record from {self.table_name}: {e}")
            return None


class CRUDProject(CRUDBase):
    def __init__(self):
        super().__init__("projects")

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        try:
            supabase = get_db()
            result = supabase.table("projects").select("*").eq("name", name).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting project by name: {e}")
            return None


class CRUDCommit(CRUDBase):
    def __init__(self):
        super().__init__("commits")

    def get_by_hash(self, hash: str, project_id: int) -> Optional[Dict[str, Any]]:
        try:
            supabase = get_db()
            result = supabase.table("commits").select("*").eq("hash", hash).eq("project_id", project_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting commit by hash: {e}")
            return None

    def get_by_project(self, project_id: int, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        try:
            supabase = get_db()
            result = supabase.table("commits").select("*").eq("project_id", project_id).range(skip, skip + limit - 1).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting commits by project: {e}")
            return []

    def create_commit(self, commit_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            supabase = get_db()
            result = supabase.table("commits").insert(commit_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating commit: {e}")
            return None


class CRUDFeedback(CRUDBase):
    def __init__(self):
        super().__init__("feedback")

    def get_by_debug_query(self, debug_query_id: int) -> List[Dict[str, Any]]:
        try:
            supabase = get_db()
            result = supabase.table("feedback").select("*").eq("debug_query_id", debug_query_id).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting feedback by debug query: {e}")
            return []


class CRUDSymbol(CRUDBase):
    def __init__(self):
        super().__init__("symbols")

    def get_by_file_and_line(self, project_id: int, file_path: str, start_line: int, end_line: int = None) -> List[Dict[str, Any]]:
        """Get symbols by file and line range"""
        try:
            supabase = get_db()
            query = supabase.table("symbols").select("*").eq("project_id", project_id).eq("file_path", file_path)

            if end_line:
                query = query.gte("start_line", start_line).lte("end_line", end_line)
            else:
                query = query.eq("start_line", start_line)

            result = query.execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting symbols by file and line: {e}")
            return []

    def get_by_unique(self, project_id: int, file_path: str, symbol_name: str, start_line: int) -> Optional[Dict[str, Any]]:
        """Get symbol by unique combination"""
        try:
            supabase = get_db()
            result = supabase.table("symbols").select("*").eq("project_id", project_id).eq("file_path", file_path).eq("symbol_name", symbol_name).eq("start_line", start_line).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting symbol by unique: {e}")
            return None

    def get_by_project(self, project_id: int, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get symbols by project"""
        try:
            supabase = get_db()
            result = supabase.table("symbols").select("*").eq("project_id", project_id).range(skip, skip + limit - 1).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting symbols by project: {e}")
            return []


class CRUDSymbolChunk(CRUDBase):
    def __init__(self):
        super().__init__("symbol_chunks")

    def get_by_symbol(self, symbol_id: int) -> List[Dict[str, Any]]:
        """Get chunks by symbol ID"""
        try:
            supabase = get_db()
            result = supabase.table("symbol_chunks").select("*").eq("symbol_id", symbol_id).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting symbol chunks: {e}")
            return []


class CRUDReference(CRUDBase):
    def __init__(self):
        super().__init__("references")

    def get_by_symbol(self, symbol_id: int) -> List[Dict[str, Any]]:
        """Get references by symbol ID"""
        try:
            supabase = get_db()
            result = supabase.table("references").select("*").eq("from_symbol_id", symbol_id).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting references by symbol: {e}")
            return []

    def get_to_symbol(self, symbol_id: int) -> List[Dict[str, Any]]:
        """Get references pointing to symbol ID"""
        try:
            supabase = get_db()
            result = supabase.table("references").select("*").eq("to_symbol_id", symbol_id).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting references to symbol: {e}")
            return []


class CRUDSymbolEmbedding(CRUDBase):
    def __init__(self):
        super().__init__("symbol_embeddings_metadata")

    def get_by_symbol(self, symbol_id: int) -> List[Dict[str, Any]]:
        """Get embeddings by symbol ID"""
        try:
            supabase = get_db()
            result = supabase.table("symbol_embeddings_metadata").select("*").eq("symbol_id", symbol_id).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting symbol embeddings: {e}")
            return []


class CRUDIndexingJob(CRUDBase):
    def __init__(self):
        super().__init__("indexing_jobs")

    def get_by_project(self, project_id: int) -> List[Dict[str, Any]]:
        """Get indexing jobs by project"""
        try:
            supabase = get_db()
            result = supabase.table("indexing_jobs").select("*").eq("project_id", project_id).order("created_at", desc=True).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting indexing jobs: {e}")
            return []


class CRUDUser(CRUDBase):
    def __init__(self):
        super().__init__("users")

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            supabase = get_db()
            result = supabase.table("users").select("*").eq("email", email).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None

    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        try:
            supabase = get_db()
            result = supabase.table("users").select("*").eq("username", username).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None

    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            # Hash password
            if 'password' in user_data:
                user_data['hashed_password'] = auth_service.get_password_hash(user_data.pop('password'))

            supabase = get_db()
            result = supabase.table("users").insert(user_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            # Don't allow updating sensitive fields directly
            user_data.pop('hashed_password', None)
            user_data.pop('role', None)
            user_data.pop('subscription_plan', None)

            supabase = get_db()
            result = supabase.table("users").update(user_data).eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return None

    def update_subscription(self, user_id: int, plan: "SubscriptionPlan", expires_at: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        try:
            update_data = {"subscription_plan": plan}
            if expires_at:
                update_data["subscription_expires_at"] = expires_at

            supabase = get_db()
            result = supabase.table("users").update(update_data).eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error updating subscription: {e}")
            return None


class CRUDNotification(CRUDBase):
    def __init__(self):
        super().__init__("notifications")

    def get_user_notifications(self, user_id: int, skip: int = 0, limit: int = 100, unread_only: bool = False) -> List[Dict[str, Any]]:
        try:
            supabase = get_db()
            query = supabase.table("notifications").select("*").eq("user_id", user_id)

            if unread_only:
                query = query.eq("read", False)

            result = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
            return result.data
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []

    def mark_as_read(self, notification_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            supabase = get_db()
            result = supabase.table("notifications").update({"read": True}).eq("id", notification_id).eq("user_id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return None

    def mark_all_as_read(self, user_id: int) -> bool:
        try:
            supabase = get_db()
            supabase.table("notifications").update({"read": True}).eq("user_id", user_id).eq("read", False).execute()
            return True
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            return False


# CRUD instances
user = CRUDUser()
notification = CRUDNotification()
symbol = CRUDSymbol()
symbol_chunk = CRUDSymbolChunk()
reference = CRUDReference()
symbol_embedding = CRUDSymbolEmbedding()
indexing_job = CRUDIndexingJob()
project = CRUDProject()
commit = CRUDCommit()
feedback = CRUDFeedback()
