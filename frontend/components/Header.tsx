import { Menu, Bot, MessageSquare, Star } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  onMenuClick: () => void;
  onLogoClick?: () => void;
  onNavigateToTestimonials: () => void;
  onNavigateToChat: () => void;
  currentPage: "chat" | "testimonials";
}

export function Header({ onMenuClick, onLogoClick, onNavigateToTestimonials, onNavigateToChat, currentPage }: HeaderProps) {
  return (
    <header className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={onMenuClick}
            className="lg:hidden"
          >
            <Menu className="h-5 w-5" />
          </Button>
          
          <button
            onClick={onLogoClick}
            className="flex items-center space-x-2 hover:opacity-80 transition-opacity cursor-pointer"
          >
            <Bot className="h-6 w-6 text-blue-600" />
            <h1 className="text-xl font-semibold text-gray-900">
              MCP Assistant
            </h1>
          </button>
        </div>
        
        <div className="flex items-center space-x-4">
          <nav className="hidden md:flex items-center space-x-2">
            <Button
              variant={currentPage === "chat" ? "default" : "ghost"}
              size="sm"
              onClick={onNavigateToChat}
              className="flex items-center space-x-2"
            >
              <MessageSquare className="h-4 w-4" />
              <span>Chat</span>
            </Button>
            <Button
              variant={currentPage === "testimonials" ? "default" : "ghost"}
              size="sm"
              onClick={onNavigateToTestimonials}
              className="flex items-center space-x-2"
            >
              <Star className="h-4 w-4" />
              <span>Testimonials</span>
            </Button>
          </nav>
          
          <div className="text-sm text-gray-500">
            AI-powered MCP development helper
          </div>
        </div>
      </div>
    </header>
  );
}
