import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, Download, Server, Settings, ArrowUp, Save, History } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/components/ui/use-toast";
import backend from "~backend/client";
import type { ChatMessage } from "./types";
import { MessageBubble } from "./MessageBubble";
import { ExamplePrompts } from "./ExamplePrompts";
import { GenerateServerForm } from "./GenerateServerForm";
import { GenerateClientForm } from "./GenerateClientForm";
import { GeneratedFiles } from "./GeneratedFiles";
import { useNavigation } from "./AppShell";

type ViewMode = "chat" | "generate-server" | "generate-client" | "files";

interface ProjectFile {
  path: string;
  content: string;
}

export function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("chat");
  const [generatedFiles, setGeneratedFiles] = useState<ProjectFile[]>([]);
  const [setupInstructions, setSetupInstructions] = useState("");
  const [projectType, setProjectType] = useState<"server" | "client">("server");
  const [showUpgradePrompt, setShowUpgradePrompt] = useState(false);
  const [projectName, setProjectName] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  const { currentMode, setMode, setPage } = useNavigation();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (message?: string) => {
    const messageToSend = message || input.trim();
    if (!messageToSend || isLoading) return;

    const userMessage: ChatMessage = {
      role: "user",
      content: messageToSend
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await backend.ai.chat({
        messages: [...messages, userMessage]
      });

      setMessages(prev => [...prev, response.message]);
    } catch (error) {
      console.error("Chat error:", error);
      toast({
        title: "Error",
        description: "Failed to get response from AI assistant. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleGenerated = (files: ProjectFile[], instructions: string, type: "server" | "client" = "server") => {
    setGeneratedFiles(files);
    setSetupInstructions(instructions);
    setProjectType(type);
    setViewMode("files");
    
    // Show upgrade prompt after successful generation in quick mode
    if (currentMode === 'quick' && files.length > 0) {
      setTimeout(() => setShowUpgradePrompt(true), 2000);
    }
  };

  const handleSaveProject = () => {
    // TODO: Implement project saving functionality
    const name = projectName || `MCP ${projectType} - ${new Date().toLocaleDateString()}`;
    toast({
      title: "Project Saved",
      description: `"${name}" has been saved to your projects.`,
    });
    setPage('projects');
  };

  const handleUpgradeToAdvanced = () => {
    setMode('advanced');
    setShowUpgradePrompt(false);
    toast({
      title: "Upgraded to Advanced Mode",
      description: "You now have access to multi-language support, production configs, and more!",
    });
  };

  const handleBackToChat = () => {
    setViewMode("chat");
  };

  const handleBackToGenerateServer = () => {
    setViewMode("generate-server");
  };

  const handleBackToGenerateClient = () => {
    setViewMode("generate-client");
  };

  if (viewMode === "generate-server") {
    return (
      <div className="flex flex-col h-full">
        <div className="border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Generate MCP Server</h2>
            <Button variant="outline" onClick={handleBackToChat}>
              Back to Chat
            </Button>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6">
          <GenerateServerForm onGenerated={(files, instructions) => handleGenerated(files, instructions, "server")} />
        </div>
      </div>
    );
  }

  if (viewMode === "generate-client") {
    return (
      <div className="flex flex-col h-full">
        <div className="border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Generate MCP Client</h2>
            <Button variant="outline" onClick={handleBackToChat}>
              Back to Chat
            </Button>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6">
          <GenerateClientForm onGenerated={(files, instructions) => handleGenerated(files, instructions, "client")} />
        </div>
      </div>
    );
  }

  if (viewMode === "files") {
    return (
      <div className="flex flex-col h-full">
        <div className="border-b border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Generated Files</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {currentMode === 'quick' ? 'TypeScript/Node.js' : 'Multi-language'} MCP {projectType}
              </p>
            </div>
            <div className="flex space-x-2">
              {/* Save Project Button */}
              <Button 
                variant="outline" 
                onClick={() => {
                  const name = prompt("Enter project name:", `MCP ${projectType} - ${new Date().toLocaleDateString()}`);
                  if (name) {
                    setProjectName(name);
                    handleSaveProject();
                  }
                }}
                className="flex items-center space-x-2"
              >
                <Save className="h-4 w-4" />
                <span>Save Project</span>
              </Button>
              
              {/* View Projects Button */}
              <Button 
                variant="outline" 
                onClick={() => setPage('projects')}
                className="flex items-center space-x-2"
              >
                <History className="h-4 w-4" />
                <span>View Projects</span>
              </Button>
              
              {projectType === "server" ? (
                <Button variant="outline" onClick={handleBackToGenerateServer}>
                  Back to Server Generator
                </Button>
              ) : (
                <Button variant="outline" onClick={handleBackToGenerateClient}>
                  Back to Client Generator
                </Button>
              )}
              <Button variant="outline" onClick={handleBackToChat}>
                Back to Chat
              </Button>
            </div>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6 relative">
          <GeneratedFiles 
            files={generatedFiles}
            instructions={setupInstructions}
            onBack={projectType === "client" ? handleBackToGenerateClient : handleBackToGenerateServer}
            projectType={projectType}
          />
          
          {/* Upgrade Prompt Overlay */}
          {showUpgradePrompt && currentMode === 'quick' && (
            <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-10">
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-8 max-w-md mx-4">
                <div className="text-center">
                  <div className="p-3 bg-blue-100 dark:bg-blue-900/20 rounded-full w-fit mx-auto mb-4">
                    <ArrowUp className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                    Ready for More?
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-6">
                    Great job! Want to take your MCP server to the next level with production features, 
                    multi-language support, and advanced configurations?
                  </p>
                  
                  <div className="space-y-3">
                    <Button
                      onClick={handleUpgradeToAdvanced}
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      <Settings className="mr-2 h-4 w-4" />
                      Upgrade to Advanced Mode
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setShowUpgradePrompt(false)}
                      className="w-full"
                    >
                      Maybe Later
                    </Button>
                  </div>
                  
                  <div className="mt-4 text-xs text-gray-500 dark:text-gray-400">
                    You can always upgrade later from the sidebar
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header with Generate Buttons */}
      <div className="border-b border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              MCP Assistant Chat
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {currentMode === 'quick' ? 'Quick Generate Mode - TypeScript/Node.js' : 'Advanced Build Mode - Multi-language'}
            </p>
          </div>
          <div className="flex space-x-2">
            <Button onClick={() => setViewMode("generate-server")}>
              <Download className="h-4 w-4 mr-2" />
              Generate Server
            </Button>
            <Button variant="outline" onClick={() => setViewMode("generate-client")}>
              <Server className="h-4 w-4 mr-2" />
              Generate Client
            </Button>
            {currentMode === 'quick' && (
              <Button 
                variant="outline" 
                onClick={() => setMode('advanced')}
                className="text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-800"
              >
                <Settings className="h-4 w-4 mr-2" />
                Upgrade to Advanced
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full space-y-6">
            <div className="text-center">
              <Bot className="h-12 w-12 text-blue-600 dark:text-blue-400 mx-auto mb-4" />
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Welcome to MCP Assistant
              </h2>
              <p className="text-gray-600 dark:text-gray-400 max-w-md mb-4">
                I'm here to help you build MCP (Model Context Protocol) servers and clients. 
                Ask me anything about MCP development or use the generators to create boilerplate code!
              </p>
              
              {/* Mode-specific welcome message */}
              {currentMode === 'quick' ? (
                <div className="bg-yellow-50 dark:bg-yellow-900/10 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 max-w-md mx-auto mb-4">
                  <p className="text-yellow-800 dark:text-yellow-200 text-sm">
                    <strong>Quick Mode:</strong> Fast TypeScript/Node.js generation with immediate results. 
                    Perfect for learning and prototyping!
                  </p>
                </div>
              ) : (
                <div className="bg-blue-50 dark:bg-blue-900/10 border border-blue-200 dark:border-blue-800 rounded-lg p-4 max-w-md mx-auto mb-4">
                  <p className="text-blue-800 dark:text-blue-200 text-sm">
                    <strong>Advanced Mode:</strong> Production-ready builds with multi-language support, 
                    comprehensive validation, and deployment configurations.
                  </p>
                </div>
              )}
            </div>
            
            <ExamplePrompts onSelectPrompt={handleSend} />
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <MessageBubble key={index} message={message} />
            ))}
            
            {isLoading && (
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                    <Bot className="h-5 w-5 text-white" />
                  </div>
                </div>
                <div className="flex-1">
                  <div className="bg-gray-100 rounded-lg p-4">
                    <div className="flex items-center space-x-2">
                      <Loader2 className="h-4 w-4 animate-spin text-gray-500" />
                      <span className="text-gray-500">Thinking...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex space-x-3">
          <div className="flex-1">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me about MCP development..."
              className="min-h-[60px] resize-none"
              disabled={isLoading}
            />
          </div>
          <Button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            size="lg"
            className="px-6"
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
