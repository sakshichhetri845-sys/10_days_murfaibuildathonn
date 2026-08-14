'use client';

import React, { useState } from 'react';
import { Calendar, Clock, Phone, PhoneCall, X } from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/shadcn/utils';
import { getPersistentUserId } from '@/lib/utils';

interface HealthRemindersSectionProps {
  isOpen: boolean;
  onClose: () => void;
}

export type CallState = 'Ready' | 'Calling' | 'Ringing' | 'Connected' | 'Call Ended' | 'Failed';

export function HealthRemindersSection({ isOpen, onClose }: HealthRemindersSectionProps) {
  const [activeTab, setActiveTab] = useState<'call_now' | 'schedule'>('call_now');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [userName, setUserName] = useState('');

  // Immediate call state
  const [callState, setCallState] = useState<CallState>('Ready');
  const [callErrorMessage, setCallErrorMessage] = useState('');

  // Schedule call state
  const [scheduleDate, setScheduleDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [scheduleTime, setScheduleTime] = useState('08:00');
  const [scheduleTopic, setScheduleTopic] = useState('Daily Health Reminder');
  const [scheduleStatus, setScheduleStatus] = useState<'idle' | 'loading' | 'success' | 'error'>(
    'idle'
  );
  const [scheduleMessage, setScheduleMessage] = useState('');

  // Handle Immediate Call
  const handleCallMeNow = async () => {
    if (callState === 'Calling' || callState === 'Ringing' || callState === 'Connected') {
      return; // Prevent duplicate clicks while call is active
    }
    if (!phoneNumber.trim()) {
      setCallErrorMessage('Please enter a valid phone number or SIP address.');
      setCallState('Failed');
      return;
    }

    setCallErrorMessage('');
    setCallState('Calling');

    // Simulated progress transitions for realistic UX while worker dials
    const ringingTimer = setTimeout(() => {
      setCallState('Ringing');
    }, 1500);

    const connectedTimer = setTimeout(() => {
      setCallState('Connected');
    }, 4000);

    const userId = getPersistentUserId();

    try {
      const res = await fetch('/api/outbound/practice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId,
          phoneNumber: phoneNumber.trim(),
          name: userName.trim(),
          action: 'immediate',
        }),
      });

      const data = await res.json();
      if (!data.success && !data.call_id) {
        clearTimeout(ringingTimer);
        clearTimeout(connectedTimer);
        setCallState('Failed');
        setCallErrorMessage('Unable to connect the call. Please try again.');
      }
    } catch {
      clearTimeout(ringingTimer);
      clearTimeout(connectedTimer);
      setCallState('Failed');
      setCallErrorMessage('Unable to connect the call. Please try again.');
    }
  };

  // Handle Schedule Call
  const handleScheduleCall = async () => {
    if (!phoneNumber.trim()) {
      setScheduleMessage('Please enter your phone number.');
      setScheduleStatus('error');
      return;
    }

    setScheduleStatus('loading');
    const userId = getPersistentUserId();

    try {
      const res = await fetch('/api/schedule-reminder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId,
          phoneNumber: phoneNumber.trim(),
          scheduledTime: scheduleTime,
          topic: scheduleTopic,
          date: scheduleDate,
        }),
      });

      const data = await res.json();
      if (data.success) {
        setScheduleStatus('success');
        const formattedDisplayTime = `${scheduleDate} at ${scheduleTime}`;
        setScheduleMessage(`Your HealthSathi call is scheduled for ${formattedDisplayTime}.`);
      } else {
        throw new Error(data.error ?? 'Scheduling failed');
      }
    } catch {
      setScheduleStatus('error');
      setScheduleMessage('Unable to schedule call. Please try again.');
    }
  };

  const isCallActive =
    callState === 'Calling' || callState === 'Ringing' || callState === 'Connected';

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            key="drawer"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="fixed top-0 right-0 z-50 flex h-full w-full max-w-md flex-col bg-white shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-teal-100 bg-teal-50 p-5">
              <div className="flex items-center gap-3">
                <div className="flex size-9 items-center justify-center rounded-xl bg-teal-500/10">
                  <PhoneCall className="size-5 text-teal-600" />
                </div>
                <div>
                  <p className="text-base font-extrabold text-slate-900">
                    HealthSathi Call Controls
                  </p>
                  <p className="text-xs text-teal-700">Call Me Now or Schedule a Follow-up Call</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="rounded-full hover:bg-teal-100"
              >
                <X className="size-4 text-slate-500" />
              </Button>
            </div>

            {/* Action Tabs */}
            <div className="flex border-b border-slate-100 bg-slate-50 p-2">
              <button
                onClick={() => setActiveTab('call_now')}
                className={cn(
                  'flex-1 rounded-lg py-2 text-xs font-bold transition-all',
                  activeTab === 'call_now'
                    ? 'bg-white text-teal-700 shadow-sm'
                    : 'text-slate-500 hover:text-slate-800'
                )}
              >
                📞 Call Me Now
              </button>
              <button
                onClick={() => setActiveTab('schedule')}
                className={cn(
                  'flex-1 rounded-lg py-2 text-xs font-bold transition-all',
                  activeTab === 'schedule'
                    ? 'bg-white text-teal-700 shadow-sm'
                    : 'text-slate-500 hover:text-slate-800'
                )}
              >
                🗓 Schedule a Call
              </button>
            </div>

            <div className="flex flex-1 flex-col gap-5 overflow-y-auto p-5">
              {/* Phone Input (Common) */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold tracking-wider text-slate-400 uppercase">
                  Your Phone / SIP Number
                </label>
                <input
                  type="tel"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  disabled={isCallActive}
                  placeholder="+977 9876543210 or linphone_user"
                  className="rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-800 transition-all outline-none focus:border-teal-400 focus:ring-2 focus:ring-teal-200 disabled:bg-slate-100"
                />
              </div>

              {/* TAB 1: CALL ME NOW */}
              {activeTab === 'call_now' && (
                <div className="flex flex-col gap-4">
                  <div className="flex flex-col gap-2">
                    <label className="text-xs font-bold tracking-wider text-slate-400 uppercase">
                      Your Name (Optional)
                    </label>
                    <input
                      type="text"
                      value={userName}
                      onChange={(e) => setUserName(e.target.value)}
                      disabled={isCallActive}
                      placeholder="e.g. Ramesh"
                      className="rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-800 transition-all outline-none focus:border-teal-400 focus:ring-2 focus:ring-teal-200 disabled:bg-slate-100"
                    />
                  </div>

                  {/* Call State Display */}
                  <div className="rounded-xl border border-slate-100 bg-slate-50 p-4 text-center">
                    <p className="text-xs font-bold tracking-wider text-slate-400 uppercase">
                      Call Status
                    </p>
                    <p className="mt-1 text-lg font-extrabold text-teal-700">
                      {callState === 'Calling' && 'Calling HealthSathi…'}
                      {callState === 'Ringing' && 'Ringing…'}
                      {callState === 'Connected' && 'Connected 🟢'}
                      {callState === 'Call Ended' && 'Call Ended'}
                      {callState === 'Failed' && 'Call Failed 🔴'}
                      {callState === 'Ready' && 'Ready'}
                    </p>
                    {callErrorMessage && (
                      <p className="mt-2 text-xs font-medium text-rose-600">{callErrorMessage}</p>
                    )}
                  </div>

                  {/* Call Me Now Button */}
                  <Button
                    onClick={handleCallMeNow}
                    disabled={isCallActive}
                    className={cn(
                      'w-full rounded-xl py-4 font-bold text-white shadow-md transition-all',
                      isCallActive
                        ? 'cursor-not-allowed bg-slate-400'
                        : 'bg-teal-600 hover:bg-teal-700'
                    )}
                  >
                    <Phone className="mr-2 size-4" />
                    {isCallActive ? `State: ${callState}` : '📞 Call Me Now'}
                  </Button>

                  {callState === 'Connected' && (
                    <Button
                      variant="outline"
                      onClick={() => setCallState('Call Ended')}
                      className="w-full rounded-xl border-rose-200 text-rose-600 hover:bg-rose-50"
                    >
                      Hang Up Call
                    </Button>
                  )}
                </div>
              )}

              {/* TAB 2: SCHEDULE A CALL */}
              {activeTab === 'schedule' && (
                <div className="flex flex-col gap-4">
                  <div className="flex flex-col gap-2">
                    <label className="text-xs font-bold tracking-wider text-slate-400 uppercase">
                      Date
                    </label>
                    <div className="flex items-center rounded-xl border border-slate-200 px-3 py-2">
                      <Calendar className="mr-2 size-4 text-slate-400" />
                      <input
                        type="date"
                        value={scheduleDate}
                        onChange={(e) => setScheduleDate(e.target.value)}
                        className="w-full bg-transparent text-sm text-slate-800 outline-none"
                      />
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    <label className="text-xs font-bold tracking-wider text-slate-400 uppercase">
                      Time
                    </label>
                    <div className="flex items-center rounded-xl border border-slate-200 px-3 py-2">
                      <Clock className="mr-2 size-4 text-slate-400" />
                      <input
                        type="time"
                        value={scheduleTime}
                        onChange={(e) => setScheduleTime(e.target.value)}
                        className="w-full bg-transparent text-sm text-slate-800 outline-none"
                      />
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    <label className="text-xs font-bold tracking-wider text-slate-400 uppercase">
                      Reminder Topic
                    </label>
                    <input
                      type="text"
                      value={scheduleTopic}
                      onChange={(e) => setScheduleTopic(e.target.value)}
                      placeholder="e.g. Daily Medication Check-in"
                      className="rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-800 transition-all outline-none focus:border-teal-400 focus:ring-2 focus:ring-teal-200"
                    />
                  </div>

                  {/* Status Message */}
                  {scheduleMessage && (
                    <motion.div
                      initial={{ opacity: 0, y: 4 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={cn(
                        'rounded-xl p-4 text-sm font-medium',
                        scheduleStatus === 'success'
                          ? 'border border-emerald-200 bg-emerald-50 text-emerald-800'
                          : scheduleStatus === 'error'
                            ? 'border border-rose-200 bg-rose-50 text-rose-800'
                            : 'border border-amber-200 bg-amber-50 text-amber-800'
                      )}
                    >
                      {scheduleMessage}
                    </motion.div>
                  )}

                  {/* Schedule Button */}
                  <Button
                    onClick={handleScheduleCall}
                    disabled={scheduleStatus === 'loading'}
                    className="w-full rounded-xl bg-teal-600 py-4 font-bold text-white shadow-md hover:bg-teal-700 disabled:opacity-50"
                  >
                    <Calendar className="mr-2 size-4" />
                    {scheduleStatus === 'loading' ? 'Scheduling…' : '🗓 Schedule a Call'}
                  </Button>
                </div>
              )}

              <div className="mt-auto rounded-xl border border-teal-100 bg-teal-50/60 p-4 text-xs text-teal-800">
                💡 <strong>Health Access Outbound Calling</strong>: HealthSathi will initiate a
                voice call to your phone or SIP account at the specified time or immediately upon
                request.
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
