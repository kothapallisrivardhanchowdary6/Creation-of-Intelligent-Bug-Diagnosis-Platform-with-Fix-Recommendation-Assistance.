/**
 * M4.2 — Knowledge Base Growth Mechanism Page
 *
 * Allows users to add confirmed-resolved bugs to the existing ChromaDB
 * vector knowledge base so they become available for future RAG retrieval.
 *
 * Workflow:
 *   Fill form → Validate → Check duplicates → Embed → Store → Verify retrieval
 */

import { useState, useEffect } from 'react';
import {
  BookOpen, CheckCircle2, AlertTriangle, XCircle, Loader2,
  Plus, Search, Clock, Database, ShieldCheck, Zap, RefreshCw,
  ChevronDown, ChevronUp, ExternalLink,
} from 'lucide-react';
import type {
  ResolvedBugSubmission, KBValidationResult, KBAddResult,
  KBRecentEntry, KBStatusExtended,
} from '../types';
import {
  validateResolvedBug, addResolvedBug, getRecentKBEntries,
  getKBStatusExtended, verifyKBEntry,
} from '../services/api';

// ── Constants ─────────────────────────────────────────────────────────────────

const SEVERITIES = ['critical', 'high', 'medium', 'low'];
const PRIORITIES = ['P0', 'P1', 'P2', 'P3'];
const CATEGORIES = [
  'Null Reference', 'Memory Management', 'Concurrency', 'Network/IO',
  'Security', 'Input Validation', 'Performance', 'Configuration', 'Logic Error', 'Other',
];

const EMPTY_FORM: ResolvedBugSubmission = {
  title: '',
  description: '',
  rootCause: '',
  resolution: '',
  resolutionConfirmed: false,
  component: '',
  severity: '',
  priority: '',
  bugId: '',
  errorMessage: '',
  exceptionType: '',
  stackTrace: '',
  confirmedFix: '',
  source: '',
  category: '',
};

// ── Step indicator ────────────────────────────────────────────────────────────

const WORKFLOW_STEPS = [
  { id: 'form', label: 'Fill Details', icon: Plus },
  { id: 'validate', label: 'Validate', icon: ShieldCheck },
  { id: 'duplicate', label: 'Dup Check', icon: Search },
  { id: 'embed', label: 'Generate Embedding', icon: Zap },
  { id: 'index', label: 'Index to KB', icon: Database },
  { id: 'verify', label: 'Verify Retrieval', icon: CheckCircle2 },
];

function WorkflowProgress({
  currentStep, result,
}: {
  currentStep: number;
  result: KBAddResult | null;
}) {
  return (
    <div className="flex items-center gap-0 overflow-x-auto pb-1">
      {WORKFLOW_STEPS.map((step, i) => {
        const done = i < currentStep;
        const active = i === currentStep;
        const failed = result && !result.success && i >= currentStep;

        let bg = 'bg-gray-800 border-gray-700';
        let textColor = 'text-gray-500';
        if (done) { bg = 'bg-emerald-900/50 border-emerald-700'; textColor = 'text-emerald-400'; }
        if (active) { bg = 'bg-blue-900/50 border-blue-600'; textColor = 'text-blue-400'; }

        return (
          <div key={step.id} className="flex items-center shrink-0">
            <div className={`flex items-center gap-1.5 px-3 py-2 rounded-lg border text-xs font-medium ${bg} ${textColor}`}>
              {done ? (
                <CheckCircle2 className="w-3.5 h-3.5" />
              ) : active ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <step.icon className="w-3.5 h-3.5" />
              )}
              <span className="hidden sm:inline">{step.label}</span>
            </div>
            {i < WORKFLOW_STEPS.length - 1 && (
              <div className={`w-4 h-px mx-0.5 ${i < currentStep ? 'bg-emerald-600' : 'bg-gray-700'}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Status display card ───────────────────────────────────────────────────────

function StatusStep({
  label, status, detail,
}: {
  label: string;
  status: 'pending' | 'running' | 'pass' | 'fail' | 'skip';
  detail?: string;
}) {
  const icons = {
    pending: <div className="w-4 h-4 rounded-full border-2 border-gray-600" />,
    running: <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />,
    pass: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
    fail: <XCircle className="w-4 h-4 text-red-400" />,
    skip: <div className="w-4 h-4 rounded-full border-2 border-gray-700 bg-gray-800" />,
  };
  const textColors = {
    pending: 'text-gray-500',
    running: 'text-blue-300',
    pass: 'text-emerald-300',
    fail: 'text-red-300',
    skip: 'text-gray-600',
  };
  return (
    <div className="flex items-start gap-3 py-2">
      <div className="mt-0.5 shrink-0">{icons[status]}</div>
      <div>
        <p className={`text-sm font-medium ${textColors[status]}`}>{label}</p>
        {detail && <p className="text-xs text-gray-500 mt-0.5">{detail}</p>}
      </div>
    </div>
  );
}

// ── KB Status sidebar ─────────────────────────────────────────────────────────

function KBStatusPanel({ status }: { status: KBStatusExtended | null }) {
  if (!status) return null;
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-4">
      <div className="flex items-center gap-2">
        <Database className="w-4 h-4 text-emerald-400" />
        <h4 className="text-sm font-semibold text-gray-200">Knowledge Base Status</h4>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gray-800 rounded-lg p-3 text-center">
          <p className="text-xl font-bold text-white">{status.totalDocuments}</p>
          <p className="text-xs text-gray-400">Total Documents</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-3 text-center">
          <p className="text-xl font-bold text-emerald-400">{status.userAddedResolvedBugs ?? 0}</p>
          <p className="text-xs text-gray-400">User-added</p>
        </div>
      </div>
      <div>
        <p className="text-xs text-gray-500 mb-2">Components covered:</p>
        <div className="flex flex-wrap gap-1">
          {Object.entries(status.componentBreakdown ?? {}).slice(0, 6).map(([comp, count]) => (
            <span key={comp} className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded-full">
              {comp} ({count})
            </span>
          ))}
        </div>
      </div>
      <div>
        <p className="text-xs text-gray-500 mb-1">Embedding model:</p>
        <p className="text-xs text-blue-400 font-mono">{status.embeddingModel}</p>
      </div>
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${status.indexStatus === 'ready' ? 'bg-emerald-400 animate-pulse' : 'bg-yellow-400'}`} />
        <span className="text-xs text-gray-400 capitalize">{status.indexStatus}</span>
      </div>
    </div>
  );
}

// ── Recent entries ────────────────────────────────────────────────────────────

function RecentEntries({ entries }: { entries: KBRecentEntry[] }) {
  if (entries.length === 0) return (
    <div className="text-center py-6 text-gray-600 text-sm">
      No entries added yet this session.
    </div>
  );
  return (
    <div className="space-y-2">
      {entries.map((e, i) => (
        <div key={i} className="bg-gray-800 rounded-lg p-3 flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <span className="text-xs font-mono text-blue-400">{e.doc_id}</span>
              {e.severity && (
                <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                  e.severity === 'critical' ? 'bg-red-900/50 text-red-400' :
                  e.severity === 'high' ? 'bg-orange-900/50 text-orange-400' :
                  e.severity === 'medium' ? 'bg-yellow-900/50 text-yellow-400' :
                  'bg-green-900/50 text-green-400'
                }`}>{e.severity}</span>
              )}
            </div>
            <p className="text-sm text-gray-300 truncate">{e.title}</p>
            <div className="flex items-center gap-3 mt-1">
              {e.component && <span className="text-xs text-gray-500">{e.component}</span>}
              {e.added_at && (
                <span className="text-xs text-gray-600">
                  {new Date(e.added_at).toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>
          {e.retrievable && (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-1" />
          )}
        </div>
      ))}
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function KnowledgeGrowth() {
  const [form, setForm] = useState<ResolvedBugSubmission>(EMPTY_FORM);
  const [workflowStep, setWorkflowStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationResult, setValidationResult] = useState<KBValidationResult | null>(null);
  const [addResult, setAddResult] = useState<KBAddResult | null>(null);
  const [kbStatus, setKbStatus] = useState<KBStatusExtended | null>(null);
  const [recentEntries, setRecentEntries] = useState<KBRecentEntry[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [activeTab, setActiveTab] = useState<'form' | 'recent'>('form');
  const [verifyResult, setVerifyResult] = useState<{ exists: boolean; retrievable: boolean; score?: number | null } | null>(null);

  useEffect(() => {
    loadSidebar();
  }, []);

  const loadSidebar = async () => {
    const [st, rc] = await Promise.allSettled([getKBStatusExtended(), getRecentKBEntries(10)]);
    if (st.status === 'fulfilled') setKbStatus(st.value);
    if (rc.status === 'fulfilled') setRecentEntries(rc.value.session_added);
  };

  const update = (field: keyof ResolvedBugSubmission, value: unknown) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleValidate = async () => {
    setIsSubmitting(true);
    setWorkflowStep(1);
    setValidationResult(null);
    setAddResult(null);
    setVerifyResult(null);
    try {
      const res = await validateResolvedBug(form);
      setValidationResult(res);
      if (res.valid) setWorkflowStep(2);
    } catch (e: unknown) {
      setValidationResult({
        valid: false,
        errors: [`Validation request failed: ${(e as Error).message}`],
        warnings: [],
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAdd = async () => {
    setIsSubmitting(true);
    setWorkflowStep(2);
    try {
      // Step: duplicate check + embedding
      setWorkflowStep(3);
      await new Promise(r => setTimeout(r, 100)); // allow UI to update
      setWorkflowStep(4);
      const res = await addResolvedBug(form);
      setAddResult(res);

      if (res.success) {
        setWorkflowStep(5);
        // Verify retrieval
        await new Promise(r => setTimeout(r, 300));
        try {
          const verify = await verifyKBEntry(res.doc_id);
          setVerifyResult({
            exists: verify.exists,
            retrievable: verify.retrievable,
            score: verify.retrieval_score,
          });
        } catch {
          setVerifyResult({ exists: res.indexed, retrievable: res.retrievable });
        }
        setWorkflowStep(6);
        // Refresh sidebar
        await loadSidebar();
      } else {
        setWorkflowStep(3); // reset to pre-add if failed
      }
    } catch (e: unknown) {
      setAddResult({
        success: false,
        doc_id: '',
        validation: validationResult ?? { valid: false, errors: [], warnings: [] },
        embedding_generated: false,
        duplicate_check: { checked: false },
        indexed: false,
        retrievable: false,
        message: `Add failed: ${(e as Error).message}`,
        timestamp: new Date().toISOString(),
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setForm(EMPTY_FORM);
    setWorkflowStep(0);
    setValidationResult(null);
    setAddResult(null);
    setVerifyResult(null);
  };

  const fieldClass =
    'w-full bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:ring-1 focus:ring-blue-500 focus:outline-none placeholder-gray-600';
  const labelClass = 'block text-xs font-medium text-gray-400 mb-1';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white">Knowledge Base Growth</h2>
        <p className="text-sm text-gray-400 mt-0.5">
          Add confirmed-resolved bugs to the vector knowledge base for future RAG retrieval
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── Main panel ──────────────────────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-5">
          {/* Workflow progress */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-xs text-gray-500 mb-3">Workflow progress</p>
            <WorkflowProgress currentStep={workflowStep} result={addResult} />
          </div>

          {/* Tab selector */}
          <div className="flex gap-1 bg-gray-900 border border-gray-800 rounded-xl p-1 w-fit">
            <button
              onClick={() => setActiveTab('form')}
              className={`px-4 py-1.5 text-sm rounded-lg transition-colors ${
                activeTab === 'form' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              Add Resolved Bug
            </button>
            <button
              onClick={() => setActiveTab('recent')}
              className={`px-4 py-1.5 text-sm rounded-lg transition-colors ${
                activeTab === 'recent' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              Recent Entries ({recentEntries.length})
            </button>
          </div>

          {activeTab === 'recent' ? (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-gray-200">Recently Added Entries</h3>
                <button onClick={loadSidebar} className="text-gray-500 hover:text-gray-300">
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              </div>
              <RecentEntries entries={recentEntries} />
            </div>
          ) : (
            <>
              {/* ── Form ──────────────────────────────────────────────── */}
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
                <h3 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-blue-400" />
                  Resolved Bug Details
                  <span className="text-xs text-gray-600 font-normal ml-2">
                    * required fields
                  </span>
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="sm:col-span-2">
                    <label className={labelClass}>Title *</label>
                    <input
                      type="text"
                      className={fieldClass}
                      placeholder="Short descriptive title of the bug"
                      value={form.title}
                      onChange={e => update('title', e.target.value)}
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <label className={labelClass}>Description *</label>
                    <textarea
                      className={`${fieldClass} h-24 resize-none`}
                      placeholder="Describe the bug, reproduction steps, and observed behavior"
                      value={form.description}
                      onChange={e => update('description', e.target.value)}
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <label className={labelClass}>Root Cause *</label>
                    <textarea
                      className={`${fieldClass} h-20 resize-none`}
                      placeholder="The identified root cause of the bug"
                      value={form.rootCause}
                      onChange={e => update('rootCause', e.target.value)}
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <label className={labelClass}>Resolution *</label>
                    <textarea
                      className={`${fieldClass} h-20 resize-none`}
                      placeholder="How the bug was fixed"
                      value={form.resolution}
                      onChange={e => update('resolution', e.target.value)}
                    />
                  </div>

                  <div>
                    <label className={labelClass}>Component</label>
                    <input
                      type="text"
                      className={fieldClass}
                      placeholder="e.g. Authentication, Database"
                      value={form.component ?? ''}
                      onChange={e => update('component', e.target.value)}
                    />
                  </div>

                  <div>
                    <label className={labelClass}>Severity</label>
                    <select
                      className={fieldClass}
                      value={form.severity ?? ''}
                      onChange={e => update('severity', e.target.value)}
                    >
                      <option value="">Select severity</option>
                      {SEVERITIES.map(s => (
                        <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className={labelClass}>Priority</label>
                    <select
                      className={fieldClass}
                      value={form.priority ?? ''}
                      onChange={e => update('priority', e.target.value)}
                    >
                      <option value="">Select priority</option>
                      {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                  </div>

                  <div>
                    <label className={labelClass}>Category</label>
                    <select
                      className={fieldClass}
                      value={form.category ?? ''}
                      onChange={e => update('category', e.target.value)}
                    >
                      <option value="">Select category</option>
                      {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                </div>

                {/* Resolution confirmed toggle */}
                <div className={`rounded-lg border p-3 ${form.resolutionConfirmed ? 'border-emerald-700 bg-emerald-900/20' : 'border-gray-700 bg-gray-800'}`}>
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      className="mt-0.5 w-4 h-4 accent-emerald-500"
                      checked={form.resolutionConfirmed}
                      onChange={e => update('resolutionConfirmed', e.target.checked)}
                    />
                    <div>
                      <p className={`text-sm font-medium ${form.resolutionConfirmed ? 'text-emerald-300' : 'text-gray-300'}`}>
                        Resolution Confirmed *
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        I confirm this resolution has been validated and the bug is fully resolved.
                        Only confirmed fixes are added to the knowledge base.
                      </p>
                    </div>
                  </label>
                </div>

                {/* Advanced fields */}
                <button
                  onClick={() => setShowAdvanced(v => !v)}
                  className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-400"
                >
                  {showAdvanced ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  {showAdvanced ? 'Hide' : 'Show'} advanced fields
                </button>

                {showAdvanced && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-gray-800">
                    <div>
                      <label className={labelClass}>Original Bug ID</label>
                      <input
                        type="text"
                        className={fieldClass}
                        placeholder="e.g. BUG-001, JIRA-1234"
                        value={form.bugId ?? ''}
                        onChange={e => update('bugId', e.target.value)}
                      />
                    </div>
                    <div>
                      <label className={labelClass}>Exception Type</label>
                      <input
                        type="text"
                        className={fieldClass}
                        placeholder="e.g. NullPointerException"
                        value={form.exceptionType ?? ''}
                        onChange={e => update('exceptionType', e.target.value)}
                      />
                    </div>
                    <div>
                      <label className={labelClass}>Error Message</label>
                      <input
                        type="text"
                        className={fieldClass}
                        placeholder="Primary error message"
                        value={form.errorMessage ?? ''}
                        onChange={e => update('errorMessage', e.target.value)}
                      />
                    </div>
                    <div>
                      <label className={labelClass}>Source / Project</label>
                      <input
                        type="text"
                        className={fieldClass}
                        placeholder="e.g. payment-service, Mozilla Firefox"
                        value={form.source ?? ''}
                        onChange={e => update('source', e.target.value)}
                      />
                    </div>
                    <div>
                      <label className={labelClass}>Confirmed Fix</label>
                      <input
                        type="text"
                        className={fieldClass}
                        placeholder="Short description of the actual code fix"
                        value={form.confirmedFix ?? ''}
                        onChange={e => update('confirmedFix', e.target.value)}
                      />
                    </div>
                    <div className="sm:col-span-2">
                      <label className={labelClass}>Stack Trace (optional)</label>
                      <textarea
                        className={`${fieldClass} h-24 resize-none font-mono text-xs`}
                        placeholder="Paste relevant stack trace..."
                        value={form.stackTrace ?? ''}
                        onChange={e => update('stackTrace', e.target.value)}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* ── Action buttons ─────────────────────────────────────────── */}
              <div className="flex gap-3 flex-wrap">
                <button
                  onClick={handleValidate}
                  disabled={isSubmitting || workflowStep >= 2}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-white text-sm rounded-lg transition-colors"
                >
                  {isSubmitting && workflowStep === 1 ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <ShieldCheck className="w-4 h-4" />
                  )}
                  Validate First
                </button>

                <button
                  onClick={handleAdd}
                  disabled={isSubmitting || workflowStep >= 6}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm rounded-lg transition-colors"
                >
                  {isSubmitting && workflowStep >= 2 ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Database className="w-4 h-4" />
                  )}
                  Add to Knowledge Base
                </button>

                {(addResult || validationResult) && (
                  <button
                    onClick={handleReset}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded-lg transition-colors"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Add Another
                  </button>
                )}
              </div>

              {/* ── Results panel ──────────────────────────────────────────── */}
              {(validationResult || addResult) && (
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
                  <h3 className="text-sm font-semibold text-gray-200">Workflow Status</h3>

                  {/* Validation */}
                  {validationResult && (
                    <div>
                      <StatusStep
                        label="Field Validation"
                        status={validationResult.valid ? 'pass' : 'fail'}
                        detail={
                          validationResult.valid
                            ? `${validationResult.warnings.length} warning(s)`
                            : `${validationResult.errors.length} error(s): ${validationResult.errors.join('; ')}`
                        }
                      />
                      {validationResult.errors.length > 0 && (
                        <div className="ml-7 space-y-1">
                          {validationResult.errors.map((e, i) => (
                            <p key={i} className="text-xs text-red-400">• {e}</p>
                          ))}
                        </div>
                      )}
                      {validationResult.warnings.length > 0 && (
                        <div className="ml-7 space-y-1">
                          {validationResult.warnings.map((w, i) => (
                            <p key={i} className="text-xs text-yellow-400">⚠ {w}</p>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Duplicate check */}
                  {(validationResult?.duplicate_check?.checked || addResult?.duplicate_check?.checked) && (
                    <div>
                      <StatusStep
                        label="Duplicate Check"
                        status="pass"
                        detail={
                          (addResult?.duplicate_check ?? validationResult?.duplicate_check)?.is_near_duplicate ||
                          (validationResult?.duplicate_check?.potential_duplicates ?? 0) > 0
                            ? `Similar entry found — added as distinct resolution`
                            : 'No close duplicates found in knowledge base'
                        }
                      />
                      {(addResult?.duplicate_check ?? validationResult?.duplicate_check)?.top_match && (
                        <div className="ml-7 bg-gray-800 rounded-lg p-2.5 mt-1">
                          <p className="text-xs text-gray-400">
                            Closest match:{' '}
                            <span className="font-mono text-blue-400">
                              {(addResult?.duplicate_check ?? validationResult?.duplicate_check)?.top_match?.id}
                            </span>{' '}
                            — similarity{' '}
                            <span className="text-yellow-400">
                              {(((addResult?.duplicate_check ?? validationResult?.duplicate_check)?.top_match as { id: string | null; similarity: number; document: string } | undefined)?.similarity ?? 0 * 100).toFixed(0)}%
                            </span>
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Embedding + indexing */}
                  {addResult && (
                    <>
                      <StatusStep
                        label="Embedding Generation"
                        status={addResult.embedding_generated ? 'pass' : 'fail'}
                        detail={
                          addResult.embedding_generated
                            ? 'Generated 384-dim embedding using all-MiniLM-L6-v2'
                            : 'Embedding generation failed'
                        }
                      />
                      <StatusStep
                        label="Indexed to Knowledge Base"
                        status={addResult.indexed ? 'pass' : 'fail'}
                        detail={
                          addResult.indexed
                            ? `Stored as document ID: ${addResult.doc_id}`
                            : 'Indexing failed'
                        }
                      />
                      <StatusStep
                        label="Retrieval Verification"
                        status={
                          verifyResult === null ? 'running' :
                          (verifyResult.retrievable || addResult.retrievable) ? 'pass' : 'fail'
                        }
                        detail={
                          verifyResult
                            ? verifyResult.retrievable
                              ? `Retrievable via similarity search${verifyResult.score != null ? ` (score: ${(verifyResult.score * 100).toFixed(0)}%)` : ''}`
                              : 'Not yet top-ranked — will appear as KB grows'
                            : 'Verifying...'
                        }
                      />
                    </>
                  )}

                  {/* Final result banner */}
                  {addResult && (
                    <div className={`mt-2 rounded-lg border p-3 ${
                      addResult.success
                        ? 'bg-emerald-900/20 border-emerald-700/50'
                        : 'bg-red-900/20 border-red-700/50'
                    }`}>
                      <div className="flex items-start gap-2">
                        {addResult.success ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                        ) : (
                          <XCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                        )}
                        <div>
                          <p className={`text-sm font-medium ${addResult.success ? 'text-emerald-300' : 'text-red-300'}`}>
                            {addResult.success ? 'Successfully added to Knowledge Base' : 'Failed to add'}
                          </p>
                          <p className="text-xs text-gray-400 mt-0.5">{addResult.message}</p>
                          {addResult.success && (
                            <p className="text-xs text-gray-500 mt-1">
                              This bug is now available for retrieval by Root Cause, Duplicate Detection,
                              and Remediation agents in future analyses.
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* ── Sidebar ────────────────────────────────────────────────────── */}
        <div className="space-y-4">
          <KBStatusPanel status={kbStatus} />

          {/* Info card */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center gap-2">
              <ExternalLink className="w-4 h-4 text-blue-400" />
              <h4 className="text-sm font-semibold text-gray-200">How it works</h4>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              Resolved bugs are embedded using the same{' '}
              <span className="text-blue-400 font-mono">all-MiniLM-L6-v2</span> model
              as the existing RAG pipeline and stored in the{' '}
              <span className="text-blue-400 font-mono">defect_knowledge_base</span> ChromaDB
              collection.
            </p>
            <p className="text-xs text-gray-400 leading-relaxed">
              After adding, the new entry becomes immediately retrievable by the Root Cause,
              Duplicate Detection, and Remediation agents when analyzing similar bugs.
            </p>
            <div className="space-y-1">
              {[
                'Validate required fields',
                'Check for near-duplicates',
                'Generate 384-dim embedding',
                'Store in existing vector store',
                'Verify retrieval works',
              ].map((step, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-gray-500">
                  <div className="w-4 h-4 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center text-[10px] text-gray-400 shrink-0">
                    {i + 1}
                  </div>
                  {step}
                </div>
              ))}
            </div>
          </div>

          {/* Quick recent */}
          {recentEntries.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <Clock className="w-4 h-4 text-gray-400" />
                <h4 className="text-sm font-semibold text-gray-200">Recently Added</h4>
              </div>
              <RecentEntries entries={recentEntries.slice(0, 3)} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
