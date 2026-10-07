/**
 * M4.3 — End-to-End Testing & System Validation Page
 *
 * Runs the complete pipeline against 8 test scenarios + 3 error-handling tests.
 * Evaluates every agent stage and displays structured results with assertions,
 * performance metrics, RAG evaluation, and duplicate detection F1 score.
 */

import { useState } from 'react';
import {
  PlayCircle, CheckCircle2, XCircle, AlertTriangle, Loader2,
  Clock, Zap, BarChart3, GitBranch, Database, ChevronDown,
  ChevronUp, Cpu, ShieldCheck, RefreshCw, Info,
} from 'lucide-react';
import type { E2ESuiteResult, E2ETestResult, TestStatus } from '../types';
import { runE2ETests } from '../services/api';

// ── Constants ─────────────────────────────────────────────────────────────────

const STAGE_LABELS: Record<string, string> = {
  submission: 'Bug Submission',
  rag_retrieval: 'RAG Retrieval',
  triage: 'Triage Agent',
  log_analysis: 'Log Analysis',
  root_cause: 'Root Cause',
  duplicate_detection: 'Duplicate Detection',
  remediation: 'Remediation',
};

// ── Status badge ──────────────────────────────────────────────────────────────

function StatusBadge({ status, size = 'sm' }: { status: TestStatus; size?: 'sm' | 'lg' }) {
  const configs: Record<TestStatus, { bg: string; text: string; icon: React.ReactNode; label: string }> = {
    pass: { bg: 'bg-emerald-900/40 border border-emerald-700/50', text: 'text-emerald-400', icon: <CheckCircle2 className={size === 'lg' ? 'w-5 h-5' : 'w-3.5 h-3.5'} />, label: 'PASS' },
    fail: { bg: 'bg-red-900/40 border border-red-700/50', text: 'text-red-400', icon: <XCircle className={size === 'lg' ? 'w-5 h-5' : 'w-3.5 h-3.5'} />, label: 'FAIL' },
    warning: { bg: 'bg-yellow-900/40 border border-yellow-700/50', text: 'text-yellow-400', icon: <AlertTriangle className={size === 'lg' ? 'w-5 h-5' : 'w-3.5 h-3.5'} />, label: 'WARN' },
    running: { bg: 'bg-blue-900/40 border border-blue-700/50', text: 'text-blue-400', icon: <Loader2 className={`${size === 'lg' ? 'w-5 h-5' : 'w-3.5 h-3.5'} animate-spin`} />, label: 'RUNNING' },
    pending: { bg: 'bg-gray-800 border border-gray-700', text: 'text-gray-500', icon: <Clock className={size === 'lg' ? 'w-5 h-5' : 'w-3.5 h-3.5'} />, label: 'PENDING' },
    skip: { bg: 'bg-gray-800 border border-gray-700', text: 'text-gray-600', icon: <div className={`${size === 'lg' ? 'w-5 h-5' : 'w-3.5 h-3.5'} rounded-full bg-gray-700`} />, label: 'SKIP' },
  };
  const c = configs[status];
  return (
    <span className={`inline-flex items-center gap-1 ${size === 'lg' ? 'px-3 py-1' : 'px-2 py-0.5'} rounded-lg ${c.bg} ${c.text} ${size === 'lg' ? 'text-sm' : 'text-xs'} font-medium`}>
      {c.icon}
      {c.label}
    </span>
  );
}

// ── Pipeline stage grid ───────────────────────────────────────────────────────

function PipelineGrid({ result }: { result: E2ETestResult }) {
  const stages: [string, TestStatus][] = [
    ['submission', result.submission],
    ['rag_retrieval', result.rag_retrieval],
    ['triage', result.triage],
    ['log_analysis', result.log_analysis],
    ['root_cause', result.root_cause],
    ['duplicate_detection', result.duplicate_detection],
    ['remediation', result.remediation],
  ];
  return (
    <div className="flex flex-wrap gap-2">
      {stages.map(([key, status]) => (
        <div key={key} className="flex flex-col items-center gap-1">
          <StatusBadge status={status} />
          <span className="text-[10px] text-gray-600">{STAGE_LABELS[key]}</span>
        </div>
      ))}
    </div>
  );
}

// ── Individual test card ──────────────────────────────────────────────────────

function TestCard({ result, index }: { result: E2ETestResult; index: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`bg-gray-900 border rounded-xl overflow-hidden ${
      result.status === 'pass' ? 'border-emerald-800/60' :
      result.status === 'fail' ? 'border-red-800/60' :
      result.status === 'warning' ? 'border-yellow-800/60' :
      'border-gray-800'
    }`}>
      {/* Header row */}
      <div className="flex items-center gap-3 p-4">
        <span className="text-xs font-mono text-gray-500 w-16 shrink-0">{result.test_case}</span>
        <StatusBadge status={result.status} size="lg" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white truncate">{result.title}</p>
          {result.bug_id && (
            <p className="text-xs text-gray-500 font-mono mt-0.5">{result.bug_id}</p>
          )}
        </div>
        {result.total_processing_time && (
          <div className="flex items-center gap-1 text-xs text-gray-500 shrink-0">
            <Clock className="w-3 h-3" />
            {result.total_processing_time}
          </div>
        )}
        <button
          onClick={() => setExpanded(v => !v)}
          className="text-gray-500 hover:text-gray-300 shrink-0"
        >
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Pipeline stages */}
      <div className="px-4 pb-3">
        <PipelineGrid result={result} />
      </div>

      {/* Expanded details */}
      {expanded && (
        <div className="border-t border-gray-800 p-4 space-y-4">
          {/* Errors */}
          {result.errors.length > 0 && (
            <div className="bg-red-900/20 border border-red-800/40 rounded-lg p-3">
              <p className="text-xs font-semibold text-red-400 mb-1">Errors</p>
              {result.errors.map((e, i) => (
                <p key={i} className="text-xs text-red-300">• {e}</p>
              ))}
            </div>
          )}

          {/* Warnings */}
          {result.warnings.length > 0 && (
            <div className="bg-yellow-900/20 border border-yellow-800/40 rounded-lg p-3">
              <p className="text-xs font-semibold text-yellow-400 mb-1">Warnings</p>
              {result.warnings.map((w, i) => (
                <p key={i} className="text-xs text-yellow-300">⚠ {w}</p>
              ))}
            </div>
          )}

          {/* Assertions */}
          {result.assertions.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-400 mb-2">Assertions</p>
              <div className="space-y-1.5">
                {result.assertions.map((a, i) => (
                  <div
                    key={i}
                    className={`flex items-start gap-2 text-xs rounded-lg px-3 py-2 ${
                      a.passed ? 'bg-emerald-900/20' : 'bg-red-900/20'
                    }`}
                  >
                    {a.passed
                      ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
                      : <XCircle className="w-3.5 h-3.5 text-red-400 mt-0.5 shrink-0" />
                    }
                    <div className="flex-1 min-w-0">
                      <span className={`font-medium ${a.passed ? 'text-emerald-300' : 'text-red-300'}`}>
                        {a.name}
                      </span>
                      <div className="flex gap-4 mt-0.5 text-gray-500">
                        <span>Expected: <span className="text-gray-400">{a.expected}</span></span>
                        <span>Actual: <span className="text-gray-400">{a.actual}</span></span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Agent results */}
          {result.agent_results.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-400 mb-2">Agent Results</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {result.agent_results.map((ar, i) => (
                  <div key={i} className="bg-gray-800 rounded-lg px-3 py-2 flex items-start gap-2">
                    <StatusBadge status={ar.status} />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-gray-300">{ar.agent}</p>
                      {ar.detail && <p className="text-xs text-gray-500 mt-0.5 truncate">{ar.detail}</p>}
                      {ar.confidence != null && (
                        <p className="text-xs text-gray-600 mt-0.5">
                          Confidence: {(ar.confidence * 100).toFixed(0)}%
                        </p>
                      )}
                    </div>
                    {ar.durationMs != null && ar.durationMs > 0 && (
                      <span className="text-xs text-gray-600 shrink-0">{ar.durationMs}ms</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Expected values */}
          <div className="flex flex-wrap gap-2">
            {result.severity_expected && (
              <span className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded">
                Expected severity: <span className="text-white">{result.severity_expected}</span>
              </span>
            )}
            {result.component_expected && (
              <span className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded">
                Expected component: <span className="text-white">{result.component_expected}</span>
              </span>
            )}
            {result.exception_expected && (
              <span className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded">
                Expected exception: <span className="text-white font-mono">{result.exception_expected}</span>
              </span>
            )}
            {result.is_duplicate_expected !== undefined && (
              <span className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded">
                Expected duplicate: <span className="text-white">{result.is_duplicate_expected ? 'yes' : 'no'}</span>
              </span>
            )}
            {result.insufficient_evidence_expected && (
              <span className="text-xs bg-yellow-900/30 text-yellow-400 px-2 py-1 rounded">
                Insufficient evidence expected ✓
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Suite summary ─────────────────────────────────────────────────────────────

function SuiteSummary({ suite }: { suite: E2ESuiteResult }) {
  const passRate = suite.total_tests > 0
    ? Math.round((suite.passed / suite.total_tests) * 100)
    : 0;

  return (
    <div className="space-y-4">
      {/* Top stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-white">{suite.total_tests}</p>
          <p className="text-xs text-gray-400">Total Tests</p>
        </div>
        <div className="bg-emerald-900/20 border border-emerald-800/40 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-emerald-400">{suite.passed}</p>
          <p className="text-xs text-gray-400">Passed</p>
        </div>
        <div className="bg-red-900/20 border border-red-800/40 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-red-400">{suite.failed}</p>
          <p className="text-xs text-gray-400">Failed</p>
        </div>
        <div className="bg-yellow-900/20 border border-yellow-800/40 rounded-xl p-4 text-center">
          <p className="text-2xl font-bold text-yellow-400">{suite.warnings}</p>
          <p className="text-xs text-gray-400">Warnings</p>
        </div>
      </div>

      {/* Pass rate bar */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-300">Pass Rate</span>
          <span className="text-lg font-bold text-white">{passRate}%</span>
        </div>
        <div className="h-3 bg-gray-800 rounded-full overflow-hidden">
          <div
            className={`h-3 rounded-full transition-all ${
              passRate >= 80 ? 'bg-emerald-500' : passRate >= 60 ? 'bg-yellow-500' : 'bg-red-500'
            }`}
            style={{ width: `${passRate}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-600 mt-1">
          <span>0%</span>
          <span>{suite.total_duration_ms}ms total</span>
          <span>100%</span>
        </div>
      </div>

      {/* Performance */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <Clock className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-xs text-gray-400">Avg Analysis</span>
          </div>
          <p className="text-lg font-bold text-white">
            {suite.performance.avg_analysis_ms > 0
              ? `${(suite.performance.avg_analysis_ms / 1000).toFixed(1)}s`
              : 'N/A'}
          </p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <Zap className="w-3.5 h-3.5 text-yellow-400" />
            <span className="text-xs text-gray-400">Fastest</span>
          </div>
          <p className="text-lg font-bold text-white">
            {suite.performance.min_analysis_ms > 0
              ? `${(suite.performance.min_analysis_ms / 1000).toFixed(1)}s`
              : 'N/A'}
          </p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <Clock className="w-3.5 h-3.5 text-orange-400" />
            <span className="text-xs text-gray-400">Slowest</span>
          </div>
          <p className="text-lg font-bold text-white">
            {suite.performance.max_analysis_ms > 0
              ? `${(suite.performance.max_analysis_ms / 1000).toFixed(1)}s`
              : 'N/A'}
          </p>
        </div>
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <BarChart3 className="w-3.5 h-3.5 text-purple-400" />
            <span className="text-xs text-gray-400">P95</span>
          </div>
          <p className="text-lg font-bold text-white">
            {suite.performance.p95_analysis_ms > 0
              ? `${(suite.performance.p95_analysis_ms / 1000).toFixed(1)}s`
              : 'N/A'}
          </p>
        </div>
      </div>

      {/* RAG + Duplicate evaluation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* RAG */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Database className="w-4 h-4 text-blue-400" />
            <h4 className="text-sm font-semibold text-gray-200">RAG Evaluation</h4>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="text-center">
              <p className="text-xl font-bold text-white">{suite.rag_evaluation.total_retrievals}</p>
              <p className="text-xs text-gray-500">Retrievals</p>
            </div>
            <div className="text-center">
              <p className="text-xl font-bold text-emerald-400">{suite.rag_evaluation.successful_retrievals}</p>
              <p className="text-xs text-gray-500">Successful</p>
            </div>
            <div className="text-center">
              <p className="text-xl font-bold text-blue-400">
                {suite.rag_evaluation.avg_similarity > 0
                  ? `${(suite.rag_evaluation.avg_similarity * 100).toFixed(0)}%`
                  : 'N/A'}
              </p>
              <p className="text-xs text-gray-500">Avg Sim</p>
            </div>
          </div>
        </div>

        {/* Duplicate detection metrics */}
        {suite.duplicate_evaluation && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <GitBranch className="w-4 h-4 text-purple-400" />
              <h4 className="text-sm font-semibold text-gray-200">Duplicate Detection Metrics</h4>
            </div>
            <div className="grid grid-cols-3 gap-3 mb-3">
              <div className="text-center">
                <p className="text-xl font-bold text-white">
                  {suite.duplicate_evaluation.precision > 0
                    ? `${(suite.duplicate_evaluation.precision * 100).toFixed(0)}%`
                    : 'N/A'}
                </p>
                <p className="text-xs text-gray-500">Precision</p>
              </div>
              <div className="text-center">
                <p className="text-xl font-bold text-white">
                  {suite.duplicate_evaluation.recall > 0
                    ? `${(suite.duplicate_evaluation.recall * 100).toFixed(0)}%`
                    : 'N/A'}
                </p>
                <p className="text-xs text-gray-500">Recall</p>
              </div>
              <div className="text-center">
                <p className="text-xl font-bold text-purple-400">
                  {suite.duplicate_evaluation.f1 > 0
                    ? `${(suite.duplicate_evaluation.f1 * 100).toFixed(0)}%`
                    : 'N/A'}
                </p>
                <p className="text-xs text-gray-500">F1 Score</p>
              </div>
            </div>
            <div className="grid grid-cols-4 gap-1 text-center text-xs">
              <div className="bg-emerald-900/30 rounded p-1">
                <p className="font-bold text-emerald-400">{suite.duplicate_evaluation.true_positives}</p>
                <p className="text-gray-600">TP</p>
              </div>
              <div className="bg-red-900/30 rounded p-1">
                <p className="font-bold text-red-400">{suite.duplicate_evaluation.false_positives}</p>
                <p className="text-gray-600">FP</p>
              </div>
              <div className="bg-emerald-900/20 rounded p-1">
                <p className="font-bold text-emerald-300">{suite.duplicate_evaluation.true_negatives}</p>
                <p className="text-gray-600">TN</p>
              </div>
              <div className="bg-red-900/20 rounded p-1">
                <p className="font-bold text-red-300">{suite.duplicate_evaluation.false_negatives}</p>
                <p className="text-gray-600">FN</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Test scenario overview cards ──────────────────────────────────────────────

const TEST_SCENARIO_DESCRIPTIONS = [
  { id: 'BUG-001', title: 'NullPointerException — User Profile', tags: ['Java', 'NPE', 'Cache'], color: 'border-blue-700/40' },
  { id: 'BUG-002', title: 'DB Connection Pool Exhaustion', tags: ['PostgreSQL', 'Timeout', 'Critical'], color: 'border-red-700/40' },
  { id: 'BUG-003', title: 'API Gateway 500 Error', tags: ['Concurrency', 'Payment', 'REST'], color: 'border-orange-700/40' },
  { id: 'BUG-004', title: 'Memory Leak / OutOfMemoryError', tags: ['JVM', 'Heap', 'Worker'], color: 'border-yellow-700/40' },
  { id: 'BUG-005', title: 'JWT Auth Token Failure', tags: ['Security', 'JWT', 'Auth'], color: 'border-purple-700/40' },
  { id: 'BUG-006', title: 'Known Duplicate (BUG-001)', tags: ['Duplicate', 'NPE', 'Test'], color: 'border-pink-700/40' },
  { id: 'BUG-007', title: 'Related 503 Service Error', tags: ['Non-duplicate', 'Load Balancer'], color: 'border-teal-700/40' },
  { id: 'BUG-008', title: 'Insufficient Evidence', tags: ['Vague', 'No stack trace'], color: 'border-gray-700/40' },
  { id: 'ERR-001', title: 'Invalid submission rejected', tags: ['Error handling', 'API'], color: 'border-gray-700/40' },
  { id: 'ERR-002', title: '404 for non-existent bug', tags: ['Error handling', '404'], color: 'border-gray-700/40' },
  { id: 'ERR-003', title: 'KB incomplete record rejected', tags: ['KB Validation'], color: 'border-gray-700/40' },
];

function ScenarioOverview() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
      {TEST_SCENARIO_DESCRIPTIONS.map(s => (
        <div key={s.id} className={`bg-gray-900 border ${s.color} rounded-xl p-3`}>
          <div className="flex items-center gap-1.5 mb-1.5">
            <span className="text-xs font-mono text-gray-500">{s.id}</span>
          </div>
          <p className="text-xs font-medium text-gray-300 mb-2 leading-tight">{s.title}</p>
          <div className="flex flex-wrap gap-1">
            {s.tags.slice(0, 3).map(t => (
              <span key={t} className="text-[10px] bg-gray-800 text-gray-500 px-1.5 py-0.5 rounded">
                {t}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function E2ETest() {
  const [suiteResult, setSuiteResult] = useState<E2ESuiteResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState({ completed: 0, total: 0, current: '' });
  const [activeView, setActiveView] = useState<'scenarios' | 'results'>('scenarios');
  const [filter, setFilter] = useState<TestStatus | 'all'>('all');

  const handleRunTests = async () => {
    setIsRunning(true);
    setSuiteResult(null);
    setActiveView('results');
    setProgress({ completed: 0, total: 11, current: 'Starting...' });

    try {
      const result = await runE2ETests((completed, total, latest) => {
        setProgress({
          completed,
          total,
          current: `${latest.test_case}: ${latest.title.slice(0, 40)}...`,
        });
      });
      setSuiteResult(result);
    } catch (e: unknown) {
      console.error('E2E test suite failed:', e);
    } finally {
      setIsRunning(false);
      setProgress(p => ({ ...p, current: 'Complete' }));
    }
  };

  const filteredTests = suiteResult?.tests.filter(t =>
    filter === 'all' ? true : t.status === filter
  ) ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-xl font-bold text-white">End-to-End Testing & Validation</h2>
          <p className="text-sm text-gray-400 mt-0.5">
            Complete pipeline validation — 8 bug scenarios + 3 error-handling tests
          </p>
        </div>
        <div className="flex gap-2">
          {suiteResult && (
            <button
              onClick={() => setSuiteResult(null)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded-lg"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Reset
            </button>
          )}
          <button
            onClick={handleRunTests}
            disabled={isRunning}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white text-sm rounded-lg transition-colors font-medium"
          >
            {isRunning ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <PlayCircle className="w-4 h-4" />
            )}
            {isRunning ? 'Running Tests...' : 'Run All Tests'}
          </button>
        </div>
      </div>

      {/* Progress bar while running */}
      {isRunning && (
        <div className="bg-gray-900 border border-blue-700/40 rounded-xl p-4">
          <div className="flex items-center gap-3 mb-3">
            <Loader2 className="w-4 h-4 text-blue-400 animate-spin shrink-0" />
            <span className="text-sm text-blue-300 font-medium">Running test suite...</span>
            <span className="text-sm text-gray-400 ml-auto">{progress.completed}/{progress.total}</span>
          </div>
          <div className="h-2 bg-gray-800 rounded-full overflow-hidden mb-2">
            <div
              className="h-2 bg-blue-500 rounded-full transition-all duration-300"
              style={{ width: `${progress.total > 0 ? (progress.completed / progress.total) * 100 : 0}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 truncate">{progress.current}</p>
        </div>
      )}

      {/* Info banner */}
      {!suiteResult && !isRunning && (
        <div className="bg-blue-900/20 border border-blue-700/40 rounded-xl p-4 flex items-start gap-3">
          <Info className="w-4 h-4 text-blue-400 mt-0.5 shrink-0" />
          <div className="text-sm text-blue-200">
            <p className="font-medium">What this tests</p>
            <p className="text-blue-300/70 mt-1">
              Submits real bugs to the backend, runs the complete M3 pipeline (Triage → Log Analysis →
              Root Cause → Duplicate Detection → Remediation) on each, and evaluates the results
              against expected outcomes. Includes one known duplicate, one insufficient-evidence case,
              and three error-handling edge cases.
            </p>
          </div>
        </div>
      )}

      {/* View tabs */}
      <div className="flex gap-1 bg-gray-900 border border-gray-800 rounded-xl p-1 w-fit">
        <button
          onClick={() => setActiveView('scenarios')}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg transition-colors ${
            activeView === 'scenarios' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          Test Scenarios ({TEST_SCENARIO_DESCRIPTIONS.length})
        </button>
        {suiteResult && (
          <button
            onClick={() => setActiveView('results')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg transition-colors ${
              activeView === 'results' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            Results ({suiteResult.total_tests})
          </button>
        )}
      </div>

      {/* Scenarios overview */}
      {activeView === 'scenarios' && (
        <div>
          <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-blue-400" />
            Test Scenarios
          </h3>
          <ScenarioOverview />

          {/* Pipeline diagram */}
          <div className="mt-6 bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h4 className="text-sm font-semibold text-gray-300 mb-4">Complete Evaluation Pipeline</h4>
            <div className="flex flex-wrap items-center gap-2 text-xs">
              {[
                ['Bug Submission', 'bg-blue-900/40 text-blue-300'],
                ['→', 'text-gray-600'],
                ['RAG Retrieval', 'bg-purple-900/40 text-purple-300'],
                ['→', 'text-gray-600'],
                ['Triage Agent', 'bg-yellow-900/40 text-yellow-300'],
                ['→', 'text-gray-600'],
                ['Log Analysis', 'bg-orange-900/40 text-orange-300'],
                ['→', 'text-gray-600'],
                ['Root Cause', 'bg-red-900/40 text-red-300'],
                ['→', 'text-gray-600'],
                ['Duplicate Detection', 'bg-pink-900/40 text-pink-300'],
                ['→', 'text-gray-600'],
                ['Remediation', 'bg-emerald-900/40 text-emerald-300'],
              ].map((item, i) =>
                item[0] === '→' ? (
                  <span key={i} className={item[1]}>{item[0]}</span>
                ) : (
                  <span key={i} className={`px-2.5 py-1.5 rounded-lg font-medium ${item[1]}`}>
                    {item[0]}
                  </span>
                )
              )}
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      {activeView === 'results' && suiteResult && (
        <div className="space-y-6">
          {/* Suite summary */}
          <div>
            <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-blue-400" />
              Suite Summary
            </h3>
            <SuiteSummary suite={suiteResult} />
          </div>

          {/* Individual test results */}
          <div>
            <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
              <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-blue-400" />
                Individual Test Results
              </h3>
              <div className="flex gap-1">
                {(['all', 'pass', 'warning', 'fail'] as const).map(f => (
                  <button
                    key={f}
                    onClick={() => setFilter(f)}
                    className={`px-3 py-1 text-xs rounded-lg transition-colors ${
                      filter === f
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                    }`}
                  >
                    {f === 'all' ? `All (${suiteResult.total_tests})` : `${f.charAt(0).toUpperCase() + f.slice(1)} (${suiteResult.tests.filter(t => t.status === f).length})`}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              {filteredTests.map((result, i) => (
                <TestCard key={result.test_case} result={result} index={i} />
              ))}
              {filteredTests.length === 0 && (
                <div className="text-center py-8 text-gray-600 text-sm">
                  No tests match the selected filter.
                </div>
              )}
            </div>
          </div>

          {/* Raw JSON export */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <h4 className="text-xs font-semibold text-gray-400 mb-2">Structured Test Report (JSON)</h4>
            <pre className="text-xs text-gray-500 overflow-x-auto bg-gray-950 rounded-lg p-3 max-h-64">
              {JSON.stringify(
                {
                  suite: suiteResult.suite,
                  started_at: suiteResult.started_at,
                  completed_at: suiteResult.completed_at,
                  total_tests: suiteResult.total_tests,
                  passed: suiteResult.passed,
                  failed: suiteResult.failed,
                  warnings: suiteResult.warnings,
                  total_duration_ms: suiteResult.total_duration_ms,
                  performance: suiteResult.performance,
                  rag_evaluation: suiteResult.rag_evaluation,
                  duplicate_evaluation: suiteResult.duplicate_evaluation,
                  test_cases: suiteResult.tests.map(t => ({
                    test_case: t.test_case,
                    status: t.status,
                    total_processing_time: t.total_processing_time,
                    submission: t.submission,
                    rag_retrieval: t.rag_retrieval,
                    triage: t.triage,
                    log_analysis: t.log_analysis,
                    root_cause: t.root_cause,
                    duplicate_detection: t.duplicate_detection,
                    remediation: t.remediation,
                  })),
                },
                null,
                2
              )}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
