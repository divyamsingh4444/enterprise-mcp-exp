import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Activity, AlertCircle, CheckCircle2, Clock } from 'lucide-react';

interface TraceEvent {
  timestamp: string;
  tool_name: string;
  user: string;
  org_id: string;
  status: string;
  duration_ms: number;
  exit_code?: number;
  error?: string;
}

interface TracesResponse {
  traces: TraceEvent[];
  stats: {
    total: number;
    success: number;
    errors: number;
    avg_duration_ms: number;
  };
}

export const Traces: React.FC = () => {
  const [traces, setTraces] = useState<TraceEvent[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<'all' | 'success' | 'error'>('all');
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadTraces = async () => {
    try {
      setLoading(true);
      const response = await api.getTraces(50);
      setTraces(response.traces);
      setStats(response.stats);
    } catch (err) {
      console.error('Failed to load traces', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTraces();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(loadTraces, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const filteredTraces = traces.filter(t => {
    if (filter === 'success') return t.status === 'success';
    if (filter === 'error') return t.status === 'error';
    return true;
  });

  const getStatusColor = (status: string) => {
    if (status === 'success') return 'text-green-600 bg-green-50';
    if (status === 'error') return 'text-red-600 bg-red-50';
    return 'text-yellow-600 bg-yellow-50';
  };

  const getStatusIcon = (status: string) => {
    if (status === 'success') return <CheckCircle2 className="w-4 h-4" />;
    if (status === 'error') return <AlertCircle className="w-4 h-4" />;
    return <Activity className="w-4 h-4" />;
  };

  const formatTime = (isoString: string) => {
    return new Date(isoString).toLocaleTimeString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Execution Traces</h2>
          <p className="text-sm text-slate-600 mt-1">Real-time monitoring of tool executions</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            Auto-refresh
          </label>
          <button
            onClick={loadTraces}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded transition disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase">Total Executions</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{stats.total}</p>
              </div>
              <Activity className="w-8 h-8 text-slate-300" />
            </div>
          </div>

          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase">Success Rate</p>
                <p className="text-2xl font-bold text-green-600 mt-1">
                  {stats.total > 0 ? Math.round((stats.success / stats.total) * 100) : 0}%
                </p>
              </div>
              <CheckCircle2 className="w-8 h-8 text-green-300" />
            </div>
          </div>

          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase">Errors</p>
                <p className="text-2xl font-bold text-red-600 mt-1">{stats.errors}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-red-300" />
            </div>
          </div>

          <div className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase">Avg Duration</p>
                <p className="text-2xl font-bold text-blue-600 mt-1">
                  {stats.avg_duration_ms.toFixed(0)}ms
                </p>
              </div>
              <Clock className="w-8 h-8 text-blue-300" />
            </div>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {(['all', 'success', 'error'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded text-sm font-medium transition ${
              filter === f
                ? 'bg-blue-600 text-white'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Traces Table */}
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Tool</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">User</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Duration</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Timestamp</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {filteredTraces.length > 0 ? (
              filteredTraces.map((trace, idx) => (
                <tr key={idx} className="hover:bg-slate-50 transition">
                  <td className="px-6 py-4">
                    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full ${getStatusColor(trace.status)}`}>
                      {getStatusIcon(trace.status)}
                      <span className="text-xs font-medium">{trace.status}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="font-mono text-sm text-slate-900">{trace.tool_name}</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-700">{trace.user}</td>
                  <td className="px-6 py-4 text-sm text-slate-700">{trace.duration_ms.toFixed(1)}ms</td>
                  <td className="px-6 py-4 text-sm text-slate-600">{formatTime(trace.timestamp)}</td>
                  <td className="px-6 py-4 text-sm">
                    {trace.error ? (
                      <span className="text-red-600 font-mono text-xs">{trace.error.substring(0, 50)}...</span>
                    ) : trace.exit_code !== undefined ? (
                      <span className="text-slate-600">Exit: {trace.exit_code}</span>
                    ) : (
                      <span className="text-slate-400">-</span>
                    )}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                  {loading ? 'Loading...' : 'No traces found'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
