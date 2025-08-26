from sqlalchemy.orm import Session
from .database import Base
from typing import Type, TypeVar, List, Optional
import models  # Import models directly

ModelType = TypeVar("ModelType", bound=Base)

class CRUDBase:
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in) -> ModelType:
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: ModelType, obj_in) -> ModelType:
        obj_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            setattr(db_obj, field, obj_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, id: int) -> ModelType:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj

class CRUDProject(CRUDBase):
    def __init__(self):
        super().__init__(models.Project)

    def get_by_name(self, db: Session, name: str) -> Optional[models.Project]:
        return db.query(models.Project).filter(models.Project.name == name).first()

class CRUDCommit(CRUDBase):
    def __init__(self):
        super().__init__(models.Commit)

    def get_by_hash(self, db: Session, hash: str, project_id: int) -> Optional[models.Commit]:
        return db.query(models.Commit).filter(
            models.Commit.hash == hash, 
            models.Commit.project_id == project_id
        ).first()

    def get_by_project(self, db: Session, project_id: int, skip: int = 0, limit: int = 100) -> List[models.Commit]:
        return db.query(models.Commit).filter(
            models.Commit.project_id == project_id
        ).offset(skip).limit(limit).all()

    def create_commit(self, db: Session, commit_data: dict) -> models.Commit:
        """Create a commit with proper data handling"""
        db_commit = models.Commit(
            hash=commit_data["hash"],
            author=commit_data["author"],
            message=commit_data["message"],
            timestamp=commit_data["timestamp"],
            files_changed=commit_data["files_changed"],  # This should be a list
            project_id=commit_data["project_id"]
        )
        db.add(db_commit)
        db.commit()
        db.refresh(db_commit)
        return db_commit

class CRUDFeedback(CRUDBase):
    def __init__(self):
        super().__init__(models.Feedback)

    def get_by_debug_query(self, db: Session, debug_query_id: int) -> List[models.Feedback]:
        return db.query(models.Feedback).filter(
            models.Feedback.debug_query_id == debug_query_id
        ).all()

project = CRUDProject()
commit = CRUDCommit()
feedback = CRUDFeedback()