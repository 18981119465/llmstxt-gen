"""
FastAPI backend application for llms.txt-gen
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Optional, List, Sequence
from datetime import datetime
import redis
import uvicorn

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Import and register services
from src.services import DocumentProcessingService, get_service_factory, create_service
from src.config.routes import router as config_router
from src.config.web import router as config_web_router
from src.config.management import init_config_system, shutdown_config_system

# Initialize configuration system
try:
    config_manager = init_config_system()
    print("Configuration system initialized successfully")
except Exception as e:
    print(f"Failed to initialize configuration system: {e}")
    # Continue without config system for now

# Register services with the factory
service_factory = get_service_factory()
service_factory.register_service('document_processor', DocumentProcessingService)

app = FastAPI(
    title="llms.txt-gen API",
    description="API for llms.txt generation service",
    version="1.0.0",
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
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:password@localhost:5432/llms_txt_gen"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis setup
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL)

# Database model
Base = declarative_base()


class Document(Base):  # type: ignore
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
    source_url: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    title: str
    content: str
    source_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Create tables
Base.metadata.create_all(bind=engine)


@app.get("/")
async def root() -> dict:
    return {"message": "llms.txt-gen API is running", "version": "1.0.0"}


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint"""
    try:
        # Check database
        db = SessionLocal()
        from sqlalchemy import text

        db.execute(text("SELECT 1"))
        db.close()

        # Check Redis
        redis_client.ping()

        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected",
            "timestamp": datetime.utcnow(),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "timestamp": datetime.utcnow()}


@app.post("/documents/", response_model=DocumentResponse)
async def create_document(document: DocumentCreate) -> DocumentResponse:
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
async def get_documents() -> List[DocumentResponse]:
    """Get all documents"""
    db = SessionLocal()
    try:
        documents = db.query(Document).all()
        return [DocumentResponse.model_validate(doc.__dict__) for doc in documents]
    finally:
        db.close()


@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int) -> DocumentResponse:
    """Get a specific document"""
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    finally:
        db.close()


@app.get("/service/status")
async def get_service_status():
    """Get the status of configured services"""
    global document_service
    if document_service:
        try:
            status = await document_service.get_service_status()
            return status
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get service status: {str(e)}")
    else:
        return {"service_name": "DocumentProcessingService", "status": "not_initialized"}


@app.post("/documents/{document_id}/process")
async def process_document(document_id: int):
    """Process a document using the configured service"""
    global document_service
    if not document_service:
        raise HTTPException(status_code=503, detail="Document processing service not available")
    
    db = SessionLocal()
    try:
        # Get document from database
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Process document using configured service
        result = await document_service.process_document(document_id, document.content)
        
        return {
            "document_id": document_id,
            "processing_result": result,
            "message": "Document processed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")
    finally:
        db.close()



# Initialize document processing service
document_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global document_service
    try:
        document_service = await create_service('document_processor')
        print("Document processing service initialized successfully")
    except Exception as e:
        print(f"Failed to initialize document processing service: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown"""
    global document_service
    if document_service:
        try:
            await document_service.stop()
            print("Document processing service stopped successfully")
        except Exception as e:
            print(f"Failed to stop document processing service: {e}")
    
    # Shutdown configuration system
    try:
        shutdown_config_system()
        print("Configuration system shutdown successfully")
    except Exception as e:
        print(f"Failed to shutdown configuration system: {e}")

# Include configuration routes
app.include_router(config_router, prefix="/api/v1/config", tags=["Configuration Management"])
app.include_router(config_web_router, prefix="/config", tags=["Configuration Web Interface"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("RELOAD", "True").lower() == "true",
    )
