import React, { useState, useEffect } from 'react';
import { api, Tool, ToolCallResponse } from '../services/api';
import { useAuthStore } from '../store/auth';
import { LogOut, Play, Loader, AlertCircle, CheckCircle, Terminal, FileText, Folder, Globe } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [tools, setTools] = useState<Tool[]>([]);
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
      const token = localStorage.getItem('auth_token');
      console.log('Loading tools with token:', token ? 'present' : 'missing');
      const response = await api.listTools();
      console.log('Tools response:', response);
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

  const handleLogout = () => {
    logout();
  };

  const getToolIcon = (toolName: string) => {
    switch (toolName) {
      case 'run_command':
        return <Terminal className="w-5 h-5" />;
      case 'read_file':
      case 'write_file':
        return <FileText className="w-5 h-5" />;
      case 'list_directory':
        return <Folder className="w-5 h-5" />;
      case 'fetch_url':
        return <Globe className="w-5 h-5" />;
      default:
        return <Play className="w-5 h-5" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-6 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              🚀 MCP Dashboard
            </h1>
            <p className="text-sm text-gray-600 mt-1">Organization: <span className="font-semibold">{user?.org_id}</span></p>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition font-medium"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-gray-600 text-sm font-medium">Total Tools</div>
            <div className="text-3xl font-bold text-blue-600 mt-2">{tools.length}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-gray-600 text-sm font-medium">Status</div>
            <div className="text-2xl font-bold text-green-600 mt-2">✅ Ready</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-gray-600 text-sm font-medium">Selected</div>
            <div className="text-lg font-bold text-indigo-600 mt-2">{selectedTool?.name || 'None'}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-gray-600 text-sm font-medium">Execution</div>
            <div className={`text-2xl font-bold mt-2 ${isExecuting ? 'text-yellow-600' : 'text-gray-600'}`}>
              {isExecuting ? '⏳ Running' : '⏸️ Idle'}
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-800">Error</h3>
              <p className="text-red-700 text-sm mt-1">{error}</p>
              <button
                onClick={loadTools}
                className="text-red-600 hover:text-red-800 text-sm font-medium mt-2 underline"
              >
                Retry Loading Tools
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tools Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4">
                <h2 className="text-lg font-semibold text-white">Available Tools</h2>
              </div>

              <div className="p-6">
                {isLoading ? (
                  <div className="flex flex-col items-center justify-center py-12">
                    <Loader className="w-8 h-8 animate-spin text-blue-600 mb-3" />
                    <p className="text-gray-600 text-sm">Loading tools...</p>
                  </div>
                ) : tools.length === 0 ? (
                  <div className="text-center py-12">
                    <AlertCircle className="w-8 h-8 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-600">No tools available</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {tools.map((tool) => (
                      <button
                        key={tool.name}
                        onClick={() => {
                          setSelectedTool(tool);
                          setArguments({});
                          setResult(null);
                        }}
                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition text-left ${
                          selectedTool?.name === tool.name
                            ? 'bg-indigo-600 text-white shadow-lg'
                            : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                        }`}
                      >
                        {getToolIcon(tool.name)}
                        <div>
                          <div className="font-medium">{tool.name}</div>
                          <div className={`text-xs ${selectedTool?.name === tool.name ? 'text-indigo-100' : 'text-gray-600'}`}>
                            {tool.required_scope}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Tool Details & Executor */}
          <div className="lg:col-span-2 space-y-6">
            {/* Tool Details */}
            {selectedTool && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-800 mb-2 flex items-center gap-2">
                  {getToolIcon(selectedTool.name)}
                  {selectedTool.name}
                </h3>
                <p className="text-gray-600 mb-4">{selectedTool.description}</p>

                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                  <p className="text-sm"><span className="font-semibold text-blue-900">Scope:</span> <code className="bg-blue-100 px-2 py-1 rounded text-blue-900">{selectedTool.required_scope}</code></p>
                </div>

                {/* Arguments Input */}
                <div className="space-y-4">
                  <h4 className="font-semibold text-gray-800">Arguments</h4>
                  {Object.keys(selectedTool.input_schema.properties || {}).map((key) => {
                    const prop = selectedTool.input_schema.properties[key];
                    const isRequired = selectedTool.input_schema.required?.includes(key);
                    return (
                      <div key={key}>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          {key} {isRequired && <span className="text-red-600">*</span>}
                        </label>
                        <input
                          type={prop.type === 'number' ? 'number' : 'text'}
                          placeholder={prop.description || `Enter ${key}`}
                          value={arguments_[key] || ''}
                          onChange={(e) => handleArgumentChange(key, e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-600 focus:border-transparent"
                        />
                        <p className="text-xs text-gray-600 mt-1">{prop.description}</p>
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
                      ? 'bg-gray-400 text-white cursor-not-allowed'
                      : 'bg-indigo-600 hover:bg-indigo-700 text-white'
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
            )}

            {/* Results */}
            {result && (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center gap-2 mb-4">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <h4 className="font-semibold text-gray-800">Execution Result</h4>
                </div>
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <pre className="text-xs text-gray-700 overflow-x-auto">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};
