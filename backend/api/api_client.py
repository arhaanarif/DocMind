import requests
import streamlit as st
from typing import Dict, Any, List, Optional
import json

class DocMindAPIClient:
    """API Client for DocMind AI Backend"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {
                    "success": False, 
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "status_code": response.status_code
                }
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Cannot connect to API server"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        return self._make_request("GET", "/health")
    
    def upload_pdf(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Upload PDF file"""
        files = {"file": (filename, file_content, "application/pdf")}
        return self._make_request("POST", "/upload-pdf", files=files)
    
    def get_documents(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get list of documents"""
        params = {"limit": limit, "offset": offset}
        return self._make_request("GET", "/documents", params=params)
    
    def get_document(self, document_id: int) -> Dict[str, Any]:
        """Get specific document details"""
        return self._make_request("GET", f"/documents/{document_id}")
    
    def delete_document(self, document_id: int) -> Dict[str, Any]:
        """Delete document"""
        return self._make_request("DELETE", f"/documents/{document_id}")
    
    def chat(self, question: str, document_id: Optional[int] = None, 
             conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Chat with documents"""
        data = {
            "question": question,
            "document_id": document_id,
            "conversation_history": conversation_history or []
        }
        return self._make_request("POST", "/chat", json=data)
    
    def summarize_document(self, document_id: int) -> Dict[str, Any]:
        """Generate document summary"""
        return self._make_request("POST", f"/documents/{document_id}/summarize")
    
    def generate_questions(self, document_id: int) -> Dict[str, Any]:
        """Generate suggested questions"""
        return self._make_request("POST", f"/documents/{document_id}/questions")

# Singleton instance
@st.cache_resource
def get_api_client():
    return DocMindAPIClient()