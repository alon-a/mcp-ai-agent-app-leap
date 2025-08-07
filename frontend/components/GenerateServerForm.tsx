import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FileCode, Database, Globe, GitBranch, Settings, Download, Loader2 } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import backend from "~backend/client";
import type { ServerType, GenerateServerRequest } from "~backend/ai/generate";

interface GenerateServerFormProps {
  onGenerated: (files: any[], instructions: string) => void;
}

export function GenerateServerForm({ onGenerated }: GenerateServerFormProps) {
  const [formData, setFormData] = useState<GenerateServerRequest>({
    serverType: "filesystem" as ServerType,
    projectName: "",
    description: "",
    features: [],
    customRequirements: "",
  });
  const [isGenerating, setIsGenerating] = useState(false);
  const { toast } = useToast();

  const serverTypes = [
    {
      value: "filesystem" as ServerType,
      label: "File System Server",
      description: "Read and write files within a secure directory",
      icon: FileCode,
    },
    {
      value: "database" as ServerType,
      label: "Database Server",
      description: "Query PostgreSQL databases safely",
      icon: Database,
    },
    {
      value: "api" as ServerType,
      label: "API Integration Server",
      description: "Proxy requests to external REST APIs",
      icon: Globe,
    },
    {
      value: "git" as ServerType,
      label: "Git Repository Server",
      description: "Browse Git repositories and history",
      icon: GitBranch,
    },
    {
      value: "custom" as ServerType,
      label: "Custom Server",
      description: "Start with a basic template for custom functionality",
      icon: Settings,
    },
  ];

  const selectedServerType = serverTypes.find(type => type.value === formData.serverType);

  const handleGenerate = async () => {
    if (!formData.projectName.trim()) {
      toast({
        title: "Error",
        description: "Project name is required",
        variant: "destructive",
      });
      return;
    }

    setIsGenerating(true);
    try {
      const response = await backend.ai.generate(formData);
      onGenerated(response.files, response.instructions);
      
      toast({
        title: "Success",
        description: "MCP server generated successfully!",
      });
    } catch (error) {
      console.error("Generation error:", error);
      toast({
        title: "Error",
        description: "Failed to generate MCP server. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Download className="h-5 w-5" />
          <span>Generate MCP Server</span>
        </CardTitle>
        <CardDescription>
          Create a complete MCP server project with boilerplate code, configuration, and documentation.
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Server Type Selection */}
        <div className="space-y-3">
          <Label htmlFor="serverType">Server Type</Label>
          <Select
            value={formData.serverType}
            onValueChange={(value: ServerType) => 
              setFormData(prev => ({ ...prev, serverType: value }))
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Select server type" />
            </SelectTrigger>
            <SelectContent>
              {serverTypes.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  <div className="flex items-center space-x-2">
                    <type.icon className="h-4 w-4" />
                    <span>{type.label}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          {selectedServerType && (
            <div className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
              <selectedServerType.icon className="h-5 w-5 text-blue-600 mt-0.5" />
              <div>
                <div className="font-medium text-blue-900">
                  {selectedServerType.label}
                </div>
                <div className="text-sm text-blue-700">
                  {selectedServerType.description}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Project Name */}
        <div className="space-y-2">
          <Label htmlFor="projectName">Project Name *</Label>
          <Input
            id="projectName"
            placeholder="my-mcp-server"
            value={formData.projectName}
            onChange={(e) => 
              setFormData(prev => ({ ...prev, projectName: e.target.value }))
            }
          />
        </div>

        {/* Description */}
        <div className="space-y-2">
          <Label htmlFor="description">Description</Label>
          <Textarea
            id="description"
            placeholder="Brief description of your MCP server..."
            value={formData.description}
            onChange={(e) => 
              setFormData(prev => ({ ...prev, description: e.target.value }))
            }
            rows={3}
          />
        </div>

        {/* Custom Requirements (only for custom type) */}
        {formData.serverType === "custom" && (
          <div className="space-y-2">
            <Label htmlFor="customRequirements">Custom Requirements</Label>
            <Textarea
              id="customRequirements"
              placeholder="Describe the specific functionality you need..."
              value={formData.customRequirements}
              onChange={(e) => 
                setFormData(prev => ({ ...prev, customRequirements: e.target.value }))
              }
              rows={4}
            />
          </div>
        )}

        {/* Generate Button */}
        <Button
          onClick={handleGenerate}
          disabled={!formData.projectName.trim() || isGenerating}
          className="w-full"
          size="lg"
        >
          {isGenerating ? (
            <>
              <Loader2 className="h-5 w-5 mr-2 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Download className="h-5 w-5 mr-2" />
              Generate MCP Server
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
