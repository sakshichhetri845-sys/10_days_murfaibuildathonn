'use client';

import React, { useEffect, useState } from 'react';
import { Calendar, CheckCircle2, Phone, PhoneCall, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { getPersistentUserId } from '@/lib/utils';

export interface DailyScheduleData {
  user_id: string;
  phone_number: string;
  practice_topic: string;
  preferred_time: string;
  timezone: string;
  enabled: boolean;
  next_call_at: string;
}

export const PracticeCallSection = () => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [scheduledTime, setScheduledTime] = useState('8:00 PM');
  const [practiceTopic, setPracticeTopic] = useState('Job Interview Preparation');
  const [consentGiven, setConsentGiven] = useState(false);
  const [schedule, setSchedule] = useState<DailyScheduleData | null>(null);
  const [statusMessage, setStatusMessage] = useState<{
    type: 'success' | 'error' | 'info';
    text: string;
  } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load existing schedule on mount
  useEffect(() => {
    async function loadSchedule() {
      const userId = getPersistentUserId();
      if (!userId) return;
      try {
        const res = await fetch(`/api/outbound/practice?userId=${encodeURIComponent(userId)}`);
        const data = await res.json();
        if (data.success && data.schedule && data.schedule.enabled) {
          setSchedule(data.schedule);
          if (data.schedule.phone_number) setPhoneNumber(data.schedule.phone_number);
          if (data.schedule.preferred_time) setScheduledTime(data.schedule.preferred_time);
          if (data.schedule.practice_topic) setPracticeTopic(data.schedule.practice_topic);
          setConsentGiven(true);
        }
      } catch (err) {
        console.warn('Failed to fetch practice call schedule:', err);
      }
    }
    loadSchedule();
  }, []);

  const handleSaveSchedule = async () => {
    const userId = getPersistentUserId() || 'default_user';
    if (!phoneNumber.trim()) {
      setStatusMessage({ type: 'error', text: 'Please enter a valid phone number.' });
      return;
    }
    if (!consentGiven) {
      setStatusMessage({ type: 'error', text: 'Please agree to receive daily practice calls.' });
      return;
    }

    setIsSubmitting(true);
    setStatusMessage(null);

    try {
      const res = await fetch('/api/outbound/practice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId,
          action: 'save_schedule',
          phoneNumber: phoneNumber.trim(),
          scheduledTime: scheduledTime.trim() || '8:00 PM',
          practiceTopic: practiceTopic.trim() || 'Spoken English Practice',
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata',
        }),
      });

      const data = await res.json();
      setIsSubmitting(false);

      if (data.success && data.schedule) {
        setSchedule(data.schedule);
        setStatusMessage({
          type: 'success',
          text: `Daily practice scheduled! BolBuddy will call you every day at ${scheduledTime.trim()}.`,
        });
      } else {
        setStatusMessage({
          type: 'error',
          text: "BolBuddy couldn't place your practice call this time.",
        });
      }
    } catch {
      setIsSubmitting(false);
      setStatusMessage({
        type: 'error',
        text: "BolBuddy couldn't place your practice call this time.",
      });
    }
  };

  const handleCallNow = async () => {
    const userId = getPersistentUserId() || 'default_user';
    if (!phoneNumber.trim()) {
      setStatusMessage({ type: 'error', text: 'Please enter your phone number or Linphone ID.' });
      return;
    }

    setIsSubmitting(true);
    setStatusMessage(null);

    try {
      const res = await fetch('/api/outbound/practice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId,
          action: 'immediate',
          phoneNumber: phoneNumber.trim(),
          practiceTopic: practiceTopic.trim() || 'Spoken English Practice',
        }),
      });

      const data = await res.json();
      setIsSubmitting(false);

      if (data.success) {
        setStatusMessage({
          type: 'success',
          text: `Calling ${phoneNumber.trim()} now... Answer your phone/Linphone app!`,
        });
      } else {
        setStatusMessage({
          type: 'error',
          text: data.error || "BolBuddy couldn't place the call right now.",
        });
      }
    } catch {
      setIsSubmitting(false);
      setStatusMessage({
        type: 'error',
        text: "BolBuddy couldn't place your call right now.",
      });
    }
  };

  const handleCancelSchedule = async () => {
    const userId = getPersistentUserId() || 'default_user';
    setIsSubmitting(true);

    try {
      const res = await fetch('/api/outbound/practice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId,
          action: 'cancel_schedule',
        }),
      });

      const data = await res.json();
      setIsSubmitting(false);

      if (data.success) {
        setSchedule(null);
        setStatusMessage({
          type: 'info',
          text: 'Daily practice calls cancelled. You can schedule again anytime.',
        });
      }
    } catch {
      setIsSubmitting(false);
      setStatusMessage({
        type: 'error',
        text: "BolBuddy couldn't update your schedule right now.",
      });
    }
  };

  const formatNextCall = (isoStr?: string) => {
    if (!isoStr) return `Tomorrow at ${scheduledTime}`;
    try {
      const date = new Date(isoStr);
      return date.toLocaleString(undefined, {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      });
    } catch {
      return `Tomorrow at ${scheduledTime}`;
    }
  };

  return (
    <div className="rounded-3xl border border-indigo-100 bg-white p-6 shadow-sm sm:p-8">
      <div className="flex items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-2xl border border-indigo-100 bg-indigo-50 text-indigo-600">
            <PhoneCall className="size-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Daily Practice Call</h2>
            <p className="text-xs font-medium text-slate-500">
              Let BolBuddy call you every day for a short English practice session.
            </p>
          </div>
        </div>
        <span className="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-3 py-1 text-xs font-bold text-indigo-700">
          <Sparkles className="size-3" /> Outbound Voice
        </span>
      </div>

      <div className="mt-6 space-y-4">
        {schedule && schedule.enabled ? (
          /* Active Schedule State */
          <div className="space-y-4">
            <div className="flex items-center gap-2 rounded-2xl border border-emerald-200 bg-emerald-50/70 p-4 text-emerald-900">
              <CheckCircle2 className="size-5 text-emerald-600" />
              <div>
                <p className="text-sm font-bold">✓ Daily practice scheduled</p>
                <p className="text-xs font-medium text-emerald-700">
                  BolBuddy will call you every day at {schedule.preferred_time}.
                </p>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-100 bg-slate-50/60 p-4 text-xs">
              <div className="flex items-center justify-between">
                <div>
                  <span className="mb-1 block font-bold tracking-wider text-slate-500 uppercase">
                    Next call:
                  </span>
                  <span className="text-sm font-bold text-slate-900">
                    {formatNextCall(schedule.next_call_at)}
                  </span>
                </div>
                <div className="text-right">
                  <span className="mb-1 block font-bold tracking-wider text-slate-500 uppercase">
                    Topic:
                  </span>
                  <span className="font-semibold text-slate-800">{schedule.practice_topic}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 pt-1">
              <Button
                variant="outline"
                onClick={() => setSchedule(null)}
                className="rounded-xl border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-50"
              >
                Change Time
              </Button>
              <Button
                variant="outline"
                onClick={handleCallNow}
                disabled={isSubmitting || !phoneNumber.trim()}
                className="rounded-xl border-emerald-300 bg-emerald-50 text-xs font-bold text-emerald-800 hover:bg-emerald-100"
              >
                <Phone className="mr-1.5 size-3.5 text-emerald-600" />
                Call Me Now
              </Button>
              <Button
                variant="outline"
                onClick={handleCancelSchedule}
                disabled={isSubmitting}
                className="rounded-xl border-rose-200 text-xs font-bold text-rose-700 hover:bg-rose-50"
              >
                {isSubmitting ? 'Cancelling...' : 'Cancel Daily Calls'}
              </Button>
            </div>
          </div>
        ) : (
          /* Schedule Form State */
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              {/* Practice Topic Field */}
              <div>
                <label className="mb-1.5 block text-xs font-bold text-slate-700">
                  Practice Topic
                </label>
                <input
                  type="text"
                  value={practiceTopic}
                  onChange={(e) => setPracticeTopic(e.target.value)}
                  placeholder="e.g. Job Interview Preparation"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
                />
              </div>

              {/* Preferred Time Field */}
              <div>
                <label className="mb-1.5 block flex items-center gap-1.5 text-xs font-bold text-slate-700">
                  <Calendar className="size-3.5 text-indigo-600" />
                  Preferred Time
                </label>
                <input
                  type="text"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                  placeholder="e.g. 8:00 PM or 20:00"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
                />
              </div>

              {/* Phone Number Field */}
              <div>
                <label className="mb-1.5 block flex items-center gap-1.5 text-xs font-bold text-slate-700">
                  <Phone className="size-3.5 text-indigo-600" />
                  Phone Number / Linphone ID
                </label>
                <input
                  type="tel"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  placeholder="sakshyambhttr or phone number"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/50 px-3.5 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:outline-none"
                />
              </div>
            </div>

            {/* Consent Checkbox */}
            <div className="flex items-center gap-2 pt-1">
              <input
                type="checkbox"
                id="consent-check"
                checked={consentGiven}
                onChange={(e) => setConsentGiven(e.target.checked)}
                className="size-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              />
              <label htmlFor="consent-check" className="text-xs font-semibold text-slate-700">
                I agree to receive daily practice calls.
              </label>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Button
                onClick={handleSaveSchedule}
                disabled={isSubmitting || !consentGiven}
                className="rounded-xl bg-indigo-600 px-6 py-2.5 text-xs font-bold text-white shadow-md shadow-indigo-600/20 hover:bg-indigo-700 disabled:opacity-50"
              >
                {isSubmitting ? 'Scheduling...' : 'Schedule Daily Practice'}
              </Button>
              <Button
                variant="outline"
                onClick={handleCallNow}
                disabled={isSubmitting || !phoneNumber.trim()}
                className="rounded-xl border-emerald-300 bg-emerald-50 px-6 py-2.5 text-xs font-bold text-emerald-800 hover:bg-emerald-100 disabled:opacity-50"
              >
                <Phone className="mr-1.5 size-3.5 text-emerald-600" />
                {isSubmitting ? 'Dialing...' : 'Call Me Now'}
              </Button>
            </div>
          </div>
        )}

        {/* Status Message */}
        {statusMessage && (
          <div
            className={`mt-4 rounded-xl border p-3.5 text-xs font-medium ${
              statusMessage.type === 'success'
                ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                : statusMessage.type === 'error'
                  ? 'border-rose-200 bg-rose-50 text-rose-800'
                  : 'border-blue-200 bg-blue-50 text-blue-800'
            }`}
          >
            {statusMessage.text}
          </div>
        )}
      </div>
    </div>
  );
};
