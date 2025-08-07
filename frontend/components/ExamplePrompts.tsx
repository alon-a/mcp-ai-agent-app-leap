import { Button } from "@/components/ui/button";
import { FileCode, Database, Globe, GitBranch, Server } from "lucide-react";

interface ExamplePromptsProps {
  onSelectPrompt: (prompt: string) => void;
}

export function ExamplePrompts({ onSelectPrompt }: ExamplePromptsProps) {
  const examples = [
    {
      icon: FileCode,
      title: "File System Server",
      prompt: "Help me create an MCP server that can read and write files from a specific directory. I want to be able to list files, read file contents, and create new files."
    },
    {
      icon: Database,
      title: "Database Integration",
      prompt: "I need to build an MCP server that connects to a PostgreSQL database. It should allow querying tables and executing safe read operations."
    },
    {
      icon: Globe,
      title: "REST API Server",
      prompt: "Show me how to create an MCP server that acts as a proxy to a REST API. I want to make HTTP requests and return the responses to the MCP client."
    },
    {
      icon: GitBranch,
      title: "Git Repository Access",
      prompt: "I want to create an MCP server that can interact with Git repositories - reading file contents, getting commit history, and checking branch information."
    },
    {
      icon: Server,
      title: "MCP Client Development",
      prompt: "How do I build an MCP client that can connect to multiple servers and provide a command-line interface for interacting with them?"
    }
  ];

  return (
    <div className="w-full max-w-2xl">
      <h3 className="text-lg font-medium text-gray-900 mb-4 text-center">
        Try these examples to get started:
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {examples.map((example, index) => (
          <Button
            key={index}
            variant="outline"
            className="h-auto p-4 text-left justify-start"
            onClick={() => onSelectPrompt(example.prompt)}
          >
            <div className="flex items-start space-x-3">
              <example.icon className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div>
                <div className="font-medium text-gray-900 mb-1">
                  {example.title}
                </div>
                <div className="text-sm text-gray-600 line-clamp-2">
                  {example.prompt.substring(0, 80)}...
                </div>
              </div>
            </div>
          </Button>
        ))}
      </div>
    </div>
  );
}
