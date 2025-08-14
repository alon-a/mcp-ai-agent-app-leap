import React from 'react';
import { Bot } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigation } from './AppShell';
import { ModeSelector } from './ModeSelector';

export const HomePage: React.FC = () => {
  const { setPage, userPreferences } = useNavigation();

  return (
    <div className="flex-1 overflow-auto bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="max-w-6xl mx-auto px-4 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="flex justify-center mb-6">
            <Bot className="h-16 w-16 text-blue-600 dark:text-blue-400" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            MCP Unified Interface
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-3xl mx-auto">
            Build powerful Model Context Protocol servers with AI assistance. 
            Choose between quick generation for rapid prototyping or advanced builds for production-ready solutions.
          </p>
        </div>

        {/* Mode Selection */}
        <div className="mb-16">
          <ModeSelector showOnboarding={userPreferences.showOnboarding} />
        </div>

        {/* Quick Actions */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 border border-gray-200 dark:border-gray-700">
          <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-6">
            Quick Actions
          </h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Button
              variant="outline"
              onClick={() => setPage('projects')}
              className="h-auto p-4 flex flex-col items-center space-y-2"
            >
              <span className="text-sm font-medium">View Projects</span>
              <span className="text-xs text-gray-500 dark:text-gray-400">Manage your builds</span>
            </Button>
            <Button
              variant="outline"
              onClick={() => setPage('templates')}
              className="h-auto p-4 flex flex-col items-center space-y-2"
            >
              <span className="text-sm font-medium">Browse Templates</span>
              <span className="text-xs text-gray-500 dark:text-gray-400">Explore examples</span>
            </Button>
            <Button
              variant="outline"
              onClick={() => setPage('testimonials')}
              className="h-auto p-4 flex flex-col items-center space-y-2"
            >
              <span className="text-sm font-medium">Success Stories</span>
              <span className="text-xs text-gray-500 dark:text-gray-400">User testimonials</span>
            </Button>
            <Button
              variant="outline"
              onClick={() => window.open('https://docs.anthropic.com/en/docs/mcp', '_blank')}
              className="h-auto p-4 flex flex-col items-center space-y-2"
            >
              <span className="text-sm font-medium">Documentation</span>
              <span className="text-xs text-gray-500 dark:text-gray-400">Learn about MCP</span>
            </Button>
          </div>
        </div>


      </div>
    </div>
  );
};