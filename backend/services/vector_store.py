import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import logging


class VectorStore:
    """
    Clean, production-like ChromaDB vector store.
    Stores and retrieves document chunks with embeddings for RAG systems.
    """

    def __init__(self, collection_name: str = "document_chunks", host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._connect()

    def _connect(self):
        try:
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=ChromaSettings(allow_reset=True, anonymized_telemetry=False)
            )
            self.client.heartbeat()
            self.collection = self.client.get_or_create_collection(self.collection_name)
            logging.info(f"Connected to ChromaDB at {self.host}:{self.port}, collection: '{self.collection_name}'")
        except Exception as e:
            logging.error(f"Failed to connect to ChromaDB: {e}")
            self.client = None
            self.collection = None

    def store_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        if not self.collection or not chunks:
            logging.warning("No valid collection or chunks provided for storage.")
            return False

        documents, ids, embeddings, metadatas = [], [], [], []

        for chunk in chunks:
            if 'content' not in chunk or not chunk['content'].strip() or 'embeddings' not in chunk:
                continue

            documents.append(chunk['content'])
            ids.append(f"{chunk['document_id']}_{chunk['chunk_index']}")
            embeddings.append(chunk['embeddings'])
            metadata = {
                'document_id': str(chunk.get('document_id', 'unknown')),
                'chunk_index': chunk.get('chunk_index', 0),
                'source': chunk.get('source', 'pdf')
            }
            metadatas.append(metadata)

        if not documents:
            logging.warning("No valid chunks with embeddings found.")
            return False

        try:
            self.collection.add(
                documents=documents,
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logging.info(f"Stored {len(documents)} chunks in ChromaDB collection '{self.collection_name}'.")
            return True
        except Exception as e:
            logging.error(f"Failed to store chunks in ChromaDB: {e}")
            return False

    def query_similar(self, query_embedding: List[float], n_results: int = 5, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.collection:
            logging.error("No active ChromaDB collection.")
            return []

        where = {'document_id': str(document_id)} if document_id else None

        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
            if not results['documents'] or not results['documents'][0]:
                logging.info("No similar chunks found.")
                return []

            return [{
                'content': doc,
                'metadata': meta,
                'distance': dist
            } for doc, meta, dist in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )]
        except Exception as e:
            logging.error(f"Query to ChromaDB failed: {e}")
            return []

    def delete_collection(self) -> bool:
        if not self.client:
            logging.error("ChromaDB client not initialized.")
            return False
        try:
            self.client.delete_collection(self.collection_name)
            logging.info(f"Deleted ChromaDB collection: '{self.collection_name}'.")
            self.collection = None
            return True
        except Exception as e:
            logging.error(f"Failed to delete collection '{self.collection_name}': {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        if not self.client:
            return {"status": "disconnected", "error": "ChromaDB client not initialized"}

        try:
            self.client.heartbeat()
            collections = self.client.list_collections()
            return {
                "status": "healthy",
                "host": f"{self.host}:{self.port}",
                "collections": [col.name for col in collections]
            }
        except Exception as e:
            return {
                "status": "error",
                "host": f"{self.host}:{self.port}",
                "error": str(e)
            }
