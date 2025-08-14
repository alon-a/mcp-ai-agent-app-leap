import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, Download, Server } from "lucide-react";
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
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

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
        <div className="border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Generated Files</h2>
            <div className="flex space-x-2">
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
        
        <div className="flex-1 overflow-y-auto p-6">
          <GeneratedFiles 
            files={generatedFiles}
            instructions={setupInstructions}
            onBack={projectType === "client" ? handleBackToGenerateClient : handleBackToGenerateServer}
            projectType={projectType}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header with Generate Buttons */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">MCP Assistant Chat</h2>
          <div className="flex space-x-2">
            <Button onClick={() => setViewMode("generate-server")}>
              <Download className="h-4 w-4 mr-2" />
              Generate Server
            </Button>
            <Button variant="outline" onClick={() => setViewMode("generate-client")}>
              <Server className="h-4 w-4 mr-2" />
              Generate Client
            </Button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full space-y-6">
            <div className="text-center">
              <Bot className="h-12 w-12 text-blue-600 mx-auto mb-4" />
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                Welcome to MCP Assistant
              </h2>
              <p className="text-gray-600 max-w-md">
                I'm here to help you build MCP (Model Context Protocol) servers and clients. 
                Ask me anything about MCP development or use the generators to create boilerplate code!
              </p>
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
