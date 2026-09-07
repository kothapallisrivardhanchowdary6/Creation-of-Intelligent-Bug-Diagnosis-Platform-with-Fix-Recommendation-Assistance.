import { useState } from 'react';
import { GitBranch, Cpu, Database, Layers, FileText, Zap, BookOpen } from 'lucide-react';

type Tab = 'architecture' | 'agents' | 'rag' | 'datasets' | 'api';

export default function Architecture() {
  const [activeTab, setActiveTab] = useState<Tab>('architecture');

  const tabs = [
    { id: 'architecture' as Tab, label: 'System Architecture', icon: GitBranch },
    { id: 'agents' as Tab, label: 'AI Agents', icon: Cpu },
    { id: 'rag' as Tab, label: 'RAG Pipeline', icon: Layers },
    { id: 'datasets' as Tab, label: 'Datasets', icon: Database },
    { id: 'api' as Tab, label: 'API Reference', icon: FileText },
  ];

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="flex flex-wrap gap-2 border-b border-gray-800 pb-3">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${
              activeTab === tab.id
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Architecture Tab */}
      {activeTab === 'architecture' && (
        <div className="space-y-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-blue-400" />
              System Architecture
            </h3>
            <div className="bg-gray-950 rounded-lg p-6 border border-gray-800 overflow-x-auto">
              <pre className="text-xs text-gray-300 font-mono leading-relaxed whitespace-pre">{`
┌─────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + TypeScript)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │Dashboard │  │Bug Submit│  │Bug List  │  │Analysis  │  │Knowledge │ │
│  │  Page    │  │  Page    │  │  Page    │  │  Page    │  │  Base    │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       └──────────────┴──────────────┴──────────────┴──────────────┘      │
│                              │ API Calls                                  │
└──────────────────────────────┼──────────────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────────────┐
│                     BACKEND (FastAPI + Python)                           │
│                              │                                          │
│  ┌───────────────────────────▼──────────────────────────────────────┐  │
│  │                     API ROUTER LAYER                               │  │
│  │  POST /api/bugs  │  GET /api/bugs/{id}  │  POST /api/search      │  │
│  │  POST /api/bugs/{id}/analyze  │  GET /api/health                  │  │
│  └───────────────────────────┬──────────────────────────────────────┘  │
│                              │                                          │
│  ┌───────────────────────────▼──────────────────────────────────────┐  │
│  │                   AGENT ORCHESTRATOR                               │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │  │
│  │  │  Triage  │→│Log Anal. │→│Root Cause│→│Duplicate │→│Remediat│ │  │
│  │  │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │ │  ion   │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘ │  │
│  └───────────────────────────┬──────────────────────────────────────┘  │
│                              │                                          │
│  ┌───────────────────────────▼──────────────────────────────────────┐  │
│  │                      RAG PIPELINE                                  │  │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │  │
│  │  │Embeddings│──▶│ ChromaDB │──▶│ Semantic │──▶│  Top-K   │     │  │
│  │  │ MiniLM   │   │  Vector  │   │ Retrieval│   │ Results  │     │  │
│  │  └──────────┘   └──────────┘   └──────────┘   └──────────┘     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              │                                          │
│  ┌───────────────────────────▼──────────────────────────────────────┐  │
│  │                    DATA LAYER                                      │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │  │
│  │  │  PostgreSQL  │  │   ChromaDB   │  │  LLM (Mock)  │           │  │
│  │  │  + SQLAlchemy│  │   Vectors    │  │  OpenAI API  │           │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
`}</pre>
            </div>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4">Technology Stack</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                { name: 'React + TypeScript', desc: 'Frontend UI framework with type safety', category: 'Frontend' },
                { name: 'Vite', desc: 'Fast build tool and dev server', category: 'Frontend' },
                { name: 'Tailwind CSS', desc: 'Utility-first CSS framework', category: 'Frontend' },
                { name: 'FastAPI', desc: 'High-performance Python API framework', category: 'Backend' },
                { name: 'PostgreSQL', desc: 'Primary relational database', category: 'Database' },
                { name: 'SQLAlchemy', desc: 'Python ORM for database operations', category: 'Database' },
                { name: 'ChromaDB', desc: 'Vector database for embeddings', category: 'Vector DB' },
                { name: 'sentence-transformers', desc: 'Text embedding model (MiniLM-L6-v2)', category: 'ML' },
                { name: 'OpenAI API', desc: 'LLM for analysis (mock mode available)', category: 'AI' },
                { name: 'Docker', desc: 'Containerization for deployment', category: 'DevOps' },
              ].map(tech => (
                <div key={tech.name} className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs px-1.5 py-0.5 bg-blue-900/30 text-blue-300 rounded">{tech.category}</span>
                  </div>
                  <p className="text-sm font-medium text-white">{tech.name}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{tech.desc}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4">Data Flow</h3>
            <div className="bg-gray-950 rounded-lg p-4 border border-gray-800">
              <pre className="text-xs text-gray-300 font-mono leading-relaxed">{`
Bug Submission → Validation → PostgreSQL Storage
                                    ↓
                            Analysis Trigger
                                    ↓
                    ┌───────────────────────────────┐
                    │      Agent Orchestrator        │
                    │                                │
                    │  1. Triage Agent               │
                    │     → Severity, Priority,      │
                    │       Category, Component      │
                    │                                │
                    │  2. Log Analysis Agent          │
                    │     → Exceptions, Patterns,    │
                    │       Stack trace analysis     │
                    │                                │
                    │  3. Root Cause Agent            │
                    │     → Probable cause,          │
                    │       Evidence, Confidence     │
                    │                                │
                    │  4. Duplicate Detection Agent   │
                    │     → RAG search, similarity   │
                    │       scoring, matching bugs   │
                    │                                │
                    │  5. Remediation Agent           │
                    │     → Fix suggestions,         │
                    │       Debugging steps          │
                    └───────────────────────────────┘
                                    ↓
                         Structured JSON Results
                                    ↓
                        Frontend Display & Storage
`}</pre>
            </div>
          </div>
        </div>
      )}

      {/* Agents Tab */}
      {activeTab === 'agents' && (
        <div className="space-y-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-purple-400" />
              AI Agent Definitions
            </h3>
            <div className="space-y-4">
              {[
                {
                  name: 'Triage Agent',
                  color: 'border-blue-500/30 bg-blue-950/10',
                  icon: '🛡️',
                  desc: 'Classifies bug severity, priority, category, and component assignment.',
                  inputs: ['Bug title', 'Description', 'Stack trace', 'Error logs'],
                  outputs: ['Severity (critical/high/medium/low)', 'Priority (P0-P3)', 'Category', 'Component', 'Confidence score'],
                  method: 'Pattern matching + LLM classification with historical context'
                },
                {
                  name: 'Log Analysis Agent',
                  color: 'border-purple-500/30 bg-purple-950/10',
                  icon: '🔍',
                  desc: 'Parses and analyzes error logs, stack traces, and exception patterns.',
                  inputs: ['Stack trace', 'Error logs', 'Environment details'],
                  outputs: ['Exception list', 'Stack trace analysis', 'Error patterns', 'Suspicious log entries'],
                  method: 'Regex parsing + semantic analysis + pattern recognition'
                },
                {
                  name: 'Root Cause Agent',
                  color: 'border-orange-500/30 bg-orange-950/10',
                  icon: '🎯',
                  desc: 'Identifies the most probable root cause with supporting evidence.',
                  inputs: ['Triage results', 'Log analysis', 'Historical similar bugs'],
                  outputs: ['Probable root cause', 'Evidence list', 'Confidence score', 'Related components'],
                  method: 'RAG retrieval + LLM reasoning + causal chain analysis'
                },
                {
                  name: 'Duplicate Detection Agent',
                  color: 'border-green-500/30 bg-green-950/10',
                  icon: '📋',
                  desc: 'Detects potential duplicates using semantic similarity search.',
                  inputs: ['Bug description', 'Title', 'Category'],
                  outputs: ['Similarity score', 'Duplicate probability', 'Matching historical bugs', 'Analysis summary'],
                  method: 'ChromaDB vector search + cosine similarity + threshold classification'
                },
                {
                  name: 'Remediation Agent',
                  color: 'border-red-500/30 bg-red-950/10',
                  icon: '🔧',
                  desc: 'Suggests fixes, debugging steps, and regression testing strategies.',
                  inputs: ['Root cause analysis', 'Historical resolutions', 'Component context'],
                  outputs: ['Suggested fix', 'Debugging steps', 'Validation steps', 'Regression tests', 'Effort estimate'],
                  method: 'RAG-powered resolution retrieval + LLM synthesis + best practices'
                },
              ].map(agent => (
                <div key={agent.name} className={`border rounded-xl p-5 ${agent.color}`}>
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-2xl">{agent.icon}</span>
                    <h4 className="font-semibold text-white text-lg">{agent.name}</h4>
                  </div>
                  <p className="text-sm text-gray-300 mb-3">{agent.desc}</p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div>
                      <p className="text-xs text-gray-400 font-medium mb-1">Inputs</p>
                      <ul className="space-y-0.5">
                        {agent.inputs.map((inp, i) => (
                          <li key={i} className="text-xs text-gray-300">• {inp}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <p className="text-xs text-gray-400 font-medium mb-1">Outputs</p>
                      <ul className="space-y-0.5">
                        {agent.outputs.map((out, i) => (
                          <li key={i} className="text-xs text-gray-300">• {out}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <p className="text-xs text-gray-400 font-medium mb-1">Method</p>
                      <p className="text-xs text-gray-300">{agent.method}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* RAG Tab */}
      {activeTab === 'rag' && (
        <div className="space-y-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Layers className="w-5 h-5 text-green-400" />
              RAG Architecture & Retrieval Pipeline
            </h3>
            <div className="space-y-4 text-sm text-gray-300">
              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                <h4 className="font-medium text-white mb-2">What is RAG?</h4>
                <p>Retrieval-Augmented Generation (RAG) combines information retrieval with LLM generation. Instead of relying solely on the model's training data, RAG retrieves relevant documents from a knowledge base and uses them as context for generating responses.</p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                <h4 className="font-medium text-white mb-2">Embeddings & Vector Search</h4>
                <p className="mb-2">Text is converted to dense vector representations using <code className="text-blue-300 bg-blue-900/20 px-1 rounded">sentence-transformers/all-MiniLM-L6-v2</code> (384 dimensions). These vectors capture semantic meaning, allowing similarity comparison via cosine similarity.</p>
                <p><strong>Cosine Similarity:</strong> Measures the angle between two vectors. Score ranges from -1 (opposite) to 1 (identical). Higher scores indicate greater semantic similarity.</p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                <h4 className="font-medium text-white mb-2">Retrieval Pipeline</h4>
                <pre className="text-xs text-gray-300 font-mono bg-gray-950 rounded p-3 mt-2">{`
1. INGESTION
   Raw Defect Data → Cleaning → Normalization → Chunking
   → Embedding Generation → ChromaDB Indexing

2. RETRIEVAL
   Query → Embedding → ChromaDB Search → Top-K Results
   → Cosine Similarity Scoring → Metadata Filtering

3. GENERATION
   Retrieved Context + Query → LLM Prompt → Analysis Result
`}</pre>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                <h4 className="font-medium text-white mb-2">Vector Metadata</h4>
                <p>Each stored vector retains metadata for filtering and context:</p>
                <ul className="mt-2 space-y-1 text-xs">
                  <li>• <code className="text-blue-300">bug_id</code> — Unique identifier</li>
                  <li>• <code className="text-blue-300">project</code> — Source project (Mozilla/Apache/Eclipse)</li>
                  <li>• <code className="text-blue-300">component</code> — Software component</li>
                  <li>• <code className="text-blue-300">severity</code> — Bug severity level</li>
                  <li>• <code className="text-blue-300">section</code> — Document section (title/description/resolution)</li>
                  <li>• <code className="text-blue-300">resolution</code> — How the bug was fixed</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Datasets Tab */}
      {activeTab === 'datasets' && (
        <div className="space-y-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Database className="w-5 h-5 text-orange-400" />
              Historical Defect Datasets
            </h3>
            <div className="space-y-4">
              {[
                {
                  name: 'Mozilla Firefox (MDVP)',
                  desc: 'Defects from Mozilla\'s Bugzilla tracking system. Covers Firefox browser components including networking, layout engine, graphics, and JavaScript engine.',
                  samples: '4 sample defects',
                  fields: ['Bug ID', 'Component', 'Severity', 'Description', 'Resolution', 'Status']
                },
                {
                  name: 'Apache HTTP Server & Tomcat',
                  desc: 'Defects from Apache JIRA issue tracker. Includes HTTP server core issues, thread pool problems, connection handling, and security vulnerabilities.',
                  samples: '4 sample defects',
                  fields: ['Issue Key', 'Project', 'Type', 'Priority', 'Summary', 'Description', 'Resolution']
                },
                {
                  name: 'Eclipse JDT & Platform',
                  desc: 'Defects from Eclipse bug tracking. Covers Java Development Tools compiler issues, UI framework problems, and plugin architecture defects.',
                  samples: '4 sample defects',
                  fields: ['Bug ID', 'Product', 'Component', 'Severity', 'Summary', 'Description', 'Status']
                }
              ].map(ds => (
                <div key={ds.name} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                  <h4 className="font-medium text-white mb-1">{ds.name}</h4>
                  <p className="text-sm text-gray-400 mb-2">{ds.desc}</p>
                  <div className="flex items-center gap-4 text-xs">
                    <span className="text-green-400">✓ {ds.samples} included</span>
                    <span className="text-gray-500">Fields: {ds.fields.join(', ')}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-blue-400" />
              Research References
            </h3>
            <div className="space-y-3 text-sm text-gray-300">
              <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
                <p className="font-medium text-white">Software Defect Analysis Workflow</p>
                <p className="text-xs text-gray-400 mt-1">Traditional: Manual triage → Assignment → Investigation → Fix → Verify. AI-enhanced: Automated classification → RAG-powered analysis → Agent-based diagnosis → Remediation suggestions.</p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
                <p className="font-medium text-white">Bug Report Structures</p>
                <p className="text-xs text-gray-400 mt-1">Standard fields: Title, Description, Steps to Reproduce, Expected/Actual Behavior, Severity, Priority, Component, Environment, Stack Trace, Logs, Attachments.</p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
                <p className="font-medium text-white">Semantic Chunking Strategy</p>
                <p className="text-xs text-gray-400 mt-1">Defects are chunked by semantic sections (title, description, stack trace, resolution) rather than fixed-size chunks. This preserves context and improves retrieval accuracy.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* API Tab */}
      {activeTab === 'api' && (
        <div className="space-y-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-400" />
              API Endpoints
            </h3>
            <div className="space-y-3">
              {[
                { method: 'POST', path: '/api/bugs', desc: 'Submit a new bug report', body: '{ title, description, stackTrace?, errorLogs?, environment?, files? }' },
                { method: 'POST', path: '/api/bugs/upload', desc: 'Upload file attachment', body: 'multipart/form-data with file' },
                { method: 'GET', path: '/api/bugs/{id}', desc: 'Get bug by ID', body: null },
                { method: 'POST', path: '/api/bugs/{id}/analyze', desc: 'Run AI analysis pipeline', body: null },
                { method: 'POST', path: '/api/search', desc: 'Semantic search knowledge base', body: '{ query, topK? }' },
                { method: 'GET', path: '/api/bugs/{id}/analysis', desc: 'Get analysis results', body: null },
                { method: 'GET', path: '/api/knowledge-base/status', desc: 'Get knowledge base status', body: null },
                { method: 'GET', path: '/api/health', desc: 'Health check endpoint', body: null },
              ].map((ep, i) => (
                <div key={i} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                      ep.method === 'GET' ? 'bg-green-900/40 text-green-300' : 'bg-blue-900/40 text-blue-300'
                    }`}>
                      {ep.method}
                    </span>
                    <code className="text-sm text-white font-mono">{ep.path}</code>
                  </div>
                  <p className="text-sm text-gray-300">{ep.desc}</p>
                  {ep.body && (
                    <p className="text-xs text-gray-500 mt-1 font-mono">Body: {ep.body}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
