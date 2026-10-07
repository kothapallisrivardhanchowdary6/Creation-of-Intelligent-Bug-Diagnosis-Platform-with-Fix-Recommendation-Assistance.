/**
 * M4.1 — Defect Pattern Analytics Dashboard
 *
 * Displays real analytics from submitted bugs + ChromaDB knowledge base.
 * All data fetched from backend /api/analytics/* endpoints.
 * Uses recharts for visualizations.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';
import {
  BarChart3, PieChart as PieIcon, TrendingUp, AlertTriangle, CheckCircle2,
  RefreshCw, Filter, X, Layers, GitBranch, Cpu, Clock, Database,
} from 'lucide-react';
import type {
  AnalyticsOverview, AnalyticsTrends, AnalyticsComponents,
  AnalyticsExceptions, AnalyticsRootCauses, DuplicateStats, AnalyticsClusters,
  AnalyticsFilters,
} from '../types';
import {
  getAnalyticsOverview, getAnalyticsTrends, getAnalyticsComponents,
  getAnalyticsExceptions, getAnalyticsRootCauses, getAnalyticsDuplicates,
  getAnalyticsClusters,
} from '../services/api';

// ── Colour palettes ────────────────────────────────────────────────────────────
const SEVERITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
  unknown: '#6b7280',
};

const PRIORITY_COLORS: Record<string, string> = {
  P0: '#ef4444',
  P1: '#f97316',
  P2: '#3b82f6',
  P3: '#22c55e',
  unknown: '#6b7280',
};

const CHART_COLORS = [
  '#3b82f6', '#8b5cf6', '#ec4899', '#f97316', '#22c55e',
  '#06b6d4', '#eab308', '#ef4444', '#14b8a6', '#a855f7',
];

// ── Tiny helper components ────────────────────────────────────────────────────

function StatCard({
  label, value, sub, color, icon: Icon,
}: {
  label: string; value: number | string; sub?: string; color: string; icon: React.FC<{className?: string}>;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-start gap-3">
      <div className={`p-2 rounded-lg ${color}`}>
        <Icon className="w-4 h-4 text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-sm font-medium text-gray-300">{label}</p>
        {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

function SectionHeader({ title, icon: Icon }: { title: string; icon: React.FC<{className?: string}> }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <Icon className="w-4 h-4 text-blue-400" />
      <h3 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">{title}</h3>
    </div>
  );
}

function ChartCard({ title, children, className = '' }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-xl p-5 ${className}`}>
      <h4 className="text-sm font-semibold text-gray-300 mb-4">{title}</h4>
      {children}
    </div>
  );
}

function EmptyChart({ message = 'No data yet — submit and analyze bugs to populate analytics.' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-10 text-gray-600">
      <BarChart3 className="w-8 h-8 mb-2" />
      <p className="text-sm">{message}</p>
    </div>
  );
}

// ── Filter bar ────────────────────────────────────────────────────────────────

const SEVERITIES = ['critical', 'high', 'medium', 'low'];
const PRIORITIES = ['P0', 'P1', 'P2', 'P3'];

function FilterBar({
  filters, onChange, onClear,
}: {
  filters: AnalyticsFilters;
  onChange: (f: AnalyticsFilters) => void;
  onClear: () => void;
}) {
  const hasFilters = Object.values(filters).some(v => v != null && v !== '');
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-6">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-1.5 text-sm text-gray-400 shrink-0">
          <Filter className="w-3.5 h-3.5" />
          <span>Filters:</span>
        </div>

        <select
          value={filters.severity ?? ''}
          onChange={e => onChange({ ...filters, severity: e.target.value || undefined })}
          className="bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-1.5 focus:ring-1 focus:ring-blue-500 focus:outline-none"
        >
          <option value="">All Severities</option>
          {SEVERITIES.map(s => (
            <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
          ))}
        </select>

        <select
          value={filters.priority ?? ''}
          onChange={e => onChange({ ...filters, priority: e.target.value || undefined })}
          className="bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-1.5 focus:ring-1 focus:ring-blue-500 focus:outline-none"
        >
          <option value="">All Priorities</option>
          {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
        </select>

        <input
          type="text"
          placeholder="Component..."
          value={filters.component ?? ''}
          onChange={e => onChange({ ...filters, component: e.target.value || undefined })}
          className="bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-1.5 w-36 focus:ring-1 focus:ring-blue-500 focus:outline-none placeholder-gray-600"
        />

        <input
          type="text"
          placeholder="Exception type..."
          value={filters.exceptionType ?? ''}
          onChange={e => onChange({ ...filters, exceptionType: e.target.value || undefined })}
          className="bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-1.5 w-40 focus:ring-1 focus:ring-blue-500 focus:outline-none placeholder-gray-600"
        />

        <div className="flex items-center gap-2">
          <input
            type="date"
            value={filters.dateFrom ?? ''}
            onChange={e => onChange({ ...filters, dateFrom: e.target.value || undefined })}
            className="bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-1.5 focus:ring-1 focus:ring-blue-500 focus:outline-none"
          />
          <span className="text-gray-600 text-xs">to</span>
          <input
            type="date"
            value={filters.dateTo ?? ''}
            onChange={e => onChange({ ...filters, dateTo: e.target.value || undefined })}
            className="bg-gray-800 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-1.5 focus:ring-1 focus:ring-blue-500 focus:outline-none"
          />
        </div>

        <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.isDuplicate === true}
            onChange={e => onChange({ ...filters, isDuplicate: e.target.checked ? true : undefined })}
            className="w-3.5 h-3.5 accent-blue-500"
          />
          Duplicates only
        </label>

        {hasFilters && (
          <button
            onClick={onClear}
            className="flex items-center gap-1.5 text-xs text-red-400 hover:text-red-300 ml-auto"
          >
            <X className="w-3 h-3" /> Clear filters
          </button>
        )}
      </div>
    </div>
  );
}

// ── Main Analytics component ──────────────────────────────────────────────────

export default function Analytics() {
  const [filters, setFilters] = useState<AnalyticsFilters>({});
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [trends, setTrends] = useState<AnalyticsTrends | null>(null);
  const [components, setComponents] = useState<AnalyticsComponents | null>(null);
  const [exceptions, setExceptions] = useState<AnalyticsExceptions | null>(null);
  const [rootCauses, setRootCauses] = useState<AnalyticsRootCauses | null>(null);
  const [duplicates, setDuplicates] = useState<DuplicateStats | null>(null);
  const [clusters, setClusters] = useState<AnalyticsClusters | null>(null);
  const [granularity, setGranularity] = useState<'day' | 'week' | 'month'>('day');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [ov, tr, co, ex, rc, du, cl] = await Promise.allSettled([
        getAnalyticsOverview(filters),
        getAnalyticsTrends(filters, granularity),
        getAnalyticsComponents(filters),
        getAnalyticsExceptions(filters),
        getAnalyticsRootCauses(filters),
        getAnalyticsDuplicates(filters),
        getAnalyticsClusters(5, 0.55),
      ]);
      if (ov.status === 'fulfilled') setOverview(ov.value);
      if (tr.status === 'fulfilled') setTrends(tr.value);
      if (co.status === 'fulfilled') setComponents(co.value);
      if (ex.status === 'fulfilled') setExceptions(ex.value);
      if (rc.status === 'fulfilled') setRootCauses(rc.value);
      if (du.status === 'fulfilled') setDuplicates(du.value);
      if (cl.status === 'fulfilled') setClusters(cl.value);
      // Surface any errors
      const firstFailed = [ov, tr, co, ex, rc, du, cl].find(r => r.status === 'rejected');
      if (firstFailed && firstFailed.status === 'rejected') {
        setError(`Some analytics failed to load: ${(firstFailed as PromiseRejectedResult).reason?.message}`);
      }
    } catch (e: unknown) {
      setError(`Failed to load analytics: ${(e as Error).message}`);
    } finally {
      setLoading(false);
      setLastRefresh(new Date());
    }
  }, [filters, granularity]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  // ── Build chart data ───────────────────────────────────────────────────────

  const severityPieData = overview
    ? Object.entries(overview.severity_distribution)
        .filter(([, v]) => v > 0)
        .map(([name, value]) => ({ name, value }))
    : [];

  const priorityPieData = overview
    ? Object.entries(overview.priority_distribution)
        .filter(([, v]) => v > 0)
        .map(([name, value]) => ({ name, value }))
    : [];

  const componentBarData = (components?.components ?? []).slice(0, 8).map(c => ({
    name: c.component.length > 14 ? c.component.slice(0, 14) + '…' : c.component,
    total: c.total,
    critical: c.critical,
    high: c.high,
    medium: c.medium,
    low: c.low,
  }));

  const exceptionBarData = (exceptions?.exception_distribution ?? []).slice(0, 8).map(e => ({
    name: e.exception.length > 18 ? e.exception.slice(0, 18) + '…' : e.exception,
    count: e.count,
  }));

  const trendLineData = (trends?.trend_series ?? []).slice(-20).map(t => ({
    period: t.period.length > 10 ? t.period.slice(5) : t.period,
    total: t.total,
    critical: t.critical ?? 0,
    high: t.high ?? 0,
    medium: t.medium ?? 0,
    low: t.low ?? 0,
    kb: t.historical_kb_entries ?? 0,
  }));

  const dupClassData = duplicates
    ? Object.entries(duplicates.classification_distribution)
        .filter(([, v]) => v > 0)
        .map(([name, value]) => ({ name, value }))
    : [];

  const rcData = (rootCauses?.top_root_causes ?? []).slice(0, 5).map(r => ({
    name: r.cause.length > 30 ? r.cause.slice(0, 30) + '…' : r.cause,
    count: r.count,
  }));

  const kbClusterData = (clusters?.kb_clusters ?? []).slice(0, 6).map(c => ({
    subject: c.label.length > 12 ? c.label.slice(0, 12) + '…' : c.label,
    count: c.size,
    critical: c.severity_breakdown.critical ?? 0,
  }));

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-xl font-bold text-white">Defect Pattern Analytics</h2>
          <p className="text-sm text-gray-400 mt-0.5">
            Real-time analysis of submitted bugs and historical defect patterns
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-600">
            Last refresh: {lastRefresh.toLocaleTimeString()}
          </span>
          <button
            onClick={fetchAll}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm rounded-lg transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="bg-red-900/30 border border-red-700/50 rounded-lg p-3 text-sm text-red-300 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Filter bar */}
      <FilterBar
        filters={filters}
        onChange={f => setFilters(f)}
        onClear={() => setFilters({})}
      />

      {/* Loading skeleton */}
      {loading && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-4 h-20 animate-pulse" />
          ))}
        </div>
      )}

      {!loading && (
        <>
          {/* ── Overview stat cards ─────────────────────────────────────────── */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              label="Total Bugs"
              value={overview?.total_bugs ?? 0}
              sub={`${overview?.analyzed_bugs ?? 0} analyzed`}
              color="bg-blue-600"
              icon={BarChart3}
            />
            <StatCard
              label="Critical / High"
              value={`${overview?.severity_distribution?.critical ?? 0} / ${overview?.severity_distribution?.high ?? 0}`}
              sub="require immediate attention"
              color="bg-red-600"
              icon={AlertTriangle}
            />
            <StatCard
              label="Duplicates"
              value={overview?.duplicate_stats?.duplicates ?? 0}
              sub={`${((overview?.duplicate_stats?.duplicate_rate ?? 0) * 100).toFixed(0)}% duplicate rate`}
              color="bg-purple-600"
              icon={GitBranch}
            />
            <StatCard
              label="Knowledge Base"
              value={overview?.knowledge_base?.total_documents ?? 0}
              sub="historical defects indexed"
              color="bg-emerald-600"
              icon={Database}
            />
          </div>

          {/* Secondary stat row */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {(['critical', 'high', 'medium', 'low'] as const).map(sev => (
              <div
                key={sev}
                className="bg-gray-900 border border-gray-800 rounded-xl p-4"
                style={{ borderLeftWidth: 3, borderLeftColor: SEVERITY_COLORS[sev] }}
              >
                <p className="text-lg font-bold text-white">
                  {overview?.severity_distribution?.[sev] ?? 0}
                </p>
                <p className="text-xs text-gray-400 capitalize mt-0.5">{sev}</p>
              </div>
            ))}
          </div>

          {/* ── Row 1: Severity + Priority pies ────────────────────────────── */}
          <div>
            <SectionHeader title="Severity & Priority Distribution" icon={PieIcon} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <ChartCard title="Severity Distribution">
                {severityPieData.length === 0 ? <EmptyChart /> : (
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie
                        data={severityPieData}
                        cx="50%" cy="50%"
                        innerRadius={55} outerRadius={90}
                        paddingAngle={3}
                        dataKey="value"
                        label={({ name, percent }) =>
                          `${name} ${(percent * 100).toFixed(0)}%`
                        }
                        labelLine={false}
                      >
                        {severityPieData.map(entry => (
                          <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name] ?? '#6b7280'} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                        labelStyle={{ color: '#e5e7eb' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>

              <ChartCard title="Priority Distribution">
                {priorityPieData.length === 0 ? <EmptyChart /> : (
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie
                        data={priorityPieData}
                        cx="50%" cy="50%"
                        innerRadius={55} outerRadius={90}
                        paddingAngle={3}
                        dataKey="value"
                        label={({ name, percent }) =>
                          `${name} ${(percent * 100).toFixed(0)}%`
                        }
                        labelLine={false}
                      >
                        {priorityPieData.map(entry => (
                          <Cell key={entry.name} fill={PRIORITY_COLORS[entry.name] ?? '#6b7280'} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>
            </div>
          </div>

          {/* ── Row 2: Components stacked bar ──────────────────────────────── */}
          <div>
            <SectionHeader title="Component-wise Bug Frequency" icon={Layers} />
            <ChartCard title="Bugs per Component (by severity)">
              {componentBarData.length === 0 ? <EmptyChart /> : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={componentBarData} margin={{ left: -10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12, color: '#9ca3af' }} />
                    {(['critical', 'high', 'medium', 'low'] as const).map(sev => (
                      <Bar key={sev} dataKey={sev} stackId="a" fill={SEVERITY_COLORS[sev]} />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              )}
            </ChartCard>
          </div>

          {/* ── Row 3: Exceptions + Root Causes ────────────────────────────── */}
          <div>
            <SectionHeader title="Exception & Root Cause Analysis" icon={Cpu} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <ChartCard title="Top Exception Types">
                {exceptionBarData.length === 0 ? <EmptyChart /> : (
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={exceptionBarData} layout="vertical" margin={{ left: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                      <YAxis dataKey="name" type="category" tick={{ fill: '#9ca3af', fontSize: 10 }} width={120} />
                      <Tooltip
                        contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                      />
                      <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                        {exceptionBarData.map((_, i) => (
                          <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>

              <ChartCard title="Most Common Root Causes">
                {rcData.length === 0 ? <EmptyChart message="No analyzed bugs yet." /> : (
                  <div className="space-y-2">
                    {rcData.map((r, i) => (
                      <div key={i} className="flex items-center gap-3">
                        <div
                          className="w-2 h-2 rounded-full shrink-0"
                          style={{ background: CHART_COLORS[i % CHART_COLORS.length] }}
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-xs text-gray-300 truncate">{r.name}</p>
                          <div className="h-1.5 bg-gray-800 rounded-full mt-1">
                            <div
                              className="h-1.5 rounded-full"
                              style={{
                                width: `${(r.count / (rcData[0]?.count || 1)) * 100}%`,
                                background: CHART_COLORS[i % CHART_COLORS.length],
                              }}
                            />
                          </div>
                        </div>
                        <span className="text-xs text-gray-500 shrink-0 w-5 text-right">{r.count}</span>
                      </div>
                    ))}
                  </div>
                )}
              </ChartCard>
            </div>
          </div>

          {/* ── Row 4: Trends ──────────────────────────────────────────────── */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <SectionHeader title="Defect Trends Over Time" icon={TrendingUp} />
              <div className="flex gap-1 -mt-4">
                {(['day', 'week', 'month'] as const).map(g => (
                  <button
                    key={g}
                    onClick={() => setGranularity(g)}
                    className={`px-3 py-1 text-xs rounded-lg transition-colors ${
                      granularity === g
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                    }`}
                  >
                    {g.charAt(0).toUpperCase() + g.slice(1)}
                  </button>
                ))}
              </div>
            </div>
            <ChartCard title={`Bug volume over time (${granularity})`}>
              {trendLineData.length === 0 || trendLineData.every(t => t.total === 0) ? (
                <EmptyChart message="No trend data yet — submit bugs to track trends." />
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <LineChart data={trendLineData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="period" tick={{ fill: '#9ca3af', fontSize: 10 }} />
                    <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12, color: '#9ca3af' }} />
                    <Line type="monotone" dataKey="total" stroke="#3b82f6" strokeWidth={2} dot={false} name="Total" />
                    <Line type="monotone" dataKey="critical" stroke="#ef4444" strokeWidth={1.5} dot={false} name="Critical" />
                    <Line type="monotone" dataKey="high" stroke="#f97316" strokeWidth={1.5} dot={false} name="High" />
                    <Line type="monotone" dataKey="kb" stroke="#22c55e" strokeWidth={1} strokeDasharray="4 2" dot={false} name="KB Entries" />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </ChartCard>
          </div>

          {/* ── Row 5: Duplicates + Clusters ───────────────────────────────── */}
          <div>
            <SectionHeader title="Duplicate Statistics & Similar Bug Clusters" icon={GitBranch} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Duplicate pie + stats */}
              <ChartCard title="Duplicate Classification">
                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div className="bg-gray-800 rounded-lg p-3 text-center">
                    <p className="text-xl font-bold text-white">{duplicates?.duplicates ?? 0}</p>
                    <p className="text-xs text-red-400">Duplicates</p>
                  </div>
                  <div className="bg-gray-800 rounded-lg p-3 text-center">
                    <p className="text-xl font-bold text-white">{duplicates?.related_issues ?? 0}</p>
                    <p className="text-xs text-yellow-400">Related</p>
                  </div>
                  <div className="bg-gray-800 rounded-lg p-3 text-center">
                    <p className="text-xl font-bold text-white">{duplicates?.unique ?? 0}</p>
                    <p className="text-xs text-green-400">Unique</p>
                  </div>
                </div>
                {dupClassData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={160}>
                    <PieChart>
                      <Pie data={dupClassData} cx="50%" cy="50%" outerRadius={65} dataKey="value"
                        label={({ name, percent }) => `${name.replace(/_/g, ' ')} ${(percent * 100).toFixed(0)}%`}
                        labelLine={false}
                      >
                        {dupClassData.map((_, i) => (
                          <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyChart message="No duplicate data yet." />
                )}
              </ChartCard>

              {/* KB Clusters radar / bar */}
              <ChartCard title="Knowledge Base Bug Clusters by Component">
                {kbClusterData.length === 0 ? (
                  <EmptyChart message="Knowledge base is empty. Ingest datasets first." />
                ) : kbClusterData.length >= 3 ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <RadarChart data={kbClusterData}>
                      <PolarGrid stroke="#374151" />
                      <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 10 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 'auto']} tick={{ fill: '#6b7280', fontSize: 9 }} />
                      <Radar name="Total" dataKey="count" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.25} />
                      <Radar name="Critical" dataKey="critical" stroke="#ef4444" fill="#ef4444" fillOpacity={0.2} />
                      <Legend wrapperStyle={{ fontSize: 11, color: '#9ca3af' }} />
                    </RadarChart>
                  </ResponsiveContainer>
                ) : (
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={kbClusterData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 10 }} />
                      <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
                      <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }} />
                      <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>
            </div>
          </div>

          {/* ── Row 6: Similar bug cluster table ───────────────────────────── */}
          {(clusters?.submitted_bug_clusters?.length ?? 0) > 0 && (
            <div>
              <SectionHeader title="Submitted Bug Similarity Clusters" icon={Clock} />
              <div className="space-y-3">
                {(clusters!.submitted_bug_clusters ?? []).map((c, i) => (
                  <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-xs font-mono text-blue-400 bg-blue-900/30 px-2 py-0.5 rounded">
                        {c.submitted_bug_id}
                      </span>
                      <span className="text-sm text-gray-300 font-medium">{c.submitted_bug_title}</span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      {c.similar_kb_bugs.map((s, j) => (
                        <div key={j} className="bg-gray-800 rounded-lg p-3">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-mono text-gray-400">{s.id}</span>
                            <span
                              className={`text-xs font-bold ${
                                s.similarity >= 0.82 ? 'text-red-400' : s.similarity >= 0.55 ? 'text-yellow-400' : 'text-green-400'
                              }`}
                            >
                              {(s.similarity * 100).toFixed(0)}%
                            </span>
                          </div>
                          <p className="text-xs text-gray-400 line-clamp-2">{s.document}</p>
                          {s.component && (
                            <span className="text-xs text-gray-600 mt-1 block">{s.component}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Row 7: Error patterns table ─────────────────────────────────── */}
          {(exceptions?.error_patterns?.length ?? 0) > 0 && (
            <div>
              <SectionHeader title="Common Error Patterns" icon={AlertTriangle} />
              <ChartCard title="Recurring error patterns across all analyzed bugs">
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                  {(exceptions!.error_patterns ?? []).slice(0, 12).map((p, i) => (
                    <div key={i} className="bg-gray-800 rounded-lg p-2.5 flex items-center justify-between">
                      <span className="text-xs text-gray-300 truncate mr-2">{p.pattern}</span>
                      <span className="text-xs font-bold text-blue-400 shrink-0">{p.count}</span>
                    </div>
                  ))}
                </div>
              </ChartCard>
            </div>
          )}

          {/* ── Root cause confidence distribution ───────────────────────────── */}
          {rootCauses && rootCauses.total > 0 && (
            <div>
              <SectionHeader title="Root Cause Analysis Confidence" icon={CheckCircle2} />
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                {Object.entries(rootCauses.confidence_distribution).map(([label, count]) => {
                  const color =
                    label.startsWith('high') ? '#22c55e' :
                    label.startsWith('medium') ? '#3b82f6' :
                    label.startsWith('low') ? '#eab308' : '#ef4444';
                  return (
                    <div key={label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                      <p className="text-2xl font-bold text-white">{count}</p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {label.replace(/_/g, ' ').replace(/\d+/g, m => ` ${m}`).trim()}
                      </p>
                      <div className="h-1 bg-gray-800 rounded-full mt-2">
                        <div
                          className="h-1 rounded-full"
                          style={{
                            width: `${(count / rootCauses.total) * 100}%`,
                            background: color,
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
