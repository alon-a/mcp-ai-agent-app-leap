import { Menu, Bot } from "lucide-react";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  onMenuClick: () => void;
  onLogoClick?: () => void;
}

export function Header({ onMenuClick, onLogoClick }: HeaderProps) {
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
        
        <div className="text-sm text-gray-500">
          AI-powered MCP development helper
        </div>
      </div>
    </header>
  );
}
