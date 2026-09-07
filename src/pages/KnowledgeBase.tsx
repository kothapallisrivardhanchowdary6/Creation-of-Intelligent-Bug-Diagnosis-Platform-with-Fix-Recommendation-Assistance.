import { useState, useEffect } from 'react';
import { SearchResult, KnowledgeBaseStatus } from '../types';
import { Search, Database, FileText, AlertCircle, Loader2, BarChart3 } from 'lucide-react';
import { getKnowledgeBaseStatus, searchBugs } from '../services/api';

interface KnowledgeBaseProps {
  onSearch: (query: string) => Promise<SearchResult[]>;
}

export default function KnowledgeBase({ onSearch }: KnowledgeBaseProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [status, setStatus] = useState<KnowledgeBaseStatus | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    getKnowledgeBaseStatus().then(setStatus);
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setHasSearched(true);
    try {
      const data = await searchBugs(query, 5);
      setResults(data);
    } catch {
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Knowledge Base Status */}
      {status && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center gap-3 mb-4">
            <Database className="w-5 h-5 text-blue-400" />
            <h3 className="font-semibold text-white">Knowledge Base Status</h3>
            <span className={`ml-auto text-xs px-2 py-0.5 rounded-full border ${
              status.indexStatus === 'ready' ? 'bg-green-900/30 text-green-400 border-green-700/50' : 'bg-yellow-900/30 text-yellow-400 border-yellow-700/50'
            }`}>
              {status.indexStatus}
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-xs text-gray-400">Documents</p>
              <p className="text-xl font-bold text-white">{status.totalDocuments}</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-xs text-gray-400">Embedding Model</p>
              <p className="text-xs font-mono text-white mt-1 truncate">{status.embeddingModel}</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-xs text-gray-400">Vector Dimensions</p>
              <p className="text-xl font-bold text-white">{status.vectorDimensions}</p>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-xs text-gray-400">Projects</p>
              <p className="text-xs text-white mt-1">{status.projects.join(', ')}</p>
            </div>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
          <Search className="w-5 h-5 text-purple-400" />
          Semantic Search
        </h3>
        <form onSubmit={handleSearch} className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              placeholder="Search for similar defects... (e.g., 'null pointer exception in network handler')"
            />
          </div>
          <button
            type="submit"
            disabled={isSearching || !query.trim()}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
          >
            {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Search
          </button>
        </form>
        <p className="text-xs text-gray-500 mt-2">
          Powered by RAG pipeline with sentence-transformers/all-MiniLM-L6-v2 embeddings and ChromaDB vector search
        </p>
      </div>

      {/* Results */}
      {hasSearched && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-green-400" />
            Search Results ({results.length} matches)
          </h3>
          {isSearching ? (
            <div className="text-center py-8">
              <Loader2 className="w-8 h-8 text-blue-400 animate-spin mx-auto mb-3" />
              <p className="text-sm text-gray-400">Performing semantic search...</p>
            </div>
          ) : results.length === 0 ? (
            <div className="text-center py-8">
              <AlertCircle className="w-8 h-8 text-gray-600 mx-auto mb-3" />
              <p className="text-sm text-gray-400">No results found</p>
            </div>
          ) : (
            <div className="space-y-3">
              {results.map((result, i) => (
                <div key={i} className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <FileText className="w-3.5 h-3.5 text-blue-400" />
                        <span className="text-xs font-mono text-blue-400">{result.bugId}</span>
                        <span className="text-xs text-gray-500">•</span>
                        <span className="text-xs text-gray-400">{result.project}</span>
                      </div>
                      <h4 className="text-sm font-medium text-white">{result.title}</h4>
                      <p className="text-xs text-gray-400 mt-1">{result.description}</p>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {Object.entries(result.metadata).map(([key, value]) => (
                          <span key={key} className="text-xs px-2 py-0.5 bg-gray-700/50 text-gray-300 rounded">
                            {key}: {value}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className="text-lg font-bold text-blue-400">{(result.score * 100).toFixed(1)}%</div>
                      <p className="text-xs text-gray-500">similarity</p>
                    </div>
                  </div>
                  {/* Similarity bar */}
                  <div className="mt-3 bg-gray-700 rounded-full h-1.5">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-purple-500 h-1.5 rounded-full transition-all"
                      style={{ width: `${result.score * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Sample Queries */}
      {!hasSearched && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-medium text-gray-300 mb-3">Try searching for:</h3>
          <div className="flex flex-wrap gap-2">
            {[
              'null pointer exception network',
              'memory leak rendering',
              'deadlock thread pool',
              'buffer overflow parser',
              'connection timeout',
              'CSS layout calculation',
              'race condition concurrent',
              'stack overflow recursive'
            ].map(q => (
              <button
                key={q}
                onClick={() => { setQuery(q); }}
                className="text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-full border border-gray-700 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
