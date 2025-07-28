// API service to connect to your FastAPI backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

interface ChatRequest {
  question: string;
  document_id?: number;
  conversation_history?: Array<{ role: string; content: string }>;
}

interface UploadResponse {
  success: boolean;
  data: {
    document_id: number;
    document_title: string;
    metadata: any;
  };
}

interface Document {
  document_id: number;
  title: string;
  file_name: string;
  authors?: string;
  page_count?: number;
  upload_timestamp?: string;
}

interface DocumentsResponse {
  success: boolean;
  data: {
    documents: Document[];
    total_count: number;
  };
}

interface ChatResponse {
  success: boolean;
  data: {
    question: string;
    answer: string;
    sources: Array<{
      document_id: number;
      page_number: number;
      content_preview: string;
    }>;
    metadata: any;
  };
}

interface SummaryResponse {
  success: boolean;
  data: {
    document_id: number;
    document_title: string;
    summary: string;
    key_points: string[];
    metadata: any;
  };
}

interface QuestionsResponse {
  success: boolean;
  data: {
    document_id: number;
    document_title: string;
    questions: string[];
    metadata: any;
  };
}

interface HealthResponse {
  success: boolean;
  data: {
    status: string;
    components: {
      database: { status: string };
      pdf_processor: { system_status: string };
      rag_pipeline: { rag_pipeline: string };
    };
    timestamp: string;
  };
}

interface SingleDocumentResponse {
  success: boolean;
  data: {
    document: Document;
  };
}

class DocMindAPI {
  private baseURL: string;

  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // Health check
  async healthCheck(): Promise<HealthResponse['data']> {
    const response = await fetch(`${this.baseURL}/health`);
    if (!response.ok) {
      throw new Error('Health check failed');
    }
    const data: HealthResponse = await response.json();
    return data.data;
  }

  // Upload PDF
  async uploadPDF(file: File): Promise<UploadResponse['data']> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseURL}/upload-pdf`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }

    const data: UploadResponse = await response.json();
    return data.data;
  }

  // Get all documents
  async getDocuments(limit = 50, offset = 0): Promise<DocumentsResponse> {
    const response = await fetch(
      `${this.baseURL}/documents?limit=${limit}&offset=${offset}`
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch documents');
    }

    return response.json();
  }

  // Get single document
  async getDocument(documentId: number): Promise<SingleDocumentResponse['data']> {
    const response = await fetch(`${this.baseURL}/documents/${documentId}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch document');
    }

    const data: SingleDocumentResponse = await response.json();
    return data.data;
  }

  // Delete document
  async deleteDocument(documentId: number): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${this.baseURL}/documents/${documentId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete document');
    }

    return response.json();
  }

  // Chat with documents
  async chat(chatRequest: ChatRequest): Promise<ChatResponse['data']> {
    const response = await fetch(`${this.baseURL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(chatRequest),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Chat failed');
    }

    const data: ChatResponse = await response.json();
    return data.data;
  }

  // Summarize document
  async summarizeDocument(documentId: number): Promise<SummaryResponse['data']> {
    const response = await fetch(`${this.baseURL}/documents/${documentId}/summarize`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Summarization failed');
    }

    const data: SummaryResponse = await response.json();
    return data.data;
  }

  // Generate questions
  async generateQuestions(documentId: number): Promise<QuestionsResponse['data']> {
    const response = await fetch(`${this.baseURL}/documents/${documentId}/questions`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Question generation failed');
    }

    const data: QuestionsResponse = await response.json();
    return data.data;
  }
}

// Export singleton instance
export const docMindAPI = new DocMindAPI();

// Export types for use in components
export type {
  ChatRequest,
  UploadResponse,
  Document,
  DocumentsResponse,
  ChatResponse,
  SummaryResponse,
  QuestionsResponse,
  HealthResponse,
};