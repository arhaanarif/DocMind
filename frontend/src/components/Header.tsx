import { Brain } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

const Header = () => {
  const location = useLocation();

  const navItems = [
    { path: "/", label: "Home" },
    { path: "/about", label: "About" },
    { path: "/source", label: "Source" }
  ];

  return (
    <header className="bg-gradient-to-r from-green-500 to-green-400 shadow-lg">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-3 hover:opacity-90 transition-opacity">
            <Brain className="h-8 w-8 text-white" />
            <div>
              <h1 className="text-3xl font-bold text-white">
                DocMind-AI
              </h1>
              <p className="text-white/90 text-sm mt-1">
                Intelligent Document Analysis
              </p>
            </div>
          </Link>
          
          <nav className="hidden md:flex items-center space-x-6">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-4 py-2 rounded-lg transition-all duration-300 ${
                  location.pathname === item.path
                    ? "bg-white/20 text-white font-medium"
                    : "text-white/80 hover:text-white hover:bg-white/10"
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;