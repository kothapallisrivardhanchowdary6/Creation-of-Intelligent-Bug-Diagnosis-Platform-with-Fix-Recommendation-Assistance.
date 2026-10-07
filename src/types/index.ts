// ============================================================
// AI Defect Analysis System — Type Definitions (Milestone 3)
// ============================================================

export interface BugSubmission {
  id?: string;
  title: string;
  description: string;
  stackTrace?: string;
  errorLogs?: string;
  environment?: string;
  files?: UploadedFile[];
  createdAt?: string;
  status?: BugStatus;
}

export interface UploadedFile {
  name: string;
  type: string;
  size: number;
  content?: string;
}

export type BugStatus = 'submitted' | 'analyzing' | 'analyzed' | 'error';

export interface Bug extends BugSubmission {
  id: string;
  createdAt: string;
  status: BugStatus;
  analysis?: AnalysisResult;
}

// ── Full analysis result (all 5 agents) ─────────────────────────────────────
export interface AnalysisResult {
  bugId: string;
  timestamp: string;
  milestone?: string;
  totalDuration?: number;

  // Agent results (top-level convenience copies)
  triage: TriageResult;
  logAnalysis: LogAnalysisResult;
  rootCause: RootCauseResult;
  duplicateDetection: DuplicateDetectionResult;
  remediation: RemediationResult;

  // Raw agent wrapper objects (optional — from backend agents dict)
  agents?: {
    triage?: AgentWrapper;
    log_analysis?: AgentWrapper;
    root_cause?: AgentWrapper;
    duplicate_detection?: AgentWrapper;
    remediation?: AgentWrapper;
  };
}

// ── Agent wrapper (metadata from orchestrator) ───────────────────────────────
export interface AgentWrapper {
  agent: string;
  version?: string;
  status: 'success' | 'error' | 'insufficient_evidence';
  result: Record<string, unknown>;
  duration: number;
  timestamp: string;
  error?: string;
}

// ── Triage ────────────────────────────────────────────────────────────────────
export interface TriageResult {
  severity: 'critical' | 'high' | 'medium' | 'low';
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  category: string;
  component: string;
  confidence: number;
  reasoning: string;
}

// ── Log Analysis ──────────────────────────────────────────────────────────────
export interface LogAnalysisResult {
  exceptions: ExceptionInfo[];
  stackTraceAnalysis?: string;
  errorPatterns: string[];
  suspiciousLogs: string[];
  summary: string;
  failurePoint?: string;
  codePath?: string;
  confidence?: number;
}

export interface ExceptionInfo {
  // M1 / legacy names
  type?: string;
  message?: string;
  file?: string;
  line?: number;
  // M2 / M3 names from backend
  exceptionType?: string;
  errorMessage?: string;
  fileName?: string;
  className?: string;
  methodName?: string;
  lineNumber?: number;
  codePath?: string;
  confidence?: number;
}

// ── Root Cause (M3) ───────────────────────────────────────────────────────────
export interface RootCauseResult {
  status: 'success' | 'insufficient_evidence' | 'error';

  // Primary result
  probableCause: string;          // snake_case alias: probable_cause
  confidence: number;
  reasoning: string;
  relatedComponents: string[];    // snake_case alias: related_components

  // Evidence separation (M3)
  hypotheses: RootCauseHypothesis[];
  retrievedEvidence: HistoricalEvidence[];   // retrieved_evidence
  agentReasoning: string;                    // agent_reasoning
  evidenceSummary: string;                   // evidence_summary
  insufficientEvidenceReason?: string;       // insufficient_evidence_reason
}

export interface RootCauseHypothesis {
  hypothesis: string;
  confidence: number;
  supportingEvidence: string[];   // supporting_evidence
  causalChain: string;            // causal_chain
}

export interface HistoricalEvidence {
  bugId: string;            // bug_id
  document: string;
  component?: string;
  severity?: string;
  resolution?: string;
  similarityScore: number;  // similarity_score
  source: string;
}

// ── Duplicate Detection (M3) ──────────────────────────────────────────────────
export interface DuplicateDetectionResult {
  // M3 primary fields
  classification: 'likely_duplicate' | 'related_issue' | 'new_unmatched' | 'insufficient_evidence';
  topMatchSimilarity: number;       // top_match_similarity
  duplicateProbability: number;     // duplicate_probability
  matchedBugs: MatchedBug[];        // matched_bugs
  analysisSummary: string;          // analysis_summary
  thresholdsUsed: { likely_duplicate: number; related_issue: number }; // thresholds_used

  // Legacy fields (for backward compat)
  isDuplicate?: boolean;            // is_duplicate
  similarityScore?: number;         // similarity_score
  matchingBugs?: LegacyHistoricalBug[];  // matching_bugs
}

export interface MatchedBug {
  bugId: string;            // bug_id
  title: string;
  similarityScore: number;  // similarity_score
  classification: string;
  component?: string;
  severity?: string;
  exceptionType?: string;   // exception_type
  resolutionSummary?: string; // resolution_summary
}

// Legacy shape used by older frontend code
export interface LegacyHistoricalBug {
  bugId: string;
  title: string;
  similarity: number;
  project: string;
  component: string;
  severity: string;
  resolution: string;
}

// Keep for backward compat
export type HistoricalBug = LegacyHistoricalBug;

// ── Remediation (M3) ──────────────────────────────────────────────────────────
export interface RemediationResult {
  status: 'success' | 'insufficient_evidence' | 'error';

  // Primary fix
  suggestedFix: string;         // suggested_fix
  fixSource: string;            // fix_source: historical_evidence | best_practice | agent_reasoning
  confidence: number;

  // Actionable guidance
  implementationSteps: ImplementationStep[];   // implementation_steps
  debuggingSteps: string[];     // debugging_steps
  validationSteps: string[];    // validation_steps
  regressionTests: string[];    // regression_tests

  // Evidence
  historicalResolutions: HistoricalResolution[]; // historical_resolutions
  bestPractices: string[];      // best_practices

  // Meta
  estimatedEffort: string;      // estimated_effort
  riskLevel: 'low' | 'medium' | 'high'; // risk_level
  evidenceSummary: string;      // evidence_summary
  agentReasoning: string;       // agent_reasoning
}

export interface ImplementationStep {
  step: string;
  detail?: string;
  isSpeculative: boolean;   // is_speculative
}

export interface HistoricalResolution {
  bugId: string;         // bug_id
  document: string;
  resolution: string;
  component?: string;
  severity?: string;
  similarityScore: number; // similarity_score
  source: string;
}

// ── Knowledge Base ────────────────────────────────────────────────────────────
export interface KnowledgeBaseStatus {
  totalDocuments: number;
  projects: string[];
  lastUpdated: string;
  indexStatus: 'ready' | 'building' | 'error';
  embeddingModel: string;
  vectorDimensions: number;
}

export interface SearchResult {
  bugId: string;
  title: string;
  description: string;
  score: number;
  project: string;
  metadata: Record<string, string>;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'error';
  version: string;
  services: {
    api: string;
    database: string;
    chromadb: string;
    embeddings: string;
    llm: string;
  };
  uptime: string;
}

export interface AgentResult {
  agentName: string;
  status: 'success' | 'error' | 'timeout';
  result: unknown;
  duration: number;
  timestamp: string;
}

// ============================================================
// M4 — Defect Pattern Analytics Types
// ============================================================

export interface SeverityCount {
  critical: number;
  high: number;
  medium: number;
  low: number;
  unknown: number;
}

export interface ComponentStat {
  component: string;
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  unknown: number;
}

export interface ExceptionStat {
  exception: string;
  count: number;
}

export interface ErrorPatternStat {
  pattern: string;
  count: number;
}

export interface RootCauseStat {
  cause: string;
  count: number;
}

export interface TrendPoint {
  period: string;
  total: number;
  critical?: number;
  high?: number;
  medium?: number;
  low?: number;
  unanalyzed?: number;
  historical_kb_entries?: number;
}

export interface ClusterBug {
  id: string;
  document: string;
  severity: string;
  component: string;
  project: string;
}

export interface KBCluster {
  cluster_id: string;
  label: string;
  size: number;
  representative_bugs: ClusterBug[];
  severity_breakdown: Record<string, number>;
}

export interface SubmittedBugCluster {
  submitted_bug_id: string;
  submitted_bug_title: string;
  similar_kb_bugs: {
    id: string;
    document: string;
    similarity: number;
    component?: string;
  }[];
}

export interface DuplicateStats {
  total_analyzed: number;
  duplicates: number;
  unique: number;
  related_issues: number;
  duplicate_rate: number;
  classification_distribution: Record<string, number>;
  similarity_distribution: Record<string, number>;
  duplicates_by_component: Record<string, number>;
}

export interface AnalyticsOverview {
  total_bugs: number;
  analyzed_bugs: number;
  unanalyzed_bugs: number;
  severity_distribution: Record<string, number>;
  priority_distribution: Record<string, number>;
  top_components: { component: string; count: number }[];
  top_exceptions: { exception: string; count: number }[];
  duplicate_stats: {
    duplicates: number;
    unique: number;
    duplicate_rate: number;
  };
  resolution_distribution: Record<string, number>;
  knowledge_base: {
    total_documents: number;
    collection_name: string;
    status: string;
  };
  filters_applied: {
    component?: string | null;
    severity?: string | null;
    priority?: string | null;
    exception_type?: string | null;
    date_from?: string | null;
    date_to?: string | null;
    is_duplicate?: boolean | null;
  };
}

export interface AnalyticsSeverity {
  severity_distribution: Record<string, number>;
  severity_by_component: Record<string, Record<string, number>>;
  severity_over_time: Record<string, Record<string, number>>;
  total: number;
}

export interface AnalyticsPriority {
  priority_distribution: Record<string, number>;
  priority_by_severity: Record<string, Record<string, number>>;
  total: number;
}

export interface AnalyticsComponents {
  components: ComponentStat[];
  total_components: number;
  most_affected: string | null;
  total: number;
}

export interface AnalyticsExceptions {
  exception_distribution: ExceptionStat[];
  exception_by_component: Record<string, Record<string, number>>;
  error_patterns: ErrorPatternStat[];
  unique_exception_types: number;
  total: number;
}

export interface AnalyticsRootCauses {
  top_root_causes: RootCauseStat[];
  root_cause_status: Record<string, number>;
  confidence_distribution: Record<string, number>;
  total: number;
}

export interface AnalyticsTrends {
  granularity: string;
  trend_series: TrendPoint[];
  total_bugs: number;
  date_range: { from: string | null; to: string | null };
}

export interface AnalyticsClusters {
  kb_clusters: KBCluster[];
  submitted_bug_clusters: SubmittedBugCluster[];
  total_documents: number;
  min_similarity_threshold: number;
  error?: string;
  message?: string;
}

export interface AnalyticsFilters {
  component?: string;
  severity?: string;
  priority?: string;
  exceptionType?: string;
  dateFrom?: string;
  dateTo?: string;
  isDuplicate?: boolean;
}

// ============================================================
// M4 — Knowledge Base Growth Types
// ============================================================

export interface ResolvedBugSubmission {
  title: string;
  description: string;
  rootCause: string;
  resolution: string;
  resolutionConfirmed: boolean;
  component?: string;
  severity?: string;
  priority?: string;
  bugId?: string;
  errorMessage?: string;
  exceptionType?: string;
  stackTrace?: string;
  confirmedFix?: string;
  source?: string;
  category?: string;
}

export interface KBValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  duplicate_check?: {
    checked: boolean;
    potential_duplicates?: number;
    top_match?: {
      id: string;
      document: string;
      similarity: number;
    } | null;
    recommendation?: string;
    error?: string;
  };
}

export interface KBAddResult {
  success: boolean;
  doc_id: string;
  validation: KBValidationResult;
  embedding_generated: boolean;
  duplicate_check: {
    checked: boolean;
    potential_duplicates?: number;
    top_match?: { id: string | null; similarity: number; document: string };
    is_near_duplicate?: boolean;
    error?: string;
  };
  indexed: boolean;
  retrievable: boolean;
  retrieval_score?: number | null;
  message: string;
  timestamp: string;
}

export interface KBRecentEntry {
  doc_id: string;
  title: string;
  component?: string;
  severity?: string;
  added_at?: string;
  retrievable?: boolean;
  source?: string;
  resolution_confirmed?: boolean;
}

export interface KBRecentResult {
  session_added: KBRecentEntry[];
  all_m4_entries: KBRecentEntry[];
  total_session_added: number;
  limit: number;
}

export interface KBStatusExtended {
  totalDocuments: number;
  projects: string[];
  lastUpdated: string;
  indexStatus: 'ready' | 'building' | 'error';
  embeddingModel: string;
  vectorDimensions: number;
  // M4 additions
  projectBreakdown?: Record<string, number>;
  componentBreakdown?: Record<string, number>;
  severityBreakdown?: Record<string, number>;
  userAddedResolvedBugs?: number;
  error?: string;
}

export interface KBVerifyResult {
  doc_id: string;
  exists: boolean;
  document_preview?: string;
  metadata?: Record<string, unknown>;
  retrievable: boolean;
  retrieval_score?: number | null;
  message: string;
}

// ============================================================
// M4.3 — End-to-End Test Types
// ============================================================

export type TestStatus = 'pending' | 'running' | 'pass' | 'fail' | 'skip' | 'warning';

export interface AgentTestResult {
  agent: string;
  status: TestStatus;
  detail?: string;
  durationMs?: number;
  confidence?: number;
}

export interface E2ETestResult {
  test_case: string;
  bug_id?: string;
  title: string;
  description: string;
  status: TestStatus;
  total_processing_time?: string;
  total_processing_ms?: number;

  // Per-step results
  submission: TestStatus;
  rag_retrieval: TestStatus;
  triage: TestStatus;
  log_analysis: TestStatus;
  root_cause: TestStatus;
  duplicate_detection: TestStatus;
  remediation: TestStatus;
  analytics?: TestStatus;

  // Agent detail
  agent_results: AgentTestResult[];

  // Assertions
  assertions: {
    name: string;
    expected: string;
    actual: string;
    passed: boolean;
  }[];

  errors: string[];
  warnings: string[];

  // Metadata
  severity_expected?: string;
  component_expected?: string;
  exception_expected?: string;
  is_duplicate_expected?: boolean;
  insufficient_evidence_expected?: boolean;
}

export interface E2ESuiteResult {
  suite: string;
  started_at: string;
  completed_at: string;
  total_tests: number;
  passed: number;
  failed: number;
  warnings: number;
  skipped: number;
  total_duration_ms: number;
  tests: E2ETestResult[];
  performance: {
    avg_analysis_ms: number;
    min_analysis_ms: number;
    max_analysis_ms: number;
    p95_analysis_ms: number;
  };
  rag_evaluation: {
    total_retrievals: number;
    successful_retrievals: number;
    avg_similarity: number;
  };
  duplicate_evaluation?: {
    true_positives: number;
    false_positives: number;
    true_negatives: number;
    false_negatives: number;
    precision: number;
    recall: number;
    f1: number;
  };
}
