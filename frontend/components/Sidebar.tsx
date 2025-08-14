import { X, FileCode, Server, Zap, Book, Github, MessageSquare, Star, FolderOpen, FileTemplate, Home, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { AppMode, AppPage } from "./AppShell";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  currentPage: AppPage;
  currentMode: AppMode;
  onNavigate: (page: AppPage) => void;
  onModeChange: (mode: AppMode) => void;
}

export function Sidebar({ isOpen, onClose, currentPage, currentMode, onNavigate, onModeChange }: SidebarProps) {
  const resources = [
    {
      title: "MCP Documentation",
      url: "https://docs.anthropic.com/en/docs/mcp",
      icon: Book,
      description: "Official MCP documentation"
    },
    {
      title: "MCP SDK",
      url: "https://github.com/modelcontextprotocol/typescript-sdk",
      icon: Github,
      description: "TypeScript SDK for MCP"
    },
    {
      title: "Example Servers",
      url: "https://github.com/modelcontextprotocol/servers",
      icon: Server,
      description: "Collection of example MCP servers"
    }
  ];

  const examples = [
    {
      title: "File System Server",
      description: "Access and manipulate files"
    },
    {
      title: "Database Server", 
      description: "Query and update databases"
    },
    {
      title: "API Integration Server",
      description: "Connect to external APIs"
    },
    {
      title: "Git Repository Server",
      description: "Interact with Git repositories"
    }
  ];

  const navigationItems = [
    {
      title: "Home",
      icon: Home,
      page: "home" as AppPage,
      description: "Mode selection and overview"
    },
    {
      title: "Generate Server",
      icon: MessageSquare,
      page: "chat" as AppPage,
      description: "AI-powered server generation"
    },
    {
      title: "My Projects",
      icon: FolderOpen,
      page: "projects" as AppPage,
      description: "Manage your MCP projects"
    },
    {
      title: "Templates",
      icon: FileTemplate,
      page: "templates" as AppPage,
      description: "Browse and manage templates"
    },
    {
      title: "Testimonials",
      icon: Star,
      page: "testimonials" as AppPage,
      description: "User success stories"
    }
  ];

  const modeOptions = [
    {
      mode: "quick" as AppMode,
      title: "Quick Generate",
      icon: Zap,
      description: "Fast TypeScript/Node.js generation"
    },
    {
      mode: "advanced" as AppMode,
      title: "Advanced Build",
      icon: Settings,
      description: "Production-ready multi-language"
    }
  ];

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <div className={cn(
        "fixed inset-y-0 left-0 z-50 w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Navigation</h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="lg:hidden"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
          
          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
            {/* Mode Selection */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">Mode</h3>
              <div className="space-y-2">
                {modeOptions.map((option) => (
                  <button
                    key={option.mode}
                    onClick={() => onModeChange(option.mode)}
                    className={cn(
                      "flex items-start space-x-3 p-3 rounded-lg transition-colors w-full text-left",
                      currentMode === option.mode
                        ? "bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300" 
                        : "hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
                    )}
                  >
                    <option.icon className={cn(
                      "h-5 w-5 mt-0.5",
                      currentMode === option.mode ? "text-blue-600 dark:text-blue-400" : "text-gray-400"
                    )} />
                    <div>
                      <div className="text-sm font-medium">
                        {option.title}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {option.description}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Navigation */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">Navigation</h3>
              <div className="space-y-2">
                {navigationItems.map((item) => (
                  <button
                    key={item.page}
                    onClick={() => {
                      onNavigate(item.page);
                      onClose();
                    }}
                    className={cn(
                      "flex items-start space-x-3 p-3 rounded-lg transition-colors w-full text-left",
                      currentPage === item.page
                        ? "bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300" 
                        : "hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
                    )}
                  >
                    <item.icon className={cn(
                      "h-5 w-5 mt-0.5",
                      currentPage === item.page ? "text-blue-600 dark:text-blue-400" : "text-gray-400"
                    )} />
                    <div>
                      <div className="text-sm font-medium">
                        {item.title}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {item.description}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Documentation Links */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">Documentation</h3>
              <div className="space-y-2">
                {resources.map((resource, index) => (
                  <a
                    key={index}
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <resource.icon className="h-5 w-5 text-gray-400 mt-0.5" />
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {resource.title}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {resource.description}
                      </div>
                    </div>
                  </a>
                ))}
              </div>
            </div>
            
            {/* Example Use Cases */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">Common Examples</h3>
              <div className="space-y-2">
                {examples.map((example, index) => (
                  <div
                    key={index}
                    className="flex items-start space-x-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-700"
                  >
                    <FileCode className="h-5 w-5 text-blue-500 dark:text-blue-400 mt-0.5" />
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {example.title}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {example.description}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Quick Tips */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">Quick Tips</h3>
              <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <div className="flex items-start space-x-2">
                  <Zap className="h-4 w-4 text-yellow-500 mt-0.5" />
                  <span>Start with a simple file system server</span>
                </div>
                <div className="flex items-start space-x-2">
                  <Zap className="h-4 w-4 text-yellow-500 mt-0.5" />
                  <span>Use TypeScript for better type safety</span>
                </div>
                <div className="flex items-start space-x-2">
                  <Zap className="h-4 w-4 text-yellow-500 mt-0.5" />
                  <span>Test with Claude Desktop integration</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
