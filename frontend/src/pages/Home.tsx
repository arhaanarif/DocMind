import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Layout from "@/components/Layout";
import PDFUpload from "@/components/PDFUpload";
import MetadataCard from "@/components/MetadataCard";
import SummaryCard from "@/components/SummaryCard";
import ChatInterface from "@/components/ChatInterface";
import { Loader2, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { docMindAPI, type Document, type SummaryResponse } from "@/services/api";

interface ProcessedData {
  metadata: {
    title: string;
    authors: string[];
    publicationDate?: string;
    pages: number;
    keywords?: string[];
    abstract?: string;
  };
  summary: string;
  suggestedQuestions: string[];
}

const Home = () => {
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [processedData, setProcessedData] = useState<ProcessedData | null>(null);
  const [selectedQuestion, setSelectedQuestion] = useState<string>("");
  const queryClient = useQueryClient();

  // Health check query
  const { data: healthData, isError: healthError } = useQuery({
    queryKey: ['health'],
    queryFn: () => docMindAPI.healthCheck(),
    refetchInterval: 30000,
    retry: 3,
    staleTime: 10000,
  });

  // Documents query
  const { data: documentsData, isLoading: documentsLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => docMindAPI.getDocuments(),
    enabled: healthData?.status === 'healthy',
    retry: 2,
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => docMindAPI.uploadPDF(file),
    onSuccess: (data) => {
      console.log('Upload successful:', data);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      
      setTimeout(() => {
        queryClient.refetchQueries({ queryKey: ['documents'] }).then(() => {
          setSelectedDocument({
            document_id: data.document_id,
            title: data.document_title,
            file_name: data.document_title,
            authors: '',
            page_count: 0,
            upload_timestamp: new Date().toISOString(),
          });
        });
      }, 1000);
    },
    onError: (error) => {
      console.error('Upload failed:', error);
    },
  });

  // Summary mutation
  const summaryMutation = useMutation({
    mutationFn: (documentId: number) => docMindAPI.summarizeDocument(documentId),
    onSuccess: (data) => {
      setProcessedData({
        metadata: {
          title: data.document_title,
          authors: selectedDocument?.authors ? [selectedDocument.authors] : [],
          pages: selectedDocument?.page_count || 0,
          publicationDate: selectedDocument?.upload_timestamp?.split('T')[0],
        },
        summary: data.summary,
        suggestedQuestions: [],
      });
      
      if (selectedDocument) {
        questionsMutation.mutate(selectedDocument.document_id);
      }
    },
    onError: (error) => {
      console.error('Summary generation failed:', error);
    },
  });

  // Questions mutation
  const questionsMutation = useMutation({
    mutationFn: (documentId: number) => docMindAPI.generateQuestions(documentId),
    onSuccess: (data) => {
      setProcessedData(prev => prev ? {
        ...prev,
        suggestedQuestions: data.questions
      } : null);
    },
    onError: (error) => {
      console.error('Questions generation failed:', error);
    },
  });

  const handleFileUpload = async (file: File) => {
    uploadMutation.mutate(file);
  };

  const handleDocumentSelect = (document: Document) => {
    setSelectedDocument(document);
    setProcessedData(null);
  };

  const handleGenerateSummary = () => {
    if (selectedDocument) {
      summaryMutation.mutate(selectedDocument.document_id);
    }
  };

  const handleSendMessage = async (message: string): Promise<string> => {
    try {
      const response = await docMindAPI.chat({
        question: message,
        document_id: selectedDocument?.document_id,
      });
      return response.answer;
    } catch (error) {
      console.error('Chat error:', error);
      return "Sorry, I encountered an error. Please try again.";
    }
  };

  const handleQuestionClick = (question: string) => {
    setSelectedQuestion(question);
  };

  // Show health error if API is down
  if (healthError) {
    return (
      <Layout>
        <div className="container mx-auto px-4 py-8">
          <Alert className="mb-8">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Unable to connect to the backend API. Please ensure the backend is running at http://localhost:8000.
            </AlertDescription>
          </Alert>
          
          <div className="mt-4 p-4 bg-muted rounded-lg">
            <h3 className="font-semibold mb-2">Troubleshooting Steps:</h3>
            <ol className="list-decimal list-inside space-y-1 text-sm text-muted-foreground">
              <li>Ensure the backend server is running: <code>python -m backend.api.main</code></li>
              <li>Check if the API is accessible at: <a href="http://localhost:8000" target="_blank" rel="noopener noreferrer" className="text-primary underline">http://localhost:8000</a></li>
              <li>Verify CORS settings in your FastAPI backend</li>
              <li>Check browser console for detailed error messages</li>
            </ol>
          </div>
        </div>
      </Layout>
    );
  }

  // Show loading if health check hasn't completed
  if (!healthData) {
    return (
      <Layout>
        <div className="container mx-auto px-4 py-8 flex items-center justify-center min-h-[60vh]">
          <div className="flex flex-col items-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <div className="text-center">
              <h3 className="font-semibold">Connecting to backend...</h3>
              <p className="text-sm text-muted-foreground">Please wait while we establish connection</p>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8 space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-foreground mb-4">
            DocMind Research Assistant
          </h1>
          <p className="text-xl text-muted-foreground">
            Upload, analyze, and interact with research papers using AI
          </p>
        </div>

        <div className="flex justify-center">
          <div className="flex items-center space-x-4 text-sm bg-muted/50 rounded-lg px-4 py-2">
            <div className="flex items-center space-x-1">
              <div className={`w-2 h-2 rounded-full ${
                healthData.components?.database?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
              }`} />
              <span>Database</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className={`w-2 h-2 rounded-full ${
                healthData.components?.pdf_processor?.system_status === 'operational' ? 'bg-green-500' : 'bg-red-500'
              }`} />
              <span>PDF Processor</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className={`w-2 h-2 rounded-full ${
                healthData.components?.rag_pipeline?.rag_pipeline === 'healthy' ? 'bg-green-500' : 'bg-red-500'
              }`} />
              <span>AI Pipeline</span>
            </div>
          </div>
        </div>

        <PDFUpload 
          onUpload={handleFileUpload}
          isProcessing={uploadMutation.isPending}
        />

        {documentsData?.documents && documentsData.documents.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold">Your Documents</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {documentsData.documents.map((doc) => (
                <div
                  key={doc.document_id}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedDocument?.document_id === doc.document_id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                  onClick={() => handleDocumentSelect(doc)}
                >
                  <h3 className="font-medium truncate">{doc.title}</h3>
                  <p className="text-sm text-muted-foreground">{doc.file_name}</p>
                  {doc.page_count && (
                    <p className="text-xs text-muted-foreground">{doc.page_count} pages</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedDocument && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold">
                Analyze: {selectedDocument.title}
              </h2>
              <button
                onClick={handleGenerateSummary}
                disabled={summaryMutation.isPending || questionsMutation.isPending}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {summaryMutation.isPending ? (
                  <div className="flex items-center space-x-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Analyzing...</span>
                  </div>
                ) : (
                  'Generate Summary'
                )}
              </button>
            </div>

            {processedData && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="space-y-6">
                  <MetadataCard metadata={processedData.metadata} />
                  <SummaryCard 
                    summary={[processedData.summary]}
                    suggestedQuestions={processedData.suggestedQuestions}
                    onQuestionClick={handleQuestionClick}
                  />
                </div>

                <div className="lg:sticky lg:top-8">
                  <ChatInterface 
                    onSendMessage={handleSendMessage}
                    initialMessage={selectedQuestion}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {documentsData?.documents && documentsData.documents.length === 0 && !uploadMutation.isPending && (
          <div className="text-center py-12">
            <div className="max-w-md mx-auto">
              <h3 className="text-lg font-semibold text-foreground mb-2">No documents yet</h3>
              <p className="text-muted-foreground mb-4">
                Upload your first research paper to get started with AI-powered analysis
              </p>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Home;