import { Bug } from '../types';
import { Play, Eye, Trash2, RefreshCw, Bug as BugIcon, Clock, CheckCircle, AlertTriangle } from 'lucide-react';

interface BugListProps {
  bugs: Bug[];
  onAnalyze: (id: string) => void;
  onViewAnalysis: (id: string) => void;
  onDelete: (id: string) => void;
  onRefresh: () => void;
}

export default function BugList({ bugs, onAnalyze, onViewAnalysis, onDelete, onRefresh }: BugListProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'analyzed': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'analyzing': return <Clock className="w-4 h-4 text-yellow-400 animate-pulse" />;
      case 'error': return <AlertTriangle className="w-4 h-4 text-red-400" />;
      default: return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      submitted: 'bg-gray-700/50 text-gray-300 border-gray-600',
      analyzing: 'bg-yellow-900/30 text-yellow-400 border-yellow-700/50',
      analyzed: 'bg-green-900/30 text-green-400 border-green-700/50',
      error: 'bg-red-900/30 text-red-400 border-red-700/50',
    };
    return styles[status] || styles.submitted;
  };

  const getSeverityBadge = (severity?: string) => {
    if (!severity) return null;
    const styles: Record<string, string> = {
      critical: 'bg-red-900/40 text-red-300 border-red-700/50',
      high: 'bg-orange-900/40 text-orange-300 border-orange-700/50',
      medium: 'bg-yellow-900/40 text-yellow-300 border-yellow-700/50',
      low: 'bg-blue-900/40 text-blue-300 border-blue-700/50',
    };
    return (
      <span className={`text-xs px-2 py-0.5 rounded-full border ${styles[severity] || ''}`}>
        {severity}
      </span>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Bug Reports</h2>
          <p className="text-sm text-gray-400">{bugs.length} total submissions</p>
        </div>
        <button
          onClick={onRefresh}
          className="px-3 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm flex items-center gap-2 transition-colors"
        >
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {bugs.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
          <BugIcon className="w-16 h-16 text-gray-700 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-300 mb-2">No bugs submitted yet</h3>
          <p className="text-sm text-gray-500">Submit your first bug report to begin AI analysis</p>
        </div>
      ) : (
        <div className="space-y-3">
          {bugs.map(bug => (
            <div key={bug.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition-colors">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="text-xs font-mono text-blue-400">{bug.id}</span>
                    {getStatusIcon(bug.status)}
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${getStatusBadge(bug.status)}`}>
                      {bug.status}
                    </span>
                    {bug.analysis && getSeverityBadge(bug.analysis.triage.severity)}
                    {bug.analysis && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-purple-900/30 text-purple-300 border border-purple-700/50">
                        {bug.analysis.triage.priority}
                      </span>
                    )}
                  </div>
                  <h3 className="text-sm font-medium text-white mt-1">{bug.title}</h3>
                  <p className="text-xs text-gray-400 mt-1 line-clamp-2">{bug.description}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                    <span>Submitted: {new Date(bug.createdAt).toLocaleString()}</span>
                    {bug.analysis && <span>Component: {bug.analysis.triage.component}</span>}
                    {bug.environment && <span>Env: {bug.environment}</span>}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {bug.status === 'submitted' && (
                    <button
                      onClick={() => onAnalyze(bug.id)}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs rounded-md font-medium flex items-center gap-1.5 transition-colors"
                    >
                      <Play className="w-3 h-3" /> Analyze
                    </button>
                  )}
                  {bug.status === 'analyzed' && (
                    <button
                      onClick={() => onViewAnalysis(bug.id)}
                      className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded-md font-medium flex items-center gap-1.5 transition-colors"
                    >
                      <Eye className="w-3 h-3" /> Results
                    </button>
                  )}
                  <button
                    onClick={() => onDelete(bug.id)}
                    className="p-1.5 text-gray-500 hover:text-red-400 hover:bg-red-900/20 rounded-md transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
