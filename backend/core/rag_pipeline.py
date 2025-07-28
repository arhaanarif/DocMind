import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import openai
from backend.api.config import Settings
from backend.core.pdf_processor import PDFProcessor
from backend.services.vector_store import VectorStore
from backend.services.embedding_service import EmbeddingService
from backend.core.databases import DatabaseConn


settings = Settings()

@dataclass
class RAGConfig:
    """Simplified configuration for RAG pipeline."""
    openrouter_api_key: str = settings.OPENROUTER_API_KEY
    primary_model: str = "moonshotai/kimi-k2:free"
    max_chunks: int = 5
    similarity_threshold: float = 0.4  # Adjusted for cosine distance
    max_tokens: int = 1000
    temperature: float = 0.3

class RAGPipeline:
    """
    Simplified RAG pipeline with OpenRouter for query, summarization, and question generation.
    """
    def __init__(self, config: Optional[RAGConfig] = None):
        self.settings = Settings()
        self.config = config or self._load_default_config()
        self.pdf_processor = PDFProcessor()
        self.vector_store = VectorStore()
        self.embedding_service = EmbeddingService()
        self.db = DatabaseConn()
        self._setup_openrouter_client()
        self.system_prompts = self._load_system_prompts()
        logging.info("✓ RAG Pipeline initialized with OpenRouter")

    def _load_default_config(self) -> RAGConfig:
        """Load default configuration."""
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        if not openrouter_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        return RAGConfig(
            openrouter_api_key=openrouter_key,
            primary_model=os.getenv("RAG_PRIMARY_MODEL", "moonshotai/kimi-k2:free")
        )

    def _setup_openrouter_client(self):
        """Setup OpenRouter client."""
        self.client = openai.OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        self.openrouter_headers = {
            "HTTP-Referer": "https://docmindai.local",
            "X-Title": "DocMind AI - RAG System",
        }
        print("✓ OpenRouter client configured")

    def _load_system_prompts(self) -> Dict[str, str]:
        """Load simplified system prompts."""
        return {
            "default": """You are an AI assistant for academic documents.

Guidelines:
- Use only the provided context to answer questions
- For research papers, focus on methodology, findings, and conclusions
- Cite specific parts of the context when possible
- Be precise, factual, and professional
- If context is insufficient, state limitations
- For summaries, provide concise bullet points (background → methods → results → conclusions)
- For question generation, create 4 analytical questions

Context:
{context}

Task: {task}""",
            "question_generation": """Generate 4 analytical questions based on the document content.

Guidelines:
- Focus on methodology, findings, implications, and applications
- Ensure questions are specific to the content
- Return one question per line, without numbering

Content:
{content}"""
        }

    def query(self, question: str, document_id: Optional[int] = None, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Retrieve context and generate response.
        """
        try:
            print(f"🤖 Processing query: {question[:50]}...")
            processed_query = self._preprocess_query(question, conversation_history)
            retrieval_results = self._retrieve_context(processed_query, document_id)
            if not retrieval_results["chunks"]:
                return {
                    "success": True,
                    "answer": "No relevant information found. Please rephrase or check the document.",
                    "sources": [],
                    "metadata": {"reason": "no_relevant_context"}
                }
            llm_response = self._generate_response(processed_query, retrieval_results["chunks"])
            return self._format_response(question, llm_response["response"], retrieval_results["chunks"], llm_response.get("metadata", {}))
        except Exception as e:
            logging.error(f"RAG query failed: {e}")
            return {
                "success": False,
                "answer": "Error processing your question.",
                "sources": [],
                "error": str(e)
            }

    def generate_document_summary(self, document_id: int) -> Dict[str, Any]:
        try:
            print(f"📄 Generating summary for document {document_id}...")
            
            print("Step 1: Getting document metadata...")
            doc_info = self.db.get_document_metadata(document_id)
            if not doc_info:
                return {"success": False, "error": f"Document {document_id} not found", "summary": None}
            print(f"✓ Got document metadata: {doc_info.get('title', 'No title')}")
            
            print("Step 2: Retrieving context chunks...")
            retrieval_result = self._retrieve_context("summarize document", document_id)
            chunks = retrieval_result["chunks"]
            if not chunks:
                return {"success": False, "error": "No content found for summarization", "summary": None}
            print(f"✓ Retrieved {len(chunks)} chunks")
            
            print("Step 3: Generating summary with OpenRouter...")
            summary_response = self._generate_summary(chunks, doc_info)
            print("✓ Summary generated successfully")
            
            return {
                "success": True,
                "document_id": document_id,
                "document_title": doc_info.get("title") or doc_info.get("file_name"),
                "summary": summary_response["summary"],
                "key_points": summary_response["key_points"],
                "metadata": {"chunks_analyzed": len(chunks), "model_used": summary_response.get("model_used")}
            }
        except Exception as e:
            print(f"✗ Summary generation failed at: {e}")
            import traceback
            traceback.print_exc()
            logging.error(f"Summary generation failed: {e}")
            return {"success": False, "error": str(e), "summary": None}

    def generate_question_suggestions(self, document_id: int) -> Dict[str, Any]:
        """
        Generate suggested questions for a document.
        """
        try:
            print(f"❓ Generating questions for document {document_id}...")
            doc_info = self.db.get_document_metadata(document_id)
            if not doc_info:
                return {"success": False, "error": f"Document {document_id} not found", "questions": []}
            chunks = self._retrieve_context("analyze document content", document_id)["chunks"]
            if not chunks:
                return {"success": False, "error": "No content found for question generation", "questions": []}
            content = "\n".join([chunk.get("content", "") for chunk in chunks])
            questions = self._generate_questions(content, doc_info)
            return {
                "success": True,
                "document_id": document_id,
                "document_title": doc_info.get("title") or doc_info.get("file_name"),
                "questions": questions,
                "metadata": {"model_used": self.config.primary_model}
            }
        except Exception as e:
            logging.error(f"Question generation failed: {e}")
            return {"success": False, "error": str(e), "questions": []}

    def _preprocess_query(self, question: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Preprocess query with conversation context."""
        if not conversation_history:
            return question.strip()
        context_parts = []
        for entry in conversation_history[-3:]:
            if entry.get("role") == "user":
                context_parts.append(f"Previous question: {entry.get('content', '')}")
            elif entry.get("role") == "assistant":
                context_parts.append(f"Previous answer: {entry.get('content', '')[:100]}...")
        return f"{' '.join(context_parts)}\n\nCurrent question: {question}" if context_parts else question.strip()

    def _retrieve_context(self, query: str, document_id: Optional[int] = None) -> Dict[str, Any]:
        try:
            print(f"  - Encoding query: '{query}' for document {document_id}")
            
            # Encode query text to embedding
            query_embeddings = self.embedding_service.encode_text(query)
            print(f"  - Got {len(query_embeddings)} embeddings")
            
            if not query_embeddings:
                raise ValueError("No embeddings generated for query")
                
            query_embedding = query_embeddings[0]
            print(f"  - Using embedding of dimension {len(query_embedding)}")
            
            print(f"  - Querying vector store for document {document_id}")
            results = self.vector_store.query_similar(
                query_embedding=query_embedding,
                n_results=self.config.max_chunks,
                document_id=str(document_id) if document_id else None
            )
            print(f"  - Found {len(results)} results from vector store")
            
            # Debug: Print distances
            for i, chunk in enumerate(results):
                print(f"    Chunk {i}: distance = {chunk.get('distance', 'N/A')}")
            
            # Use a more reasonable filtering threshold
            filtered_chunks = [
                {**chunk, "similarity_score": 1 - chunk["distance"]/2}
                for chunk in results
                if chunk["distance"] <= 1.5  # More reasonable threshold
            ]
            
            # If no chunks pass the filter, take the top results anyway
            if not filtered_chunks and results:
                print("  - No chunks passed similarity filter, using top results")
                filtered_chunks = [
                    {**chunk, "similarity_score": 1 - chunk["distance"]/2}
                    for chunk in results[:3]  # Take top 3
                ]
            
            print(f"  - Filtered to {len(filtered_chunks)} chunks")
            
            return {
                "success": True,
                "chunks": filtered_chunks,
                "total_found": len(results),
                "filtered_count": len(filtered_chunks)
            }
        except Exception as e:
            print(f"  - Context retrieval failed: {e}")
            import traceback
            traceback.print_exc()
            logging.error(f"Context retrieval failed: {e}")
            return {"success": False, "chunks": [], "error": str(e)}

    def _generate_response(self, question: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response using OpenRouter LLM."""
        try:
            context_text = self._format_context(context_chunks)
            prompt = self.system_prompts["default"].format(context=context_text, task=f"Answer: {question}")
            response = self._call_openrouter(prompt)
            return {
                "success": True,
                "response": response["content"],
                "metadata": {"model_used": response["model"], "tokens_used": response.get("tokens", 0)}
            }
        except Exception as e:
            logging.error(f"Response generation failed: {e}")
            return {"success": False, "response": "Error generating response.", "error": str(e)}

    def _generate_summary(self, chunks: List[Dict[str, Any]], doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate document summary."""
        try:
            content_text = "\n".join([chunk.get("content", "") for chunk in chunks])
            metadata_context = f"Document: {doc_info.get('title') or doc_info.get('file_name')}\nAuthors: {doc_info.get('authors') or 'Unknown'}"
            prompt = self.system_prompts["default"].format(context=metadata_context + "\n\n" + content_text, task="Summarize the document in concise bullet points.")
            response = self._call_openrouter(prompt)
            summary_text = response["content"]
            key_points = self._extract_bullet_points(summary_text)
            return {
                "summary": summary_text,
                "key_points": key_points,
                "model_used": response["model"]
            }
        except Exception as e:
            logging.error(f"Summary generation failed: {e}")
            raise

    def _generate_questions(self, content: str, doc_info: Dict[str, Any]) -> List[str]:
        """Generate suggested questions."""
        try:
            metadata_context = f"Document Title: {doc_info.get('title') or doc_info.get('file_name')}\nAuthors: {doc_info.get('authors') or 'Unknown'}"
            prompt = self.system_prompts["question_generation"].format(content=metadata_context + "\n\n" + content)
            response = self._call_openrouter(prompt)
            return self._parse_questions(response["content"])[:4]
        except Exception as e:
            logging.error(f"Question generation failed: {e}")
            return [
                "What are the main findings of this document?",
                "What methodology was used in this research?",
                "What are the practical applications mentioned?",
                "What limitations or future work are discussed?"
            ]

    def _call_openrouter(self, prompt: str) -> Dict[str, Any]:
        """Call OpenRouter API."""
        try:
            response = self.client.chat.completions.create(
                extra_headers=self.openrouter_headers,
                model=self.config.primary_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            return {
                "content": response.choices[0].message.content,
                "model": self.config.primary_model,
                "tokens": response.usage.total_tokens if hasattr(response, "usage") and response.usage else 0
            }
        except Exception as e:
            logging.error(f"OpenRouter call failed: {e}")
            raise

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into context."""
        if not chunks:
            return "No relevant context found."
        context_parts = [
            f"[Document {chunk.get('metadata', {}).get('document_id', 'unknown')}, Page {chunk.get('metadata', {}).get('page_number', 'unknown')}, Relevance: {chunk.get('similarity_score', 0):.2f}]\n{chunk.get('content', '')}"
            for chunk in chunks
        ]
        return "\n".join(context_parts)

    def _format_response(self, question: str, answer: str, chunks: List[Dict[str, Any]], generation_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Format final response."""
        sources = [
            {
                "document_id": chunk.get("metadata", {}).get("document_id"),
                "page_number": chunk.get("metadata", {}).get("page_number"),
                "similarity_score": round(chunk.get("similarity_score", 0), 3),
                "content_preview": chunk.get("content", "")[:150] + "..." if len(chunk.get("content", "")) > 150 else chunk.get("content", "")
            }
            for chunk in chunks
        ]
        return {
            "success": True,
            "question": question,
            "answer": answer,
            "sources": sources,
            "metadata": {
                "model_used": generation_metadata.get("model_used"),
                "tokens_used": generation_metadata.get("tokens_used", 0),
                "chunks_used": len(chunks)
            }
        }

    def _extract_bullet_points(self, text: str) -> List[str]:
        """Extract bullet points from text."""
        lines = text.split('\n')
        bullet_points = [
            line.lstrip('•-*→0123456789. ').strip()
            for line in lines
            if line.strip() and (line.startswith(('•', '-', '*', '→')) or any(line.startswith(f"{i}.") for i in range(1, 20)))
            and len(line.lstrip('•-*→0123456789. ').strip()) > 10
        ]
        return bullet_points[:10]

    def _parse_questions(self, text: str) -> List[str]:
        """Parse questions from LLM response."""
        lines = text.split('\n')
        questions = [
            line.lstrip('0123456789.- ').strip()
            for line in lines
            if line.strip() and '?' in line and len(line.strip()) > 10
        ]
        return questions

    def health_check(self) -> Dict[str, Any]:
        """Check health of RAG components."""
        try:
            test_response = self.client.chat.completions.create(
                extra_headers=self.openrouter_headers,
                model=self.config.primary_model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            openrouter_status = "healthy"
        except Exception as e:
            openrouter_status = f"error: {str(e)}"
        return {
            "rag_pipeline": "healthy",
            "openrouter": openrouter_status,
            "vector_store": self.vector_store.health_check(),
            "embedding_service": {"status": "ready" if self.embedding_service.model else "not_loaded"},
            "database": self.db.health_check()
        }
        
    def summarize_document(self, document_id: int) -> dict:
        return self.generate_document_summary(document_id)