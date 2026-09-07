import { Bug, HistoricalBug, KnowledgeBaseStatus, HealthStatus, AnalysisResult } from '../types';

// ============================================================
// Sample Historical Defects (10+ realistic defects)
// ============================================================

export const sampleHistoricalBugs: HistoricalBug[] = [
  {
    bugId: 'MOZ-1001',
    title: 'NullPointerException in NetworkManager when connection drops during file download',
    similarity: 0.92,
    project: 'Mozilla Firefox',
    component: 'Networking',
    severity: 'critical',
    resolution: 'Fixed by adding null check before accessing connection object in retry handler'
  },
  {
    bugId: 'MOZ-1002',
    title: 'Memory leak in tab rendering engine when switching tabs rapidly',
    similarity: 0.78,
    project: 'Mozilla Firefox',
    component: 'Layout Engine',
    severity: 'high',
    resolution: 'Implemented proper cleanup of render contexts in tab switch handler'
  },
  {
    bugId: 'APC-2001',
    title: 'StackOverflowError in recursive XML parser with deeply nested elements',
    similarity: 0.85,
    project: 'Apache HTTP Server',
    component: 'Core',
    severity: 'critical',
    resolution: 'Converted recursive parser to iterative approach with explicit stack'
  },
  {
    bugId: 'APC-2002',
    title: 'Race condition in thread pool causing deadlock under high concurrency',
    similarity: 0.71,
    project: 'Apache Tomcat',
    component: 'Thread Pool',
    severity: 'critical',
    resolution: 'Added proper lock ordering and timeout mechanism to prevent deadlock'
  },
  {
    bugId: 'APC-2003',
    title: 'Buffer overflow in HTTP header parsing with malformed Content-Type',
    similarity: 0.88,
    project: 'Apache HTTP Server',
    component: 'HTTP Parser',
    severity: 'critical',
    resolution: 'Implemented bounds checking and input validation for all header fields'
  },
  {
    bugId: 'ECL-3001',
    title: 'ClassCastException when refactoring generic types in JDT compiler',
    similarity: 0.65,
    project: 'Eclipse JDT',
    component: 'Compiler',
    severity: 'medium',
    resolution: 'Added type erasure handling in generic type resolution algorithm'
  },
  {
    bugId: 'ECL-3002',
    title: 'UI freeze when opening large workspace with 500+ projects',
    similarity: 0.59,
    project: 'Eclipse Platform',
    component: 'UI Framework',
    severity: 'high',
    resolution: 'Moved workspace loading to background thread with progress reporting'
  },
  {
    bugId: 'ECL-3003',
    title: 'IndexOutOfBoundsException in code completion with partial token matching',
    similarity: 0.82,
    project: 'Eclipse JDT',
    component: 'Content Assist',
    severity: 'medium',
    resolution: 'Added boundary checks in token matching algorithm and fallback for empty results'
  },
  {
    bugId: 'MOZ-1003',
    title: 'Segmentation fault in WebGL renderer with unsupported shader operations',
    similarity: 0.74,
    project: 'Mozilla Firefox',
    component: 'Graphics',
    severity: 'high',
    resolution: 'Added shader capability validation before execution in WebGL context'
  },
  {
    bugId: 'APC-2004',
    title: 'Connection leak in connection pool when exception occurs during checkout',
    similarity: 0.91,
    project: 'Apache Tomcat',
    component: 'Connection Pool',
    severity: 'high',
    resolution: 'Added try-finally block to ensure connection return on checkout failure'
  },
  {
    bugId: 'ECL-3004',
    title: 'Deadlock in plugin activation when circular dependencies exist',
    similarity: 0.68,
    project: 'Eclipse Platform',
    component: 'Plugin Framework',
    severity: 'critical',
    resolution: 'Implemented dependency graph cycle detection with topological sort ordering'
  },
  {
    bugId: 'MOZ-1004',
    title: 'CSS Grid layout miscalculation with auto-fit and minmax constraints',
    similarity: 0.55,
    project: 'Mozilla Firefox',
    component: 'CSS Engine',
    severity: 'medium',
    resolution: 'Fixed constraint solving algorithm for auto-fit tracks with minmax functions'
  }
];

// ============================================================
// Mock Analysis Results Generator
// ============================================================

export function generateMockAnalysis(bug: Bug): AnalysisResult {
  const hasStackTrace = bug.stackTrace && bug.stackTrace.length > 0;
  const hasErrorLogs = bug.errorLogs && bug.errorLogs.length > 0;

  return {
    bugId: bug.id,
    timestamp: new Date().toISOString(),
    triage: {
      severity: determineSeverity(bug),
      priority: determinePriority(bug),
      category: determineCategory(bug),
      component: determineComponent(bug),
      confidence: 0.87,
      reasoning: `Based on analysis of the bug report, this issue appears to be a ${determineCategory(bug).toLowerCase()} defect in the ${determineComponent(bug)} component. The severity assessment considers the potential impact on system stability and user experience.`
    },
    logAnalysis: {
      exceptions: extractExceptions(bug),
      stackTraceAnalysis: hasStackTrace
        ? 'Stack trace indicates a cascading failure originating from the core processing module. The error propagates through 4 layers before reaching the error handler.'
        : 'No stack trace provided. Analysis based on description and error patterns.',
      errorPatterns: [
        'Null reference access pattern detected',
        'Unhandled exception in async operation',
        'Resource cleanup failure on error path',
        'Missing input validation before processing'
      ].filter(() => Math.random() > 0.3),
      suspiciousLogs: hasErrorLogs
        ? ['ERROR: Connection timeout after 30000ms', 'WARN: Retry attempt 3/3 failed', 'FATAL: Unrecoverable state detected']
        : ['No suspicious log patterns identified without log data'],
      summary: `Analysis identified ${extractExceptions(bug).length} exception(s) and ${hasStackTrace ? 'a multi-layer' : 'no'} failure pattern. The root cause appears to be related to ${determineCategory(bug).toLowerCase()} handling.`
    },
    rootCause: {
      probableCause: `The most likely root cause is a ${determineCategory(bug).toLowerCase()} issue in the ${determineComponent(bug)} component, specifically related to ${getSpecificCause(bug)}.`,
      evidence: [
        `Error pattern matches historical bug patterns in ${determineComponent(bug)}`,
        `Similar issues found in ${Math.floor(Math.random() * 3) + 1} related components`,
        `Failure occurs under ${getConditionContext(bug)}`,
        `Stack trace points to ${determineComponent(bug)} module`
      ],
      confidence: 0.79,
      relatedComponents: [determineComponent(bug), 'Error Handler', 'Resource Manager'],
      explanation: `The defect originates from insufficient ${determineCategory(bug).toLowerCase()} handling in the ${determineComponent(bug)} module. When the system encounters ${getConditionContext(bug)}, it fails to properly manage the error state, leading to the observed behavior.`
    },
    duplicateDetection: {
      isDuplicate: Math.random() > 0.6,
      similarityScore: 0.65 + Math.random() * 0.3,
      duplicateProbability: 0.4 + Math.random() * 0.4,
      matchingBugs: sampleHistoricalBugs
        .sort(() => Math.random() - 0.5)
        .slice(0, 3)
        .map(b => ({ ...b, similarity: 0.5 + Math.random() * 0.45 })),
      analysis: `Semantic analysis found ${Math.floor(Math.random() * 3) + 1} potentially related historical defects. The highest similarity match shares common patterns in error handling and component interaction.`
    },
    remediation: {
      suggestedFix: getRemediationFix(bug),
      debuggingSteps: [
        `Reproduce the issue in a controlled environment with ${getConditionContext(bug)}`,
        'Add detailed logging around the suspected failure point',
        'Verify input validation and null checks',
        'Check resource lifecycle management',
        'Review error handling in the call chain'
      ],
      validationSteps: [
        'Create unit test reproducing the failure scenario',
        'Verify fix resolves the original issue',
        'Test edge cases and boundary conditions',
        'Run integration tests for affected components',
        'Perform load testing under similar conditions'
      ],
      regressionTests: [
        'Run existing test suite for the affected module',
        'Execute end-to-end tests covering the user flow',
        'Verify no performance degradation introduced',
        'Check compatibility with dependent modules'
      ],
      estimatedEffort: '2-4 hours',
      riskLevel: 'medium'
    }
  };
}

function determineSeverity(bug: Bug): 'critical' | 'high' | 'medium' | 'low' {
  const text = `${bug.title} ${bug.description}`.toLowerCase();
  if (text.includes('crash') || text.includes('fatal') || text.includes('data loss') || text.includes('security')) return 'critical';
  if (text.includes('error') || text.includes('fail') || text.includes('broken') || text.includes('exception')) return 'high';
  if (text.includes('slow') || text.includes('incorrect') || text.includes('wrong') || text.includes('issue')) return 'medium';
  return 'low';
}

function determinePriority(bug: Bug): 'P0' | 'P1' | 'P2' | 'P3' {
  const severity = determineSeverity(bug);
  const map = { critical: 'P0', high: 'P1', medium: 'P2', low: 'P3' } as const;
  return map[severity];
}

function determineCategory(bug: Bug): string {
  const text = `${bug.title} ${bug.description}`.toLowerCase();
  if (text.includes('null') || text.includes('undefined') || text.includes('reference')) return 'Null Reference';
  if (text.includes('memory') || text.includes('leak') || text.includes('overflow')) return 'Memory Management';
  if (text.includes('thread') || text.includes('race') || text.includes('deadlock') || text.includes('concurrent')) return 'Concurrency';
  if (text.includes('network') || text.includes('connection') || text.includes('timeout')) return 'Network/IO';
  if (text.includes('ui') || text.includes('render') || text.includes('display') || text.includes('layout')) return 'UI/Rendering';
  if (text.includes('parse') || text.includes('format') || text.includes('input')) return 'Input Validation';
  if (text.includes('performance') || text.includes('slow') || text.includes('latency')) return 'Performance';
  return 'Logic Error';
}

function determineComponent(bug: Bug): string {
  const text = `${bug.title} ${bug.description}`.toLowerCase();
  if (text.includes('database') || text.includes('query') || text.includes('sql')) return 'Database Layer';
  if (text.includes('api') || text.includes('endpoint') || text.includes('request')) return 'API Layer';
  if (text.includes('auth') || text.includes('permission') || text.includes('token')) return 'Authentication';
  if (text.includes('cache') || text.includes('session')) return 'Cache/Session';
  if (text.includes('file') || text.includes('upload') || text.includes('storage')) return 'File System';
  if (text.includes('ui') || text.includes('component') || text.includes('page')) return 'UI Component';
  return 'Core Module';
}

function extractExceptions(bug: Bug) {
  const exceptions = [];
  if (bug.stackTrace) {
    const lines = bug.stackTrace.split('\n');
    for (const line of lines) {
      if (line.includes('Exception') || line.includes('Error') || line.includes('at ')) {
        exceptions.push({
          type: line.split(':')[0].trim() || 'Unknown Exception',
          message: line.trim(),
          file: line.includes('at ') ? line.split('(')[1]?.replace(')', '') : undefined
        });
      }
    }
  }
  if (exceptions.length === 0) {
    exceptions.push({
      type: 'RuntimeException',
      message: 'Unhandled exception in processing pipeline'
    });
  }
  return exceptions.slice(0, 5);
}

function getSpecificCause(bug: Bug): string {
  const text = `${bug.title} ${bug.description}`.toLowerCase();
  if (text.includes('null')) return 'missing null safety checks on object references';
  if (text.includes('memory')) return 'improper resource lifecycle management';
  if (text.includes('thread') || text.includes('race')) return 'insufficient synchronization between concurrent operations';
  if (text.includes('network') || text.includes('connection')) return 'inadequate error handling in network operations';
  if (text.includes('timeout')) return 'missing timeout configuration and retry logic';
  return 'insufficient error handling and input validation';
}

function getConditionContext(bug: Bug): string {
  const text = `${bug.title} ${bug.description}`.toLowerCase();
  if (text.includes('high') || text.includes('load') || text.includes('concurrent')) return 'high concurrency conditions';
  if (text.includes('large') || text.includes('big') || text.includes('many')) return 'large data volume processing';
  if (text.includes('network') || text.includes('connection')) return 'unstable network conditions';
  return 'normal operating conditions with edge case inputs';
}

function getRemediationFix(bug: Bug): string {
  const category = determineCategory(bug);
  const component = determineComponent(bug);

  const fixes: Record<string, string> = {
    'Null Reference': `Add comprehensive null checks and optional chaining in ${component}. Implement defensive programming patterns with early returns for null inputs. Consider using Option/Maybe types for safer null handling.`,
    'Memory Management': `Implement proper resource cleanup using try-with-resources or defer patterns. Add memory usage monitoring and implement object pooling for frequently allocated objects in ${component}.`,
    'Concurrency': `Add proper synchronization mechanisms in ${component}. Use concurrent data structures and implement lock-free algorithms where possible. Add thread-safety annotations and documentation.`,
    'Network/IO': `Implement circuit breaker pattern in ${component}. Add retry logic with exponential backoff, connection pooling, and proper timeout configuration. Handle partial failures gracefully.`,
    'UI/Rendering': `Optimize rendering pipeline in ${component}. Implement virtual scrolling for large lists, add requestAnimationFrame batching, and ensure proper cleanup of event listeners and subscriptions.`,
    'Input Validation': `Add comprehensive input validation in ${component}. Implement schema validation, sanitize all inputs, and add proper error messages for invalid data. Use whitelist validation approach.`,
    'Performance': `Profile and optimize hot paths in ${component}. Implement caching strategies, batch operations where possible, and add performance monitoring. Consider lazy loading and code splitting.`,
    'Logic Error': `Review and correct the business logic in ${component}. Add comprehensive unit tests covering edge cases, implement property-based testing, and add assertion checks for invariants.`
  };

  return fixes[category] || `Review and fix the error handling in ${component}. Add proper validation, implement defensive programming patterns, and ensure comprehensive test coverage for the affected code paths.`;
}

// ============================================================
// Mock Knowledge Base Status
// ============================================================

export const mockKnowledgeBaseStatus: KnowledgeBaseStatus = {
  totalDocuments: 12,
  projects: ['Mozilla Firefox', 'Apache HTTP Server', 'Apache Tomcat', 'Eclipse JDT', 'Eclipse Platform'],
  lastUpdated: new Date().toISOString(),
  indexStatus: 'ready',
  embeddingModel: 'sentence-transformers/all-MiniLM-L6-v2',
  vectorDimensions: 384
};

// ============================================================
// Mock Health Status
// ============================================================

export const mockHealthStatus: HealthStatus = {
  status: 'healthy',
  version: '1.0.0-M1',
  services: {
    api: 'running',
    database: 'connected',
    chromadb: 'ready',
    embeddings: 'loaded',
    llm: 'mock-mode'
  },
  uptime: '2h 34m 12s'
};
