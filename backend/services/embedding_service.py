from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Union
import logging
from backend.api.config import Settings

class EmbeddingService:
    """
    Embedding service for generating chunk embeddings in a RAG pipeline.
    Uses all-MiniLM-L6-v2 to generate embeddings for text chunks.
    Integrates with vector_store.py for ChromaDB storage.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service with specified model.
        
        Args:
            model_name: HuggingFace sentence-transformer model name
        """
        self.settings = Settings()
        self.model_name = model_name
        self.model = None
        self.embedding_dim = None
        self._load_model()

    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            print(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            print(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logging.error(f"Failed to load embedding model {self.model_name}: {e}")
            raise

    def encode_text(self, text: Union[str, List[str]], normalize: bool = True) -> List[List[float]]:
        """
        Generate embeddings for text or list of texts.
        
        Args:
            text: Single text string or list of text strings
            normalize: Whether to normalize embeddings to unit vectors
            
        Returns:
            List of embeddings
        """
        try:
            if not self.model:
                raise RuntimeError("Model not loaded")
            if isinstance(text, str):
                text = [text]
            embeddings = self.model.encode(text, normalize_embeddings=normalize).tolist()
            return embeddings
        except Exception as e:
            logging.error(f"Error generating embeddings: {e}")
            raise

    def encode_chunks(self, chunks: List[Dict[str, Any]], text_field: str = "content") -> List[Dict[str, Any]]:
        """
        Generate embeddings for chunks from PDFProcessor.
        
        Args:
            chunks: List of chunk dictionaries with content, document_id, chunk_id
            text_field: Field name containing the text to embed
            
        Returns:
            Updated chunks with embeddings
        """
        try:
            if not chunks:
                print("No chunks provided for embedding")
                return []

            texts = []
            valid_chunks = []
            for chunk in chunks:
                if text_field in chunk and chunk[text_field].strip():
                    texts.append(chunk[text_field])
                    valid_chunks.append(chunk)

            if not texts:
                print("No valid text found in chunks")
                return chunks

            print(f"Generating embeddings for {len(texts)} chunks...")
            embeddings = self.encode_text(texts)

            for i, chunk in enumerate(valid_chunks):
                chunk['embeddings'] = embeddings[i]
                chunk['embedding_model'] = self.model_name
                chunk['embedding_dim'] = self.embedding_dim

            print(f"Generated embeddings for {len(valid_chunks)} chunks")
            return valid_chunks

        except Exception as e:
            logging.error(f"Error processing chunks: {e}")
            return chunks