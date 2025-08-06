"""
FastAPI backend application for llms.txt-gen
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import redis
import uvicorn

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(
    title="llms.txt-gen API",
    description="API for llms.txt generation service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/llms_txt_gen")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis setup
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL)

# Database model
Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pydantic model
class DocumentCreate(BaseModel):
    title: str
    content: str
    source_url: str = None

class DocumentResponse(BaseModel):
    id: int
    title: str
    content: str
    source_url: str = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Create tables
Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "llms.txt-gen API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        # Check Redis
        redis_client.ping()
        
        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

@app.post("/documents/", response_model=DocumentResponse)
async def create_document(document: DocumentCreate):
    """Create a new document"""
    db = SessionLocal()
    try:
        db_document = Document(**document.dict())
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        return db_document
    finally:
        db.close()

@app.get("/documents/", response_model=list[DocumentResponse])
async def get_documents():
    """Get all documents"""
    db = SessionLocal()
    try:
        documents = db.query(Document).all()
        return documents
    finally:
        db.close()

@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int):
    """Get a specific document"""
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8001)),
        reload=os.getenv("RELOAD", "True").lower() == "true"
    )