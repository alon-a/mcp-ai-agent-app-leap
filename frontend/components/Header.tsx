import { Menu, Bot, MessageSquare, Star, FolderOpen, FileTemplate, Zap, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AppMode, AppPage } from "./AppShell";

interface HeaderProps {
  onMenuClick: () => void;
  currentPage: AppPage;
  currentMode: AppMode;
  onNavigate: (page: AppPage) => void;
  onModeChange: (mode: AppMode) => void;
}

export function Header({ onMenuClick, currentPage, currentMode, onNavigate, onModeChange }: HeaderProps) {
  const handleLogoClick = () => {
    onNavigate('home');
  };

  const getModeIcon = (mode: AppMode) => {
    return mode === 'quick' ? <Zap className="h-4 w-4" /> : <Settings className="h-4 w-4" />;
  };

  const getModeLabel = (mode: AppMode) => {
    return mode === 'quick' ? 'Quick' : 'Advanced';
  };

  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
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
            onClick={handleLogoClick}
            className="flex items-center space-x-2 hover:opacity-80 transition-opacity cursor-pointer"
          >
            <Bot className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              MCP Unified Interface
            </h1>
          </button>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Mode Indicator */}
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-full">
            {getModeIcon(currentMode)}
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {getModeLabel(currentMode)} Mode
            </span>
          </div>

          <nav className="hidden md:flex items-center space-x-2">
            <Button
              variant={currentPage === "chat" ? "default" : "ghost"}
              size="sm"
              onClick={() => onNavigate("chat")}
              className="flex items-center space-x-2"
            >
              <MessageSquare className="h-4 w-4" />
              <span>Generate</span>
            </Button>
            <Button
              variant={currentPage === "projects" ? "default" : "ghost"}
              size="sm"
              onClick={() => onNavigate("projects")}
              className="flex items-center space-x-2"
            >
              <FolderOpen className="h-4 w-4" />
              <span>Projects</span>
            </Button>
            <Button
              variant={currentPage === "templates" ? "default" : "ghost"}
              size="sm"
              onClick={() => onNavigate("templates")}
              className="flex items-center space-x-2"
            >
              <FileTemplate className="h-4 w-4" />
              <span>Templates</span>
            </Button>
            <Button
              variant={currentPage === "testimonials" ? "default" : "ghost"}
              size="sm"
              onClick={() => onNavigate("testimonials")}
              className="flex items-center space-x-2"
            >
              <Star className="h-4 w-4" />
              <span>Testimonials</span>
            </Button>
          </nav>
          
          <div className="hidden lg:block text-sm text-gray-500 dark:text-gray-400">
            Unified MCP development platform
          </div>
        </div>
      </div>
    </header>
  );
}
