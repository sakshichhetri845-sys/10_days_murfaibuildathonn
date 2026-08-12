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
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'medium':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      default:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'RESOLVED':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'IN_PROGRESS':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      default:
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
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
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, x: 400 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 400 }}
            transition={{ type: 'spring', damping: 25, stiffness: 250 }}
            className="fixed top-0 right-0 bottom-0 z-50 flex w-full max-w-md flex-col border-l border-neutral-800 bg-neutral-900 shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-neutral-800 bg-neutral-900/80 p-5 backdrop-blur">
              <div className="flex items-center gap-3">
                <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-2 text-amber-400">
                  <LifeBuoy className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-neutral-100">Human Help Requests</h3>
                  <p className="text-xs text-neutral-400">Day 7 Escalation Tickets & Desk</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={fetchTickets}
                  disabled={loading}
                  className="text-neutral-400 hover:text-neutral-200"
                >
                  <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onClose}
                  className="text-neutral-400 hover:text-neutral-200"
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>
            </div>

            {/* Content List */}
            <div className="flex-1 space-y-4 overflow-y-auto p-5">
              {tickets.length === 0 ? (
                <div className="flex flex-col items-center justify-center space-y-3 py-12 text-center text-neutral-500">
                  <UserCheck className="h-12 w-12 stroke-[1.5] text-neutral-600" />
                  <p className="text-sm font-medium">No open escalation tickets</p>
                  <p className="max-w-xs text-xs text-neutral-600">
                    When a learner needs human help or requests a human teacher, escalated tickets
                    will appear here.
                  </p>
                </div>
              ) : (
                tickets.map((t) => (
                  <div
                    key={t.reference_id}
                    className="space-y-3 rounded-xl border border-neutral-800 bg-neutral-950/80 p-4 transition-colors hover:border-neutral-700"
                  >
                    <div className="flex items-center justify-between">
                      <span className="rounded border border-neutral-700 bg-neutral-800 px-2 py-0.5 font-mono text-xs font-bold text-amber-400">
                        {t.reference_id}
                      </span>
                      <div className="flex items-center gap-2">
                        <span
                          className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${getUrgencyBadge(t.urgency)}`}
                        >
                          {t.urgency.toUpperCase()}
                        </span>
                        <span
                          className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${getStatusBadge(t.status)}`}
                        >
                          {t.status}
                        </span>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-semibold text-neutral-200">{t.who_needs_help}</h4>
                      <p className="mt-1 text-xs leading-relaxed text-neutral-400">
                        {t.issue_summary}
                      </p>
                    </div>

                    {t.checked_by_agent && (
                      <div className="rounded border border-neutral-800 bg-neutral-900/60 p-2 text-[11px] text-neutral-400">
                        <span className="font-medium text-neutral-500">Checked by agent:</span>{' '}
                        {t.checked_by_agent}
                      </div>
                    )}

                    <div className="flex items-center justify-between border-t border-neutral-800/60 pt-2 text-[11px] text-neutral-500">
                      <span>
                        Lang: <strong className="text-neutral-300">{t.preferred_language}</strong>
                      </span>
                      <span>
                        Contact: <strong className="text-neutral-300">{t.preferred_contact}</strong>
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
                          className="h-7 border-emerald-500/30 text-xs text-emerald-400 hover:bg-emerald-500/10"
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
                          className="h-7 border-purple-500/30 text-xs text-purple-400 hover:bg-purple-500/10"
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
