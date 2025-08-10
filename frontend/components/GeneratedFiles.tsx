import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Download, Copy, Check, FileText, Package, Settings, BookOpen } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";

interface ProjectFile {
  path: string;
  content: string;
}

interface GeneratedFilesProps {
  files: ProjectFile[];
  instructions: string;
  onBack: () => void;
  projectType?: "server" | "client";
}

export function GeneratedFiles({ files, instructions, onBack, projectType = "server" }: GeneratedFilesProps) {
  const [copiedFile, setCopiedFile] = useState<string | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);
  const { toast } = useToast();

  const copyToClipboard = async (text: string): Promise<boolean> => {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (error) {
      console.error("Clipboard API failed:", error);
      
      // Fallback for older browsers or when clipboard API fails
      try {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.left = "-999999px";
        textArea.style.top = "-999999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        return true;
      } catch (fallbackError) {
        console.error("Fallback copy method also failed:", fallbackError);
        return false;
      }
    }
  };

  const handleCopyFile = async (file: ProjectFile) => {
    const success = await copyToClipboard(file.content);
    
    if (success) {
      setCopiedFile(file.path);
      setTimeout(() => setCopiedFile(null), 2000);
      
      toast({
        title: "Copied",
        description: `${file.path} copied to clipboard`,
      });
    } else {
      toast({
        title: "Copy Failed",
        description: "Unable to copy to clipboard. Please select and copy manually.",
        variant: "destructive",
      });
    }
  };

  const handleDownloadAll = () => {
    // Create a simple text format with all files
    const allContent = files.map(file => 
      `=== ${file.path} ===\n${file.content}\n\n`
    ).join("");

    const blob = new Blob([allContent], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `mcp-${projectType}-files.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({
      title: "Downloaded",
      description: "All files downloaded as text file",
    });
  };

  const handleCopyAll = async () => {
    const allContent = files.map(file => 
      `=== ${file.path} ===\n${file.content}\n\n`
    ).join("");
    
    const success = await copyToClipboard(allContent);
    
    if (success) {
      setCopiedAll(true);
      setTimeout(() => setCopiedAll(false), 2000);
      
      toast({
        title: "Copied",
        description: "All files copied to clipboard",
      });
    } else {
      toast({
        title: "Copy Failed",
        description: "Unable to copy to clipboard. Please try downloading instead.",
        variant: "destructive",
      });
    }
  };

  const getFileIcon = (path: string) => {
    if (path === "package.json") return Package;
    if (path === "tsconfig.json") return Settings;
    if (path === "README.md") return BookOpen;
    return FileText;
  };

  const getFileType = (path: string) => {
    const ext = path.split(".").pop()?.toLowerCase();
    switch (ext) {
      case "json": return "JSON";
      case "ts": return "TypeScript";
      case "md": return "Markdown";
      default: return "Text";
    }
  };

  const title = projectType === "client" ? "Generated MCP Client" : "Generated MCP Server";

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <Package className="h-5 w-5" />
                <span>{title}</span>
              </CardTitle>
              <CardDescription>
                {files.length} files generated successfully
              </CardDescription>
            </div>
            
            <div className="flex space-x-2">
              <Button variant="outline" onClick={onBack}>
                Generate Another
              </Button>
              <Button onClick={handleDownloadAll}>
                <Download className="h-4 w-4 mr-2" />
                Download All
              </Button>
              <Button variant="outline" onClick={handleCopyAll}>
                {copiedAll ? (
                  <>
                    <Check className="h-4 w-4 mr-2" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4 mr-2" />
                    Copy All
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      <Tabs defaultValue="files" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="files">Project Files</TabsTrigger>
          <TabsTrigger value="instructions">Setup Instructions</TabsTrigger>
        </TabsList>
        
        <TabsContent value="files" className="space-y-4">
          <div className="grid gap-4">
            {files.map((file, index) => {
              const Icon = getFileIcon(file.path);
              return (
                <Card key={index}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Icon className="h-4 w-4 text-gray-500" />
                        <span className="font-mono text-sm">{file.path}</span>
                        <Badge variant="secondary" className="text-xs">
                          {getFileType(file.path)}
                        </Badge>
                      </div>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleCopyFile(file)}
                      >
                        {copiedFile === file.path ? (
                          <>
                            <Check className="h-3 w-3 mr-1" />
                            Copied
                          </>
                        ) : (
                          <>
                            <Copy className="h-3 w-3 mr-1" />
                            Copy
                          </>
                        )}
                      </Button>
                    </div>
                  </CardHeader>
                  
                  <CardContent>
                    <ScrollArea className="h-64 w-full rounded border">
                      <pre className="p-4 text-sm">
                        <code>{file.content}</code>
                      </pre>
                    </ScrollArea>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>
        
        <TabsContent value="instructions">
          <Card>
            <CardHeader>
              <CardTitle>Setup Instructions</CardTitle>
              <CardDescription>
                Follow these steps to set up and run your MCP {projectType}
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              <div className="prose prose-sm max-w-none">
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  {instructions}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
