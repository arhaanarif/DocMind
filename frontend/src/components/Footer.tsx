import { Github, ExternalLink } from "lucide-react";

const Footer = () => {
  const techStack = [
    "Python", "FastAPI", "OpenRouter", "LangChain", "LLM", "PostgreSQL", "ChromaDB"
  ];

  return (
    <footer className="bg-gradient-to-r from-green-500 to-green-400 mt-16">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <div className="flex flex-wrap justify-center gap-2 mb-4">
            {techStack.map((tech) => (
              <span
                key={tech}
                className="px-3 py-1 bg-white/20 text-white text-xs rounded-full"
              >
                {tech}
              </span>
            ))}
          </div>
          
          <div className="flex justify-center space-x-4 mb-4">
            <a
              href="https://github.com/arhaanarif/DocMind"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 text-white/90 hover:text-white transition-colors"
            >
              <Github className="h-5 w-5" />
              <span>GitHub Repository</span>
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
          
          <p className="text-white/80 text-sm">
            © 2025 DocMind-AI. Built by Arhaan Arif.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;