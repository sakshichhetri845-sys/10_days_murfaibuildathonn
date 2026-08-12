'use client';

import React, { useEffect, useState } from 'react';
import { CheckCircle, Clock, LifeBuoy, RefreshCw, UserCheck, X } from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';
import { Button } from '@/components/ui/button';

export interface EscalationTicket {
  reference_id: string;
  user_id: string;
  who_needs_help: string;
  reason_type: string;
  issue_summary: string;
  checked_by_agent?: string;
  urgency: string;
  preferred_language: string;
  preferred_contact: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface EscalationsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export function EscalationsDrawer({ isOpen, onClose }: EscalationsDrawerProps) {
  const [tickets, setTickets] = useState<EscalationTicket[]>([]);
  const [loading, setLoading] = useState(false);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/escalations');
      const data = await res.json();
      if (data.success && Array.isArray(data.escalations)) {
        setTickets(data.escalations);
      }
    } catch (e) {
      console.warn('Failed to fetch escalations:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchTickets();
    }
  }, [isOpen]);

  const handleUpdateStatus = async (referenceId: string, newStatus: string) => {
    try {
      setUpdatingId(referenceId);
      const res = await fetch('/api/escalations', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ referenceId, status: newStatus }),
      });
      const data = await res.json();
      if (data.success) {
        setTickets((prev) =>
          prev.map((t) => (t.reference_id === referenceId ? { ...t, status: newStatus } : t))
        );
      }
    } catch (e) {
      console.error('Failed to update status:', e);
    } finally {
      setUpdatingId(null);
    }
  };

  const getUrgencyBadge = (urgency: string) => {
    switch (urgency.toLowerCase()) {
      case 'emergency':
      case 'high':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'medium':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      default:
        return 'bg-teal-50 text-teal-700 border-teal-200';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'RESOLVED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'IN_PROGRESS':
        return 'bg-sky-50 text-sky-700 border-sky-200';
      default:
        return 'bg-amber-50 text-amber-700 border-amber-200';
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, x: 400 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 400 }}
            transition={{ type: 'spring', damping: 25, stiffness: 250 }}
            className="fixed top-0 right-0 bottom-0 z-50 flex w-full max-w-md flex-col border-l border-teal-100 bg-white shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-teal-100 bg-slate-50/90 p-5 backdrop-blur">
              <div className="flex items-center gap-3">
                <div className="rounded-xl border border-teal-200 bg-teal-50 p-2 text-teal-700">
                  <LifeBuoy className="h-5 w-5 text-teal-700" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">Support Requests</h3>
                  <p className="text-xs text-slate-500">Human Health Coordinator Desk</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={fetchTickets}
                  disabled={loading}
                  className="text-slate-500 hover:bg-slate-100 hover:text-slate-800"
                >
                  <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onClose}
                  className="text-slate-500 hover:bg-slate-100 hover:text-slate-800"
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>
            </div>

            {/* Content List */}
            <div className="flex-1 space-y-4 overflow-y-auto bg-[#F8FAFC] p-5">
              {tickets.length === 0 ? (
                <div className="flex flex-col items-center justify-center space-y-3 py-16 text-center text-slate-400">
                  <UserCheck className="h-12 w-12 stroke-[1.5] text-slate-400" />
                  <p className="text-sm font-semibold text-slate-700">No open support requests</p>
                  <p className="max-w-xs text-xs text-slate-500">
                    When a user requests human health support or care coordination, escalated
                    tickets will appear here.
                  </p>
                </div>
              ) : (
                tickets.map((t) => (
                  <div
                    key={t.reference_id}
                    className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition-all hover:border-teal-300"
                  >
                    <div className="flex items-center justify-between">
                      <span className="rounded border border-teal-200 bg-teal-50 px-2.5 py-1 font-mono text-xs font-bold text-teal-800">
                        {t.reference_id}
                      </span>
                      <div className="flex items-center gap-2">
                        <span
                          className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${getUrgencyBadge(t.urgency)}`}
                        >
                          {t.urgency.toUpperCase()}
                        </span>
                        <span
                          className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${getStatusBadge(t.status)}`}
                        >
                          {t.status}
                        </span>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-bold text-slate-900">{t.who_needs_help}</h4>
                      <p className="mt-1 text-xs leading-relaxed text-slate-600">
                        {t.issue_summary}
                      </p>
                    </div>

                    {t.checked_by_agent && (
                      <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-[11px] text-slate-600">
                        <span className="font-semibold text-slate-700">Checked by agent:</span>{' '}
                        {t.checked_by_agent}
                      </div>
                    )}

                    <div className="flex items-center justify-between border-t border-slate-100 pt-2 text-[11px] text-slate-500">
                      <span>
                        Lang: <strong className="text-slate-700">{t.preferred_language}</strong>
                      </span>
                      <span>
                        Contact: <strong className="text-slate-700">{t.preferred_contact}</strong>
                      </span>
                      <span>
                        {new Date(t.created_at).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>

                    {/* Status actions */}
                    <div className="flex items-center justify-end gap-2 pt-1">
                      {t.status !== 'RESOLVED' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleUpdateStatus(t.reference_id, 'RESOLVED')}
                          disabled={updatingId === t.reference_id}
                          className="h-7 border-emerald-300 bg-emerald-50 text-xs font-bold text-emerald-700 hover:bg-emerald-100"
                        >
                          <CheckCircle className="mr-1 h-3.5 w-3.5" /> Mark Resolved
                        </Button>
                      )}
                      {t.status === 'OPEN' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleUpdateStatus(t.reference_id, 'IN_PROGRESS')}
                          disabled={updatingId === t.reference_id}
                          className="h-7 border-sky-300 bg-sky-50 text-xs font-bold text-sky-700 hover:bg-sky-100"
                        >
                          <Clock className="mr-1 h-3.5 w-3.5" /> In Progress
                        </Button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
