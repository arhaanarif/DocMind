import os
from backend.api.config import Settings
import psycopg2
from psycopg2 import OperationalError, IntegrityError, pool
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import logging

load_dotenv()

class DatabaseConn:
    """
    Enhanced database connection manager for DocMind RAG system.
    Stores document metadata in PostgreSQL for academic PDF processing.
    """
    def __init__(self):
        self.settings = Settings()
        self.db_params = {
            'dbname': self.settings.POSTGRES_DB,
            'user': self.settings.POSTGRES_USER,
            'password': self.settings.POSTGRES_PASSWORD,
            'host': self.settings.POSTGRES_HOST,
            'port': self.settings.POSTGRES_PORT,
        }
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,  # Increased for better performance
                **self.db_params
            )
            print("✓ Database connection pool initialized successfully")
        except OperationalError as e:
            print(f"✗ Error initializing connection pool: {e}")
            raise
        self.initialize_schema()

    def initialize_schema(self):
        """Initialize enhanced database schema for better PDF processing integration."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Create enhanced documents table
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS documents (
                            id SERIAL PRIMARY KEY,
                            file_name VARCHAR(255) NOT NULL,
                            title TEXT,
                            authors TEXT,
                            page_count INTEGER,
                            publication_date VARCHAR(50),
                            file_size BIGINT DEFAULT 0,
                            pdf_type VARCHAR(20) DEFAULT 'unknown',
                            processing_status VARCHAR(20) DEFAULT 'completed',
                            chunk_count INTEGER DEFAULT 0,
                            has_embeddings BOOLEAN DEFAULT FALSE,
                            upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_processed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(file_name)
                        );
                        
                        -- Add new columns to existing table if they don't exist
                        DO $$ 
                        BEGIN
                            -- Add file_size column if it doesn't exist
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                         WHERE table_name='documents' AND column_name='file_size') THEN
                                ALTER TABLE documents ADD COLUMN file_size BIGINT DEFAULT 0;
                            END IF;
                            
                            -- Add pdf_type column if it doesn't exist
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                         WHERE table_name='documents' AND column_name='pdf_type') THEN
                                ALTER TABLE documents ADD COLUMN pdf_type VARCHAR(20) DEFAULT 'unknown';
                            END IF;
                            
                            -- Add processing_status column if it doesn't exist
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                         WHERE table_name='documents' AND column_name='processing_status') THEN
                                ALTER TABLE documents ADD COLUMN processing_status VARCHAR(20) DEFAULT 'completed';
                            END IF;
                            
                            -- Add chunk_count column if it doesn't exist
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                         WHERE table_name='documents' AND column_name='chunk_count') THEN
                                ALTER TABLE documents ADD COLUMN chunk_count INTEGER DEFAULT 0;
                            END IF;
                            
                            -- Add has_embeddings column if it doesn't exist
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                         WHERE table_name='documents' AND column_name='has_embeddings') THEN
                                ALTER TABLE documents ADD COLUMN has_embeddings BOOLEAN DEFAULT FALSE;
                            END IF;
                            
                            -- Add last_processed column if it doesn't exist
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                         WHERE table_name='documents' AND column_name='last_processed') THEN
                                ALTER TABLE documents ADD COLUMN last_processed TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                            END IF;
                        END $$;
                        
                        -- Create indexes for better performance
                        CREATE INDEX IF NOT EXISTS idx_documents_upload_timestamp 
                        ON documents(upload_timestamp DESC);
                        
                        CREATE INDEX IF NOT EXISTS idx_documents_processing_status 
                        ON documents(processing_status);
                        
                        CREATE INDEX IF NOT EXISTS idx_documents_pdf_type 
                        ON documents(pdf_type);
                    """)
                    conn.commit()
                    print("✓ Enhanced database schema initialized successfully")
        except Exception as e:
            print(f"✗ Error initializing database schema: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def insert_document_metadata(self, file_name: str, title: Optional[str] = None,
                                authors: Optional[str] = None, page_count: Optional[int] = None,
                                publication_date: Optional[str] = None, 
                                file_size: Optional[int] = None,
                                pdf_type: Optional[str] = None) -> Optional[int]:
        """Enhanced document metadata insertion with new fields."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Check if document already exists
                    cur.execute("SELECT id FROM documents WHERE file_name = %s", (file_name,))
                    existing = cur.fetchone()
                    if existing:
                        print(f"Document {file_name} already exists with ID: {existing[0]}")
                        return existing[0]
                    
                    # Insert with enhanced fields
                    cur.execute("""
                        INSERT INTO documents (
                            file_name, title, authors, page_count, publication_date,
                            file_size, pdf_type, last_processed
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        RETURNING id;
                    """, (file_name, title, authors, page_count, publication_date, 
                         file_size, pdf_type))
                    
                    result = cur.fetchone()
                    conn.commit()
                    if result:
                        document_id = result[0]
                        print(f"✓ Inserted document with ID: {document_id}")
                        return document_id
        except IntegrityError as e:
            print(f"✗ Integrity error inserting document {file_name}: {e}")
            return None
        except Exception as e:
            print(f"✗ Error inserting document {file_name}: {e}")
            return None

    def update_processing_status(self, document_id: int, 
                               chunk_count: Optional[int] = None,
                               has_embeddings: Optional[bool] = None,
                               processing_status: str = 'completed') -> bool:
        """Update document processing status after PDF processing."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    update_fields = ["processing_status = %s", "last_processed = CURRENT_TIMESTAMP"]
                    values = [processing_status]
                    
                    if chunk_count is not None:
                        update_fields.append("chunk_count = %s")
                        values.append(chunk_count)
                    
                    if has_embeddings is not None:
                        update_fields.append("has_embeddings = %s")
                        values.append(has_embeddings)
                    
                    values.append(document_id)
                    
                    query = f"UPDATE documents SET {', '.join(update_fields)} WHERE id = %s"
                    cur.execute(query, values)
                    conn.commit()
                    
                    print(f"✓ Updated processing status for document {document_id}")
                    return True
                    
        except Exception as e:
            print(f"✗ Error updating processing status for document {document_id}: {e}")
            return False

    def get_document_metadata(self, document_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve enhanced metadata for a document by ID."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, file_name, title, authors, page_count, publication_date,
                               file_size, pdf_type, processing_status, chunk_count, 
                               has_embeddings, upload_timestamp, last_processed
                        FROM documents WHERE id = %s;
                    """, (document_id,))
                    result = cur.fetchone()
                    if result:
                        return {
                            'id': result[0],
                            'file_name': result[1],
                            'title': result[2],
                            'authors': result[3],
                            'page_count': result[4],
                            'publication_date': result[5],
                            'file_size': result[6],
                            'pdf_type': result[7],
                            'processing_status': result[8],
                            'chunk_count': result[9],
                            'has_embeddings': result[10],
                            'upload_timestamp': result[11],
                            'last_processed': result[12]
                        }
                    return None
        except Exception as e:
            print(f"✗ Error retrieving metadata for document {document_id}: {e}")
            return None

    def list_all_documents(self, limit: Optional[int] = None, 
                          processing_status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve all documents with optional filtering."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                        SELECT id, file_name, title, authors, page_count, publication_date,
                               file_size, pdf_type, processing_status, chunk_count, 
                               has_embeddings, upload_timestamp, last_processed
                        FROM documents
                    """
                    
                    conditions = []
                    params = []
                    
                    if processing_status:
                        conditions.append("processing_status = %s")
                        params.append(processing_status)
                    
                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)
                    
                    query += " ORDER BY upload_timestamp DESC"
                    
                    if limit:
                        query += " LIMIT %s"
                        params.append(limit)
                    
                    cur.execute(query, params)
                    results = cur.fetchall()
                    
                    documents = []
                    for result in results:
                        documents.append({
                            'id': result[0],
                            'file_name': result[1],
                            'title': result[2],
                            'authors': result[3],
                            'page_count': result[4],
                            'publication_date': result[5],
                            'file_size': result[6],
                            'pdf_type': result[7],
                            'processing_status': result[8],
                            'chunk_count': result[9],
                            'has_embeddings': result[10],
                            'upload_timestamp': result[11],
                            'last_processed': result[12]
                        })
                    
                    return documents
        except Exception as e:
            print(f"✗ Error retrieving documents: {e}")
            return []

    def delete_document(self, document_id: int) -> bool:
        """Delete a document record from the database."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT file_name FROM documents WHERE id = %s", (document_id,))
                    result = cur.fetchone()
                    if not result:
                        print(f"Document ID {document_id} not found")
                        return False
                    cur.execute("DELETE FROM documents WHERE id = %s", (document_id,))
                    conn.commit()
                    print(f"✓ Deleted document {result[0]} (ID: {document_id})")
                    return True
        except Exception as e:
            print(f"✗ Error deleting document {document_id}: {e}")
            return False

    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get total documents
                    cur.execute("SELECT COUNT(*) FROM documents")
                    total_docs = cur.fetchone()[0]
                    
                    # Get documents with embeddings
                    cur.execute("SELECT COUNT(*) FROM documents WHERE has_embeddings = TRUE")
                    docs_with_embeddings = cur.fetchone()[0]
                    
                    # Get total chunks
                    cur.execute("SELECT SUM(chunk_count) FROM documents WHERE chunk_count IS NOT NULL")
                    total_chunks = cur.fetchone()[0] or 0
                    
                    return {
                        "total_documents": total_docs,
                        "documents_with_embeddings": docs_with_embeddings,
                        "total_chunks": total_chunks,
                        "connection_status": "connected"
                    }
        except Exception as e:
            return {
                "error": str(e),
                "connection_status": "error"
            }

    def health_check(self) -> Dict[str, Any]:
        """Check database health and connectivity."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return {
                "status": "healthy",
                "database": self.db_params['dbname'],
                "host": f"{self.db_params['host']}:{self.db_params['port']}"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "database": self.db_params['dbname'],
                "host": f"{self.db_params['host']}:{self.db_params['port']}"
            }

    def close_pool(self):
        """Close the connection pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
            print("✓ Database connection pool closed")

db = DatabaseConn()