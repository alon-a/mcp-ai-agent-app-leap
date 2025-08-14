import React, { createContext, useContext, useState, useEffect } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { Breadcrumbs } from './Breadcrumbs';
import { ModeTransition } from './ModeTransition';
import { Toaster } from '@/components/ui/toaster';

// Application mode types
export type AppMode = 'quick' | 'advanced';
export type AppPage = 'home' | 'chat' | 'testimonials' | 'projects' | 'templates' | 'advanced-build';

// User preferences interface
interface UserPreferences {
  mode: AppMode;
  theme: 'light' | 'dark' | 'system';
  experienceLevel: 'beginner' | 'intermediate' | 'expert';
  showOnboarding: boolean;
}

// Navigation context interface
interface NavigationContextType {
  currentMode: AppMode;
  currentPage: AppPage;
  userPreferences: UserPreferences;
  breadcrumbs: BreadcrumbItem[];
  setMode: (mode: AppMode) => void;
  setPage: (page: AppPage) => void;
  updatePreferences: (preferences: Partial<UserPreferences>) => void;
  setBreadcrumbs: (breadcrumbs: BreadcrumbItem[]) => void;
}

// Breadcrumb item interface
export interface BreadcrumbItem {
  label: string;
  href?: string;
  onClick?: () => void;
  isActive?: boolean;
}

// Create navigation context
const NavigationContext = createContext<NavigationContextType | undefined>(undefined);

// Custom hook to use navigation context
export const useNavigation = () => {
  const context = useContext(NavigationContext);
  if (!context) {
    throw new Error('useNavigation must be used within NavigationProvider');
  }
  return context;
};

// Default user preferences
const defaultPreferences: UserPreferences = {
  mode: 'quick',
  theme: 'system',
  experienceLevel: 'beginner',
  showOnboarding: true,
};

// Session storage keys
const STORAGE_KEYS = {
  USER_PREFERENCES: 'mcp-unified-user-preferences',
  CURRENT_MODE: 'mcp-unified-current-mode',
  CURRENT_PAGE: 'mcp-unified-current-page',
};

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentMode, setCurrentMode] = useState<AppMode>('quick');
  const [currentPage, setCurrentPage] = useState<AppPage>('home');
  const [userPreferences, setUserPreferences] = useState<UserPreferences>(defaultPreferences);
  const [breadcrumbs, setBreadcrumbs] = useState<BreadcrumbItem[]>([]);
  const [pendingModeChange, setPendingModeChange] = useState<AppMode | null>(null);
  const [showModeTransition, setShowModeTransition] = useState(false);

  // Load preferences and state from session storage on mount
  useEffect(() => {
    const loadFromStorage = () => {
      try {
        const savedPreferences = sessionStorage.getItem(STORAGE_KEYS.USER_PREFERENCES);
        if (savedPreferences) {
          setUserPreferences({ ...defaultPreferences, ...JSON.parse(savedPreferences) });
        }

        const savedMode = sessionStorage.getItem(STORAGE_KEYS.CURRENT_MODE) as AppMode;
        if (savedMode) {
          setCurrentMode(savedMode);
        }

        const savedPage = sessionStorage.getItem(STORAGE_KEYS.CURRENT_PAGE) as AppPage;
        if (savedPage) {
          setCurrentPage(savedPage);
        }
      } catch (error) {
        console.warn('Failed to load preferences from storage:', error);
      }
    };

    loadFromStorage();
  }, []);

  // Save preferences and state to session storage when they change
  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEYS.USER_PREFERENCES, JSON.stringify(userPreferences));
    } catch (error) {
      console.warn('Failed to save preferences to storage:', error);
    }
  }, [userPreferences]);

  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEYS.CURRENT_MODE, currentMode);
    } catch (error) {
      console.warn('Failed to save mode to storage:', error);
    }
  }, [currentMode]);

  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEYS.CURRENT_PAGE, currentPage);
    } catch (error) {
      console.warn('Failed to save page to storage:', error);
    }
  }, [currentPage]);

  // Update breadcrumbs based on current page and mode
  useEffect(() => {
    const updateBreadcrumbs = () => {
      const baseBreadcrumbs: BreadcrumbItem[] = [
        { label: 'Home', onClick: () => setCurrentPage('home') }
      ];

      switch (currentPage) {
        case 'home':
          setBreadcrumbs([{ label: 'Home', isActive: true }]);
          break;
        case 'chat':
          setBreadcrumbs([
            ...baseBreadcrumbs,
            { label: currentMode === 'quick' ? 'Quick Generate' : 'Advanced Build', isActive: true }
          ]);
          break;
        case 'advanced-build':
          setBreadcrumbs([
            ...baseBreadcrumbs,
            { label: 'Advanced Build', isActive: true }
          ]);
          break;
        case 'projects':
          setBreadcrumbs([
            ...baseBreadcrumbs,
            { label: 'Projects', isActive: true }
          ]);
          break;
        case 'templates':
          setBreadcrumbs([
            ...baseBreadcrumbs,
            { label: 'Templates', isActive: true }
          ]);
          break;
        case 'testimonials':
          setBreadcrumbs([
            ...baseBreadcrumbs,
            { label: 'Testimonials', isActive: true }
          ]);
          break;
        default:
          setBreadcrumbs(baseBreadcrumbs);
      }
    };

    updateBreadcrumbs();
  }, [currentPage, currentMode]);

  const setMode = (mode: AppMode) => {
    if (mode !== currentMode) {
      // Show transition for mode changes (except initial load)
      if (currentPage !== 'home') {
        setPendingModeChange(mode);
        setShowModeTransition(true);
      } else {
        setCurrentMode(mode);
      }
    }
  };

  const handleModeTransitionComplete = () => {
    if (pendingModeChange) {
      setCurrentMode(pendingModeChange);
      setPendingModeChange(null);
    }
    setShowModeTransition(false);
  };

  const handleModeTransitionCancel = () => {
    setPendingModeChange(null);
    setShowModeTransition(false);
  };

  const setPage = (page: AppPage) => {
    setCurrentPage(page);
    setSidebarOpen(false); // Close sidebar when navigating
  };

  const updatePreferences = (preferences: Partial<UserPreferences>) => {
    setUserPreferences(prev => ({ ...prev, ...preferences }));
  };

  const navigationContextValue: NavigationContextType = {
    currentMode,
    currentPage,
    userPreferences,
    breadcrumbs,
    setMode,
    setPage,
    updatePreferences,
    setBreadcrumbs,
  };

  return (
    <NavigationContext.Provider value={navigationContextValue}>
      <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
        <Sidebar 
          isOpen={sidebarOpen} 
          onClose={() => setSidebarOpen(false)}
          currentPage={currentPage}
          currentMode={currentMode}
          onNavigate={setPage}
          onModeChange={setMode}
        />
        
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header 
            onMenuClick={() => setSidebarOpen(true)} 
            currentPage={currentPage}
            currentMode={currentMode}
            onNavigate={setPage}
            onModeChange={setMode}
          />
          
          {/* Breadcrumb Navigation */}
          {breadcrumbs.length > 1 && (
            <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
              <div className="px-4 py-2">
                <Breadcrumbs items={breadcrumbs} />
              </div>
            </div>
          )}
          
          <main className="flex-1 overflow-hidden">
            {children}
          </main>
        </div>
        
        {/* Mode Transition Overlay */}
        {showModeTransition && pendingModeChange && (
          <ModeTransition
            fromMode={currentMode}
            toMode={pendingModeChange}
            onComplete={handleModeTransitionComplete}
            onCancel={handleModeTransitionCancel}
          />
        )}
        
        <Toaster />
      </div>
    </NavigationContext.Provider>
  );
};