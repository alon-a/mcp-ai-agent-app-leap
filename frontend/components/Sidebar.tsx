import { X, FileCode, Server, Zap, Book, Github, MessageSquare, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigateToTestimonials: () => void;
  onNavigateToChat: () => void;
  currentPage: "chat" | "testimonials";
}

export function Sidebar({ isOpen, onClose, onNavigateToTestimonials, onNavigateToChat, currentPage }: SidebarProps) {
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
      title: "Chat Assistant",
      icon: MessageSquare,
      onClick: () => {
        onNavigateToChat();
        onClose();
      },
      isActive: currentPage === "chat"
    },
    {
      title: "Testimonials",
      icon: Star,
      onClick: () => {
        onNavigateToTestimonials();
        onClose();
      },
      isActive: currentPage === "testimonials"
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
        "fixed inset-y-0 left-0 z-50 w-80 bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Navigation</h2>
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
            {/* Navigation */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Pages</h3>
              <div className="space-y-2">
                {navigationItems.map((item, index) => (
                  <button
                    key={index}
                    onClick={item.onClick}
                    className={cn(
                      "flex items-start space-x-3 p-3 rounded-lg transition-colors w-full text-left",
                      item.isActive 
                        ? "bg-blue-50 text-blue-700" 
                        : "hover:bg-gray-50 text-gray-700"
                    )}
                  >
                    <item.icon className={cn(
                      "h-5 w-5 mt-0.5",
                      item.isActive ? "text-blue-600" : "text-gray-400"
                    )} />
                    <div>
                      <div className="text-sm font-medium">
                        {item.title}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Documentation Links */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Documentation</h3>
              <div className="space-y-2">
                {resources.map((resource, index) => (
                  <a
                    key={index}
                    href={resource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <resource.icon className="h-5 w-5 text-gray-400 mt-0.5" />
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {resource.title}
                      </div>
                      <div className="text-xs text-gray-500">
                        {resource.description}
                      </div>
                    </div>
                  </a>
                ))}
              </div>
            </div>
            
            {/* Example Use Cases */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Common Examples</h3>
              <div className="space-y-2">
                {examples.map((example, index) => (
                  <div
                    key={index}
                    className="flex items-start space-x-3 p-3 rounded-lg bg-gray-50"
                  >
                    <FileCode className="h-5 w-5 text-blue-500 mt-0.5" />
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {example.title}
                      </div>
                      <div className="text-xs text-gray-500">
                        {example.description}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Quick Tips */}
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Quick Tips</h3>
              <div className="space-y-2 text-sm text-gray-600">
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
