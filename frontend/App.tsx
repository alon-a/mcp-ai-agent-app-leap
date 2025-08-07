import { useState } from "react";
import { ChatInterface } from "./components/ChatInterface";
import { Header } from "./components/Header";
import { Sidebar } from "./components/Sidebar";

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogoClick = () => {
    // Navigate to home by reloading the page or resetting state
    window.location.reload();
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header 
          onMenuClick={() => setSidebarOpen(true)} 
          onLogoClick={handleLogoClick}
        />
        
        <main className="flex-1 overflow-hidden">
          <ChatInterface />
        </main>
      </div>
    </div>
  );
}
