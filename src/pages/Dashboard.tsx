import { Bug } from '../types';
import {
  Bug as BugIcon,
  CheckCircle,
  Clock,
  AlertTriangle,
  Cpu,
  ArrowRight,
  TrendingUp,
  Database,
  Zap
} from 'lucide-react';

interface DashboardProps {
  bugs: Bug[];
  onNavigate: (page: string) => void;
  onAnalyze: (id: string) => void;
  onViewAnalysis: (id: string) => void;
}

export default function Dashboard({ bugs, onNavigate, onAnalyze, onViewAnalysis }: DashboardProps) {
  const analyzedBugs = bugs.filter(b => b.status === 'analyzed');
  const pendingBugs = bugs.filter(b => b.status === 'submitted');
  const criticalBugs = bugs.filter(b => b.analysis?.triage.severity === 'critical');

  const stats = [
    { label: 'Total Bugs', value: bugs.length, icon: BugIcon, color: 'from-blue-500 to-blue-600', change: '+3 today' },
    { label: 'Analyzed', value: analyzedBugs.length, icon: CheckCircle, color: 'from-green-500 to-green-600', change: 'AI processed' },
    { label: 'Pending', value: pendingBugs.length, icon: Clock, color: 'from-yellow-500 to-yellow-600', change: 'Awaiting analysis' },
    { label: 'Critical', value: criticalBugs.length, icon: AlertTriangle, color: 'from-red-500 to-red-600', change: 'High priority' },
  ];

  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800 border border-gray-700/50 p-6 lg:p-8">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiMyMDIwMjAiIGZpbGwtb3BhY2l0eT0iMC4xIj48cGF0aCBkPSJNMzYgMzRoLTJ2LTRoMnY0em0wLTZoLTJ2LTRoMnY0em0wLTZoLTJ2LTRoMnY0em0wLTZoLTJWNmgydjR6bTAtNmgtMlYyaDJ2NHoiLz48L2c+PC9nPjwvc3ZnPg==')] opacity-30" />
        <div className="relative">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="w-5 h-5 text-yellow-400" />
            <span className="text-xs font-medium text-yellow-400 uppercase tracking-wider">AI-Powered Analysis</span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-bold text-white mb-2">
            Software Defect Analysis System
          </h1>
          <p className="text-gray-400 max-w-2xl mb-6">
            Submit bugs and leverage AI agents for automated triage, root cause analysis, duplicate detection,
            and remediation recommendations using RAG-powered semantic search.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => onNavigate('submit')}
              className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
            >
              Submit New Bug <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onNavigate('knowledge')}
              className="px-4 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm font-medium transition-colors border border-gray-700 flex items-center gap-2"
            >
              <Database className="w-4 h-4" /> Search Knowledge Base
            </button>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${stat.color} flex items-center justify-center`}>
                <stat.icon className="w-5 h-5 text-white" />
              </div>
              <TrendingUp className="w-4 h-4 text-gray-600" />
            </div>
            <p className="text-2xl font-bold text-white">{stat.value}</p>
            <p className="text-sm text-gray-400">{stat.label}</p>
            <p className="text-xs text-gray-500 mt-1">{stat.change}</p>
          </div>
        ))}
      </div>

      {/* Pipeline Overview */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Cpu className="w-5 h-5 text-blue-400" />
          AI Agent Pipeline
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {[
            { name: 'Triage', desc: 'Severity & Priority', color: 'border-blue-500/30 bg-blue-950/20' },
            { name: 'Log Analysis', desc: 'Exception Detection', color: 'border-purple-500/30 bg-purple-950/20' },
            { name: 'Root Cause', desc: 'Cause Identification', color: 'border-orange-500/30 bg-orange-950/20' },
            { name: 'Duplicate Check', desc: 'Similarity Search', color: 'border-green-500/30 bg-green-950/20' },
            { name: 'Remediation', desc: 'Fix Suggestions', color: 'border-red-500/30 bg-red-950/20' },
          ].map((agent, i) => (
            <div key={agent.name} className={`border rounded-lg p-3 ${agent.color}`}>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono text-gray-500">0{i + 1}</span>
                <span className="text-sm font-medium text-white">{agent.name}</span>
              </div>
              <p className="text-xs text-gray-400">{agent.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Bugs */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Recent Submissions</h3>
          <button onClick={() => onNavigate('bugs')} className="text-sm text-blue-400 hover:text-blue-300">
            View All →
          </button>
        </div>
        {bugs.length === 0 ? (
          <div className="text-center py-8">
            <BugIcon className="w-12 h-12 text-gray-700 mx-auto mb-3" />
            <p className="text-gray-400 text-sm">No bugs submitted yet</p>
            <button
              onClick={() => onNavigate('submit')}
              className="mt-3 text-sm text-blue-400 hover:text-blue-300"
            >
              Submit your first bug →
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {bugs.slice(0, 5).map(bug => (
              <div key={bug.id} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg border border-gray-700/50">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-gray-500">{bug.id}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      bug.status === 'analyzed' ? 'bg-green-900/50 text-green-400' :
                      bug.status === 'analyzing' ? 'bg-yellow-900/50 text-yellow-400' :
                      'bg-gray-700 text-gray-400'
                    }`}>
                      {bug.status}
                    </span>
                  </div>
                  <p className="text-sm text-white truncate mt-1">{bug.title}</p>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  {bug.status === 'submitted' && (
                    <button
                      onClick={() => onAnalyze(bug.id)}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs rounded-md font-medium transition-colors"
                    >
                      Analyze
                    </button>
                  )}
                  {bug.status === 'analyzed' && (
                    <button
                      onClick={() => onViewAnalysis(bug.id)}
                      className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded-md font-medium transition-colors"
                    >
                      View Results
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
