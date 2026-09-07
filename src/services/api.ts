import { Bug, BugSubmission, AnalysisResult, KnowledgeBaseStatus, HealthStatus, SearchResult } from '../types';
import { sampleHistoricalBugs, generateMockAnalysis, mockKnowledgeBaseStatus, mockHealthStatus } from './mockData';

// ============================================================
// API Service — Mock Implementation
// Simulates the FastAPI backend for demo purposes
// ============================================================

const STORAGE_KEY = 'ai-defect-bugs';

function getStoredBugs(): Bug[] {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : [];
  } catch {
    return [];
  }
}

function storeBugs(bugs: Bug[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(bugs));
}

function generateBugId(): string {
  const timestamp = Date.now().toString(36).toUpperCase();
  const random = Math.random().toString(36).substring(2, 6).toUpperCase();
  return `BUG-${timestamp}-${random}`;
}

// Simulate network delay
function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ============================================================
// API Functions
// ============================================================

/**
 * POST /api/bugs — Submit a new bug
 */
export async function submitBug(submission: BugSubmission): Promise<Bug> {
  await delay(500);

  const bug: Bug = {
    ...submission,
    id: generateBugId(),
    createdAt: new Date().toISOString(),
    status: 'submitted'
  };

  const bugs = getStoredBugs();
  bugs.unshift(bug);
  storeBugs(bugs);

  return bug;
}

/**
 * GET /api/bugs — List all bugs
 */
export async function listBugs(): Promise<Bug[]> {
  await delay(300);
  return getStoredBugs();
}

/**
 * GET /api/bugs/{id} — Get bug by ID
 */
export async function getBug(id: string): Promise<Bug | null> {
  await delay(200);
  const bugs = getStoredBugs();
  return bugs.find(b => b.id === id) || null;
}

/**
 * POST /api/bugs/{id}/analyze — Run analysis pipeline
 */
export async function analyzeBug(id: string): Promise<AnalysisResult> {
  await delay(2000); // Simulate analysis time

  const bugs = getStoredBugs();
  const bugIndex = bugs.findIndex(b => b.id === id);

  if (bugIndex === -1) {
    throw new Error(`Bug ${id} not found`);
  }

  // Update status to analyzing
  bugs[bugIndex].status = 'analyzing';
  storeBugs(bugs);

  // Simulate progressive analysis
  await delay(1500);

  const analysis = generateMockAnalysis(bugs[bugIndex]);

  // Update bug with analysis
  bugs[bugIndex].status = 'analyzed';
  bugs[bugIndex].analysis = analysis;
  storeBugs(bugs);

  return analysis;
}

/**
 * GET /api/bugs/{id}/analysis — Get analysis results
 */
export async function getAnalysis(id: string): Promise<AnalysisResult | null> {
  await delay(200);
  const bugs = getStoredBugs();
  const bug = bugs.find(b => b.id === id);
  return bug?.analysis || null;
}

/**
 * POST /api/search — Semantic search
 */
export async function searchBugs(query: string, topK: number = 5): Promise<SearchResult[]> {
  await delay(800);

  // Simple mock search — filter historical bugs by query relevance
  const queryLower = query.toLowerCase();
  const results: SearchResult[] = sampleHistoricalBugs
    .map(bug => {
      const titleMatch = bug.title.toLowerCase().includes(queryLower) ? 0.3 : 0;
      const componentMatch = bug.component.toLowerCase().includes(queryLower) ? 0.2 : 0;
      const projectMatch = bug.project.toLowerCase().includes(queryLower) ? 0.1 : 0;
      const baseScore = bug.similarity * 0.4;
      const score = Math.min(1, baseScore + titleMatch + componentMatch + projectMatch + Math.random() * 0.1);

      return {
        bugId: bug.bugId,
        title: bug.title,
        description: bug.resolution,
        score,
        project: bug.project,
        metadata: {
          component: bug.component,
          severity: bug.severity,
          resolution: bug.resolution
        }
      };
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);

  return results;
}

/**
 * GET /api/knowledge-base/status
 */
export async function getKnowledgeBaseStatus(): Promise<KnowledgeBaseStatus> {
  await delay(400);
  return mockKnowledgeBaseStatus;
}

/**
 * GET /api/health
 */
export async function getHealth(): Promise<HealthStatus> {
  await delay(200);
  return mockHealthStatus;
}

/**
 * POST /api/bugs/upload — Upload file content
 */
export async function uploadFile(file: File): Promise<{ name: string; content: string; size: number }> {
  await delay(300);

  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      resolve({
        name: file.name,
        content: reader.result as string,
        size: file.size
      });
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
}

/**
 * Delete a bug
 */
export async function deleteBug(id: string): Promise<void> {
  await delay(200);
  const bugs = getStoredBugs().filter(b => b.id !== id);
  storeBugs(bugs);
}
