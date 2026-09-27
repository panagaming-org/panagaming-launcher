from storage.data.database import Base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

class InstanceModel(Base):
    __tablename__ = "instances"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    minecraft_version = Column(String, nullable=False)
    loader_type = Column(String, nullable=False)  # "vanilla", "forge", "fabric"
    loader_version = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    