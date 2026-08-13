'use client';

import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock,
  Globe,
  HeartHandshake,
  HelpCircle,
  MapPin,
  PhoneCall,
  RefreshCw,
  ShieldAlert,
  Stethoscope,
  TrendingUp,
  X,
  XCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface CallRecord {
  id: string;
  sessionId: string;
  timestamp: string;
  duration: number;
  channel: string;
  outcome: string;
  outcomeType: string;
}

export interface AnalyticsData {
  totalCalls: number;
  successfulCalls: number;
  failedCalls: number;
  successRate: number;
  outcomeBreakdown: {
    GENERAL_GUIDANCE: number;
    TRIAGE_COMPLETED: number;
    FACILITY_FOUND: number;
    HUMAN_ESCALATION: number;
    INCOMPLETE: number;
    TECHNICAL_ERROR: number;
  };
  recentCalls: CallRecord[];
}

interface AnalyticsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AnalyticsDrawer({ isOpen, onClose }: AnalyticsDrawerProps) {
  const [range, setRange] = useState<'today' | '7days' | 'all'>('all');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<AnalyticsData>({
    totalCalls: 0,
    successfulCalls: 0,
    failedCalls: 0,
    successRate: 0,
    outcomeBreakdown: {
      GENERAL_GUIDANCE: 0,
      TRIAGE_COMPLETED: 0,
      FACILITY_FOUND: 0,
      HUMAN_ESCALATION: 0,
      INCOMPLETE: 0,
      TECHNICAL_ERROR: 0,
    },
    recentCalls: [],
  });

  const fetchAnalytics = async (filterRange: string) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/analytics?range=${filterRange}`);
      const json = await res.json();
      if (json.success && json.analytics) {
        setData(json.analytics);
      }
    } catch (err) {
      console.warn('Failed to load analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchAnalytics(range);
      const timer = setTimeout(() => {
        fetchAnalytics(range);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [isOpen, range]);

  if (!isOpen) return null;

  const formatTimestamp = (ts: string) => {
    try {
      const date = new Date(ts);
      if (isNaN(date.getTime())) return ts;
      return (
        date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true }) +
        ' · ' +
        date.toLocaleDateString([], { month: 'short', day: 'numeric' })
      );
    } catch {
      return ts;
    }
  };

  const formatDuration = (secs: number) => {
    if (!secs || secs <= 0) return '0s';
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  };

  const outcomeTypeLabels: Record<string, { label: string; icon: React.ReactNode; color: string }> =
    {
      GENERAL_GUIDANCE: {
        label: 'General Guidance',
        icon: <HelpCircle className="size-4 text-sky-600" />,
        color: 'bg-sky-50 text-sky-700 border-sky-200',
      },
      TRIAGE_COMPLETED: {
        label: 'Triage Completed',
        icon: <Stethoscope className="size-4 text-teal-600" />,
        color: 'bg-teal-50 text-teal-700 border-teal-200',
      },
      FACILITY_FOUND: {
        label: 'Facility Found',
        icon: <MapPin className="size-4 text-indigo-600" />,
        color: 'bg-indigo-50 text-indigo-700 border-indigo-200',
      },
      HUMAN_ESCALATION: {
        label: 'Human Escalation',
        icon: <HeartHandshake className="size-4 text-emerald-600" />,
        color: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      },
      INCOMPLETE: {
        label: 'Incomplete',
        icon: <AlertTriangle className="size-4 text-amber-600" />,
        color: 'bg-amber-50 text-amber-700 border-amber-200',
      },
      TECHNICAL_ERROR: {
        label: 'Technical Error',
        icon: <ShieldAlert className="size-4 text-rose-600" />,
        color: 'bg-rose-50 text-rose-700 border-rose-200',
      },
    };

  const totalBreakdownCount = Object.values(data.outcomeBreakdown).reduce((a, b) => a + b, 0);

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-sm transition-opacity">
      <div className="flex h-full w-full max-w-2xl flex-col bg-[#F8FAFC] shadow-2xl">
        {/* Header */}
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-5">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-teal-700 text-white shadow-sm">
              <BarChart3 className="size-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold tracking-tight text-slate-900">HEALTHSATHI</h2>
              <p className="text-xs font-semibold tracking-wider text-teal-700 uppercase">
                Health Access Call Analytics
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => fetchAnalytics(range)}
              className="rounded-lg text-slate-500 hover:bg-slate-100"
              title="Refresh Analytics"
            >
              <RefreshCw className={`size-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="rounded-lg text-slate-500 hover:bg-slate-100"
            >
              <X className="size-5" />
            </Button>
          </div>
        </header>

        {/* Content Body */}
        <div className="flex-1 space-y-6 overflow-y-auto p-6">
          {/* Time Range Filter Bar */}
          <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-2 shadow-sm">
            <span className="pl-3 text-xs font-bold tracking-wider text-slate-600 uppercase">
              Filter Period:
            </span>
            <div className="flex gap-1">
              {(['today', '7days', 'all'] as const).map((r) => (
                <button
                  key={r}
                  onClick={() => setRange(r)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-all ${
                    range === r
                      ? 'bg-teal-700 text-white shadow-sm'
                      : 'bg-transparent text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  {r === 'today' ? 'Today' : r === '7days' ? 'Last 7 Days' : 'All Time'}
                </button>
              ))}
            </div>
          </div>

          {/* Top Primary Metrics Cards */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {/* Total Calls */}
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="mb-2 flex items-center justify-between text-slate-500">
                <span className="text-xs font-bold tracking-wider uppercase">Total Calls</span>
                <PhoneCall className="size-4 text-slate-400" />
              </div>
              <div className="text-2xl font-black text-slate-900">{data.totalCalls}</div>
              <p className="mt-1 text-[11px] text-slate-500">Logged sessions</p>
            </div>

            {/* Successful */}
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4 shadow-sm">
              <div className="mb-2 flex items-center justify-between text-emerald-700">
                <span className="text-xs font-bold tracking-wider uppercase">Successful</span>
                <CheckCircle2 className="size-4 text-emerald-600" />
              </div>
              <div className="text-2xl font-black text-emerald-900">{data.successfulCalls}</div>
              <p className="mt-1 text-[11px] text-emerald-600">Safe outcomes reached</p>
            </div>

            {/* Failed */}
            <div className="rounded-xl border border-rose-200 bg-rose-50/50 p-4 shadow-sm">
              <div className="mb-2 flex items-center justify-between text-rose-700">
                <span className="text-xs font-bold tracking-wider uppercase">Failed</span>
                <XCircle className="size-4 text-rose-600" />
              </div>
              <div className="text-2xl font-black text-rose-900">{data.failedCalls}</div>
              <p className="mt-1 text-[11px] text-rose-600">Incomplete / errors</p>
            </div>

            {/* Success Rate */}
            <div className="rounded-xl border border-teal-200 bg-teal-50/50 p-4 shadow-sm">
              <div className="mb-2 flex items-center justify-between text-teal-700">
                <span className="text-xs font-bold tracking-wider uppercase">Success Rate</span>
                <TrendingUp className="size-4 text-teal-600" />
              </div>
              <div className="text-2xl font-black text-teal-900">{data.successRate}%</div>
              <p className="mt-1 text-[11px] text-teal-600">Resolution efficiency</p>
            </div>
          </div>

          {/* HealthSathi Call Outcome Breakdown Section */}
          <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Activity className="size-4 text-teal-700" />
                <h3 className="text-sm font-bold tracking-wider text-slate-900 uppercase">
                  Call Outcomes Breakdown
                </h3>
              </div>
              <span className="text-xs font-medium text-slate-500">
                {totalBreakdownCount} total records
              </span>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {Object.entries(data.outcomeBreakdown).map(([key, count]) => {
                const info = outcomeTypeLabels[key] || {
                  label: key,
                  icon: <Activity className="size-4 text-slate-500" />,
                  color: 'bg-slate-50 text-slate-700 border-slate-200',
                };
                const percentage =
                  totalBreakdownCount > 0 ? Math.round((count / totalBreakdownCount) * 100) : 0;

                return (
                  <div
                    key={key}
                    className="flex flex-col justify-between rounded-lg border border-slate-100 bg-slate-50/60 p-3.5"
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {info.icon}
                        <span className="text-xs font-semibold text-slate-800">{info.label}</span>
                      </div>
                      <span className="rounded border border-slate-200 bg-white px-2 py-0.5 text-xs font-bold text-slate-900 shadow-2xs">
                        {count}
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
                      <div
                        className={`h-full transition-all ${
                          key === 'HUMAN_ESCALATION'
                            ? 'bg-emerald-600'
                            : key === 'FACILITY_FOUND'
                              ? 'bg-indigo-600'
                              : key === 'TRIAGE_COMPLETED'
                                ? 'bg-teal-600'
                                : key === 'GENERAL_GUIDANCE'
                                  ? 'bg-sky-600'
                                  : key === 'INCOMPLETE'
                                    ? 'bg-amber-500'
                                    : 'bg-rose-500'
                        }`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Recent Calls Section */}
          <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Clock className="size-4 text-teal-700" />
                <h3 className="text-sm font-bold tracking-wider text-slate-900 uppercase">
                  Recent Calls
                </h3>
              </div>
              <span className="text-xs text-slate-500">Privacy Safe • No Medical PII</span>
            </div>

            {data.recentCalls.length === 0 ? (
              <div className="py-8 text-center text-xs font-medium text-slate-500">
                No recent HealthSathi call records found.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-700">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50/70 text-[11px] font-bold tracking-wider text-slate-500 uppercase">
                      <th className="px-3 py-2.5">Time</th>
                      <th className="px-3 py-2.5">Channel</th>
                      <th className="px-3 py-2.5">Outcome</th>
                      <th className="px-3 py-2.5">Outcome Type</th>
                      <th className="px-3 py-2.5 text-right">Duration</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {data.recentCalls.map((call) => {
                      const info = outcomeTypeLabels[call.outcomeType] || {
                        label: call.outcomeType,
                        color: 'bg-slate-50 text-slate-700 border-slate-200',
                      };
                      const isSuccess = call.outcome.toLowerCase() === 'successful';

                      return (
                        <tr key={call.id} className="transition-colors hover:bg-slate-50/80">
                          <td className="px-3 py-3 font-semibold whitespace-nowrap text-slate-800">
                            {formatTimestamp(call.timestamp)}
                          </td>
                          <td className="px-3 py-3 whitespace-nowrap">
                            <span className="inline-flex items-center gap-1 rounded border border-slate-200 bg-slate-100 px-2 py-0.5 text-[11px] font-bold text-slate-700">
                              {call.channel === 'SIP' ? (
                                <PhoneCall className="size-3 text-teal-700" />
                              ) : (
                                <Globe className="size-3 text-sky-700" />
                              )}
                              {call.channel === 'SIP' ? 'SIP' : 'Browser'}
                            </span>
                          </td>
                          <td className="px-3 py-3 whitespace-nowrap">
                            <span
                              className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-bold ${
                                isSuccess
                                  ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                                  : 'border-rose-200 bg-rose-50 text-rose-700'
                              }`}
                            >
                              {isSuccess ? (
                                <CheckCircle2 className="size-3 text-emerald-600" />
                              ) : (
                                <XCircle className="size-3 text-rose-600" />
                              )}
                              {isSuccess ? 'Successful' : 'Failed'}
                            </span>
                          </td>
                          <td className="px-3 py-3 whitespace-nowrap">
                            <span
                              className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-semibold ${info.color}`}
                            >
                              {info.label}
                            </span>
                          </td>
                          <td className="px-3 py-3 text-right font-mono font-medium whitespace-nowrap text-slate-600">
                            {formatDuration(call.duration)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <footer className="flex items-center justify-between border-t border-slate-200 bg-white px-6 py-4 text-xs text-slate-500">
          <span>HealthSathi Voice AI Service Monitoring</span>
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
            className="rounded-lg border-slate-200 font-semibold hover:bg-slate-50"
          >
            Close Dashboard
          </Button>
        </footer>
      </div>
    </div>
  );
}
