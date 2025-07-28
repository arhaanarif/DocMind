from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any
import re

class LangChainChunker:
    def __init__(self):
        self.default_chunk_size = 1000
        self.default_overlap = 100
        self.research_paper_chunk_size = 1500
        self.research_paper_overlap = 150

    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[Dict[str, Any]]:
        """
        Chunk text using LangChain's RecursiveCharacterTextSplitter
        """
        chunk_size = chunk_size or self.default_chunk_size
        overlap = overlap or self.default_overlap
        
        try:
            # Clean text
            cleaned_text = self._clean_text(text)
            if not cleaned_text:
                return []

            # Create splitter
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            # Split text
            chunks = splitter.split_text(cleaned_text)
            
            # Add metadata
            chunked_docs = []
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    chunked_docs.append({
                        "content": chunk.strip(),
                        "chunk_id": i,
                        "chunk_size": len(chunk.strip()),
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "chunk_type": "standard",
                        "metadata": {
                            "chunk_method": "recursive_character",
                            "chunk_size": chunk_size,
                            "chunk_overlap": overlap
                        }
                    })
            
            print(f"Text chunked into {len(chunked_docs)} pieces")
            return chunked_docs
            
        except Exception as e:
            print(f"Error chunking text: {e}")
            return []

    def chunk_research_paper(self, text: str) -> List[Dict[str, Any]]:
        """
        Simple chunking for research papers with larger chunks
        """
        return self.chunk_text(
            text, 
            chunk_size=self.research_paper_chunk_size, 
            overlap=self.research_paper_overlap
        )

    def _clean_text(self, text: str) -> str:
        """Clean text by removing excessive whitespace and page breaks"""
        try:
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'--- Page \d+.*?\n', '', text)
            return text.strip()
        except Exception as e:
            print(f"Error cleaning text: {e}")
            return text