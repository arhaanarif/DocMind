import os
import re
import fitz
import pytesseract
from PIL import Image
from io import BytesIO
from typing import List, Dict, Any, Optional, Tuple
from backend.api.config import Settings
from backend.core.utils.image_preprocessing import OCRImagePreprocessor
from backend.core.utils.pdf_analyzer import PDFAnalyzer
from backend.core.utils.langchain_chunker import LangChainChunker
from backend.services.grobid_client import GrobidClient
from backend.services.embedding_service import EmbeddingService
from backend.services.vector_store import VectorStore 
from backend.core.databases import DatabaseConn

class PDFProcessor:
    """
    Complete PDF processor with enhanced database integration for RAG pipeline.
    Processes PDFs, extracts metadata, generates embeddings, and stores everything persistently.
    Provides comprehensive document management and search capabilities.
    """
    
    def __init__(self):
        self.settings = Settings()
        self.image_preprocessor = OCRImagePreprocessor()
        self.pdf_analyzer = PDFAnalyzer()
        self.chunker = LangChainChunker()
        self.grobid_client = GrobidClient()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.db = DatabaseConn()

    def process_pdf(self, pdf_path: str, document_id: int = None) -> Dict[str, Any]:
        """
        Complete PDF processing pipeline with enhanced database integration.
        
        Args:
            pdf_path (str): Path to PDF file
            document_id (int, optional): Existing document ID (for reprocessing)
            
        Returns:
            Dict[str, Any]: Complete processing results with database integration
        """
        try:
            # Step 1: Validate PDF
            if not self._validate_pdf(pdf_path):
                raise ValueError("Invalid PDF file")

            # Step 2: Detect PDF type
            pdf_analysis = self.pdf_analyzer.detect_pdf_type(pdf_path)
            print(f"PDF Type: {pdf_analysis['pdf_type']} (confidence: {pdf_analysis['confidence']:.1f}%)")

            # Step 3: Extract text
            full_text, processing_info = self._extract_text(pdf_path)
            if not full_text.strip():
                raise ValueError("No text content extracted from PDF")

            # Step 4: Extract metadata
            metadata = self._extract_metadata(pdf_path, pdf_analysis['pdf_type'])
            
                        # ...existing code...
            if 'file_name' not in metadata or not metadata['file_name']:
                metadata['file_name'] = os.path.basename(pdf_path)
            if 'file_size' not in metadata or not metadata['file_size']:
                metadata['file_size'] = os.path.getsize(pdf_path)
            # ...existing code...
            
            # Step 4.5: Save document metadata to database and get document_id
            db_document_id = None
            if not document_id:
                try:
                    db_document_id = self.db.insert_document_metadata(
                        file_name=metadata['file_name'],
                        title=metadata.get('title'),
                        authors=metadata.get('author') or metadata.get('authors'),
                        page_count=metadata.get('page_count'),
                        publication_date=metadata.get('publication_date'),
                        file_size=metadata.get('file_size'),
                        pdf_type=pdf_analysis['pdf_type']
                    )
                    
                    if db_document_id:
                        print(f"✓ Saved document metadata to database with ID: {db_document_id}")
                        document_id = db_document_id
                    else:
                        print("✗ Failed to save document metadata to database")
                        # Continue processing without database integration
                        document_id = hash(metadata['file_name']) % 10000  # Generate temp ID
                        
                except Exception as e:
                    print(f"✗ Database save failed: {e}")
                    document_id = hash(metadata['file_name']) % 10000  # Generate temp ID
            
            # Update metadata with document_id
            metadata['document_id'] = document_id

            # Step 5: Chunk text
            is_research = metadata.get('appears_academic', False)
            if is_research:
                chunks = self.chunker.chunk_research_paper(full_text)
                print("Using research paper chunking")
            else:
                chunks = self.chunker.chunk_text(full_text)
                print("Using standard chunking")

            if not chunks:
                raise ValueError("No chunks generated from text")

            # Add document_id and chunk_index to all chunks
            for i, chunk in enumerate(chunks):
                chunk['document_id'] = document_id
                if 'chunk_index' not in chunk:
                    chunk['chunk_index'] = i

            # Step 6: Generate embeddings
            embedding_success = False
            if chunks:
                try:
                    chunks = self.embedding_service.encode_chunks(chunks)
                    print(f"✓ Generated embeddings for {len(chunks)} chunks")
                    embedding_success = True
                except Exception as e:
                    print(f"✗ Embedding generation failed: {e}")

            # Step 7: Store in vector database
            storage_success = False
            if chunks and embedding_success:
                try:
                    storage_success = self.vector_store.store_chunks(chunks)
                    if storage_success:
                        print(f"✓ Stored {len(chunks)} chunks in ChromaDB")
                    else:
                        print("✗ Failed to store chunks in ChromaDB")
                except Exception as e:
                    print(f"✗ Vector storage failed: {e}")

            # Step 8: Update database with processing status
            if db_document_id and embedding_success and storage_success:
                try:
                    update_success = self.db.update_processing_status(
                        document_id=db_document_id,
                        chunk_count=len(chunks),
                        has_embeddings=embedding_success,
                        processing_status='completed'
                    )
                    if update_success:
                        print(f"✓ Updated database processing status for document {db_document_id}")
                    else:
                        print(f"✗ Failed to update database status for document {db_document_id}")
                except Exception as e:
                    print(f"✗ Failed to update database status: {e}")

            # Step 9: Return comprehensive results
            result = {
                "success": True,
                "document_id": document_id,
                "pdf_type": pdf_analysis['pdf_type'],
                "is_research_paper": is_research,
                "metadata": metadata,
                "chunks": chunks,
                "stats": {
                    "pages": processing_info.get('total_pages', 0),
                    "chunks": len(chunks),
                    "has_embeddings": embedding_success,
                    "stored_in_vectordb": storage_success,
                    "saved_to_database": db_document_id is not None,
                    "ocr_pages": len(processing_info.get('ocr_pages', [])),
                    "processing_status": "completed" if embedding_success and storage_success else "partial"
                }
            }
            
            print(f"✓ Processing completed: Document ID {document_id}, {len(chunks)} chunks, embeddings: {embedding_success}, stored: {storage_success}")
            return result

        except Exception as e:
            error_context = {
                "error": str(e),
                "step": "unknown",
                "pdf_path": pdf_path,
                "document_id": document_id
            }
            
            # Try to identify which step failed
            if "Invalid PDF file" in str(e):
                error_context["step"] = "validation"
            elif "No text content extracted" in str(e):
                error_context["step"] = "text_extraction"
            elif "No chunks generated" in str(e):
                error_context["step"] = "chunking"
            
            print(f"✗ Error processing PDF {pdf_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_context": error_context,
                "document_id": None,
                "pdf_type": "unknown",
                "metadata": {},
                "chunks": [],
                "stats": {
                    "pages": 0, 
                    "chunks": 0, 
                    "has_embeddings": False, 
                    "stored_in_vectordb": False,
                    "saved_to_database": False,
                    "ocr_pages": 0,
                    "processing_status": "failed"
                }
            }

    def search_document(self, query: str, document_id: str = None, top_k: int = 5) -> Dict[str, Any]:
        """
        Search for similar chunks using semantic similarity
        
        Args:
            query: Search query text
            document_id: Optional document ID to search within
            top_k: Number of results to return
            
        Returns:
            Search results with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.encode_text(query)[0]
            
            # Search vector store
            if document_id:
                # Search within specific document
                results = self.vector_store.search_by_document(
                    query_embedding=query_embedding,
                    document_id=document_id,
                    top_k=top_k
                )
            else:
                # Search across all documents
                results = self.vector_store.search_similar_chunks(
                    query_embedding=query_embedding,
                    top_k=top_k
                )
            
            return {
                "success": True,
                "query": query,
                "document_id": document_id,
                "results": results,
                "total_found": len(results)
            }
            
        except Exception as e:
            print(f"✗ Search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "document_id": document_id,
                "results": [],
                "total_found": 0
            }

    def get_processed_documents(self) -> List[Dict[str, Any]]:
        """Get list of all processed documents from database"""
        try:
            documents = self.db.list_all_documents()
            print(f"Retrieved {len(documents)} documents from database")
            return documents
        except Exception as e:
            print(f"✗ Error retrieving documents: {e}")
            return []

    def get_documents_by_status(self, processing_status: str = 'completed') -> List[Dict[str, Any]]:
        """Get documents filtered by processing status"""
        try:
            documents = self.db.list_all_documents(processing_status=processing_status)
            print(f"Retrieved {len(documents)} documents with status '{processing_status}'")
            return documents
        except Exception as e:
            print(f"✗ Error retrieving documents by status: {e}")
            return []

    def get_document_info(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Get document metadata from database"""
        try:
            document = self.db.get_document_metadata(document_id)
            if document:
                print(f"Retrieved document info for ID {document_id}")
            else:
                print(f"Document ID {document_id} not found")
            return document
        except Exception as e:
            print(f"✗ Error retrieving document {document_id}: {e}")
            return None

    def update_document_metadata(self, document_id: int, metadata: Dict[str, Any]) -> bool:
        """Update document metadata in database"""
        try:
            success = self.db.update_document_metadata(document_id, metadata)
            if success:
                print(f"✓ Updated metadata for document {document_id}")
            return success
        except Exception as e:
            print(f"✗ Error updating document metadata: {e}")
            return False

    def delete_document(self, document_id: int) -> bool:
        """
        Delete document from both database and vector store
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            bool: Success status
        """
        try:
            # Delete from vector store first
            vector_success = self.vector_store.delete_document_chunks(str(document_id))
            
            # Delete from database
            db_success = self.db.delete_document(document_id)
            
            overall_success = vector_success and db_success
            
            if overall_success:
                print(f"✓ Successfully deleted document {document_id} from both database and vector store")
            else:
                print(f"✗ Partial deletion for document {document_id}: DB={db_success}, Vector={vector_success}")
            
            return overall_success
            
        except Exception as e:
            print(f"✗ Error deleting document {document_id}: {e}")
            return False

    def search_document_by_id(self, query: str, document_id: int, top_k: int = 5) -> Dict[str, Any]:
        """
        Search within a specific document using its database ID
        
        Args:
            query: Search query text
            document_id: Database document ID
            top_k: Number of results to return
            
        Returns:
            Search results from the specified document
        """
        # First verify document exists in database
        document_info = self.get_document_info(document_id)
        if not document_info:
            return {
                "success": False,
                "error": f"Document ID {document_id} not found in database",
                "query": query,
                "document_id": document_id,
                "results": [],
                "total_found": 0
            }
        
        # Search using string document_id (ChromaDB uses string IDs)
        return self.search_document(query, str(document_id), top_k)

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all system components"""
        try:
            # Enhanced database status
            db_stats = self.db.get_database_stats()
            
            # Vector store status
            vector_stats = self.vector_store.health_check()
            
            return {
                "system_status": "operational",
                "database": {
                    "status": "connected" if not db_stats.get("error") else "error",
                    "total_documents": db_stats.get("total_documents", 0),
                    "documents_with_embeddings": db_stats.get("documents_with_embeddings", 0),
                    "total_chunks": db_stats.get("total_chunks", 0)
                },
                "embedding_service": {
                    "model": self.embedding_service.model_name,
                    "dimension": self.embedding_service.embedding_dim,
                    "status": "ready" if self.embedding_service.model else "not_loaded"
                },
                "vector_store": {
                    "status": vector_stats.get("connection_status", "unknown"),
                    "total_chunks": vector_stats.get("total_chunks", 0),
                    "collection_name": vector_stats.get("collection_name", "unknown")
                },
                "services": [
                    "PDF Processor",
                    "Database (PostgreSQL)",
                    "GROBID Client", 
                    "Embedding Service",
                    "Vector Store (ChromaDB)",
                    "OCR Preprocessor"
                ],
                "grobid_available": self.grobid_client.is_available()
            }
            
        except Exception as e:
            return {
                "system_status": "error",
                "error": str(e),
                "services": ["PDF Processor (partial)"]
            }

    def health_check(self) -> Dict[str, Any]:
        """Quick health check of all system components"""
        return {
            "database": self.db.health_check(),
            "vector_store": self.vector_store.health_check(),
            "embedding_service": {
                "status": "ready" if self.embedding_service.model else "not_loaded",
                "model": self.embedding_service.model_name
            },
            "grobid": {
                "available": self.grobid_client.is_available()
            }
        }

    def reprocess_document(self, document_id: int, pdf_path: str) -> Dict[str, Any]:
        """
        Reprocess an existing document (useful for updates or fixing processing issues)
        
        Args:
            document_id: Existing document ID in database
            pdf_path: Path to PDF file
            
        Returns:
            Processing results
        """
        try:
            # First delete existing chunks from vector store
            print(f"Reprocessing document {document_id}...")
            self.vector_store.delete_document_chunks(str(document_id))
            
            # Process with existing document_id
            result = self.process_pdf(pdf_path, document_id)
            
            if result["success"]:
                print(f"✓ Successfully reprocessed document {document_id}")
            else:
                print(f"✗ Failed to reprocess document {document_id}")
            
            return result
            
        except Exception as e:
            print(f"✗ Error reprocessing document {document_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "document_id": document_id
            }

    def get_document_chunks(self, document_id: int, limit: int = 10) -> Dict[str, Any]:
        """
        Get chunks for a specific document (useful for debugging and analysis)
        
        Args:
            document_id: Database document ID
            limit: Maximum number of chunks to return
            
        Returns:
            Document chunks information
        """
        try:
            # Verify document exists
            document_info = self.get_document_info(document_id)
            if not document_info:
                return {
                    "success": False,
                    "error": f"Document ID {document_id} not found",
                    "chunks": []
                }
            
            # Get chunks from vector store
            # This would require implementing a method in vector_store to get chunks by document
            # For now, return document info
            return {
                "success": True,
                "document_id": document_id,
                "document_info": document_info,
                "message": "Chunk retrieval not yet implemented in vector store"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "chunks": []
            }

    # ========== PRIVATE HELPER METHODS ==========

    def _validate_pdf(self, pdf_path: str) -> bool:
        """Validate PDF file (exists, correct extension, size, non-empty)."""
        try:
            if not os.path.exists(pdf_path):
                print(f"File not found: {pdf_path}")
                return False
            if not pdf_path.lower().endswith('.pdf'):
                print(f"Not a PDF file: {pdf_path}")
                return False
            
            file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
            if file_size_mb > 100:
                print(f"File too large: {file_size_mb:.1f}MB (max 100MB)")
                return False
            
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            
            if page_count == 0:
                print("PDF has no pages")
                return False
                
            print(f"✓ Valid PDF: {page_count} pages, {file_size_mb:.1f}MB")
            return True
            
        except Exception as e:
            print(f"PDF validation failed: {e}")
            return False

    def _extract_text(self, pdf_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extract text using PyMuPDF with OCR fallback."""
        try:
            doc = fitz.open(pdf_path)
            extracted_text = ""
            processing_info = {
                "total_pages": len(doc),
                "ocr_pages": [],
                "pages_processed": 0,
                "extraction_method": []
            }

            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                
                if len(page_text.strip()) < 50:
                    # Use OCR for pages with minimal text
                    print(f"Page {page_num+1}: Using OCR")
                    ocr_text = self._perform_ocr(page, page_num+1)
                    if ocr_text and len(ocr_text.strip()) > 10:
                        extracted_text += ocr_text + "\n"
                        processing_info['ocr_pages'].append(page_num + 1)
                        processing_info['extraction_method'].append('ocr')
                    else:
                        extracted_text += page_text + "\n"
                        processing_info['extraction_method'].append('text_fallback')
                else:
                    extracted_text += page_text + "\n"
                    processing_info['extraction_method'].append('text')
                    
                processing_info['pages_processed'] += 1

            doc.close()
            
            cleaned_text = self._clean_text(extracted_text)
            processing_info['char_count'] = len(cleaned_text)
            processing_info['word_count'] = len(cleaned_text.split())
            
            print(f"✓ Extracted text from {processing_info['pages_processed']} pages")
            print(f"  - OCR used on {len(processing_info['ocr_pages'])} pages")
            print(f"  - Total: {processing_info['char_count']} chars, {processing_info['word_count']} words")
            
            return cleaned_text, processing_info
            
        except Exception as e:
            print(f"Text extraction failed: {e}")
            return "", {
                "total_pages": 0, 
                "pages_processed": 0, 
                "ocr_pages": [],
                "char_count": 0,
                "word_count": 0,
                "error": str(e)
            }

    def _perform_ocr(self, page, page_num: int) -> Optional[str]:
        """Perform OCR on a page with image preprocessing."""
        try:
            # Convert page to image with higher resolution
            mat = fitz.Matrix(2.0, 2.0)  # 2x scaling for better OCR
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            image = Image.open(BytesIO(img_data))
            
            # Preprocess image for better OCR
            processed_image = self.image_preprocessor.preprocess_for_ocr(image)
            
            # Perform OCR with optimized settings
            ocr_text = pytesseract.image_to_string(
                processed_image, 
                lang='eng', 
                config='--oem 3 --psm 6'
            )
            
            return ocr_text
            
        except Exception as e:
            print(f"OCR failed on page {page_num}: {e}")
            return None

    def _extract_metadata(self, pdf_path: str, pdf_type: str) -> Dict[str, Any]:
        """Extract metadata using GROBID for digital PDFs, PyMuPDF for scanned."""
        if pdf_type == 'digital':
            try:
                print("Attempting GROBID metadata extraction...")
                metadata = self.grobid_client.extract_metadata(pdf_path)
                if metadata.get('success'):
                    print("✓ Using GROBID metadata extraction")
                    return metadata
                else:
                    print(f"✗ GROBID failed: {metadata.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"✗ GROBID metadata extraction failed: {e}")
        
        print("Using basic metadata extraction")
        return self._extract_basic_metadata(pdf_path)

    def _extract_basic_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract basic metadata using PyMuPDF."""
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            
            result = {
                "title": metadata.get("title", "").strip() or None,
                "author": metadata.get("author", "").strip() or None,
                "subject": metadata.get("subject", "").strip() or None,
                "creator": metadata.get("creator", "").strip() or None,
                "producer": metadata.get("producer", "").strip() or None,
                "creation_date": metadata.get("creationDate", "").strip() or None,
                "modification_date": metadata.get("modDate", "").strip() or None,
                "page_count": len(doc),
                "file_name": os.path.basename(pdf_path),
                "file_size": os.path.getsize(pdf_path),
                "source": "basic",
                "appears_academic": False  # Basic extraction can't determine this
            }
            
            doc.close()
            print(f"✓ Extracted basic metadata for {result['file_name']}")
            return result
            
        except Exception as e:
            print(f"Metadata extraction failed: {e}")
            return {
                "title": None,
                "author": None,
                "page_count": 0,
                "file_name": os.path.basename(pdf_path) if pdf_path else None,
                "file_size": 0,
                "source": "basic",
                "appears_academic": False,
                "error": str(e)
            }

    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double newline
        text = re.sub(r' +', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'\t+', ' ', text)  # Multiple tabs to single space
        
        return text.strip()

    def save_pdf(self, file_bytes: bytes, file_name: str) -> str:
        """Save uploaded PDF file to uploads directory."""
        try:
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            # Ensure unique filename
            base_name, ext = os.path.splitext(file_name)
            counter = 1
            file_path = os.path.join(upload_dir, file_name)
            
            while os.path.exists(file_path):
                new_name = f"{base_name}_{counter}{ext}"
                file_path = os.path.join(upload_dir, new_name)
                counter += 1
            
            with open(file_path, "wb") as f:
                f.write(file_bytes)
                
            print(f"✓ Saved PDF: {os.path.basename(file_path)}")
            return file_path
            
        except Exception as e:
            print(f"Failed to save PDF: {e}")
            raise