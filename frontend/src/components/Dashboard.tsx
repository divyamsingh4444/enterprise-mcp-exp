import React, { useState, useEffect } from 'react';
import { api, Tool, ToolCallResponse } from '../services/api';
import { useAuthStore } from '../store/auth';
import { LogOut, Play, Loader, AlertCircle, CheckCircle, Terminal, FileText, Folder, Globe, BookOpen, Zap, Shield, Brain } from 'lucide-react';

interface TabType {
  id: 'overview' | 'tools' | 'docs' | 'executor';
  label: string;
  icon: React.ReactNode;
}

const TABS: TabType[] = [
  { id: 'overview', label: 'Overview', icon: <BookOpen className="w-4 h-4" /> },
  { id: 'tools', label: 'Tools', icon: <Zap className="w-4 h-4" /> },
  { id: 'docs', label: 'Documentation', icon: <FileText className="w-4 h-4" /> },
  { id: 'executor', label: 'Executor', icon: <Terminal className="w-4 h-4" /> },
];

const TOOL_INFO: Record<string, {
  icon: React.ReactNode;
  category: string;
  description: string;
  how_it_works: string[];
  ai_usage: string;
  use_cases: string[];
  security: string;
  example: string;
}> = {
  run_command: {
    icon: <Terminal className="w-6 h-6" />,
    category: 'Shell Execution',
    description: 'Execute shell commands in a fully sandboxed environment with resource limits and security restrictions.',
    how_it_works: [
      '1. Command is received and validated',
      '2. Executed in isolated Docker container',
      '3. stdout/stderr captured in real-time',
      '4. Results returned with execution time',
      '5. Container cleaned up automatically'
    ],
    ai_usage: 'Claude can use this to run system diagnostics, process files, perform calculations, or execute scripts. Perfect for automation tasks that need real system feedback.',
    use_cases: [
      'System monitoring and diagnostics',
      'Batch file processing',
      'Running scripts and automation',
      'Real-time data analysis',
      'Environment verification'
    ],
    security: 'Runs in gVisor sandbox with CPU/memory limits. Dangerous commands (format, rm -rf critical paths, etc.) are blocked.',
    example: 'ls -la /workspace'
  },
  read_file: {
    icon: <FileText className="w-6 h-6" />,
    category: 'File Operations',
    description: 'Read and retrieve contents of files within the sandbox workspace. Perfect for analyzing file contents.',
    how_it_works: [
      '1. File path is normalized and validated',
      '2. Path is checked against sandbox boundaries',
      '3. File contents are read with permission checks',
      '4. Data returned with metadata (size, type)',
      '5. Large files are streamed for efficiency'
    ],
    ai_usage: 'Claude can analyze code files, configuration files, logs, or data files. Enables intelligent code review, log analysis, and content extraction.',
    use_cases: [
      'Code analysis and review',
      'Log file parsing and analysis',
      'Configuration validation',
      'Data extraction from files',
      'Documentation reading'
    ],
    security: 'Cannot read files outside sandbox. All paths validated. Binary files handled safely with encoding.',
    example: '/workspace/config.json'
  },
  write_file: {
    icon: <FileText className="w-6 h-6" />,
    category: 'File Operations',
    description: 'Create or modify files within the sandbox. Supports overwrite and append modes for flexible file management.',
    how_it_works: [
      '1. File path validated and normalized',
      '2. Sandbox boundaries enforced',
      '3. Permissions checked',
      '4. Content written atomically',
      '5. Backup created automatically (optional)'
    ],
    ai_usage: 'Claude can create configuration files, generate code, write documentation, or transform data files. Enables autonomous file creation workflows.',
    use_cases: [
      'Code generation',
      'Configuration file creation',
      'Documentation generation',
      'Data transformation and export',
      'Template filling'
    ],
    security: 'Cannot write outside sandbox. Files are isolated. Atomic writes prevent corruption.',
    example: '/workspace/output.txt'
  },
  list_directory: {
    icon: <Folder className="w-6 h-6" />,
    category: 'File Operations',
    description: 'List directory contents and explore the sandbox filesystem structure. Includes file metadata and size information.',
    how_it_works: [
      '1. Directory path validated',
      '2. Sandbox boundaries checked',
      '3. Directory entries enumerated',
      '4. Metadata collected (size, type, date)',
      '5. Results returned sorted'
    ],
    ai_usage: 'Claude can explore workspace structure, find files, and understand project layout. Essential for context gathering in automation tasks.',
    use_cases: [
      'File discovery',
      'Workspace exploration',
      'Project structure analysis',
      'Cleanup and organization',
      'Backup preparation'
    ],
    security: 'Cannot list outside sandbox. Hidden files included. Large directories paginated.',
    example: '/workspace'
  },
};

export const Dashboard: React.FC = () => {
  const [tools, setTools] = useState<Tool[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'tools' | 'docs' | 'executor'>('overview');
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [arguments_, setArguments] = useState<Record<string, any>>({});
  const [result, setResult] = useState<ToolCallResponse | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);

  const { logout, user } = useAuthStore();

  useEffect(() => {
    loadTools();
  }, []);

  const loadTools = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.listTools();
      setTools(response.tools);
      if (response.tools.length > 0) {
        setSelectedTool(response.tools[0]);
      }
    } catch (err: any) {
      console.error('Failed to load tools:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load tools');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExecute = async () => {
    if (!selectedTool) return;
    try {
      setIsExecuting(true);
      setError(null);
      const response = await api.callTool({
        tool: selectedTool.name,
        arguments: arguments_,
      });
      setResult(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Execution failed');
      setResult(null);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleArgumentChange = (key: string, value: any) => {
    setArguments((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const getToolIcon = (toolName: string) => {
    const info = TOOL_INFO[toolName];
    return info?.icon || <Zap className="w-5 h-5" />;
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-900 to-indigo-900 shadow-xl border-b border-blue-700">
        <div className="max-w-7xl mx-auto px-6 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              🚀 MCP Dashboard
            </h1>
            <p className="text-blue-300 mt-1">Model Context Protocol - Enterprise Tool Executor</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm text-gray-400">Organization</p>
              <p className="text-lg font-semibold text-blue-300">{user?.org_id}</p>
            </div>
            <button
              onClick={logout}
              className="flex items-center gap-2 px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition font-medium"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Tab Navigation */}
        <div className="flex gap-2 mb-8 border-b border-gray-700">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-3 font-medium transition border-b-2 ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="bg-gradient-to-r from-blue-900 to-indigo-900 rounded-lg p-8 border border-blue-700">
              <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                <Brain className="w-6 h-6 text-cyan-400" />
                What is MCP?
              </h2>
              <p className="text-gray-300 mb-4">
                The <span className="text-cyan-400 font-semibold">Model Context Protocol (MCP)</span> is a standardized interface that enables AI models like Claude to safely interact with external tools and systems. This dashboard provides AI agents with structured access to powerful system capabilities while maintaining security and control.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <h3 className="font-semibold text-cyan-400 mb-2 flex items-center gap-2">
                    <Shield className="w-4 h-4" />
                    Secure Execution
                  </h3>
                  <p className="text-sm text-gray-400">All tools run in isolated sandboxed containers with resource limits and permission controls.</p>
                </div>
                <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <h3 className="font-semibold text-cyan-400 mb-2 flex items-center gap-2">
                    <Zap className="w-4 h-4" />
                    Real-time Execution
                  </h3>
                  <p className="text-sm text-gray-400">Get instant feedback from system operations with complete stdout/stderr capture and metrics.</p>
                </div>
                <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <h3 className="font-semibold text-cyan-400 mb-2 flex items-center gap-2">
                    <Brain className="w-4 h-4" />
                    AI-Powered
                  </h3>
                  <p className="text-sm text-gray-400">Claude and other AI models can intelligently use these tools to automate tasks and solve problems.</p>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <p className="text-gray-400 text-sm mb-2">Available Tools</p>
                <p className="text-3xl font-bold text-cyan-400">{tools.length}</p>
                <p className="text-xs text-gray-500 mt-2">Ready to execute</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <p className="text-gray-400 text-sm mb-2">Status</p>
                <p className="text-3xl font-bold text-green-400">✅ Live</p>
                <p className="text-xs text-gray-500 mt-2">All systems operational</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <p className="text-gray-400 text-sm mb-2">Security</p>
                <p className="text-3xl font-bold text-yellow-400">🛡️ Gated</p>
                <p className="text-xs text-gray-500 mt-2">Sandboxed execution</p>
              </div>
              <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <p className="text-gray-400 text-sm mb-2">Auth</p>
                <p className="text-3xl font-bold text-blue-400">🔐 Verified</p>
                <p className="text-xs text-gray-500 mt-2">Token validated</p>
              </div>
            </div>
          </div>
        )}

        {/* Tools Tab */}
        {activeTab === 'tools' && (
          <div className="space-y-4">
            {isLoading ? (
              <div className="flex justify-center py-12">
                <Loader className="w-8 h-8 animate-spin text-cyan-400" />
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {tools.map((tool) => {
                  const info = TOOL_INFO[tool.name];
                  return (
                    <button
                      key={tool.name}
                      onClick={() => {
                        setSelectedTool(tool);
                        setActiveTab('executor');
                        setArguments({});
                      }}
                      className={`p-6 rounded-lg border-2 transition text-left ${
                        selectedTool?.name === tool.name
                          ? 'bg-indigo-900 border-cyan-400'
                          : 'bg-gray-800 border-gray-700 hover:border-cyan-400'
                      }`}
                    >
                      <div className="flex items-center gap-3 mb-3">
                        <div className="text-2xl">{getToolIcon(tool.name)}</div>
                        <div>
                          <h3 className="font-bold text-white">{tool.name}</h3>
                          <p className="text-xs text-gray-400">{info?.category}</p>
                        </div>
                      </div>
                      <p className="text-sm text-gray-300">{info?.description || tool.description}</p>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Documentation Tab */}
        {activeTab === 'docs' && (
          <div className="space-y-6">
            {tools.map((tool) => {
              const info = TOOL_INFO[tool.name];
              if (!info) return null;
              return (
                <div key={tool.name} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="text-3xl">{info.icon}</div>
                    <div>
                      <h3 className="text-2xl font-bold text-white">{tool.name}</h3>
                      <p className="text-cyan-400">{info.category}</p>
                    </div>
                  </div>

                  <p className="text-gray-300 mb-6">{info.description}</p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* How It Works */}
                    <div>
                      <h4 className="font-bold text-cyan-400 mb-3 flex items-center gap-2">
                        <Zap className="w-4 h-4" />
                        How It Works
                      </h4>
                      <ol className="space-y-2">
                        {info.how_it_works.map((step, idx) => (
                          <li key={idx} className="text-sm text-gray-400 flex items-start gap-2">
                            <span className="text-cyan-400 font-mono flex-shrink-0">{step.split('.')[0]}.</span>
                            <span>{step.substring(step.indexOf('.') + 2)}</span>
                          </li>
                        ))}
                      </ol>
                    </div>

                    {/* AI Usage */}
                    <div>
                      <h4 className="font-bold text-cyan-400 mb-3 flex items-center gap-2">
                        <Brain className="w-4 h-4" />
                        How AI Uses This
                      </h4>
                      <p className="text-sm text-gray-400">{info.ai_usage}</p>
                    </div>
                  </div>

                  {/* Use Cases */}
                  <div className="mt-6 p-4 bg-gray-700 bg-opacity-50 rounded-lg">
                    <h4 className="font-bold text-cyan-400 mb-2">💡 Use Cases</h4>
                    <ul className="text-sm text-gray-400 space-y-1">
                      {info.use_cases.map((useCase, idx) => (
                        <li key={idx}>• {useCase}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Security & Example */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                    <div className="p-4 bg-yellow-900 bg-opacity-30 rounded-lg border border-yellow-700">
                      <h4 className="font-bold text-yellow-400 mb-2 flex items-center gap-2">
                        <Shield className="w-4 h-4" />
                        Security
                      </h4>
                      <p className="text-sm text-gray-300">{info.security}</p>
                    </div>
                    <div className="p-4 bg-blue-900 bg-opacity-30 rounded-lg border border-blue-700">
                      <h4 className="font-bold text-blue-400 mb-2">📝 Example</h4>
                      <code className="text-xs text-gray-300 font-mono">{info.example}</code>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Executor Tab */}
        {activeTab === 'executor' && (
          <div className="space-y-6">
            {error && (
              <div className="bg-red-900 border border-red-700 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-bold text-red-300">Error</h3>
                  <p className="text-red-200 text-sm mt-1">{error}</p>
                  <button
                    onClick={loadTools}
                    className="text-red-400 hover:text-red-300 text-sm font-medium mt-2 underline"
                  >
                    Retry
                  </button>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Tool Selector */}
              <div className="lg:col-span-1">
                <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
                  <div className="bg-gradient-to-r from-blue-900 to-indigo-900 px-6 py-4 border-b border-gray-700">
                    <h3 className="font-bold text-cyan-400 flex items-center gap-2">
                      <Zap className="w-4 h-4" />
                      Select Tool
                    </h3>
                  </div>
                  <div className="p-4 space-y-2">
                    {tools.map((tool) => (
                      <button
                        key={tool.name}
                        onClick={() => {
                          setSelectedTool(tool);
                          setArguments({});
                          setResult(null);
                        }}
                        className={`w-full text-left px-4 py-3 rounded-lg transition ${
                          selectedTool?.name === tool.name
                            ? 'bg-cyan-600 text-white'
                            : 'bg-gray-700 text-gray-200 hover:bg-gray-600'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          {getToolIcon(tool.name)}
                          <span className="font-semibold">{tool.name}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Executor */}
              <div className="lg:col-span-2 space-y-6">
                {selectedTool && (
                  <>
                    {/* Tool Info */}
                    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                      <div className="flex items-center gap-3 mb-4">
                        {getToolIcon(selectedTool.name)}
                        <div>
                          <h2 className="text-2xl font-bold text-white">{selectedTool.name}</h2>
                          <p className="text-gray-400">{selectedTool.description}</p>
                        </div>
                      </div>
                      <div className="p-3 bg-blue-900 bg-opacity-30 rounded-lg border border-blue-700 mt-4">
                        <p className="text-sm"><span className="font-semibold text-blue-300">Required Scope:</span> <code className="text-blue-200">{selectedTool.required_scope}</code></p>
                      </div>
                    </div>

                    {/* Arguments */}
                    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                      <h3 className="font-bold text-cyan-400 mb-4">Arguments</h3>
                      <div className="space-y-4">
                        {Object.keys(selectedTool.input_schema.properties || {}).map((key) => {
                          const prop = selectedTool.input_schema.properties[key];
                          const isRequired = selectedTool.input_schema.required?.includes(key);
                          return (
                            <div key={key}>
                              <label className="block text-sm font-medium text-gray-300 mb-2">
                                {key} {isRequired && <span className="text-red-400">*</span>}
                              </label>
                              <input
                                type={prop.type === 'number' ? 'number' : 'text'}
                                placeholder={prop.description || `Enter ${key}`}
                                value={arguments_[key] || ''}
                                onChange={(e) => handleArgumentChange(key, e.target.value)}
                                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:border-cyan-500 focus:outline-none text-white placeholder-gray-500"
                              />
                              <p className="text-xs text-gray-500 mt-1">{prop.description}</p>
                            </div>
                          );
                        })}
                      </div>

                      {/* Execute Button */}
                      <button
                        onClick={handleExecute}
                        disabled={isExecuting}
                        className={`w-full mt-6 py-3 rounded-lg font-semibold transition flex items-center justify-center gap-2 ${
                          isExecuting
                            ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                            : 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white'
                        }`}
                      >
                        {isExecuting ? (
                          <>
                            <Loader className="w-4 h-4 animate-spin" />
                            Executing...
                          </>
                        ) : (
                          <>
                            <Play className="w-4 h-4" />
                            Execute Tool
                          </>
                        )}
                      </button>
                    </div>

                    {/* Results */}
                    {result && (
                      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                        <h3 className="font-bold text-green-400 mb-4 flex items-center gap-2">
                          <CheckCircle className="w-5 h-5" />
                          Execution Result
                        </h3>
                        <div className="bg-gray-900 rounded-lg p-4 border border-gray-600 overflow-x-auto">
                          <pre className="text-xs text-gray-300 font-mono">{JSON.stringify(result, null, 2)}</pre>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
