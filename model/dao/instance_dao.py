from model.entity.instance import InstanceModel
from sqlalchemy.orm import Session
from storage.data.database import SessionLocal

class InstanceDAO:

    @staticmethod
    def get_all():
        db = SessionLocal()
        instances = db.query(InstanceModel).all()
        db.close()
        return instances

    @staticmethod
    def get_by_name(name: str) -> list:
        db = SessionLocal()
        instance = db.query(InstanceModel).filter(InstanceModel.name == name).first()
        return instance

    @staticmethod
    def create_instance(db: Session, name: str, minecraft_version: str, loader_type: str, loader_version: str = None):
        db_instance = InstanceModel(
            name=name,
            minecraft_version=minecraft_version,
            loader_type=loader_type,
            loader_version=loader_version
        )
        db.add(db_instance)
        db.commit()
        db.refresh(db_instance)

    @staticmethod
    def delete_instance(name: str) -> bool:
        db = SessionLocal()
        instance = db.query(InstanceModel).filter(InstanceModel.name == name).first()
        if instance:
            db.delete(instance)
            db.commit()
            db.close()
            return True
        db.close()
        return False

    @staticmethod
    def get_selected_instance() -> InstanceModel:
        db = SessionLocal()
        selected_instance = db.query(InstanceModel).filter(InstanceModel.selected == True).first()
        db.close()
        return selected_instance