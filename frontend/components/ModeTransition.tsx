import React, { useState, useEffect } from 'react';
import { Zap, Settings, ArrowRight, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AppMode } from './AppShell';

interface ModeTransitionProps {
  fromMode: AppMode;
  toMode: AppMode;
  onComplete: () => void;
  onCancel: () => void;
}

export const ModeTransition: React.FC<ModeTransitionProps> = ({
  fromMode,
  toMode,
  onComplete,
  onCancel
}) => {
  const [step, setStep] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);

  const getModeInfo = (mode: AppMode) => {
    return mode === 'quick' 
      ? {
          title: 'Quick Generate',
          icon: Zap,
          color: 'text-yellow-600 dark:text-yellow-400',
          bg: 'bg-yellow-50 dark:bg-yellow-900/10',
          features: ['Fast generation', 'TypeScript/Node.js', 'Immediate results']
        }
      : {
          title: 'Advanced Build',
          icon: Settings,
          color: 'text-blue-600 dark:text-blue-400',
          bg: 'bg-blue-50 dark:bg-blue-900/10',
          features: ['Multi-language', 'Production ready', 'Advanced configs']
        };
  };

  const fromModeInfo = getModeInfo(fromMode);
  const toModeInfo = getModeInfo(toMode);

  const transitionSteps = [
    {
      title: 'Switching Modes',
      description: `Transitioning from ${fromModeInfo.title} to ${toModeInfo.title}`,
      duration: 1000
    },
    {
      title: 'Preparing Interface',
      description: 'Setting up the new interface components',
      duration: 800
    },
    {
      title: 'Loading Features',
      description: `Enabling ${toModeInfo.title} features`,
      duration: 600
    }
  ];

  useEffect(() => {
    if (isTransitioning) {
      const timer = setTimeout(() => {
        if (step < transitionSteps.length - 1) {
          setStep(step + 1);
        } else {
          setTimeout(onComplete, 500);
        }
      }, transitionSteps[step].duration);

      return () => clearTimeout(timer);
    }
  }, [step, isTransitioning, onComplete]);

  const handleStartTransition = () => {
    setIsTransitioning(true);
  };

  if (!isTransitioning) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-8 max-w-2xl mx-4">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6 text-center">
            Switch to {toModeInfo.title}?
          </h2>
          
          <div className="grid md:grid-cols-2 gap-6 mb-8">
            {/* From Mode */}
            <div className={`${fromModeInfo.bg} rounded-lg p-4 opacity-60`}>
              <div className="flex items-center space-x-3 mb-3">
                <fromModeInfo.icon className={`h-6 w-6 ${fromModeInfo.color}`} />
                <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                  Current: {fromModeInfo.title}
                </h3>
              </div>
              <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                {fromModeInfo.features.map((feature, index) => (
                  <li key={index} className="flex items-center space-x-2">
                    <CheckCircle className="h-3 w-3" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* To Mode */}
            <div className={`${toModeInfo.bg} rounded-lg p-4 border-2 border-current`}>
              <div className="flex items-center space-x-3 mb-3">
                <toModeInfo.icon className={`h-6 w-6 ${toModeInfo.color}`} />
                <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                  Switch to: {toModeInfo.title}
                </h3>
              </div>
              <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                {toModeInfo.features.map((feature, index) => (
                  <li key={index} className="flex items-center space-x-2">
                    <CheckCircle className="h-3 w-3" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="text-center">
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Your current work will be preserved. You can switch back at any time.
            </p>
            
            <div className="flex justify-center space-x-4">
              <Button
                variant="outline"
                onClick={onCancel}
              >
                Cancel
              </Button>
              <Button
                onClick={handleStartTransition}
                className={toMode === 'quick' ? 'bg-yellow-600 hover:bg-yellow-700' : 'bg-blue-600 hover:bg-blue-700'}
              >
                Switch to {toModeInfo.title}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-8 max-w-md mx-4">
        <div className="text-center">
          <div className="mb-6">
            <toModeInfo.icon className={`h-16 w-16 ${toModeInfo.color} mx-auto animate-spin`} />
          </div>
          
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            {transitionSteps[step].title}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            {transitionSteps[step].description}
          </p>
          
          {/* Progress Bar */}
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-4">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                toMode === 'quick' ? 'bg-yellow-600' : 'bg-blue-600'
              }`}
              style={{ width: `${((step + 1) / transitionSteps.length) * 100}%` }}
            />
          </div>
          
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Step {step + 1} of {transitionSteps.length}
          </div>
        </div>
      </div>
    </div>
  );
};