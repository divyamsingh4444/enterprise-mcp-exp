import React, { useState, useEffect } from 'react';
import { api, Tool, ToolCallResponse } from '../services/api';
import { useAuthStore } from '../store/auth';
import { LogOut, Play, Loader, AlertCircle, CheckCircle, Terminal, FileText, Folder, Globe, BookOpen, Zap, Shield, ArrowRight, Copy } from 'lucide-react';

interface TabType {
  id: 'overview' | 'tools' | 'docs' | 'executor';
  label: string;
}

const TABS: TabType[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'tools', label: 'Tools' },
  { id: 'docs', label: 'Documentation' },
  { id: 'executor', label: 'Executor' },
];

const TOOL_INFO: Record<string, {
  icon: string;
  category: string;
  description: string;
  how_it_works: string[];
  ai_usage: string;
  use_cases: string[];
  security: string;
  example: string;
}> = {
  run_command: {
    icon: '⚙️',
    category: 'Shell Execution',
    description: 'Execute shell commands in a fully sandboxed environment with resource limits and security restrictions.',
    how_it_works: [
      'Command is received and validated against security policies',
      'Executed in isolated Docker container with CPU/memory limits',
      'Output (stdout/stderr) captured in real-time',
      'Results returned with execution metrics',
      'Container automatically cleaned up'
    ],
    ai_usage: 'Claude can use this to run diagnostics, process files, perform calculations, or execute automation scripts. Perfect for tasks that need real system feedback.',
    use_cases: [
      'System monitoring and diagnostics',
      'Batch file processing',
      'Running scripts and automation',
      'Real-time data analysis',
      'Environment verification'
    ],
    security: 'Runs in gVisor sandbox with CPU/memory limits. Dangerous commands (format, rm -rf, etc.) are blocked by security filter.',
    example: 'ls -la /workspace'
  },
  read_file: {
    icon: '📖',
    category: 'File Operations',
    description: 'Read and retrieve contents of files within the sandbox workspace. Perfect for analyzing file contents.',
    how_it_works: [
      'File path is normalized and validated',
      'Path checked against sandbox boundaries',
      'File contents read with permission checks',
      'Data returned with file metadata',
      'Large files streamed for efficiency'
    ],
    ai_usage: 'Claude can analyze code files, configuration files, logs, or data files. Enables intelligent code review, log analysis, and content extraction.',
    use_cases: [
      'Code analysis and review',
      'Log file parsing and analysis',
      'Configuration validation',
      'Data extraction from files',
      'Documentation reading'
    ],
    security: 'Cannot read files outside sandbox. All paths validated. Binary files handled safely.',
    example: '/workspace/config.json'
  },
  write_file: {
    icon: '✍️',
    category: 'File Operations',
    description: 'Create or modify files within the sandbox. Supports overwrite and append modes for flexible file management.',
    how_it_works: [
      'File path validated and normalized',
      'Sandbox boundaries enforced',
      'Permissions checked before write',
      'Content written atomically',
      'Backup created automatically'
    ],
    ai_usage: 'Claude can create configuration files, generate code, write documentation, or transform data files. Enables autonomous file creation workflows.',
    use_cases: [
      'Code generation',
      'Configuration file creation',
      'Documentation generation',
      'Data transformation and export',
      'Template filling'
    ],
    security: 'Cannot write outside sandbox. Atomic writes prevent corruption. Files are isolated.',
    example: '/workspace/output.txt'
  },
  list_directory: {
    icon: '📁',
    category: 'File Operations',
    description: 'List directory contents and explore the sandbox filesystem structure. Includes file metadata and size information.',
    how_it_works: [
      'Directory path validated',
      'Sandbox boundaries checked',
      'Directory entries enumerated',
      'Metadata collected (size, type, date)',
      'Results returned sorted and formatted'
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
    setArguments((prev) => ({ ...prev, [key]: value }));
  };

  const getToolIcon = (toolName: string) => {
    return TOOL_INFO[toolName]?.icon || '🔧';
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-8 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">MCP Dashboard</h1>
            <p className="text-sm text-gray-600 mt-1">Model Context Protocol - Enterprise Tool Executor</p>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Organization</p>
              <p className="text-sm font-semibold text-gray-900">{user?.org_id}</p>
            </div>
            <button
              onClick={logout}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-t border-gray-200">
          <div className="max-w-7xl mx-auto px-8 flex gap-8">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 text-sm font-medium border-b-2 transition ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-8 py-12">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-8">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-4">What is MCP?</h2>
              <p className="text-gray-600 text-lg leading-relaxed max-w-3xl">
                The <span className="font-semibold text-gray-900">Model Context Protocol (MCP)</span> is a standardized interface that enables AI models like Claude to safely interact with external tools and systems. This dashboard provides AI agents with structured access to powerful system capabilities while maintaining security and control.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="border border-gray-200 rounded-lg p-6 bg-gray-50">
                <div className="text-2xl mb-3">🔒</div>
                <h3 className="font-semibold text-gray-900 mb-2">Secure Execution</h3>
                <p className="text-sm text-gray-600">All tools run in isolated sandboxed containers with resource limits and permission controls.</p>
              </div>
              <div className="border border-gray-200 rounded-lg p-6 bg-gray-50">
                <div className="text-2xl mb-3">⚡</div>
                <h3 className="font-semibold text-gray-900 mb-2">Real-time Execution</h3>
                <p className="text-sm text-gray-600">Get instant feedback from system operations with complete output capture and metrics.</p>
              </div>
              <div className="border border-gray-200 rounded-lg p-6 bg-gray-50">
                <div className="text-2xl mb-3">🧠</div>
                <h3 className="font-semibold text-gray-900 mb-2">AI-Powered</h3>
                <p className="text-sm text-gray-600">Claude and other AI models can intelligently use these tools to automate tasks.</p>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-4 pt-8 border-t border-gray-200">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Available Tools</p>
                <p className="text-3xl font-bold text-gray-900">{tools.length}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Status</p>
                <p className="text-lg font-semibold text-green-600">✓ Operational</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Security</p>
                <p className="text-lg font-semibold text-blue-600">✓ Sandboxed</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wide mb-2">Auth</p>
                <p className="text-lg font-semibold text-blue-600">✓ Verified</p>
              </div>
            </div>
          </div>
        )}

        {/* Tools Tab */}
        {activeTab === 'tools' && (
          <div>
            {isLoading ? (
              <div className="flex justify-center py-12">
                <Loader className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {tools.map((tool) => (
                  <button
                    key={tool.name}
                    onClick={() => {
                      setSelectedTool(tool);
                      setActiveTab('executor');
                      setArguments({});
                    }}
                    className="text-left p-6 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition group"
                  >
                    <div className="text-3xl mb-3">{getToolIcon(tool.name)}</div>
                    <h3 className="font-semibold text-gray-900 mb-1">{tool.name}</h3>
                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-3">{TOOL_INFO[tool.name]?.category}</p>
                    <p className="text-sm text-gray-600 line-clamp-2">{tool.description}</p>
                    <div className="mt-4 flex items-center text-blue-600 opacity-0 group-hover:opacity-100 transition">
                      <span className="text-xs font-semibold">Use Tool</span>
                      <ArrowRight className="w-3 h-3 ml-1" />
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Documentation Tab */}
        {activeTab === 'docs' && (
          <div className="space-y-8">
            {tools.map((tool) => {
              const info = TOOL_INFO[tool.name];
              if (!info) return null;
              return (
                <div key={tool.name} className="border border-gray-200 rounded-lg p-8">
                  <div className="mb-6">
                    <div className="flex items-center gap-3 mb-4">
                      <span className="text-3xl">{info.icon}</span>
                      <div>
                        <h3 className="text-2xl font-bold text-gray-900">{tool.name}</h3>
                        <p className="text-sm text-gray-600">{info.category}</p>
                      </div>
                    </div>
                    <p className="text-gray-700">{info.description}</p>
                  </div>

                  <div className="grid grid-cols-2 gap-8 mb-8">
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">How It Works</h4>
                      <ol className="space-y-2">
                        {info.how_it_works.map((step, idx) => (
                          <li key={idx} className="text-sm text-gray-600">
                            <span className="font-medium text-gray-900">{idx + 1}.</span> {step}
                          </li>
                        ))}
                      </ol>
                    </div>

                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">AI Integration</h4>
                      <p className="text-sm text-gray-600">{info.ai_usage}</p>
                    </div>
                  </div>

                  <div className="border-t border-gray-200 pt-6 mb-6">
                    <h4 className="font-semibold text-gray-900 mb-3">Use Cases</h4>
                    <ul className="grid grid-cols-2 gap-2">
                      {info.use_cases.map((useCase, idx) => (
                        <li key={idx} className="text-sm text-gray-600">• {useCase}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="grid grid-cols-2 gap-6">
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                      <h4 className="font-semibold text-amber-900 mb-2">Security</h4>
                      <p className="text-sm text-amber-800">{info.security}</p>
                    </div>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h4 className="font-semibold text-blue-900 mb-2">Example</h4>
                      <code className="text-xs text-blue-900 font-mono">{info.example}</code>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Executor Tab */}
        {activeTab === 'executor' && (
          <div>
            {error && (
              <div className="mb-8 border border-red-200 bg-red-50 rounded-lg p-4 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-semibold text-red-900">Error</h3>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                  <button
                    onClick={loadTools}
                    className="text-sm text-red-600 hover:text-red-700 font-medium mt-2 underline"
                  >
                    Retry
                  </button>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Tool Selector */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-4">Select Tool</h3>
                <div className="space-y-2">
                  {tools.map((tool) => (
                    <button
                      key={tool.name}
                      onClick={() => {
                        setSelectedTool(tool);
                        setArguments({});
                        setResult(null);
                      }}
                      className={`w-full text-left px-4 py-3 rounded-lg transition text-sm ${
                        selectedTool?.name === tool.name
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                      }`}
                    >
                      <span className="mr-2">{getToolIcon(tool.name)}</span>
                      {tool.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Executor */}
              <div className="lg:col-span-2 space-y-6">
                {selectedTool && (
                  <>
                    {/* Tool Info */}
                    <div className="border border-gray-200 rounded-lg p-6">
                      <div className="mb-4">
                        <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                          {getToolIcon(selectedTool.name)} {selectedTool.name}
                        </h2>
                        <p className="text-sm text-gray-600 mt-2">{selectedTool.description}</p>
                      </div>
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <p className="text-xs text-gray-600">
                          <span className="font-semibold text-gray-900">Required Scope:</span>{' '}
                          <code className="text-xs text-blue-900 font-mono">{selectedTool.required_scope}</code>
                        </p>
                      </div>
                    </div>

                    {/* Arguments */}
                    <div className="border border-gray-200 rounded-lg p-6">
                      <h3 className="font-semibold text-gray-900 mb-4">Arguments</h3>
                      <div className="space-y-4">
                        {Object.keys(selectedTool.input_schema.properties || {}).map((key) => {
                          const prop = selectedTool.input_schema.properties[key];
                          const isRequired = selectedTool.input_schema.required?.includes(key);
                          return (
                            <div key={key}>
                              <label className="block text-sm font-medium text-gray-900 mb-2">
                                {key} {isRequired && <span className="text-red-600">*</span>}
                              </label>
                              <input
                                type={prop.type === 'number' ? 'number' : 'text'}
                                placeholder={prop.description || `Enter ${key}`}
                                value={arguments_[key] || ''}
                                onChange={(e) => handleArgumentChange(key, e.target.value)}
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-500"
                              />
                              <p className="text-xs text-gray-500 mt-1">{prop.description}</p>
                            </div>
                          );
                        })}
                      </div>

                      <button
                        onClick={handleExecute}
                        disabled={isExecuting}
                        className={`w-full mt-6 py-3 rounded-lg font-semibold transition flex items-center justify-center gap-2 ${
                          isExecuting
                            ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
                            : 'bg-blue-600 hover:bg-blue-700 text-white'
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
                            Execute
                          </>
                        )}
                      </button>
                    </div>

                    {/* Results */}
                    {result && (
                      <div className="border border-gray-200 rounded-lg p-6 bg-gray-50">
                        <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                          <CheckCircle className="w-5 h-5 text-green-600" />
                          Result
                        </h3>
                        <div className="bg-white rounded-lg p-4 border border-gray-200 overflow-x-auto">
                          <pre className="text-xs text-gray-700 font-mono">{JSON.stringify(result, null, 2)}</pre>
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
