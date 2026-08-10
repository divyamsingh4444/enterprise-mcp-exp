import React, { useState, useEffect } from 'react';
import { api, Tool, ToolCallResponse } from '../services/api';
import { useAuthStore } from '../store/auth';
import { LogOut, Play, Loader, AlertCircle, CheckCircle } from 'lucide-react';

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
      const response = await api.listTools();
      setTools(response.tools);
      if (response.tools.length > 0) {
        setSelectedTool(response.tools[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load tools');
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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">🚀 MCP Dashboard</h1>
            <p className="text-sm text-gray-600">Org: {user?.org_id}</p>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tools Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-4">Available Tools</h2>

              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader className="w-6 h-6 animate-spin text-blue-600" />
                </div>
              ) : (
                <div className="space-y-2">
                  {tools.map((tool) => (
                    <button
                      key={tool.name}
                      onClick={() => {
                        setSelectedTool(tool);
                        setArguments({});
                        setResult(null);
                      }}
                      className={`w-full text-left px-3 py-2 rounded-lg transition ${
                        selectedTool?.name === tool.name
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
                      }`}
                    >
                      <div className="font-medium">{tool.name}</div>
                      <div className={`text-xs ${
                        selectedTool?.name === tool.name ? 'text-blue-100' : 'text-gray-600'
                      }`}>
                        {tool.description}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Tool Executor Panel */}
          <div className="lg:col-span-2">
            {selectedTool ? (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-800 mb-2">
                  {selectedTool.name}
                </h2>
                <p className="text-gray-600 mb-4">{selectedTool.description}</p>

                <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-gray-700">
                    <strong>Required Scope:</strong> {selectedTool.required_scope}
                  </p>
                </div>

                {error && (
                  <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <p className="text-red-700 text-sm">{error}</p>
                  </div>
                )}

                {/* Input Arguments */}
                <div className="mb-6">
                  <h3 className="font-medium text-gray-800 mb-3">Arguments</h3>
                  <div className="space-y-3">
                    {Object.entries(selectedTool.input_schema?.properties || {}).map(
                      ([key, prop]: [string, any]) => (
                        <div key={key}>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            {key}
                            {selectedTool.input_schema?.required?.includes(key) && (
                              <span className="text-red-600">*</span>
                            )}
                          </label>
                          <input
                            type="text"
                            value={arguments_[key] || ''}
                            onChange={(e) => handleArgumentChange(key, e.target.value)}
                            placeholder={prop.description}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          />
                        </div>
                      )
                    )}
                  </div>
                </div>

                {/* Execute Button */}
                <button
                  onClick={handleExecute}
                  disabled={isExecuting}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 rounded-lg transition flex items-center justify-center gap-2"
                >
                  {isExecuting && <Loader className="w-4 h-4 animate-spin" />}
                  <Play className="w-4 h-4" />
                  Execute
                </button>

                {/* Result */}
                {result && (
                  <div className="mt-6">
                    <h3 className="font-medium text-gray-800 mb-3 flex items-center gap-2">
                      {result.success ? (
                        <>
                          <CheckCircle className="w-5 h-5 text-green-600" />
                          Success
                        </>
                      ) : (
                        <>
                          <AlertCircle className="w-5 h-5 text-red-600" />
                          Error
                        </>
                      )}
                    </h3>
                    <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto">
                      <pre>{JSON.stringify(result.result || result.error, null, 2)}</pre>
                    </div>
                    <p className="text-xs text-gray-600 mt-2">
                      Execution time: {result.duration_ms.toFixed(2)}ms
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-6 text-center text-gray-600">
                Select a tool to get started
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};
