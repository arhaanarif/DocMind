import Layout from "@/components/Layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Brain, Zap, MessageSquare, Shield, Sparkles, Users } from "lucide-react";

const About = () => {
  const features = [
    {
      icon: Brain,
      title: "AI-Powered Analysis",
      description: "Advanced language models analyze your research papers to extract key insights and generate comprehensive summaries."
    },
    {
      icon: Zap,
      title: "Fast Processing",
      description: "Upload and analyze papers in seconds with our optimized backend built on FastAPI and ChromaDB vector search."
    },
    {
      icon: MessageSquare,
      title: "Interactive Chat",
      description: "Ask questions about your papers and get instant, contextual answers powered by natural language processing."
    },
    {
      icon: Shield,
      title: "Secure & Private",
      description: "Your documents are processed securely with enterprise-grade privacy and data protection standards."
    },
    {
      icon: Sparkles,
      title: "Smart Summaries",
      description: "Get bulleted summaries highlighting the most important findings, methods, and conclusions from your papers."
    },
    {
      icon: Users,
      title: "Research-Focused",
      description: "Built specifically for researchers, academics, and students who work with scientific literature daily."
    }
  ];

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-12">
        {/* Hero Section */}
        <div className="text-center animate-fade-in">
          <h1 className="text-4xl font-bold text-foreground mb-4">
            About DocMind-AI
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            DocMind-AI is an innovative research paper intelligence tool that streamlines the analysis 
            and interaction with academic literature using cutting-edge AI technology.
          </p>
        </div>

        {/* Mission Statement */}
        <Card className="shadow-card animate-fade-in">
          <CardHeader>
            <CardTitle className="text-2xl text-center">Our Mission</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-muted-foreground leading-relaxed">
              We believe that research should be accessible, efficient, and insightful. Our goal is to 
              empower researchers, academics, and students with AI-powered tools that make it easier to 
              understand, analyze, and extract value from scientific literature. By combining advanced 
              natural language processing with intuitive user interfaces, we're making research more 
              productive and discoveries more accessible.
            </p>
          </CardContent>
        </Card>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-fade-in">
          {features.map((feature, index) => (
            <Card key={index} className="shadow-card hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <feature.icon className="h-6 w-6 text-primary" />
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Technology Stack */}
        <Card className="shadow-card animate-fade-in">
          <CardHeader>
            <CardTitle className="text-2xl text-center">Technology Stack</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h3 className="font-semibold text-foreground mb-3">Backend</h3>
                <ul className="space-y-2 text-muted-foreground">
                  <li>• <strong>FastAPI</strong> - High-performance web framework</li>
                  <li>• <strong>PostgreSQL</strong> - Robust data storage</li>
                  <li>• <strong>ChromaDB</strong> - Vector database for semantic search</li>
                  <li>• <strong>PyMuPDF</strong> - PDF parsing and processing</li>
                  <li>• <strong>LangChain</strong> - LLM orchestration framework</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-foreground mb-3">Frontend</h3>
                <ul className="space-y-2 text-muted-foreground">
                  <li>• <strong>React</strong> - Modern UI framework</li>
                  <li>• <strong>TypeScript</strong> - Type-safe development</li>
                  <li>• <strong>Tailwind CSS</strong> - Utility-first styling</li>
                  <li>• <strong>React Query</strong> - Data fetching and caching</li>
                  <li>• <strong>React Router</strong> - Client-side routing</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Contact */}
        <Card className="shadow-card animate-fade-in">
          <CardHeader>
            <CardTitle className="text-2xl text-center">Get in Touch</CardTitle>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-muted-foreground mb-4">
              Have questions, feedback, or want to contribute? We'd love to hear from you!
            </p>
            <div className="flex justify-center space-x-4">
              <a 
                href="https://github.com/your-repo" 
                className="text-primary hover:text-primary-dark transition-colors"
              >
                GitHub Repository
              </a>
              <span className="text-muted-foreground">•</span>
              <a 
                href="mailto:contact@docmind-ai.com" 
                className="text-primary hover:text-primary-dark transition-colors"
              >
                Contact Us
              </a>
            </div>
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
};

export default About;