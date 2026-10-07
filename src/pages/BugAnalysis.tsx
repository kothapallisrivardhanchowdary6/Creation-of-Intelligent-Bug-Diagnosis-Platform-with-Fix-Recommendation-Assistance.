/**
 * BugAnalysis — Milestone 3
 *
 * Renders all 5 agent result cards:
 *   1. Triage
 *   2. Log Analysis
 *   3. Root Cause          — evidence vs reasoning clearly separated
 *   4. Duplicate Detection — real similarity scores, per-match classification
 *   5. Remediation         — fix source label, implementation steps, historical resolutions
 *
 * Results shown are always for the bug currently being analyzed.
 * No hardcoded / reused values.
 */

import { Bug, AnalysisResult, RootCauseResult, DuplicateDetectionResult, RemediationResult } from '../types';
import {
  Shield, FileSearch, Target, Copy, Wrench,
  AlertTriangle, CheckCircle, Clock, ArrowRight,
  Zap, Brain, Lightbulb, Database, GitMerge,
  ChevronRight, Info, AlertCircle, BookOpen,
} from 'lucide-react';

interface BugAnalysisProps {
  bug: Bug | null;
  analysis: AnalysisResult | null;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function ConfidenceBar({ value, color = 'blue' }: { value: number; color?: string }) {
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
    orange: 'bg-orange-500',
    green: 'bg-green-500',
    red: 'bg-red-500',
    yellow: 'bg-yellow-500',
  };
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-700 rounded-full h-2">
        <div
          className={`${colorMap[color] ?? 'bg-blue-500'} h-2 rounded-full transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-300 tabular-nums w-9 text-right">{pct}%</span>
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
    <span className={`text-sm font-bold px-2 py-0.5 rounded border ${styles[severity] ?? styles.medium}`}>
      {severity.toUpperCase()}
    </span>
  );
}

function AgentStatusBadge({ status }: { status?: string }) {
  if (status === 'error') {
    return (
      <span className="ml-auto text-xs px-2 py-0.5 bg-red-900/30 text-red-400 rounded-full border border-red-700/50">
        Error
      </span>
    );
  }
  if (status === 'insufficient_evidence') {
    return (
      <span className="ml-auto text-xs px-2 py-0.5 bg-yellow-900/30 text-yellow-400 rounded-full border border-yellow-700/50">
        Insufficient Evidence
      </span>
    );
  }
  return (
    <span className="ml-auto text-xs px-2 py-0.5 bg-green-900/30 text-green-400 rounded-full border border-green-700/50">
      Complete
    </span>
  );
}

/** Label pill for fix source (historical / best practice / agent reasoning). */
function FixSourceBadge({ source }: { source: string }) {
  if (source === 'historical_evidence') {
    return (
      <span className="text-xs px-2 py-0.5 bg-green-900/30 text-green-300 rounded border border-green-700/30 flex items-center gap-1">
        <Database className="w-3 h-3" /> Historical Evidence
      </span>
    );
  }
  if (source === 'best_practice') {
    return (
      <span className="text-xs px-2 py-0.5 bg-blue-900/30 text-blue-300 rounded border border-blue-700/30 flex items-center gap-1">
        <BookOpen className="w-3 h-3" /> Best Practice
      </span>
    );
  }
  return (
    <span className="text-xs px-2 py-0.5 bg-purple-900/30 text-purple-300 rounded border border-purple-700/30 flex items-center gap-1">
      <Brain className="w-3 h-3" /> Agent Reasoning
    </span>
  );
}

/** Classification badge for duplicate detection. */
function ClassificationBadge({ classification }: { classification: string }) {
  const map: Record<string, { cls: string; label: string }> = {
    likely_duplicate: {
      cls: 'bg-red-900/30 text-red-300 border-red-700/40',
      label: '⚠ Likely Duplicate',
    },
    related_issue: {
      cls: 'bg-yellow-900/30 text-yellow-300 border-yellow-700/40',
      label: '~ Related Issue',
    },
    new_unmatched: {
      cls: 'bg-green-900/30 text-green-300 border-green-700/40',
      label: '✓ New / Unique',
    },
    insufficient_evidence: {
      cls: 'bg-gray-800 text-gray-400 border-gray-700',
      label: '? Insufficient Evidence',
    },
  };
  const { cls, label } = map[classification] ?? map.insufficient_evidence;
  return (
    <span className={`text-sm font-medium px-3 py-1.5 rounded-lg border ${cls}`}>
      {label}
    </span>
  );
}

// ── Empty State ───────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <Brain className="w-20 h-20 text-gray-700 mb-4" />
      <h3 className="text-xl font-semibold text-gray-300 mb-2">No Analysis Results</h3>
      <p className="text-sm text-gray-500 text-center max-w-md">
        Submit a bug and run the AI analysis pipeline to see results here.
        The system runs five agents: Triage → Log Analysis → Root Cause →
        Duplicate Detection → Remediation.
      </p>
    </div>
  );
}

// ── Section Divider ───────────────────────────────────────────────────────────

function SectionDivider({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 py-1">
      <div className="h-px flex-1 bg-gray-700/60" />
      <span className="text-xs text-gray-500 uppercase tracking-wider">{label}</span>
      <div className="h-px flex-1 bg-gray-700/60" />
    </div>
  );
}

// ── Agent Cards ───────────────────────────────────────────────────────────────

function TriageCard({ analysis }: { analysis: AnalysisResult }) {
  const t = analysis.triage;
  const agentStatus = analysis.agents?.triage?.status;
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Shield className="w-5 h-5 text-blue-400" />
        <h3 className="font-semibold text-white">Triage Agent</h3>
        <AgentStatusBadge status={agentStatus ?? 'success'} />
      </div>
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-800/50 rounded-lg p-3">
            <p className="text-xs text-gray-400 mb-1">Severity</p>
            <SeverityBadge severity={t.severity} />
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <p className="text-xs text-gray-400 mb-1">Priority</p>
            <span className="text-lg font-bold text-white">{t.priority}</span>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <p className="text-xs text-gray-400 mb-1">Category</p>
            <span className="text-sm text-white">{t.category}</span>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <p className="text-xs text-gray-400 mb-1">Component</p>
            <span className="text-sm text-white">{t.component}</span>
          </div>
        </div>
        <div className="bg-gray-800/50 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-2">Confidence</p>
          <ConfidenceBar value={t.confidence} color="blue" />
        </div>
        <p className="text-xs text-gray-400 italic leading-relaxed">{t.reasoning}</p>
      </div>
    </div>
  );
}

function LogAnalysisCard({ analysis }: { analysis: AnalysisResult }) {
  const la = analysis.logAnalysis;
  const agentStatus = analysis.agents?.log_analysis?.status;
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <FileSearch className="w-5 h-5 text-purple-400" />
        <h3 className="font-semibold text-white">Log Analysis Agent</h3>
        <AgentStatusBadge status={agentStatus ?? 'success'} />
      </div>
      <div className="space-y-3">
        {(la.failurePoint || la.codePath) && (
          <div className="grid grid-cols-2 gap-3">
            {la.failurePoint && (
              <div className="bg-gray-800/50 rounded-lg p-3 col-span-1">
                <p className="text-xs text-gray-400 mb-1">Failure Point</p>
                <p className="text-xs text-white font-mono break-all">{la.failurePoint}</p>
              </div>
            )}
            {la.codePath && (
              <div className="bg-gray-800/50 rounded-lg p-3 col-span-1">
                <p className="text-xs text-gray-400 mb-1">Code Path</p>
                <p className="text-xs text-white font-mono truncate">{la.codePath}</p>
              </div>
            )}
          </div>
        )}

        <div>
          <p className="text-xs text-gray-400 mb-2">
            Exceptions Found ({la.exceptions.length})
          </p>
          {la.exceptions.length === 0 ? (
            <p className="text-xs text-gray-500 italic">No structured exceptions parsed.</p>
          ) : (
            <div className="space-y-1.5">
              {la.exceptions.map((exc, i) => (
                <div key={i} className="bg-gray-800/50 rounded p-2 text-xs">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-red-400 font-mono font-medium">
                      {exc.exceptionType ?? exc.type ?? 'Unknown'}
                    </span>
                    {exc.confidence != null && (
                      <span className="text-gray-500 tabular-nums">
                        {Math.round(exc.confidence * 100)}%
                      </span>
                    )}
                  </div>
                  <p className="text-gray-400 mt-0.5 truncate">
                    {exc.errorMessage ?? exc.message ?? ''}
                  </p>
                  {(exc.fileName ?? exc.className ?? exc.methodName) && (
                    <div className="mt-1 flex flex-wrap gap-2 text-gray-500">
                      {exc.fileName && <span className="font-mono">{exc.fileName}</span>}
                      {(exc.lineNumber ?? exc.line) && (
                        <span>:line {exc.lineNumber ?? exc.line}</span>
                      )}
                      {exc.className && (
                        <span className="text-blue-400">{exc.className}</span>
                      )}
                      {exc.methodName && (
                        <span className="text-green-400">.{exc.methodName}()</span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {la.errorPatterns.length > 0 && (
          <div>
            <p className="text-xs text-gray-400 mb-1.5">Error Patterns</p>
            <div className="flex flex-wrap gap-1.5">
              {la.errorPatterns.map((p, i) => (
                <span
                  key={i}
                  className="text-xs px-2 py-0.5 bg-orange-900/20 text-orange-300 rounded border border-orange-700/30"
                >
                  {p}
                </span>
              ))}
            </div>
          </div>
        )}

        {la.confidence != null && (
          <div>
            <p className="text-xs text-gray-400 mb-1.5">Confidence</p>
            <ConfidenceBar value={la.confidence} color="purple" />
          </div>
        )}

        <p className="text-xs text-gray-400 italic leading-relaxed">{la.summary}</p>
      </div>
    </div>
  );
}

function RootCauseCard({ rc }: { rc: RootCauseResult }) {
  const isInsufficient = rc.status === 'insufficient_evidence';
  const isError = rc.status === 'error';

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Target className="w-5 h-5 text-orange-400" />
        <h3 className="font-semibold text-white">Root Cause Agent</h3>
        <AgentStatusBadge status={rc.status} />
      </div>

      {isInsufficient ? (
        <div className="bg-yellow-900/10 border border-yellow-700/30 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-yellow-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-medium text-yellow-300 mb-1">Insufficient Evidence</p>
              <p className="text-xs text-gray-400">
                {rc.insufficientEvidenceReason ?? 'Not enough data to determine root cause.'}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Probable cause */}
          <div className="bg-orange-900/10 border border-orange-700/30 rounded-lg p-3">
            <p className="text-xs text-orange-300 font-medium mb-1">Probable Root Cause</p>
            <p className="text-sm text-white leading-relaxed">{rc.probableCause}</p>
          </div>

          {/* Confidence */}
          <div>
            <p className="text-xs text-gray-400 mb-1.5">Confidence</p>
            <ConfidenceBar value={rc.confidence} color="orange" />
          </div>

          {/* Hypotheses */}
          {rc.hypotheses.length > 0 && (
            <div>
              <SectionDivider label="Hypotheses" />
              <div className="space-y-2 mt-2">
                {rc.hypotheses.map((h, i) => (
                  <div key={i} className="bg-gray-800/40 rounded-lg p-2.5">
                    <div className="flex items-start gap-2">
                      <ChevronRight className="w-3 h-3 text-orange-400 mt-0.5 shrink-0" />
                      <p className="text-xs text-white leading-relaxed">{h.hypothesis}</p>
                    </div>
                    {h.causalChain && (
                      <p className="text-xs text-gray-500 font-mono mt-1 pl-5">
                        {h.causalChain}
                      </p>
                    )}
                    {h.supportingEvidence.length > 0 && (
                      <ul className="mt-1.5 pl-5 space-y-0.5">
                        {h.supportingEvidence.slice(0, 3).map((e, j) => (
                          <li key={j} className="text-xs text-gray-400 flex items-start gap-1.5">
                            <CheckCircle className="w-3 h-3 text-green-500 mt-0.5 shrink-0" />
                            {e}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Reasoning — agent inference */}
          {rc.reasoning && (
            <div>
              <SectionDivider label="Agent Reasoning" />
              <div className="mt-2 bg-gray-800/30 rounded-lg p-2.5 border-l-2 border-orange-700/50">
                <div className="flex items-center gap-1.5 mb-1">
                  <Brain className="w-3 h-3 text-orange-400" />
                  <span className="text-xs text-orange-300 font-medium">Inferred (not from evidence)</span>
                </div>
                <p className="text-xs text-gray-400 leading-relaxed">{rc.agentReasoning || rc.reasoning}</p>
              </div>
            </div>
          )}

          {/* Retrieved Evidence from ChromaDB */}
          {rc.retrievedEvidence.length > 0 && (
            <div>
              <SectionDivider label="Retrieved Historical Evidence" />
              <div className="mt-2 space-y-1.5">
                {rc.retrievedEvidence.slice(0, 3).map((ev, i) => (
                  <div key={i} className="bg-gray-800/40 rounded p-2 flex items-start gap-2">
                    <Database className="w-3 h-3 text-blue-400 mt-0.5 shrink-0" />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-blue-400 font-mono font-medium">{ev.bugId}</span>
                        <span className="text-xs text-gray-500 tabular-nums">{(ev.similarityScore * 100).toFixed(1)}% similar</span>
                        {ev.component && (
                          <span className="text-xs text-gray-600">{ev.component}</span>
                        )}
                      </div>
                      <p className="text-xs text-gray-400 truncate mt-0.5">{ev.document}</p>
                      {ev.resolution && (
                        <p className="text-xs text-green-400/70 truncate mt-0.5">
                          Resolution: {ev.resolution}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-600 mt-1.5 italic">{rc.evidenceSummary}</p>
            </div>
          )}

          {/* Related components */}
          {rc.relatedComponents.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {rc.relatedComponents.map((c, i) => (
                <span key={i} className="text-xs px-2 py-0.5 bg-gray-800 text-gray-400 rounded border border-gray-700">
                  {c}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function DuplicateDetectionCard({ dd }: { dd: DuplicateDetectionResult }) {
  const isInsufficient = dd.classification === 'insufficient_evidence';

  // Use matchedBugs (M3) with fallback to matchingBugs (legacy)
  const displayBugs =
    dd.matchedBugs.length > 0
      ? dd.matchedBugs.map(m => ({
          bugId: m.bugId,
          title: m.title,
          score: m.similarityScore,
          cls: m.classification,
          component: m.component,
          severity: m.severity,
          resolution: m.resolutionSummary,
        }))
      : (dd.matchingBugs ?? []).map(m => ({
          bugId: m.bugId,
          title: m.title,
          score: m.similarity,
          cls: m.similarity >= 0.82 ? 'likely_duplicate' : m.similarity >= 0.55 ? 'related_issue' : 'new_unmatched',
          component: m.component,
          severity: m.severity,
          resolution: m.resolution,
        }));

  const thresholds = dd.thresholdsUsed ?? { likely_duplicate: 0.82, related_issue: 0.55 };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Copy className="w-5 h-5 text-green-400" />
        <h3 className="font-semibold text-white">Duplicate Detection Agent</h3>
        <AgentStatusBadge status={isInsufficient ? 'insufficient_evidence' : 'success'} />
      </div>

      <div className="space-y-3">
        {/* Overall classification */}
        <div className="flex items-center gap-3 flex-wrap">
          <ClassificationBadge classification={dd.classification} />
        </div>

        {!isInsufficient && (
          <>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">Top Match Similarity</p>
                <p className="text-lg font-bold text-white tabular-nums">
                  {(dd.topMatchSimilarity * 100).toFixed(1)}%
                </p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-1">Duplicate Probability</p>
                <p className="text-lg font-bold text-white tabular-nums">
                  {(dd.duplicateProbability * 100).toFixed(1)}%
                </p>
              </div>
            </div>

            {/* Thresholds used */}
            <div className="bg-gray-800/30 rounded-lg p-2.5 text-xs text-gray-500">
              <span className="font-medium text-gray-400">Thresholds: </span>
              Likely duplicate ≥ {(thresholds.likely_duplicate * 100).toFixed(0)}%  •  
              Related issue ≥ {(thresholds.related_issue * 100).toFixed(0)}%
            </div>

            {/* Matched bugs */}
            {displayBugs.length > 0 && (
              <div>
                <p className="text-xs text-gray-400 mb-2">
                  Top Matches ({displayBugs.length})
                </p>
                <div className="space-y-1.5">
                  {displayBugs.slice(0, 5).map((mb, i) => {
                    const clsColor =
                      mb.cls === 'likely_duplicate'
                        ? 'text-red-400 border-red-700/30 bg-red-900/10'
                        : mb.cls === 'related_issue'
                        ? 'text-yellow-400 border-yellow-700/30 bg-yellow-900/10'
                        : 'text-gray-500 border-gray-700/30 bg-gray-800/20';
                    return (
                      <div
                        key={i}
                        className={`rounded p-2 border flex items-start gap-2 ${clsColor}`}
                      >
                        <GitMerge className="w-3 h-3 mt-0.5 shrink-0" />
                        <div className="min-w-0 flex-1">
                          <p className="text-xs text-white truncate">{mb.title}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-xs font-mono">{mb.bugId}</span>
                            {mb.component && (
                              <span className="text-xs text-gray-500">{mb.component}</span>
                            )}
                            {mb.severity && (
                              <span className="text-xs text-gray-600">{mb.severity}</span>
                            )}
                          </div>
                          {mb.resolution && (
                            <p className="text-xs text-green-400/60 truncate mt-0.5">
                              {mb.resolution}
                            </p>
                          )}
                        </div>
                        <span className="text-xs font-mono tabular-nums shrink-0 ml-1">
                          {(mb.score * 100).toFixed(1)}%
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        )}

        <p className="text-xs text-gray-500 italic leading-relaxed">
          {dd.analysisSummary || dd.classification}
        </p>
      </div>
    </div>
  );
}

function RemediationCard({ rem }: { rem: RemediationResult }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <Wrench className="w-5 h-5 text-red-400" />
        <h3 className="font-semibold text-white">Remediation Agent</h3>
        <AgentStatusBadge status={rem.status} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Main area */}
        <div className="lg:col-span-2 space-y-4">
          {/* Suggested fix with source label */}
          <div className="bg-green-900/10 border border-green-700/30 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <Lightbulb className="w-3.5 h-3.5 text-green-400" />
              <p className="text-xs text-green-300 font-medium">Suggested Fix</p>
              <FixSourceBadge source={rem.fixSource} />
            </div>
            <p className="text-sm text-white leading-relaxed">{rem.suggestedFix}</p>
          </div>

          {/* Confidence */}
          <div>
            <p className="text-xs text-gray-400 mb-1.5">Confidence</p>
            <ConfidenceBar value={rem.confidence} color="green" />
          </div>

          {/* Implementation steps */}
          {rem.implementationSteps.length > 0 && (
            <div>
              <SectionDivider label="Implementation Steps" />
              <ol className="mt-2 space-y-2">
                {rem.implementationSteps.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs">
                    <span className="text-red-400 font-mono shrink-0 w-5">{i + 1}.</span>
                    <div className="flex-1">
                      <div className="flex items-start gap-2 flex-wrap">
                        <span className={s.isSpeculative ? 'text-gray-400' : 'text-white'}>
                          {s.step}
                        </span>
                        {s.isSpeculative && (
                          <span className="text-xs px-1.5 py-0.5 bg-purple-900/30 text-purple-300 rounded border border-purple-700/30 shrink-0">
                            Inferred
                          </span>
                        )}
                      </div>
                      {s.detail && (
                        <p className="text-gray-500 font-mono mt-0.5 text-xs">{s.detail}</p>
                      )}
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Three-column steps */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <StepList
              title="Debugging Steps"
              icon={<Zap className="w-3 h-3" />}
              steps={rem.debuggingSteps}
              accentColor="text-blue-400"
            />
            <StepList
              title="Validation"
              icon={<CheckCircle className="w-3 h-3" />}
              steps={rem.validationSteps}
              accentColor="text-green-400"
            />
            <StepList
              title="Regression Tests"
              icon={<AlertTriangle className="w-3 h-3" />}
              steps={rem.regressionTests}
              accentColor="text-orange-400"
            />
          </div>

          {/* Historical resolutions */}
          {rem.historicalResolutions.length > 0 && (
            <div>
              <SectionDivider label="Historical Resolutions (from Knowledge Base)" />
              <div className="mt-2 space-y-1.5">
                {rem.historicalResolutions.slice(0, 3).map((r, i) => (
                  <div key={i} className="bg-gray-800/40 rounded p-2 flex items-start gap-2">
                    <Database className="w-3 h-3 text-green-400 mt-0.5 shrink-0" />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-green-400 font-mono font-medium">{r.bugId}</span>
                        <span className="text-xs text-gray-500 tabular-nums">
                          {(r.similarityScore * 100).toFixed(1)}% similar
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 truncate mt-0.5">{r.document}</p>
                      <p className="text-xs text-white mt-0.5 leading-relaxed">{r.resolution}</p>
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-600 mt-1.5 italic">{rem.evidenceSummary}</p>
            </div>
          )}

          {/* Best practices */}
          {rem.bestPractices.length > 0 && (
            <div>
              <SectionDivider label="Best Practices" />
              <ul className="mt-2 space-y-1">
                {rem.bestPractices.map((p, i) => (
                  <li key={i} className="text-xs text-gray-400 flex items-start gap-2">
                    <BookOpen className="w-3 h-3 text-blue-400 mt-0.5 shrink-0" />
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Agent reasoning note */}
          {rem.agentReasoning && (
            <div className="bg-gray-800/30 rounded-lg p-2.5 border-l-2 border-purple-700/50">
              <div className="flex items-center gap-1.5 mb-1">
                <Brain className="w-3 h-3 text-purple-400" />
                <span className="text-xs text-purple-300 font-medium">Agent Reasoning</span>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">{rem.agentReasoning}</p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-3">
          <div className="bg-gray-800/50 rounded-lg p-3">
            <p className="text-xs text-gray-400 mb-1">Estimated Effort</p>
            <p className="text-sm font-medium text-white">{rem.estimatedEffort}</p>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <p className="text-xs text-gray-400 mb-1">Risk Level</p>
            <span
              className={`text-sm font-bold ${
                rem.riskLevel === 'high'
                  ? 'text-red-400'
                  : rem.riskLevel === 'medium'
                  ? 'text-yellow-400'
                  : 'text-green-400'
              }`}
            >
              {rem.riskLevel.toUpperCase()}
            </span>
          </div>
          <div className="bg-gray-800/50 rounded-lg p-3">
            <p className="text-xs text-gray-400 mb-1">Fix Source</p>
            <FixSourceBadge source={rem.fixSource} />
          </div>
        </div>
      </div>
    </div>
  );
}

function StepList({
  title,
  icon,
  steps,
  accentColor,
}: {
  title: string;
  icon: React.ReactNode;
  steps: string[];
  accentColor: string;
}) {
  if (steps.length === 0) return null;
  return (
    <div>
      <p className={`text-xs text-gray-400 mb-2 flex items-center gap-1 ${accentColor}`}>
        {icon} {title}
      </p>
      <ol className="space-y-1">
        {steps.map((s, i) => (
          <li key={i} className="text-xs text-gray-300 flex items-start gap-1.5">
            <span className={`font-mono shrink-0 ${accentColor}`}>{i + 1}.</span>
            {s}
          </li>
        ))}
      </ol>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function BugAnalysis({ bug, analysis }: BugAnalysisProps) {
  if (!analysis) return <EmptyState />;

  const duration = analysis.totalDuration
    ? `${analysis.totalDuration.toFixed(2)}s`
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shrink-0">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-lg font-bold text-white">Analysis Results</h2>
              {analysis.milestone && (
                <span className="text-xs px-2 py-0.5 bg-blue-900/30 text-blue-300 rounded border border-blue-700/30">
                  {analysis.milestone}
                </span>
              )}
            </div>
            <p className="text-xs text-gray-400 mt-0.5">
              Bug ID: {analysis.bugId} •{' '}
              {new Date(analysis.timestamp).toLocaleString()}
              {duration && ` • Pipeline: ${duration}`}
            </p>
          </div>
        </div>
        {bug && (
          <p className="text-sm text-gray-300 mt-2 leading-relaxed">{bug.title}</p>
        )}

        {/* Pipeline flow indicator */}
        <div className="mt-3 flex items-center gap-1.5 flex-wrap text-xs text-gray-500">
          {['Triage', 'Log Analysis', 'Root Cause', 'Duplicate Detection', 'Remediation'].map(
            (step, i, arr) => (
              <span key={step} className="flex items-center gap-1.5">
                <span className="text-gray-400">{step}</span>
                {i < arr.length - 1 && <ArrowRight className="w-3 h-3" />}
              </span>
            )
          )}
        </div>
      </div>

      {/* Top row: Triage + Log Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <TriageCard analysis={analysis} />
        <LogAnalysisCard analysis={analysis} />
      </div>

      {/* Second row: Root Cause + Duplicate Detection */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <RootCauseCard rc={analysis.rootCause} />
        <DuplicateDetectionCard dd={analysis.duplicateDetection} />
      </div>

      {/* Full-width: Remediation */}
      <RemediationCard rem={analysis.remediation} />
    </div>
  );
}
