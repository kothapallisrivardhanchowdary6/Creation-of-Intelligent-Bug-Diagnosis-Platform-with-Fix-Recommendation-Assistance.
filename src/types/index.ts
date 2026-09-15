// ============================================================
// AI Defect Analysis System — Type Definitions
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

export interface AnalysisResult {
  bugId: string;
  timestamp: string;
  triage: TriageResult;
  logAnalysis: LogAnalysisResult;
  rootCause: RootCauseResult;
  duplicateDetection: DuplicateDetectionResult;
  remediation: RemediationResult;
}

export interface TriageResult {
  severity: 'critical' | 'high' | 'medium' | 'low';
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  category: string;
  component: string;
  confidence: number;
  reasoning: string;
}

export interface LogAnalysisResult {
  exceptions: ExceptionInfo[];
  stackTraceAnalysis?: string;
  errorPatterns: string[];
  suspiciousLogs: string[];
  summary: string;
  // M2 additions
  failurePoint?: string;
  codePath?: string;
  confidence?: number;
}

export interface ExceptionInfo {
  type: string;
  message: string;
  file?: string;
  line?: number;
  // M2 additions
  exceptionType?: string;
  errorMessage?: string;
  fileName?: string;
  className?: string;
  methodName?: string;
  lineNumber?: number;
  codePath?: string;
  confidence?: number;
}

export interface RootCauseResult {
  probableCause: string;
  evidence: string[];
  confidence: number;
  relatedComponents: string[];
  explanation: string;
}

export interface DuplicateDetectionResult {
  isDuplicate: boolean;
  similarityScore: number;
  duplicateProbability: number;
  matchingBugs: HistoricalBug[];
  analysis: string;
}

export interface HistoricalBug {
  bugId: string;
  title: string;
  similarity: number;
  project: string;
  component: string;
  severity: string;
  resolution: string;
}

export interface RemediationResult {
  suggestedFix: string;
  debuggingSteps: string[];
  validationSteps: string[];
  regressionTests: string[];
  estimatedEffort: string;
  riskLevel: 'low' | 'medium' | 'high';
}

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
  result: any;
  duration: number;
  timestamp: string;
}
