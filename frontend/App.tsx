import { useState } from "react";
import { ChatInterface } from "./components/ChatInterface";
import { Header } from "./components/Header";
import { Sidebar } from "./components/Sidebar";
import { TestimonialsPage } from "./components/TestimonialsPage";
import { Toaster } from "@/components/ui/toaster";

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState<"chat" | "testimonials">("chat");

  const handleLogoClick = () => {
    setCurrentPage("chat");
  };

  const handleNavigateToTestimonials = () => {
    setCurrentPage("testimonials");
    setSidebarOpen(false);
  };

  const handleNavigateToChat = () => {
    setCurrentPage("chat");
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)}
        onNavigateToTestimonials={handleNavigateToTestimonials}
        onNavigateToChat={handleNavigateToChat}
        currentPage={currentPage}
      />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header 
          onMenuClick={() => setSidebarOpen(true)} 
          onLogoClick={handleLogoClick}
          onNavigateToTestimonials={handleNavigateToTestimonials}
          onNavigateToChat={handleNavigateToChat}
          currentPage={currentPage}
        />
        
        <main className="flex-1 overflow-hidden">
          {currentPage === "chat" ? (
            <ChatInterface />
          ) : (
            <TestimonialsPage />
          )}
        </main>
      </div>
      
      <Toaster />
    </div>
  );
}
