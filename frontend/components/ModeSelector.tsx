import React, { useState } from 'react';
import { Zap, Settings, ArrowRight, HelpCircle, CheckCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigation, AppMode } from './AppShell';

interface ModeSelectorProps {
  onModeSelect?: (mode: AppMode) => void;
  showOnboarding?: boolean;
  className?: string;
}

interface ModeOption {
  mode: AppMode;
  title: string;
  subtitle: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  features: string[];
  bestFor: string[];
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  estimatedTime: string;
  color: {
    bg: string;
    icon: string;
    button: string;
    buttonHover: string;
  };
}

const modeOptions: ModeOption[] = [
  {
    mode: 'quick',
    title: 'Quick Generate',
    subtitle: 'Fast & Simple',
    icon: Zap,
    description: 'Generate TypeScript/Node.js MCP servers instantly with AI assistance. Perfect for learning, prototyping, and getting started quickly.',
    features: [
      'AI-powered chat interface',
      'Instant TypeScript/Node.js generation',
      'Built-in templates and examples',
      'Immediate download and preview',
      'No configuration required'
    ],
    bestFor: [
      'Learning MCP development',
      'Rapid prototyping',
      'Simple use cases',
      'Getting started quickly'
    ],
    difficulty: 'Beginner',
    estimatedTime: '2-5 minutes',
    color: {
      bg: 'bg-yellow-50 dark:bg-yellow-900/10',
      icon: 'text-yellow-600 dark:text-yellow-400',
      button: 'bg-yellow-600 hover:bg-yellow-700',
      buttonHover: 'hover:bg-yellow-50 dark:hover:bg-yellow-900/20'
    }
  },
  {
    mode: 'advanced',
    title: 'Advanced Build',
    subtitle: 'Production Ready',
    icon: Settings,
    description: 'Build comprehensive, production-ready MCP servers with multi-language support, advanced configurations, and deployment options.',
    features: [
      'Multi-language support (Python, TypeScript, Go, Rust, Java)',
      'Production deployment configurations',
      'Comprehensive testing and validation',
      'Custom templates and frameworks',
      'Docker, Kubernetes, and cloud integration'
    ],
    bestFor: [
      'Production deployments',
      'Complex integrations',
      'Team collaboration',
      'Enterprise requirements'
    ],
    difficulty: 'Advanced',
    estimatedTime: '15-30 minutes',
    color: {
      bg: 'bg-blue-50 dark:bg-blue-900/10',
      icon: 'text-blue-600 dark:text-blue-400',
      button: 'bg-blue-600 hover:bg-blue-700',
      buttonHover: 'hover:bg-blue-50 dark:hover:bg-blue-900/20'
    }
  }
];

export const ModeSelector: React.FC<ModeSelectorProps> = ({ 
  onModeSelect, 
  showOnboarding = false,
  className = '' 
}) => {
  const { setMode, setPage, userPreferences, updatePreferences } = useNavigation();
  const [selectedMode, setSelectedMode] = useState<AppMode | null>(null);
  const [showDetails, setShowDetails] = useState<AppMode | null>(null);
  const [showOnboardingDialog, setShowOnboardingDialog] = useState(showOnboarding);

  const handleModeSelect = (mode: AppMode) => {
    setSelectedMode(mode);
    setMode(mode);
    
    if (onModeSelect) {
      onModeSelect(mode);
    } else {
      // Navigate to appropriate interface based on mode
      if (mode === 'advanced') {
        setPage('advanced-build');
      } else {
        setPage('chat');
      }
    }
  };

  const handleShowDetails = (mode: AppMode) => {
    setShowDetails(showDetails === mode ? null : mode);
  };

  const dismissOnboarding = () => {
    setShowOnboardingDialog(false);
    updatePreferences({ showOnboarding: false });
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Beginner':
        return 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/20';
      case 'Intermediate':
        return 'text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/20';
      case 'Advanced':
        return 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/20';
      default:
        return 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-900/20';
    }
  };

  return (
    <div className={`w-full max-w-6xl mx-auto ${className}`}>
      {/* Onboarding Dialog */}
      {showOnboardingDialog && (
        <div className="mb-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-6 text-white relative">
          <button
            onClick={dismissOnboarding}
            className="absolute top-4 right-4 text-white/80 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
          <div className="flex items-start space-x-4">
            <div className="p-2 bg-white/20 rounded-lg">
              <HelpCircle className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-xl font-bold mb-2">
                Welcome to MCP Development! 👋
              </h3>
              <p className="text-white/90 mb-4">
                Choose your approach based on your experience level and project requirements. 
                You can always switch between modes later.
              </p>
              <div className="flex items-center space-x-4 text-sm">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4" />
                  <span>New to MCP? Start with Quick Generate</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4" />
                  <span>Need production features? Use Advanced Build</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Mode Selection Cards */}
      <div className="grid md:grid-cols-2 gap-8">
        {modeOptions.map((option) => (
          <div
            key={option.mode}
            className={`
              ${option.color.bg} 
              rounded-xl border-2 transition-all duration-300 cursor-pointer
              ${selectedMode === option.mode 
                ? 'border-current shadow-lg scale-105' 
                : 'border-transparent hover:border-gray-200 dark:hover:border-gray-600 hover:shadow-md'
              }
            `}
            onClick={() => setSelectedMode(option.mode)}
          >
            <div className="p-8">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-4">
                  <div className={`p-3 bg-white dark:bg-gray-800 rounded-lg shadow-sm`}>
                    <option.icon className={`h-8 w-8 ${option.color.icon}`} />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                      {option.title}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400">
                      {option.subtitle}
                    </p>
                  </div>
                </div>
                <div className={`px-3 py-1 rounded-full text-xs font-medium ${getDifficultyColor(option.difficulty)}`}>
                  {option.difficulty}
                </div>
              </div>

              {/* Description */}
              <p className="text-gray-700 dark:text-gray-300 mb-6">
                {option.description}
              </p>

              {/* Quick Features */}
              <div className="space-y-2 mb-6">
                {option.features.slice(0, 3).map((feature, index) => (
                  <div key={index} className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span>{feature}</span>
                  </div>
                ))}
              </div>

              {/* Estimated Time */}
              <div className="flex items-center justify-between mb-6">
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Estimated time: <span className="font-medium">{option.estimatedTime}</span>
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleShowDetails(option.mode);
                  }}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center space-x-1"
                >
                  <span>More details</span>
                  <ArrowRight className="h-3 w-3" />
                </button>
              </div>

              {/* Action Button */}
              <Button
                onClick={(e) => {
                  e.stopPropagation();
                  handleModeSelect(option.mode);
                }}
                className={`w-full ${option.color.button} text-white`}
                size="lg"
              >
                Start {option.title}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>

              {/* Detailed Information (Expandable) */}
              {showDetails === option.mode && (
                <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-600">
                  <div className="grid md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">
                        All Features
                      </h4>
                      <ul className="space-y-2">
                        {option.features.map((feature, index) => (
                          <li key={index} className="flex items-start space-x-2 text-sm text-gray-600 dark:text-gray-400">
                            <CheckCircle className="h-4 w-4 text-green-500 mt-0.5" />
                            <span>{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">
                        Best For
                      </h4>
                      <ul className="space-y-2">
                        {option.bestFor.map((use, index) => (
                          <li key={index} className="flex items-start space-x-2 text-sm text-gray-600 dark:text-gray-400">
                            <ArrowRight className="h-4 w-4 text-blue-500 mt-0.5" />
                            <span>{use}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Progressive Disclosure Based on Experience Level */}
      {userPreferences.experienceLevel === 'beginner' && (
        <div className="mt-8 bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800 rounded-lg p-6">
          <div className="flex items-start space-x-3">
            <HelpCircle className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
            <div>
              <h4 className="font-semibold text-green-900 dark:text-green-100 mb-2">
                Recommendation for Beginners
              </h4>
              <p className="text-green-700 dark:text-green-300 text-sm mb-3">
                We recommend starting with <strong>Quick Generate</strong> to learn MCP concepts. 
                You can always upgrade to Advanced Build later when you need production features.
              </p>
              <Button
                size="sm"
                onClick={() => handleModeSelect('quick')}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                Start with Quick Generate
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Help Section */}
      <div className="mt-8 text-center">
        <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
          Need help choosing? Our AI assistant can guide you through the decision.
        </p>
        <Button
          variant="outline"
          onClick={() => {
            setPage('chat');
          }}
          className="text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-800 hover:bg-blue-50 dark:hover:bg-blue-900/20"
        >
          Ask AI Assistant
          <HelpCircle className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};