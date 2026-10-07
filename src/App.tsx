import { useState, useEffect } from 'react';
import { Bug, AnalysisResult } from './types';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import BugSubmission from './pages/BugSubmission';
import BugList from './pages/BugList';
import BugAnalysis from './pages/BugAnalysis';
import KnowledgeBase from './pages/KnowledgeBase';
// ── M4 pages ──────────────────────────────────────────────────────────────────
import Analytics from './pages/Analytics';
import KnowledgeGrowth from './pages/KnowledgeGrowth';
import E2ETest from './pages/E2ETest';

import {
  listBugs, submitBug, analyzeBug, getAnalysis, deleteBug, searchBugs,
} from './services/api';

export default function App() {
  const [currentPage, setCurrentPage] = useState<string>('dashboard');
  const [bugs, setBugs] = useState<Bug[]>([]);
  const [selectedBug, setSelectedBug] = useState<Bug | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [notification, setNotification] = useState<{
    type: 'success' | 'error' | 'info';
    message: string;
  } | null>(null);

  // Load bugs on initial mount
  useEffect(() => {
    loadBugs();
  }, []);

  const showNotification = (type: 'success' | 'error' | 'info', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 4000);
  };

  const loadBugs = async () => {
    const data = await listBugs();
    setBugs(data);
  };

  const handleSubmitBug = async (submission: Parameters<typeof submitBug>[0]) => {
    try {
      setIsLoading(true);
      const bug = await submitBug(submission);
      showNotification('success', `Bug submitted successfully! ID: ${bug.id}`);
      await loadBugs();
      setCurrentPage('bugs');
    } catch {
      showNotification('error', 'Failed to submit bug');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyzeBug = async (bugId: string) => {
    try {
      setIsLoading(true);
      const bug = bugs.find(b => b.id === bugId) || null;
      setSelectedBug(bug);
      showNotification('info', 'Starting M3 AI analysis pipeline...');
      const result = await analyzeBug(bugId);
      setAnalysisResult(result);
      await loadBugs();
      showNotification('success', 'M3 Analysis complete!');
      setCurrentPage('analysis');
    } catch (err: unknown) {
      showNotification('error', `Analysis failed: ${(err as Error)?.message ?? 'unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewAnalysis = async (bugId: string) => {
    try {
      setIsLoading(true);
      const result = await getAnalysis(bugId);
      if (result) {
        setAnalysisResult(result);
        const bug = bugs.find(b => b.id === bugId);
        setSelectedBug(bug || null);
        setCurrentPage('analysis');
      } else {
        showNotification('info', 'No analysis found. Run analysis first.');
      }
    } catch {
      showNotification('error', 'Failed to load analysis');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteBug = async (bugId: string) => {
    await deleteBug(bugId);
    await loadBugs();
    showNotification('success', 'Bug deleted');
  };

  const handleSearch = async (query: string) => {
    return await searchBugs(query);
  };

  const renderPage = () => {
    switch (currentPage) {
      // ── M1-M3 pages (unchanged) ──────────────────────────────────────────
      case 'dashboard':
        return (
          <Dashboard
            bugs={bugs}
            onNavigate={setCurrentPage}
            onAnalyze={handleAnalyzeBug}
            onViewAnalysis={handleViewAnalysis}
          />
        );
      case 'submit':
        return <BugSubmission onSubmit={handleSubmitBug} isLoading={isLoading} />;
      case 'bugs':
        return (
          <BugList
            bugs={bugs}
            onAnalyze={handleAnalyzeBug}
            onViewAnalysis={handleViewAnalysis}
            onDelete={handleDeleteBug}
            onRefresh={loadBugs}
          />
        );
      case 'analysis':
        return <BugAnalysis bug={selectedBug} analysis={analysisResult} />;
      case 'knowledge':
        return <KnowledgeBase onSearch={handleSearch} />;

      // ── M4 pages ──────────────────────────────────────────────────────────
      case 'analytics':
        return <Analytics />;
      case 'kb-growth':
        return <KnowledgeGrowth />;
      case 'e2e-test':
        return <E2ETest />;

      default:
        return (
          <Dashboard
            bugs={bugs}
            onNavigate={setCurrentPage}
            onAnalyze={handleAnalyzeBug}
            onViewAnalysis={handleViewAnalysis}
          />
        );
    }
  };

  return (
    <Layout
      currentPage={currentPage}
      onNavigate={setCurrentPage}
      notification={notification}
      isLoading={isLoading}
    >
      {renderPage()}
    </Layout>
  );
}
