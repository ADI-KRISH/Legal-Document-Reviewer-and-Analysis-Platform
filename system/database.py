from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import os
from dotenv import load_dotenv

load_dotenv()

# Check for DATABASE_URL in environment or default to a local SQLite for now (change to Postgres later)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local_dev.db")

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class ProcessingStatus(enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    upload_path = Column(String)
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.UPLOADED)
    created_at = Column(DateTime, default=datetime.utcnow)
    page_count = Column(Integer, default=0)
    summary = Column(Text, nullable=True)
    
    # Relationships to other tables (to be added)
    # extracted_clauses = relationship("ExtractedClause", back_populates="contract")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
