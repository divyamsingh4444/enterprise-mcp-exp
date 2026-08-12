import React, { useState, useEffect } from 'react';
import { api, Tool, ToolCallResponse } from '../services/api';
import { useAuthStore } from '../store/auth';
import { Play, Loader, AlertCircle, CheckCircle, Code2 } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [tools, setTools] = useState<Tool[]>([]);
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [arguments_, setArguments] = useState<Record<string, any>>({});
  const [result, setResult] = useState<ToolCallResponse | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [showDocs, setShowDocs] = useState(false);

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
      if (response.tools.length > 0) setSelectedTool(response.tools[0]);
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
      setError(err.message || 'Execution failed');
      setResult(null);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">MCP Tools</h1>
            <p className="text-sm text-slate-600">Execute sandboxed operations securely</p>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right border-r border-slate-200 pr-6">
              <p className="text-xs text-slate-500 uppercase">Organization</p>
              <p className="text-sm font-semibold text-slate-900">{user?.org_id}</p>
            </div>
            <button
              onClick={logout}
              className="text-sm text-slate-600 hover:text-slate-900 font-medium hover:bg-slate-100 px-4 py-2 rounded transition"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-semibold text-red-900">{error}</p>
              <button onClick={loadTools} className="text-xs text-red-600 hover:text-red-700 mt-1 underline">
                Retry
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Tool Selector */}
          <div>
            <h2 className="text-sm font-semibold text-slate-900 mb-4">Available Tools</h2>
            <div className="space-y-2 bg-white rounded-lg border border-slate-200 p-4">
              {isLoading ? (
                <div className="flex justify-center py-8">
                  <Loader className="w-5 h-5 animate-spin text-slate-400" />
                </div>
              ) : (
                tools.map((tool) => (
                  <button
                    key={tool.name}
                    onClick={() => {
                      setSelectedTool(tool);
                      setArguments({});
                      setResult(null);
                      setShowDocs(false);
                    }}
                    className={`w-full text-left px-3 py-2.5 rounded text-sm transition font-medium ${
                      selectedTool?.name === tool.name
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    <Code2 className="w-4 h-4 inline mr-2" />
                    {tool.name}
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            {selectedTool && (
              <>
                {/* Tool Card */}
                <div className="bg-white rounded-lg border border-slate-200 p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h2 className="text-xl font-bold text-slate-900">{selectedTool.name}</h2>
                      <p className="text-sm text-slate-600 mt-1">{selectedTool.description}</p>
                    </div>
                    <button
                      onClick={() => setShowDocs(!showDocs)}
                      className="text-sm text-blue-600 hover:text-blue-700 font-medium px-3 py-1 rounded hover:bg-blue-50 transition"
                    >
                      {showDocs ? 'Hide Docs' : 'View Docs'}
                    </button>
                  </div>

                  {showDocs && (
                    <div className="bg-slate-50 rounded border border-slate-200 p-4 mb-4 text-sm text-slate-700 space-y-2">
                      <div>
                        <p className="font-semibold text-slate-900 mb-1">Required Scope</p>
                        <code className="bg-white px-2 py-1 rounded text-blue-600">{selectedTool.required_scope}</code>
                      </div>
                      <div>
                        <p className="font-semibold text-slate-900 mb-1">Security</p>
                        <p>✓ Executes in isolated sandbox container with resource limits</p>
                      </div>
                    </div>
                  )}

                  {/* Arguments */}
                  <div className="space-y-4 mb-6">
                    <h3 className="font-semibold text-slate-900 text-sm">Arguments</h3>
                    {Object.keys(selectedTool.input_schema.properties || {}).length === 0 ? (
                      <p className="text-sm text-slate-600">No arguments required</p>
                    ) : (
                      Object.keys(selectedTool.input_schema.properties || {}).map((key) => {
                        const prop = selectedTool.input_schema.properties[key];
                        const isRequired = selectedTool.input_schema.required?.includes(key);
                        return (
                          <div key={key}>
                            <label className="block text-sm font-medium text-slate-700 mb-1">
                              {key} {isRequired && <span className="text-red-600">*</span>}
                            </label>
                            <input
                              type={prop.type === 'number' ? 'number' : 'text'}
                              placeholder={prop.description}
                              value={arguments_[key] || ''}
                              onChange={(e) =>
                                setArguments((prev) => ({ ...prev, [key]: e.target.value }))
                              }
                              className="w-full px-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />
                            <p className="text-xs text-slate-500 mt-1">{prop.description}</p>
                          </div>
                        );
                      })
                    )}
                  </div>

                  {/* Execute Button */}
                  <button
                    onClick={handleExecute}
                    disabled={isExecuting}
                    className={`w-full py-2.5 rounded font-semibold transition text-sm flex items-center justify-center gap-2 ${
                      isExecuting
                        ? 'bg-slate-300 text-slate-600 cursor-not-allowed'
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
                  <div className="bg-white rounded-lg border border-slate-200 p-6">
                    <div className="flex items-center gap-2 mb-4">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <h3 className="font-semibold text-slate-900">Result</h3>
                    </div>
                    <div className="bg-slate-900 rounded p-4 overflow-x-auto">
                      <pre className="text-xs text-slate-200 font-mono">{JSON.stringify(result, null, 2)}</pre>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};
