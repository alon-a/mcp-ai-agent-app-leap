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
}

export function GeneratedFiles({ files, instructions, onBack }: GeneratedFilesProps) {
  const [copiedFile, setCopiedFile] = useState<string | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);
  const { toast } = useToast();

  const handleCopyFile = async (file: ProjectFile) => {
    await navigator.clipboard.writeText(file.content);
    setCopiedFile(file.path);
    setTimeout(() => setCopiedFile(null), 2000);
    
    toast({
      title: "Copied",
      description: `${file.path} copied to clipboard`,
    });
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
    a.download = "mcp-server-files.txt";
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
    
    await navigator.clipboard.writeText(allContent);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2000);
    
    toast({
      title: "Copied",
      description: "All files copied to clipboard",
    });
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

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center space-x-2">
                <Package className="h-5 w-5" />
                <span>Generated MCP Server</span>
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
                Follow these steps to set up and run your MCP server
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
