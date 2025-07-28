import Layout from "@/components/Layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Github, ExternalLink, Code, Database, Cpu, Globe } from "lucide-react";

const Source = () => {
  const repositories = [
    {
      name: "DocMind-AI Backend",
      description: "FastAPI backend with PostgreSQL, ChromaDB, and LLM integration",
      tech: ["Python", "FastAPI", "PostgreSQL", "ChromaDB", "LangChain"],
      url: "https://github.com/your-username/docmind-backend",
      icon: Database
    },
    {
      name: "DocMind-AI Frontend",
      description: "Modern React frontend with Tailwind CSS and TypeScript",
      tech: ["React", "TypeScript", "Tailwind", "React Query", "Vite"],
      url: "https://github.com/your-username/docmind-frontend",
      icon: Globe
    }
  ];

  const architecture = [
    {
      component: "API Gateway",
      description: "FastAPI serves as the main entry point for all client requests",
      icon: Code
    },
    {
      component: "Document Processing",
      description: "PyMuPDF extracts text and metadata from uploaded PDF files",
      icon: Database
    },
    {
      component: "Vector Storage",
      description: "ChromaDB stores document embeddings for semantic search",
      icon: Cpu
    },
    {
      component: "LLM Integration",
      description: "LangChain orchestrates calls to language models for analysis",
      icon: Globe
    }
  ];

  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-12">
        {/* Header */}
        <div className="text-center animate-fade-in">
          <h1 className="text-4xl font-bold text-foreground mb-4">
            Source Code & Architecture
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            DocMind-AI is built with modern, scalable technologies. Explore our open-source 
            codebase and learn about the architecture that powers intelligent research paper analysis.
          </p>
        </div>

        {/* Repositories */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-fade-in">
          {repositories.map((repo, index) => (
            <Card key={index} className="shadow-card hover:shadow-lg transition-all">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <repo.icon className="h-6 w-6 text-primary" />
                    <CardTitle className="text-xl">{repo.name}</CardTitle>
                  </div>
                  <Github className="h-5 w-5 text-muted-foreground" />
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">{repo.description}</p>
                
                <div className="flex flex-wrap gap-2">
                  {repo.tech.map((tech) => (
                    <Badge key={tech} variant="secondary">
                      {tech}
                    </Badge>
                  ))}
                </div>

                <a
                  href={repo.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-2 text-primary hover:text-primary-dark transition-colors"
                >
                  <span>View Repository</span>
                  <ExternalLink className="h-4 w-4" />
                </a>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Architecture Overview */}
        <Card className="shadow-card animate-fade-in">
          <CardHeader>
            <CardTitle className="text-2xl text-center">System Architecture</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {architecture.map((item, index) => (
                <div key={index} className="text-center space-y-3">
                  <div className="flex justify-center">
                    <div className="p-3 bg-primary-light rounded-full">
                      <item.icon className="h-6 w-6 text-primary" />
                    </div>
                  </div>
                  <h3 className="font-semibold text-foreground">{item.component}</h3>
                  <p className="text-sm text-muted-foreground">{item.description}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* API Endpoints */}
        <Card className="shadow-card animate-fade-in">
          <CardHeader>
            <CardTitle className="text-2xl">API Documentation</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="border-l-4 border-primary pl-4">
                <h3 className="font-semibold text-foreground">Backend Running</h3>
                <p className="text-muted-foreground">http://localhost:8000</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-muted/30 rounded-lg">
                  <div className="flex items-center space-x-2 mb-2">
                    <Badge variant="outline">POST</Badge>
                    <code className="text-sm">/api/upload</code>
                  </div>
                  <p className="text-sm text-muted-foreground">Upload and process PDF documents</p>
                </div>

                <div className="p-4 bg-muted/30 rounded-lg">
                  <div className="flex items-center space-x-2 mb-2">
                    <Badge variant="outline">POST</Badge>
                    <code className="text-sm">/api/chat</code>
                  </div>
                  <p className="text-sm text-muted-foreground">Send questions about uploaded papers</p>
                </div>

                <div className="p-4 bg-muted/30 rounded-lg">
                  <div className="flex items-center space-x-2 mb-2">
                    <Badge variant="outline">GET</Badge>
                    <code className="text-sm">/api/metadata/{`{id}`}</code>
                  </div>
                  <p className="text-sm text-muted-foreground">Retrieve document metadata</p>
                </div>

                <div className="p-4 bg-muted/30 rounded-lg">
                  <div className="flex items-center space-x-2 mb-2">
                    <Badge variant="outline">GET</Badge>
                    <code className="text-sm">/api/summary/{`{id}`}</code>
                  </div>
                  <p className="text-sm text-muted-foreground">Get AI-generated summary</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Contribution Guidelines */}
        <Card className="shadow-card animate-fade-in">
          <CardHeader>
            <CardTitle className="text-2xl">Contributing</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              We welcome contributions from the community! Here's how you can get involved:
            </p>
            
            <ol className="list-decimal list-inside space-y-2 text-muted-foreground">
              <li>Fork the repository on GitHub</li>
              <li>Create a feature branch for your changes</li>
              <li>Follow our coding standards and add tests</li>
              <li>Submit a pull request with a clear description</li>
              <li>Participate in the code review process</li>
            </ol>

            <div className="pt-4 border-t">
              <p className="text-sm text-muted-foreground">
                <strong>License:</strong> This project is licensed under the MIT License. 
                See the LICENSE file for details.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default Source;