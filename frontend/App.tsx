import React from "react";
import { AppShell, useNavigation } from "./components/AppShell";
import { ChatInterface } from "./components/ChatInterface";
import { TestimonialsPage } from "./components/TestimonialsPage";
import { HomePage } from "./components/HomePage";
import { ProjectsPage } from "./components/ProjectsPage";
import { TemplatesPage } from "./components/TemplatesPage";
import { AdvancedBuildInterface } from "./components/AdvancedBuildInterface";

function AppContent() {
  const { currentPage, currentMode } = useNavigation();

  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return <HomePage />;
      case 'chat':
        return <ChatInterface />;
      case 'advanced-build':
        return <AdvancedBuildInterface />;
      case 'projects':
        return <ProjectsPage />;
      case 'templates':
        return <TemplatesPage />;
      case 'testimonials':
        return <TestimonialsPage />;
      default:
        return <HomePage />;
    }
  };

  return renderPage();
}

export default function App() {
  return (
    <AppShell>
      <AppContent />
    </AppShell>
  );
}
