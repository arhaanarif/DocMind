import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload, FileText, Loader2 } from "lucide-react";

interface PDFUploadProps {
  onUpload: (file: File) => void;
  isProcessing: boolean;
}

const PDFUpload = ({ onUpload, isProcessing }: PDFUploadProps) => {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === "application/pdf") {
        onUpload(file);
      } else {
        alert("Please upload a PDF file");
      }
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (file.type === "application/pdf") {
        onUpload(file);
      } else {
        alert("Please upload a PDF file");
      }
    }
  };

  return (
    <Card className="shadow-card">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Upload className="h-5 w-5 text-primary" />
          <span>Upload Research Paper</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div
          className={`
            border-2 border-dashed rounded-lg p-8 text-center transition-colors
            ${dragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'}
            ${isProcessing ? 'opacity-50 pointer-events-none' : 'hover:border-primary hover:bg-primary/5'}
          `}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {isProcessing ? (
            <div className="flex flex-col items-center space-y-4">
              <Loader2 className="h-12 w-12 animate-spin text-primary" />
              <div>
                <h3 className="text-lg font-semibold text-foreground">Processing Document</h3>
                <p className="text-muted-foreground">Please wait while we analyze your PDF...</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <FileText className="h-12 w-12 text-muted-foreground mx-auto" />
              <div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  Drop your PDF here or click to browse
                </h3>
                <p className="text-muted-foreground mb-4">
                  Upload research papers, articles, or any PDF document for AI-powered analysis
                </p>
              </div>
              
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileInput}
                className="hidden"
                id="pdf-upload"
                disabled={isProcessing}
              />
              
              <label htmlFor="pdf-upload">
                <Button className="cursor-pointer" disabled={isProcessing}>
                  <Upload className="h-4 w-4 mr-2" />
                  Choose PDF File
                </Button>
              </label>
              
              <p className="text-xs text-muted-foreground">
                Supported format: PDF (max 10MB)
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default PDFUpload;