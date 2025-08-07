import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FileCode, Database, Globe, GitBranch, Settings, Download, Loader2, Network } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import backend from "~backend/client";
import type { ClientType, GenerateClientRequest } from "~backend/ai/generate-client";

interface GenerateClientFormProps {
  onGenerated: (files: any[], instructions: string) => void;
}

export function GenerateClientForm({ onGenerated }: GenerateClientFormProps) {
  const [formData, setFormData] = useState<GenerateClientRequest>({
    clientType: "filesystem" as ClientType,
    projectName: "",
    description: "",
    serverEndpoints: [],
    features: [],
    customRequirements: "",
  });
  const [isGenerating, setIsGenerating] = useState(false);
  const { toast } = useToast();

  const clientTypes = [
    {
      value: "filesystem" as ClientType,
      label: "File System Client",
      description: "Connect to file system MCP servers",
      icon: FileCode,
    },
    {
      value: "database" as ClientType,
      label: "Database Client",
      description: "Connect to database MCP servers",
      icon: Database,
    },
    {
      value: "api" as ClientType,
      label: "API Integration Client",
      description: "Connect to API integration MCP servers",
      icon: Globe,
    },
    {
      value: "git" as ClientType,
      label: "Git Repository Client",
      description: "Connect to Git repository MCP servers",
      icon: GitBranch,
    },
    {
      value: "multi-server" as ClientType,
      label: "Multi-Server Client",
      description: "Connect to multiple MCP servers simultaneously",
      icon: Network,
    },
    {
      value: "custom" as ClientType,
      label: "Custom Client",
      description: "Start with a basic template for custom functionality",
      icon: Settings,
    },
  ];

  const selectedClientType = clientTypes.find(type => type.value === formData.clientType);

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
      const response = await backend.ai.generateClient(formData);
      onGenerated(response.files, response.instructions);
      
      toast({
        title: "Success",
        description: "MCP client generated successfully!",
      });
    } catch (error) {
      console.error("Generation error:", error);
      toast({
        title: "Error",
        description: "Failed to generate MCP client. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleServerEndpointsChange = (value: string) => {
    const endpoints = value.split('\n').filter(line => line.trim()).map(line => line.trim());
    setFormData(prev => ({ ...prev, serverEndpoints: endpoints }));
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Download className="h-5 w-5" />
          <span>Generate MCP Client</span>
        </CardTitle>
        <CardDescription>
          Create a complete MCP client project with command-line interface, interactive mode, and programmatic API.
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Client Type Selection */}
        <div className="space-y-3">
          <Label htmlFor="clientType">Client Type</Label>
          <Select
            value={formData.clientType}
            onValueChange={(value: ClientType) => 
              setFormData(prev => ({ ...prev, clientType: value }))
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Select client type" />
            </SelectTrigger>
            <SelectContent>
              {clientTypes.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  <div className="flex items-center space-x-2">
                    <type.icon className="h-4 w-4" />
                    <span>{type.label}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          {selectedClientType && (
            <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg">
              <selectedClientType.icon className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <div className="font-medium text-green-900">
                  {selectedClientType.label}
                </div>
                <div className="text-sm text-green-700">
                  {selectedClientType.description}
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
            placeholder="my-mcp-client"
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
            placeholder="Brief description of your MCP client..."
            value={formData.description}
            onChange={(e) => 
              setFormData(prev => ({ ...prev, description: e.target.value }))
            }
            rows={3}
          />
        </div>

        {/* Server Endpoints (only for multi-server type) */}
        {formData.clientType === "multi-server" && (
          <div className="space-y-2">
            <Label htmlFor="serverEndpoints">Server Endpoints</Label>
            <Textarea
              id="serverEndpoints"
              placeholder="path/to/server1/dist/index.js&#10;path/to/server2/dist/index.js&#10;path/to/server3/dist/index.js"
              value={formData.serverEndpoints?.join('\n') || ''}
              onChange={(e) => handleServerEndpointsChange(e.target.value)}
              rows={4}
            />
            <div className="text-sm text-gray-500">
              Enter one server endpoint path per line
            </div>
          </div>
        )}

        {/* Custom Requirements (only for custom type) */}
        {formData.clientType === "custom" && (
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
              Generate MCP Client
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
