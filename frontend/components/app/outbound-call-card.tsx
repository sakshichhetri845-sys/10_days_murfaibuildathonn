'use client';

import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  Clock,
  History,
  Loader2,
  PhoneCall,
  PhoneIncoming,
  Play,
  Shield,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

export type CallState =
  | 'idle'
  | 'scheduled'
  | 'calling'
  | 'ringing'
  | 'connected'
  | 'completed'
  | 'unanswered'
  | 'busy'
  | 'failed'
  | 'cancelled';

interface CallRecord {
  callId: string;
  maskedPhoneNumber: string;
  scheduledTime: string;
  timezone?: string;
  status: CallState;
  createdAt: string;
}

export function OutboundCallCard() {
  const [phoneNumber, setPhoneNumber] = useState('voiceagentagent');

  const [scheduledTime, setScheduledTime] = useState('');
  const [userTimezone, setUserTimezone] = useState('UTC');
  const [callState, setCallState] = useState<CallState>('idle');
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [callHistory, setCallHistory] = useState<CallRecord[]>([]);
  const [loadingAction, setLoadingAction] = useState<'now' | 'schedule' | null>(null);

  useEffect(() => {
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      setUserTimezone(tz || 'UTC');

      // Set default scheduled time to 30 mins from now
      const future = new Date(Date.now() + 30 * 60 * 1000);
      const localIso = new Date(future.getTime() - future.getTimezoneOffset() * 60000)
        .toISOString()
        .slice(0, 16);
      setScheduledTime(localIso);
    } catch {
      setUserTimezone('UTC');
    }

    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await fetch('/api/outbound/history');
      if (res.ok) {
        const data = await res.json();
        if (data.history) {
          setCallHistory(data.history);
        }
      }
    } catch (e) {
      console.warn('Failed to fetch call history', e);
    }
  };

  const maskPhone = (phone: string): string => {
    const p = phone.trim();
    if (!p) return '';
    if (p.startsWith('sip:')) {
      const parts = p.replace('sip:', '').split('@');
      const user = parts[0];
      const domain = parts[1] || '';
      const masked = user.length > 3 ? user.slice(0, 3) + '***' : user + '***';
      return domain ? `sip:${masked}@${domain}` : `sip:${masked}`;
    }
    if (p.startsWith('+') || /^\d+$/.test(p)) {
      if (p.length <= 6) return p;
      return `${p.slice(0, 3)} **** ${p.slice(-4)}`;
    }
    if (p.length <= 3) return `${p}***`;
    return `${p.slice(0, 3)}***`;
  };

  const handleCallMeNow = async () => {
    if (!phoneNumber || phoneNumber.trim().length < 2) {
      setStatusMessage(
        'Please enter a valid phone number or Linphone username (e.g. +15551234567, sakshi, or sip:sakshi@sip.linphone.org)'
      );
      setCallState('failed');
      return;
    }

    setLoadingAction('now');
    setCallState('calling');
    setStatusMessage('Calling HealthSaathi... Connecting your HealthSaathi follow-up call');

    try {
      const res = await fetch('/api/outbound/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phoneNumber: phoneNumber.trim() }),
      });

      const data = await res.json();

      if (res.ok && data.success) {
        setCallState('ringing');
        setStatusMessage('Your phone should ring shortly. Connecting call...');

        // Add to history list
        const newRecord: CallRecord = {
          callId: data.callId || `call_${Date.now()}`,
          maskedPhoneNumber: maskPhone(phoneNumber),
          scheduledTime: new Date().toISOString(),
          timezone: userTimezone,
          status: 'calling',
          createdAt: new Date().toISOString(),
        };
        setCallHistory((prev) => [newRecord, ...prev]);

        // Transition to connected -> completed state
        setTimeout(() => {
          setCallState('connected');
          setStatusMessage('Call Connected — HealthSaathi follow-up in progress');
          setCallHistory((prev) =>
            prev.map((item) =>
              item.callId === newRecord.callId ? { ...item, status: 'connected' } : item
            )
          );
        }, 4000);

        setTimeout(() => {
          setCallState('completed');
          setStatusMessage('Follow-up call completed. Thank you for speaking with HealthSaathi.');
          setCallHistory((prev) =>
            prev.map((item) =>
              item.callId === newRecord.callId ? { ...item, status: 'completed' } : item
            )
          );
        }, 12000);
      } else {
        setCallState('failed');
        setStatusMessage(data.error || 'Unable to connect the follow-up call.');
      }
    } catch (err: unknown) {
      setCallState('failed');
      const errStr = err instanceof Error ? err.message : 'Unable to connect the follow-up call.';
      setStatusMessage(errStr);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleScheduleCall = async () => {
    if (!phoneNumber || phoneNumber.trim().length < 7) {
      setStatusMessage('Please enter a valid phone number (e.g. +15551234567)');
      setCallState('failed');
      return;
    }

    if (!scheduledTime) {
      setStatusMessage('Please select a callback time.');
      setCallState('failed');
      return;
    }

    setLoadingAction('schedule');
    setStatusMessage('Scheduling your HealthSaathi follow-up call...');

    try {
      const res = await fetch('/api/outbound/schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phoneNumber: phoneNumber.trim(),
          scheduledTime,
          timezone: userTimezone,
        }),
      });

      const data = await res.json();

      if (res.ok && data.success) {
        setCallState('scheduled');
        setStatusMessage(
          `Call scheduled for ${new Date(scheduledTime).toLocaleString()} (${userTimezone})`
        );

        const newRecord: CallRecord = {
          callId: data.callId || `sched_${Date.now()}`,
          maskedPhoneNumber: maskPhone(phoneNumber),
          scheduledTime: new Date(scheduledTime).toISOString(),
          timezone: userTimezone,
          status: 'scheduled',
          createdAt: new Date().toISOString(),
        };
        setCallHistory((prev) => [newRecord, ...prev]);
      } else {
        setCallState('failed');
        setStatusMessage(data.error || 'Failed to schedule call.');
      }
    } catch (err: unknown) {
      setCallState('failed');
      const msg = err instanceof Error ? err.message : 'Scheduling failed due to a network error.';
      setStatusMessage(msg);
    } finally {
      setLoadingAction(null);
    }
  };

  const getStatusBadge = (status: CallState) => {
    switch (status) {
      case 'calling':
      case 'ringing':
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
            <PhoneIncoming className="size-3.5 animate-bounce text-amber-600" />
            Ringing / Calling
          </span>
        );

      case 'connected':
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
            <PhoneCall className="size-3.5 animate-pulse text-emerald-600" />
            Connected
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-teal-100 px-3 py-1 text-xs font-semibold text-teal-800">
            <CheckCircle2 className="size-3.5 text-teal-600" />
            Completed
          </span>
        );
      case 'scheduled':
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-sky-100 px-3 py-1 text-xs font-semibold text-sky-800">
            <Calendar className="size-3.5 text-sky-600" />
            Scheduled
          </span>
        );
      case 'failed':
      case 'unanswered':
      case 'busy':
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold text-rose-800">
            <AlertCircle className="size-3.5 text-rose-600" />
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
            Idle
          </span>
        );
    }
  };

  return (
    <div className="mx-auto w-full max-w-4xl rounded-3xl border border-teal-100/80 bg-white/90 p-6 shadow-xl backdrop-blur-md sm:p-8">
      {/* Header */}
      <div className="flex flex-col gap-2 border-b border-teal-100/70 pb-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex size-11 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-600 to-sky-600 text-white shadow-md shadow-teal-600/20">
            <PhoneCall className="size-6" />
          </div>
          <div>
            <div className="mb-1 inline-flex items-center gap-1.5 rounded-full border border-teal-200 bg-teal-50 px-3 py-0.5 text-[11px] font-bold tracking-wider text-teal-800 uppercase">
              <span>Day 6 Outbound Telephony</span>
            </div>
            <h2 className="text-xl font-extrabold tracking-tight text-slate-900 sm:text-2xl">
              Request a Health Follow-up Call
            </h2>
            <p className="text-xs font-medium text-slate-500 sm:text-sm">
              Schedule a callback or trigger an immediate outbound call to Linphone or any phone
              number
            </p>
          </div>
        </div>
        <div>{getStatusBadge(callState)}</div>
      </div>

      {/* Form Fields */}
      <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Phone / Linphone Username Input */}
        <div className="space-y-2">
          <label className="text-xs font-bold tracking-wider text-slate-700 uppercase">
            Phone Number or Linphone SIP Username
          </label>
          <div className="relative">
            <input
              type="text"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="+15551234567, sakshi, or sip:sakshi@sip.linphone.org"
              className="w-full rounded-2xl border border-slate-200 bg-slate-50/70 px-4 py-3.5 text-sm font-medium text-slate-900 placeholder:text-slate-400 focus:border-teal-500 focus:bg-white focus:ring-2 focus:ring-teal-500/20 focus:outline-none"
            />
          </div>
          <p className="flex items-center gap-1 text-[11px] text-slate-500">
            <Shield className="size-3 text-teal-600" /> Phone number or Linphone username is stored
            securely and masked in history.
          </p>
        </div>

        {/* Scheduled Time Input */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold tracking-wider text-slate-700 uppercase">
              Preferred Callback Time
            </label>
            <span className="text-[11px] font-semibold text-teal-700">
              Timezone: {userTimezone}
            </span>
          </div>
          <input
            type="datetime-local"
            value={scheduledTime}
            onChange={(e) => setScheduledTime(e.target.value)}
            className="w-full rounded-2xl border border-slate-200 bg-slate-50/70 px-4 py-3.5 text-sm font-medium text-slate-900 focus:border-teal-500 focus:bg-white focus:ring-2 focus:ring-teal-500/20 focus:outline-none"
          />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-end">
        <Button
          onClick={handleScheduleCall}
          disabled={loadingAction !== null}
          variant="outline"
          className="flex items-center justify-center gap-2 rounded-2xl border-teal-200 bg-teal-50/60 px-6 py-3 text-sm font-bold text-teal-800 transition-all hover:bg-teal-100 hover:text-teal-900"
        >
          {loadingAction === 'schedule' ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Calendar className="size-4" />
          )}
          <span>Schedule a Call</span>
        </Button>

        <Button
          onClick={handleCallMeNow}
          disabled={loadingAction !== null}
          className="flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-teal-700 to-sky-700 px-7 py-3 text-sm font-bold text-white shadow-md shadow-teal-700/20 transition-all hover:scale-[1.01] hover:from-teal-800 hover:to-sky-800"
        >
          {loadingAction === 'now' ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Play className="size-4 fill-white" />
          )}
          <span>Call Me Now (Demo)</span>
        </Button>
      </div>

      {/* Live Status Message Banner */}
      {statusMessage && (
        <div
          className={`mt-6 flex items-center gap-3 rounded-2xl p-4 text-xs font-semibold sm:text-sm ${
            callState === 'failed'
              ? 'border border-rose-200 bg-rose-50 text-rose-800'
              : callState === 'calling' || callState === 'ringing'
                ? 'border border-amber-200 bg-amber-50 text-amber-900'
                : callState === 'connected'
                  ? 'border border-emerald-200 bg-emerald-50 text-emerald-900'
                  : 'border border-teal-200 bg-teal-50 text-teal-900'
          }`}
        >
          {callState === 'failed' ? (
            <AlertCircle className="size-5 shrink-0 text-rose-600" />
          ) : (
            <CheckCircle2 className="size-5 shrink-0 text-teal-600" />
          )}
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Call History Table */}
      <div className="mt-8 border-t border-teal-100/80 pt-6">
        <div className="flex items-center justify-between pb-4">
          <div className="flex items-center gap-2 text-sm font-bold tracking-tight text-slate-900">
            <History className="size-4 text-teal-700" />
            <span>Call History</span>
          </div>
          <span className="text-xs text-slate-500">{callHistory.length} total call records</span>
        </div>

        {callHistory.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-200 p-6 text-center text-xs font-medium text-slate-500">
            No outbound calls requested yet. Enter your phone number above to test &quot;Call Me
            Now&quot;.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-[11px] font-bold text-slate-400 uppercase">
                  <th className="px-3 py-2.5">Date / Time</th>
                  <th className="px-3 py-2.5">Phone Number (Masked)</th>
                  <th className="px-3 py-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                {callHistory.map((item) => (
                  <tr key={item.callId} className="transition-colors hover:bg-slate-50/60">
                    <td className="px-3 py-3">
                      <div className="flex items-center gap-1.5">
                        <Clock className="size-3.5 text-slate-400" />
                        <span>
                          {new Date(item.scheduledTime || item.createdAt).toLocaleString()}
                        </span>
                      </div>
                    </td>
                    <td className="px-3 py-3 font-mono text-slate-800">{item.maskedPhoneNumber}</td>
                    <td className="px-3 py-3">{getStatusBadge(item.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
