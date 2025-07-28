import os
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from datetime import datetime
from backend.core.databases import DatabaseConn
from backend.core.pdf_processor import PDFProcessor
from backend.core.rag_pipeline import RAGPipeline
from backend.api.config import Settings
from contextlib import asynccontextmanager
import asyncio
# from fastapi_limiter import FastAPILimiter
# from fastapi_limiter import RateLimiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting DocMind AI API...")
    try:
        db.initialize_schema()  # Fixed method name
        logger.info("✅ Database initialized")
        
        # Test RAG pipeline
        rag_health = rag_pipeline.health_check()
        if rag_health.get("rag_pipeline") == "healthy":
            logger.info("✅ RAG Pipeline ready")
        else:
            logger.warning("⚠️ RAG Pipeline health check failed")
        
        logger.info("🎉 DocMind AI API is ready!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield  # Server is running
    
    # Shutdown
    logger.info("🛑 Shutting down DocMind AI API...")
    try:
        # Close database connections
        if hasattr(db, 'close'):
            db.close()
        logger.info("✅ Cleanup completed")
        
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

app = FastAPI(
    title="DocMind - AI Powered Research Paper Analyzer",
    description="API for processing and analyzing research papers using RAG",
    version="1.0.0",
    docs_url="/docs",            # Explicitly enable Swagger UI
    redoc_url="/redoc",           # Optional: enable Redoc docs too
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # React dev server
        "http://localhost:5173",      # Vite dev server
        "http://localhost:8080",      # Your frontend port from vite.config.ts
        "http://127.0.0.1:8080",      # Alternative localhost
        "https://your-frontend-domain.com"  # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = Settings()
db = DatabaseConn()
pdf_processor = PDFProcessor()
rag_pipeline = RAGPipeline()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    question: str = Field(..., description="Question about documents")
    document_id: Optional[int] = Field(None, description="Specific document ID")
    conversation_history: Optional[List[Dict[str, str]]] = Field(None, description="Previous conversation")

class ChatResponse(BaseModel):
    success: bool
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class DocumentSummaryResponse(BaseModel):
    success: bool
    document_id: int
    document_title: str
    summary: str
    key_points: List[str]
    metadata: Dict[str, Any]

class QuestionSuggestionsResponse(BaseModel):
    success: bool
    document_id: int
    document_title: str
    questions: List[str]
    metadata: Dict[str, Any]

class DocumentListResponse(BaseModel):
    success: bool
    documents: List[Dict[str, Any]]
    total_count: int

class HealthCheckResponse(BaseModel):
    status: str
    components: Dict[str, Any]
    timestamp: str

def get_database():
    return db

def get_pdf_processor():
    return pdf_processor

def get_rag_pipeline():
    return rag_pipeline



@app.get("/")
async def read_root():
    return {
        "status": "ok",
        "message": "Welcome to DocMind AI API!",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "upload": "/upload-pdf",
            "documents": "/documents",
            "chat": "/chat",
            "summarize": "/documents/{document_id}/summarize",
            "questions": "/documents/{document_id}/questions"
        }
    }

@app.get("/health")
async def health_check():
    try:
        db_health = db.health_check()
        processor_health = pdf_processor.get_system_status()
        rag_health = rag_pipeline.health_check()
        
        all_healthy = all([
            db_health.get("status") == "healthy",
            processor_health.get("system_status") == "operational",
            rag_health.get("rag_pipeline") == "healthy"
        ])
        
        # Return in expected format
        return {
            "success": True,
            "data": {
                "status": "healthy" if all_healthy else "degraded",
                "components": {
                    "database": db_health, 
                    "pdf_processor": processor_health, 
                    "rag_pipeline": rag_health
                },
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "error": f"Health check failed: {str(e)}"
        }

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), processor: PDFProcessor = Depends(get_pdf_processor)):
    try:
        logger.info(f"📄 Uploading file: {file.filename}")

        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        file_content = await file.read()
        # Save the PDF first, get the file path
        file_path = processor.save_pdf(file_content, file.filename)
        # Now process using the file path
        result = processor.process_pdf(file_path)

        if result["success"]:
            return {
                "success": True,
                "data": {
                    "document_id": result["document_id"],
                    "document_title": result["metadata"].get("title", result["metadata"].get("file_name", "")),
                    "metadata": result.get("metadata", {})
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Upload failed"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/documents", response_model=DocumentListResponse)
async def list_documents(limit: int = 50, offset: int = 0, database: DatabaseConn = Depends(get_database)):
    try:
        documents = database.list_all_documents(limit=limit)
        total_count = len(documents)
        formatted_docs = [
            {
                "document_id": doc["id"],
                "title": doc.get("title") or doc["file_name"],
                "file_name": doc["file_name"],
                "authors": doc.get("authors"),
                "page_count": doc.get("page_count"),
                "upload_timestamp": doc.get("upload_timestamp")
            }
            for doc in documents[offset:offset + limit]
        ]
        return DocumentListResponse(success=True, documents=formatted_docs, total_count=total_count)
    except Exception as e:
        logger.error(f"List documents failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@app.get("/documents/{document_id}")
async def get_document(document_id: int, database: DatabaseConn = Depends(get_database)):
    try:
        document = database.get_document_metadata(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return {
            "success": True,
            "document": {
                "document_id": document["id"],
                "title": document.get("title") or document["file_name"],
                "file_name": document["file_name"],
                "authors": document.get("authors"),
                "page_count": document.get("page_count"),
                "upload_timestamp": document.get("upload_timestamp")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

@app.delete("/documents/{document_id}")
async def delete_document(document_id: int, processor: PDFProcessor = Depends(get_pdf_processor)):
    try:
        success = processor.delete_document(document_id)
        if success:
            logger.info(f"🗑️ Deleted document {document_id}")
            return {"success": True, "message": "Document deleted", "document_id": document_id}
        raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@app.post("/chat")
async def chat_with_documents(request: ChatRequest, rag: RAGPipeline = Depends(get_rag_pipeline)):
    try:
        logger.info(f"🤖 Processing query: {request.question[:50]}...")
        result = rag.query(request.question, request.document_id, request.conversation_history)
        
        if result["success"]:
            return {
                "success": True,
                "data": {
                    "question": request.question,
                    "answer": result["answer"],
                    "sources": result.get("sources", []),
                    "metadata": result.get("metadata", {})
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Chat query failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.post("/documents/{document_id}/summarize")
async def summarize_document(document_id: int, rag: RAGPipeline = Depends(get_rag_pipeline)):
    try:
        logger.info(f"📄 Summarizing document {document_id}")
        result = rag.summarize_document(document_id)
        
        if result["success"]:
            return {
                "success": True,
                "data": {
                    "document_id": document_id,
                    "document_title": result.get("document_title", "Unknown"),
                    "summary": result["summary"],
                    "key_points": result.get("key_points", []),
                    "metadata": result.get("metadata", {})
                }
            }
        else:
            error_msg = result.get("error", "Summarization failed")
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@app.post("/documents/{document_id}/questions")
async def generate_questions(document_id: int, rag: RAGPipeline = Depends(get_rag_pipeline)):
    try:
        logger.info(f"❓ Generating questions for document {document_id}")
        result = rag.generate_question_suggestions(document_id)
        
        if result["success"]:
            return {
                "success": True,
                "data": {
                    "document_id": document_id,
                    "document_title": result.get("document_title", "Unknown"),
                    "questions": result.get("questions", []),
                    "metadata": result.get("metadata", {})
                }
            }
        else:
            error_msg = result.get("error", "Question generation failed")
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Question generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"success": False, "error": "Resource not found"})

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal error: {exc}")
    return JSONResponse(status_code=500, content={"success": False, "error": "Internal server error"})

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"success": False, "error": exc.detail})

# @app.on_event("startup")
# async def startup_event():
#     logger.info("🚀 Starting DocMind AI API...")
#     try:
#         db.initialize_schema()
#         logger.info("✅ Database initialized")
#         if rag_pipeline.health_check().get("rag_pipeline") == "healthy":
#             logger.info("✅ RAG Pipeline ready")
#         else:
#             logger.warning("⚠️ RAG Pipeline health check failed")
#     except Exception as e:
#         logger.error(f"❌ Startup failed: {e}")
#         raise

# @app.on_event("shutdown")
# async def shutdown_event():
#     logger.info("🛑 Shutting down DocMind AI API...")
#     try:
#         db.close_pool()
#         logger.info("✅ Cleanup completed")
#     except Exception as e:
#         logger.error(f"❌ Shutdown error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.api.main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True,
        log_level="info"
    )