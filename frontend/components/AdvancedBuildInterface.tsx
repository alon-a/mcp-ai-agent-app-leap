import React, { useState } from 'react';
import { ArrowLeft, Settings, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigation } from './AppShell';
import { AdvancedBuildWizard, UnifiedProjectConfig } from './AdvancedBuildWizard';
import { useToast } from '@/components/ui/use-toast';

export const AdvancedBuildInterface: React.FC = () => {
  const { setMode, setPage } = useNavigation();
  const { toast } = useToast();
  const [isBuilding, setIsBuilding] = useState(false);

  const handleConfigurationComplete = async (config: UnifiedProjectConfig) => {
    setIsBuilding(true);
    
    try {
      // TODO: Integrate with backend to start the advanced build process
      console.log('Starting advanced build with configuration:', config);
      
      // Simulate build process
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      toast({
        title: "Build Started",
        description: `Advanced build for "${config.basics.name}" has been initiated. You'll receive real-time progress updates.`,
      });
      
      // Navigate to projects page to show build progress
      setPage('projects');
      
    } catch (error) {
      console.error('Build failed:', error);
      toast({
        title: "Build Failed",
        description: "Failed to start the advanced build. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsBuilding(false);
    }
  };

  const handleCancel = () => {
    setPage('home');
  };

  const handleSwitchToQuick = () => {
    setMode('quick');
    setPage('chat');
  };

  return (
    <div className="flex-1 overflow-auto bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                onClick={handleCancel}
                className="flex items-center space-x-2"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Back to Home</span>
              </Button>
              
              <div className="h-6 w-px bg-gray-300 dark:bg-gray-600" />
              
              <Button
                variant="outline"
                onClick={handleSwitchToQuick}
                className="flex items-center space-x-2 text-yellow-600 dark:text-yellow-400 border-yellow-200 dark:border-yellow-800"
              >
                <Zap className="h-4 w-4" />
                <span>Switch to Quick Mode</span>
              </Button>
            </div>
            
            <div className="flex items-center space-x-2">
              <Settings className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Advanced Build Mode
              </span>
            </div>
          </div>
        </div>

        {/* Wizard */}
        <AdvancedBuildWizard
          onConfigurationComplete={handleConfigurationComplete}
          onCancel={handleCancel}
          className="mb-8"
        />
        
        {/* Loading State */}
        {isBuilding && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-8 max-w-md mx-4">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                  Starting Advanced Build
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Initializing your production-ready MCP server...
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};