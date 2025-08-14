import React, { useState } from 'react';
import {
  X,
  FileText,
  Folder,
  FolderOpen,
  Code,
  Settings,
  Package,
  Star,
  Download,
  Clock,
  User,
  Tag,
  ChevronRight,
  ChevronDown,
  Eye,
  Copy,
  ExternalLink
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';

interface Template {
  id: string;
  name: string;
  description: string;
  category: 'built-in' | 'custom' | 'community';
  language: 'python' | 'typescript' | 'go' | 'rust' | 'java' | 'multi';
  framework: string;
  version: string;
  metadata: {
    author?: string;
    tags: string[];
    difficulty: 'beginner' | 'intermediate' | 'advanced';
    estimatedTime: number;
    lastUpdated: Date;
    downloadCount: number;
    rating: number;
    ratingCount: number;
  };
  configuration: {
    schema: any;
    defaultValues: Record<string, any>;
    requiredFields: string[];
  };
  structure: {
    files: Array<{
      path: string;
      content: string;
      isTemplate: boolean;
    }>;
    directories: string[];
    entryPoint?: string;
  };
  dependencies: {
    runtime: Record<string, string>;
    development: Record<string, string>;
    system: string[];
    services: string[];
  };
}

interface TemplatePreviewProps {
  template: Template;
  onClose: () => void;
  onUseTemplate: () => void;
}

interface FileTreeNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileTreeNode[];
  content?: string;
  isTemplate?: boolean;
}

export const TemplatePreview: React.FC<TemplatePreviewProps> = ({
  template,
  onClose,
  onUseTemplate
}) => {
  const { toast } = useToast();
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set());

  // Build file tree structure
  const buildFileTree = (): FileTreeNode[] => {
    const tree: FileTreeNode[] = [];
    const pathMap = new Map<string, FileTreeNode>();

    // Add directories first
    template.structure.directories.forEach(dir => {
      const parts = dir.split('/');
      let currentPath = '';
      
      parts.forEach((part, index) => {
        const parentPath = currentPath;
        currentPath = currentPath ? `${currentPath}/${part}` : part;
        
        if (!pathMap.has(currentPath)) {
          const node: FileTreeNode = {
            name: part,
            path: currentPath,
            type: 'directory',
            children: []
          };
          
          pathMap.set(currentPath, node);
          
          if (parentPath && pathMap.has(parentPath)) {
            pathMap.get(parentPath)!.children!.push(node);
          } else if (index === 0) {
            tree.push(node);
          }
        }
      });
    });

    // Add files
    template.structure.files.forEach(file => {
      const parts = file.path.split('/');
      const fileName = parts.pop()!;
      const dirPath = parts.join('/');
      
      const fileNode: FileTreeNode = {
        name: fileName,
        path: file.path,
        type: 'file',
        content: file.content,
        isTemplate: file.isTemplate
      };
      
      if (dirPath && pathMap.has(dirPath)) {
        pathMap.get(dirPath)!.children!.push(fileNode);
      } else {
        tree.push(fileNode);
      }
    });

    // Sort children (directories first, then files, both alphabetically)
    const sortChildren = (nodes: FileTreeNode[]) => {
      nodes.sort((a, b) => {
        if (a.type !== b.type) {
          return a.type === 'directory' ? -1 : 1;
        }
        return a.name.localeCompare(b.name);
      });
      
      nodes.forEach(node => {
        if (node.children) {
          sortChildren(node.children);
        }
      });
    };
    
    sortChildren(tree);
    return tree;
  };

  const fileTree = buildFileTree();

  const toggleDirectory = (path: string) => {
    const newExpanded = new Set(expandedDirs);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedDirs(newExpanded);
  };

  const getFileIcon = (fileName: string, isTemplate: boolean = false) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    
    if (isTemplate) {
      return <Settings className="h-4 w-4 text-blue-500" />;
    }
    
    switch (ext) {
      case 'py':
        return <Code className="h-4 w-4 text-blue-600" />;
      case 'ts':
      case 'js':
        return <Code className="h-4 w-4 text-yellow-600" />;
      case 'go':
        return <Code className="h-4 w-4 text-cyan-600" />;
      case 'rs':
        return <Code className="h-4 w-4 text-orange-600" />;
      case 'java':
        return <Code className="h-4 w-4 text-red-600" />;
      case 'json':
        return <Settings className="h-4 w-4 text-green-600" />;
      case 'md':
        return <FileText className="h-4 w-4 text-gray-600" />;
      default:
        return <FileText className="h-4 w-4 text-gray-500" />;
    }
  };

  const renderFileTree = (nodes: FileTreeNode[], depth: number = 0) => {
    return nodes.map(node => (
      <div key={node.path}>
        <div
          className={`
            flex items-center space-x-2 py-1 px-2 rounded cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800
            ${selectedFile === node.path ? 'bg-blue-50 dark:bg-blue-900/20 border-l-2 border-blue-500' : ''}
          `}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={() => {
            if (node.type === 'directory') {
              toggleDirectory(node.path);
            } else {
              setSelectedFile(node.path);
            }
          }}
        >
          {node.type === 'directory' ? (
            <>
              {expandedDirs.has(node.path) ? (
                <ChevronDown className="h-4 w-4 text-gray-400" />
              ) : (
                <ChevronRight className="h-4 w-4 text-gray-400" />
              )}
              {expandedDirs.has(node.path) ? (
                <FolderOpen className="h-4 w-4 text-blue-500" />
              ) : (
                <Folder className="h-4 w-4 text-blue-500" />
              )}
            </>
          ) : (
            <>
              <div className="w-4" />
              {getFileIcon(node.name, node.isTemplate)}
            </>
          )}
          
          <span className={`text-sm ${
            node.type === 'directory' 
              ? 'font-medium text-gray-900 dark:text-gray-100' 
              : 'text-gray-700 dark:text-gray-300'
          }`}>
            {node.name}
          </span>
          
          {node.isTemplate && (
            <Badge variant="outline" className="text-xs ml-auto">
              Template
            </Badge>
          )}
          
          {node.path === template.structure.entryPoint && (
            <Badge variant="secondary" className="text-xs ml-auto">
              Entry
            </Badge>
          )}
        </div>
        
        {node.type === 'directory' && expandedDirs.has(node.path) && node.children && (
          <div>
            {renderFileTree(node.children, depth + 1)}
          </div>
        )}
      </div>
    ));
  };

  const selectedFileContent = selectedFile 
    ? template.structure.files.find(f => f.path === selectedFile)?.content 
    : null;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      toast({
        title: "Copied to clipboard",
        description: "File content has been copied to your clipboard.",
      });
    });
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-700 border-green-200';
      case 'intermediate': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'advanced': return 'bg-red-100 text-red-700 border-red-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-7xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-4">
            <div className="text-3xl">
              {template.category === 'built-in' ? '🏗️' : template.category === 'custom' ? '🎨' : '👥'}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {template.name}
              </h2>
              <div className="flex items-center space-x-2 mt-1">
                <Badge variant="secondary">{template.language}</Badge>
                <Badge variant="outline" className={getDifficultyColor(template.metadata.difficulty)}>
                  {template.metadata.difficulty}
                </Badge>
                <div className="flex items-center space-x-1 text-sm text-gray-500">
                  <Star className="h-4 w-4 text-yellow-500 fill-current" />
                  <span>{template.metadata.rating}</span>
                  <span>({template.metadata.ratingCount})</span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button onClick={onUseTemplate}>
              Use Template
            </Button>
            <Button variant="outline" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="flex h-[calc(90vh-120px)]">
          {/* Sidebar with template info and file tree */}
          <div className="w-1/3 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
            <Tabs defaultValue="overview" className="h-full">
              <TabsList className="grid w-full grid-cols-3 m-4">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="structure">Structure</TabsTrigger>
                <TabsTrigger value="config">Config</TabsTrigger>
              </TabsList>
              
              <TabsContent value="overview" className="px-4 pb-4 space-y-4">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    Description
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {template.description}
                  </p>
                </div>
                
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    Details
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Framework:</span>
                      <Badge variant="outline">{template.framework}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Version:</span>
                      <span className="font-mono text-xs">{template.version}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Est. Time:</span>
                      <div className="flex items-center space-x-1">
                        <Clock className="h-3 w-3" />
                        <span>{template.metadata.estimatedTime}min</span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Downloads:</span>
                      <div className="flex items-center space-x-1">
                        <Download className="h-3 w-3" />
                        <span>{template.metadata.downloadCount}</span>
                      </div>
                    </div>
                    {template.metadata.author && (
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600 dark:text-gray-400">Author:</span>
                        <div className="flex items-center space-x-1">
                          <User className="h-3 w-3" />
                          <span>{template.metadata.author}</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    Tags
                  </h3>
                  <div className="flex flex-wrap gap-1">
                    {template.metadata.tags.map((tag, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    Dependencies
                  </h3>
                  <div className="space-y-2">
                    {Object.keys(template.dependencies.runtime).length > 0 && (
                      <div>
                        <h4 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Runtime
                        </h4>
                        <div className="space-y-1">
                          {Object.entries(template.dependencies.runtime).map(([pkg, version]) => (
                            <div key={pkg} className="flex items-center justify-between text-xs">
                              <span className="font-mono text-gray-600 dark:text-gray-400">{pkg}</span>
                              <span className="text-gray-500">{version}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {template.dependencies.system.length > 0 && (
                      <div>
                        <h4 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          System
                        </h4>
                        <div className="flex flex-wrap gap-1">
                          {template.dependencies.system.map((dep, index) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              {dep}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="structure" className="px-4 pb-4">
                <div className="space-y-2">
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    File Structure
                  </h3>
                  <div className="text-sm">
                    {renderFileTree(fileTree)}
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="config" className="px-4 pb-4 space-y-4">
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                    Configuration Schema
                  </h3>
                  {template.configuration.requiredFields.length > 0 ? (
                    <div className="space-y-2">
                      <div>
                        <h4 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Required Fields
                        </h4>
                        <div className="space-y-1">
                          {template.configuration.requiredFields.map(field => (
                            <Badge key={field} variant="outline" className="text-xs mr-1">
                              {field}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      
                      {Object.keys(template.configuration.defaultValues).length > 0 && (
                        <div>
                          <h4 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Default Values
                          </h4>
                          <div className="space-y-1 text-xs">
                            {Object.entries(template.configuration.defaultValues).map(([key, value]) => (
                              <div key={key} className="flex items-center justify-between">
                                <span className="font-mono text-gray-600 dark:text-gray-400">{key}</span>
                                <span className="text-gray-500">{String(value)}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      No configuration required - ready to use!
                    </p>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          </div>

          {/* Main content area - file preview */}
          <div className="flex-1 flex flex-col">
            {selectedFile && selectedFileContent ? (
              <>
                <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center space-x-2">
                    {getFileIcon(selectedFile.split('/').pop() || '', 
                      template.structure.files.find(f => f.path === selectedFile)?.isTemplate
                    )}
                    <span className="font-mono text-sm text-gray-900 dark:text-gray-100">
                      {selectedFile}
                    </span>
                    {template.structure.files.find(f => f.path === selectedFile)?.isTemplate && (
                      <Badge variant="outline" className="text-xs">
                        Template File
                      </Badge>
                    )}
                  </div>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(selectedFileContent)}
                  >
                    <Copy className="h-4 w-4 mr-2" />
                    Copy
                  </Button>
                </div>
                
                <div className="flex-1 overflow-auto p-4">
                  <pre className="text-sm bg-gray-50 dark:bg-gray-800 rounded-lg p-4 overflow-auto">
                    <code className="text-gray-900 dark:text-gray-100">
                      {selectedFileContent}
                    </code>
                  </pre>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <Eye className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                    Select a file to preview
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Click on any file in the structure tab to view its contents
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};