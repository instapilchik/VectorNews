from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base

class AgentSettings(Base):
    __tablename__ = "agent_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    settings = Column(JSONB, nullable=False)
