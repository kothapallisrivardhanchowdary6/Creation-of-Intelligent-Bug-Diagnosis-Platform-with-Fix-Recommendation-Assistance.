import { ReactNode } from 'react';
import {
  LayoutDashboard,
  Bug,
  FileText,
  Search,
  Cpu,
  Menu,
  X,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Info
} from 'lucide-react';
import { useState } from 'react';

interface LayoutProps {
  children: ReactNode;
  currentPage: string;
  onNavigate: (page: string) => void;
  notification: { type: 'success' | 'error' | 'info'; message: string } | null;
  isLoading: boolean;
}

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'submit', label: 'Submit Bug', icon: FileText },
  { id: 'bugs', label: 'Bug List', icon: Bug },
  { id: 'analysis', label: 'Analysis', icon: Cpu },
  { id: 'knowledge', label: 'Knowledge Base', icon: Search },
];

export default function Layout({ children, currentPage, onNavigate, notification, isLoading }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-gray-900 border-r border-gray-800 transform transition-transform duration-200 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
        <div className="flex items-center gap-3 p-5 border-b border-gray-800">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Bug className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-sm text-white">AI Defect Analysis</h1>
            <p className="text-xs text-gray-400">Milestone 1 — Foundation</p>
          </div>
        </div>

        <nav className="p-3 space-y-1">
          {navItems.map(item => (
            <button
              key={item.id}
              onClick={() => { onNavigate(item.id); setSidebarOpen(false); }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                currentPage === item.id
                  ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </button>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-800">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span>System Healthy</span>
          </div>
          <p className="text-xs text-gray-600 mt-1">v1.0.0-M1 • Mock Mode</p>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 min-h-screen overflow-auto">
        {/* Top bar */}
        <header className="sticky top-0 z-30 bg-gray-950/80 backdrop-blur-xl border-b border-gray-800 px-4 lg:px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => setSidebarOpen(!sidebarOpen)} className="lg:hidden p-2 rounded-lg hover:bg-gray-800">
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            <h2 className="text-lg font-semibold text-white">
              {navItems.find(n => n.id === currentPage)?.label || 'Dashboard'}
            </h2>
          </div>
          {isLoading && (
            <div className="flex items-center gap-2 text-sm text-blue-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Processing...</span>
            </div>
          )}
        </header>

        {/* Notification */}
        {notification && (
          <div className={`mx-4 lg:mx-6 mt-4 p-3 rounded-lg border flex items-center gap-3 text-sm animate-in fade-in slide-in-from-top-2 ${
            notification.type === 'success' ? 'bg-green-900/30 border-green-700/50 text-green-300' :
            notification.type === 'error' ? 'bg-red-900/30 border-red-700/50 text-red-300' :
            'bg-blue-900/30 border-blue-700/50 text-blue-300'
          }`}>
            {notification.type === 'success' && <CheckCircle2 className="w-4 h-4" />}
            {notification.type === 'error' && <AlertCircle className="w-4 h-4" />}
            {notification.type === 'info' && <Info className="w-4 h-4" />}
            {notification.message}
          </div>
        )}

        {/* Page content */}
        <div className="p-4 lg:p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
