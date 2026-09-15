import { Bug, AnalysisResult } from '../types';
import {
  Shield, FileSearch, Target, Copy, Wrench,
  AlertTriangle, CheckCircle, Clock, ArrowRight,
  Zap, Brain, Search, Lightbulb
} from 'lucide-react';

interface BugAnalysisProps {
  bug: Bug | null;
  analysis: AnalysisResult | null;
}

export default function BugAnalysis({ bug, analysis }: BugAnalysisProps) {
  if (!analysis) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Brain className="w-20 h-20 text-gray-700 mb-4" />
        <h3 className="text-xl font-semibold text-gray-300 mb-2">No Analysis Results</h3>
        <p className="text-sm text-gray-500 text-center max-w-md">
          Submit a bug and run the AI analysis pipeline to see results here.
          The system will perform triage, log analysis, root cause identification,
          duplicate detection, and remediation suggestions.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Analysis Results</h2>
            <p className="text-xs text-gray-400">Bug ID: {analysis.bugId} • {new Date(analysis.timestamp).toLocaleString()}</p>
          </div>
        </div>
        {bug && <p className="text-sm text-gray-300 mt-2">{bug.title}</p>}
      </div>

      {/* Agent Pipeline Results */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Triage Agent */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-blue-400" />
            <h3 className="font-semibold text-white">Triage Agent</h3>
            <span className="ml-auto text-xs px-2 py-0.5 bg-green-900/30 text-green-400 rounded-full border border-green-700/50">Complete</span>
          </div>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">Severity</p>
                <SeverityBadge severity={analysis.triage.severity} />
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">Priority</p>
                <span className="text-lg font-bold text-white">{analysis.triage.priority}</span>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">Category</p>
                <span className="text-sm text-white">{analysis.triage.category}</span>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">Component</p>
                <span className="text-sm text-white">{analysis.triage.component}</span>
              </div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-xs text-gray-400 mb-1">Confidence</p>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-gray-700 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${analysis.triage.confidence * 100}%` }} />
                </div>
                <span className="text-xs text-gray-300">{(analysis.triage.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
            <p className="text-xs text-gray-400 italic">{analysis.triage.reasoning}</p>
          </div>
        </div>

        {/* Log Analysis Agent */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <FileSearch className="w-5 h-5 text-purple-400" />
            <h3 className="font-semibold text-white">Log Analysis Agent</h3>
            <span className="ml-auto text-xs px-2 py-0.5 bg-green-900/30 text-green-400 rounded-full border border-green-700/50">Complete</span>
          </div>
          <div className="space-y-3">
            {/* M2: Failure Point & Code Path */}
            {(analysis.logAnalysis.failurePoint || analysis.logAnalysis.codePath) && (
              <div className="grid grid-cols-2 gap-3">
                {analysis.logAnalysis.failurePoint && (
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <p className="text-xs text-gray-400 mb-1">Failure Point</p>
                    <p className="text-sm text-white font-mono">{analysis.logAnalysis.failurePoint}</p>
                  </div>
                )}
                {analysis.logAnalysis.codePath && (
                  <div className="bg-gray-800/50 rounded-lg p-3">
                    <p className="text-xs text-gray-400 mb-1">Code Path</p>
                    <p className="text-sm text-white font-mono truncate">{analysis.logAnalysis.codePath}</p>
                  </div>
                )}
              </div>
            )}
            
            <div>
              <p className="text-xs text-gray-400 mb-2">Exceptions Found ({analysis.logAnalysis.exceptions.length})</p>
              <div className="space-y-1.5">
                {analysis.logAnalysis.exceptions.map((exc, i) => (
                  <div key={i} className="bg-gray-800/50 rounded p-2 text-xs">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-red-400 font-mono">{exc.exceptionType || exc.type}</span>
                      {exc.confidence && (
                        <span className="text-xs text-gray-500">{(exc.confidence * 100).toFixed(0)}%</span>
                      )}
                    </div>
                    <p className="text-gray-400 mt-0.5 truncate">{exc.errorMessage || exc.message}</p>
                    {(exc.fileName || exc.className || exc.methodName) && (
                      <div className="mt-1 flex flex-wrap gap-2 text-gray-500">
                        {exc.fileName && <span className="font-mono">{exc.fileName}</span>}
                        {exc.lineNumber && <span>:line {exc.lineNumber}</span>}
                        {exc.className && <span className="text-blue-400">{exc.className}</span>}
                        {exc.methodName && <span className="text-green-400">.{exc.methodName}()</span>}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-1">Error Patterns</p>
              <div className="flex flex-wrap gap-1.5">
                {analysis.logAnalysis.errorPatterns.map((p, i) => (
                  <span key={i} className="text-xs px-2 py-1 bg-orange-900/20 text-orange-300 rounded border border-orange-700/30">
                    {p}
                  </span>
                ))}
              </div>
            </div>
            {/* M2: Confidence */}
            {analysis.logAnalysis.confidence && (
              <div className="flex items-center gap-2">
                <p className="text-xs text-gray-400">Confidence:</p>
                <div className="flex-1 bg-gray-700 rounded-full h-2">
                  <div className="bg-purple-500 h-2 rounded-full" style={{ width: `${analysis.logAnalysis.confidence * 100}%` }} />
                </div>
                <span className="text-xs text-gray-300">{(analysis.logAnalysis.confidence * 100).toFixed(0)}%</span>
              </div>
            )}
            <p className="text-xs text-gray-400 italic">{analysis.logAnalysis.summary}</p>
          </div>
        </div>

        {/* Root Cause Agent */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Target className="w-5 h-5 text-orange-400" />
            <h3 className="font-semibold text-white">Root Cause Agent</h3>
            <span className="ml-auto text-xs px-2 py-0.5 bg-green-900/30 text-green-400 rounded-full border border-green-700/50">Complete</span>
          </div>
          <div className="space-y-3">
            <div className="bg-orange-900/10 border border-orange-700/30 rounded-lg p-3">
              <p className="text-xs text-orange-300 font-medium mb-1">Probable Root Cause</p>
              <p className="text-sm text-white">{analysis.rootCause.probableCause}</p>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-1">Evidence</p>
              <ul className="space-y-1">
                {analysis.rootCause.evidence.map((e, i) => (
                  <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                    <CheckCircle className="w-3 h-3 text-green-500 mt-0.5 shrink-0" />
                    {e}
                  </li>
                ))}
              </ul>
            </div>
            <div className="flex items-center gap-2">
              <p className="text-xs text-gray-400">Confidence:</p>
              <div className="flex-1 bg-gray-700 rounded-full h-2">
                <div className="bg-orange-500 h-2 rounded-full" style={{ width: `${analysis.rootCause.confidence * 100}%` }} />
              </div>
              <span className="text-xs text-gray-300">{(analysis.rootCause.confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>

        {/* Duplicate Detection Agent */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Copy className="w-5 h-5 text-green-400" />
            <h3 className="font-semibold text-white">Duplicate Detection Agent</h3>
            <span className="ml-auto text-xs px-2 py-0.5 bg-green-900/30 text-green-400 rounded-full border border-green-700/50">Complete</span>
          </div>
          <div className="space-y-3">
            <div className="flex items-center gap-4">
              <div className={`px-3 py-1.5 rounded-lg border text-sm font-medium ${
                analysis.duplicateDetection.isDuplicate
                  ? 'bg-red-900/20 border-red-700/50 text-red-300'
                  : 'bg-green-900/20 border-green-700/50 text-green-300'
              }`}>
                {analysis.duplicateDetection.isDuplicate ? '⚠️ Likely Duplicate' : '✓ Unique Bug'}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">Similarity Score</p>
                <p className="text-lg font-bold text-white">{(analysis.duplicateDetection.similarityScore * 100).toFixed(1)}%</p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">Duplicate Probability</p>
                <p className="text-lg font-bold text-white">{(analysis.duplicateDetection.duplicateProbability * 100).toFixed(1)}%</p>
              </div>
            </div>
            <div>
              <p className="text-xs text-gray-400 mb-2">Matching Historical Bugs</p>
              <div className="space-y-1.5">
                {analysis.duplicateDetection.matchingBugs.slice(0, 3).map((mb, i) => (
                  <div key={i} className="bg-gray-800/50 rounded p-2 flex items-center justify-between">
                    <div className="min-w-0">
                      <p className="text-xs text-white truncate">{mb.title}</p>
                      <p className="text-xs text-gray-500">{mb.bugId} • {mb.project}</p>
                    </div>
                    <span className="text-xs text-blue-400 font-mono shrink-0 ml-2">{(mb.similarity * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Remediation Agent - Full Width */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <div className="flex items-center gap-2 mb-4">
          <Wrench className="w-5 h-5 text-red-400" />
          <h3 className="font-semibold text-white">Remediation Agent</h3>
          <span className="ml-auto text-xs px-2 py-0.5 bg-green-900/30 text-green-400 rounded-full border border-green-700/50">Complete</span>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <div className="bg-green-900/10 border border-green-700/30 rounded-lg p-4 mb-4">
              <p className="text-xs text-green-300 font-medium mb-2 flex items-center gap-1">
                <Lightbulb className="w-3 h-3" /> Suggested Fix
              </p>
              <p className="text-sm text-white leading-relaxed">{analysis.remediation.suggestedFix}</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <p className="text-xs text-gray-400 mb-2 flex items-center gap-1"><Zap className="w-3 h-3" /> Debugging Steps</p>
                <ol className="space-y-1">
                  {analysis.remediation.debuggingSteps.map((s, i) => (
                    <li key={i} className="text-xs text-gray-300 flex items-start gap-1.5">
                      <span className="text-blue-400 font-mono">{i + 1}.</span> {s}
                    </li>
                  ))}
                </ol>
              </div>
              <div>
                <p className="text-xs text-gray-400 mb-2 flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Validation</p>
                <ol className="space-y-1">
                  {analysis.remediation.validationSteps.map((s, i) => (
                    <li key={i} className="text-xs text-gray-300 flex items-start gap-1.5">
                      <span className="text-green-400 font-mono">{i + 1}.</span> {s}
                    </li>
                  ))}
                </ol>
              </div>
              <div>
                <p className="text-xs text-gray-400 mb-2 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> Regression Tests</p>
                <ol className="space-y-1">
                  {analysis.remediation.regressionTests.map((s, i) => (
                    <li key={i} className="text-xs text-gray-300 flex items-start gap-1.5">
                      <span className="text-orange-400 font-mono">{i + 1}.</span> {s}
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          </div>
          <div className="space-y-3">
            <div className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-xs text-gray-400 mb-1">Estimated Effort</p>
              <p className="text-sm font-medium text-white">{analysis.remediation.estimatedEffort}</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-xs text-gray-400 mb-1">Risk Level</p>
              <span className={`text-sm font-medium ${
                analysis.remediation.riskLevel === 'high' ? 'text-red-400' :
                analysis.remediation.riskLevel === 'medium' ? 'text-yellow-400' : 'text-green-400'
              }`}>
                {analysis.remediation.riskLevel.toUpperCase()}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const styles: Record<string, string> = {
    critical: 'bg-red-900/40 text-red-300 border-red-700/50',
    high: 'bg-orange-900/40 text-orange-300 border-orange-700/50',
    medium: 'bg-yellow-900/40 text-yellow-300 border-yellow-700/50',
    low: 'bg-blue-900/40 text-blue-300 border-blue-700/50',
  };
  return (
    <span className={`text-sm font-bold px-2 py-0.5 rounded border ${styles[severity] || ''}`}>
      {severity.toUpperCase()}
    </span>
  );
}
