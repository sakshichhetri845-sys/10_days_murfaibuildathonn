'use client';

import React, { useEffect, useState } from 'react';
import {
  Activity,
  BarChart3,
  Calendar,
  Heart,
  LifeBuoy,
  MapPin,
  Phone,
  ShieldCheck,
  Stethoscope,
  UserCheck,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { getPersistentUserId } from '@/lib/utils';
import { AnalyticsDrawer } from './analytics-drawer';
import { EscalationTicket, EscalationsDrawer } from './escalations-drawer';
import { HealthRemindersSection } from './health-reminders-section';
import { MemoryPanel, UserMemoryData } from './memory-panel';

interface WelcomeViewProps {
  startButtonText?: string;
  onStartCall: () => void;
  onSelectTopic?: (topic: string) => void;
}

export const WelcomeView = ({
  startButtonText = '🩺 Talk to HealthSathi',
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [memory, setMemory] = useState<UserMemoryData | null>(null);
  const [recentTicket, setRecentTicket] = useState<EscalationTicket | null>(null);
  const [isMemoryOpen, setIsMemoryOpen] = useState(false);
  const [isEscalationsOpen, setIsEscalationsOpen] = useState(false);
  const [isRemindersOpen, setIsRemindersOpen] = useState(false);
  const [isAnalyticsOpen, setIsAnalyticsOpen] = useState(false);

  useEffect(() => {
    async function loadData() {
      const userId = getPersistentUserId();
      if (!userId) return;

      // Load Memory
      try {
        const res = await fetch(`/api/memory?userId=${encodeURIComponent(userId)}`);
        const data = await res.json();
        if (data.success && data.memory) {
          setMemory(data.memory);
        }
      } catch (err) {
        console.warn('Memory fetch warning:', err);
      }

      // Load Recent Escalation Support Ticket
      try {
        const escRes = await fetch('/api/escalations');
        const escData = await escRes.json();
        if (
          escData.success &&
          Array.isArray(escData.escalations) &&
          escData.escalations.length > 0
        ) {
          setRecentTicket(escData.escalations[0]);
        }
      } catch (err) {
        console.warn('Escalations fetch warning:', err);
      }
    }
    loadData();
  }, []);

  const handleMemoryCleared = () => {
    setMemory(null);
  };

  const greetingTitle = memory?.name
    ? `Welcome back, ${memory.name}`
    : 'HealthSathi • Personal Health Support';

  return (
    <div
      ref={ref}
      className="flex min-h-screen flex-col bg-[#F8FAFC] font-sans text-slate-900 selection:bg-teal-100 selection:text-teal-900"
    >
      {/* Clinical Medical Navigation Bar */}
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/95 px-6 py-4 backdrop-blur-md">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-slate-900 text-teal-400 shadow-sm">
              <Stethoscope className="size-5 text-teal-400" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-slate-900">HealthSathi</span>
              <p className="text-[11px] font-semibold tracking-wide text-slate-500 uppercase">
                Personal Health Support Companion
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsAnalyticsOpen(true)}
              className="rounded-lg border-slate-200 bg-white text-xs font-semibold text-slate-700 hover:border-slate-300 hover:bg-slate-50"
            >
              <BarChart3 className="mr-1.5 size-3.5 text-teal-600" />
              <span>Call Analytics</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsRemindersOpen(true)}
              className="rounded-lg border-slate-200 bg-white text-xs font-semibold text-slate-700 hover:border-slate-300 hover:bg-slate-50"
            >
              <Phone className="mr-1.5 size-3.5 text-teal-600" />
              <span>Call Controls</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsEscalationsOpen(true)}
              className="rounded-lg border-slate-200 bg-white text-xs font-semibold text-slate-700 hover:border-slate-300 hover:bg-slate-50"
            >
              <LifeBuoy className="mr-1.5 size-3.5 text-slate-600" />
              <span>Support Requests</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsMemoryOpen(true)}
              className="rounded-lg border-slate-200 bg-white text-xs font-semibold text-slate-700 hover:border-slate-300 hover:bg-slate-50"
            >
              <UserCheck className="mr-1.5 size-3.5 text-slate-600" />
              <span>Preferences</span>
            </Button>

            <Button
              onClick={onStartCall}
              size="sm"
              className="rounded-lg bg-teal-700 px-4 py-2 text-xs font-bold text-white shadow-sm hover:bg-teal-800"
            >
              {startButtonText}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Clinical Dashboard Layout */}
      <main className="mx-auto flex max-w-4xl flex-1 flex-col gap-8 px-6 py-8 sm:py-10">
        {/* Drawers */}
        <AnalyticsDrawer isOpen={isAnalyticsOpen} onClose={() => setIsAnalyticsOpen(false)} />
        <EscalationsDrawer isOpen={isEscalationsOpen} onClose={() => setIsEscalationsOpen(false)} />
        <MemoryPanel
          isOpen={isMemoryOpen}
          memory={memory}
          onClose={() => setIsMemoryOpen(false)}
          onMemoryCleared={handleMemoryCleared}
        />
        <HealthRemindersSection
          isOpen={isRemindersOpen}
          onClose={() => setIsRemindersOpen(false)}
        />

        {/* Safety Disclaimer Banner */}
        <div className="flex items-center gap-3.5 rounded-xl border border-teal-200/80 bg-teal-50/60 p-4 text-xs text-slate-700 shadow-sm">
          <div className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-teal-600 text-white">
            <ShieldCheck className="size-4" />
          </div>
          <div>
            <span className="font-bold text-slate-900">Health Guidance Disclaimer:</span>
            <span className="ml-1 text-slate-600">
              HealthSathi provides general health information and triage support. It does not
              replace a qualified medical professional. For emergencies, always call{' '}
              <strong>112</strong> or visit a hospital immediately.
            </span>
          </div>
        </div>

        {/* Main Hero & Action Card */}
        <section className="flex flex-col gap-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="flex flex-col gap-2">
            <div className="inline-flex w-fit items-center gap-2 rounded-md bg-slate-100 px-3 py-1 text-[11px] font-bold tracking-wider text-slate-700 uppercase">
              <Activity className="size-3 text-teal-600" />
              Voice-First Health Guidance • English · Hindi · Hinglish
            </div>
            <h1 className="text-2xl font-extrabold text-slate-900 sm:text-3xl">{greetingTitle}</h1>
            <p className="text-sm font-medium text-slate-600">
              Describe your symptoms naturally, receive non-diagnostic triage advice, or request
              human health support.
            </p>
          </div>

          {/* Primary Action Buttons */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Button
              onClick={onStartCall}
              size="lg"
              className="flex items-center gap-2.5 rounded-xl bg-teal-700 px-6 py-6 text-sm font-bold text-white shadow-sm hover:bg-teal-800"
            >
              <Stethoscope className="size-4 text-teal-200" />
              <span>Start Health Check</span>
            </Button>

            <Button
              onClick={onStartCall}
              variant="outline"
              size="lg"
              className="flex items-center gap-2 rounded-xl border-slate-300 bg-white px-6 py-6 text-sm font-bold text-slate-800 hover:bg-slate-50"
            >
              <Heart className="size-4 text-teal-600" />
              <span>Talk to HealthSathi</span>
            </Button>
          </div>
        </section>

        {/* Quick Actions Grid */}
        <section className="flex flex-col gap-3">
          <h2 className="text-xs font-bold tracking-wider text-slate-400 uppercase">
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {/* Action 1: Call Me Now */}
            <button
              onClick={() => setIsRemindersOpen(true)}
              className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 text-left transition-all hover:border-teal-300 hover:shadow-sm"
            >
              <div className="flex size-9 items-center justify-center rounded-lg bg-teal-50 text-teal-700">
                <Phone className="size-5" />
              </div>
              <div className="mt-4">
                <p className="text-sm font-bold text-slate-900">Call Me Now</p>
                <p className="mt-1 text-xs text-slate-500">
                  Trigger an immediate outbound voice check-in to your phone
                </p>
              </div>
            </button>

            {/* Action 2: Schedule a Call */}
            <button
              onClick={() => setIsRemindersOpen(true)}
              className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 text-left transition-all hover:border-teal-300 hover:shadow-sm"
            >
              <div className="flex size-9 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
                <Calendar className="size-5" />
              </div>
              <div className="mt-4">
                <p className="text-sm font-bold text-slate-900">Schedule a Call</p>
                <p className="mt-1 text-xs text-slate-500">
                  Set a daily medication or follow-up call time
                </p>
              </div>
            </button>

            {/* Action 3: Find Nearby Care */}
            <button
              onClick={onStartCall}
              className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 text-left transition-all hover:border-teal-300 hover:shadow-sm"
            >
              <div className="flex size-9 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
                <MapPin className="size-5" />
              </div>
              <div className="mt-4">
                <p className="text-sm font-bold text-slate-900">Find Nearby Care</p>
                <p className="mt-1 text-xs text-slate-500">
                  Locate local health posts, PHCs, or general clinics
                </p>
              </div>
            </button>
          </div>
        </section>

        {/* Recent Support Section */}
        <section className="flex flex-col gap-3">
          <h2 className="text-xs font-bold tracking-wider text-slate-400 uppercase">
            Recent Support Request
          </h2>
          {recentTicket ? (
            <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="flex size-8 items-center justify-center rounded-lg bg-teal-100 text-xs font-extrabold text-teal-800">
                  {recentTicket.reference_id}
                </div>
                <div>
                  <p className="text-sm font-bold text-slate-900">
                    {recentTicket.reason_type.replace('_', ' ').toUpperCase()}
                  </p>
                  <p className="text-xs text-slate-500">
                    {recentTicket.issue_summary.slice(0, 70)}…
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-bold text-amber-700">
                  {recentTicket.status}
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsEscalationsOpen(true)}
                  className="text-xs font-bold text-teal-700 hover:bg-teal-50"
                >
                  View Details
                </Button>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-200 bg-white p-5 text-center text-xs text-slate-400">
              No recent human support requests. HealthSathi can submit a ticket if you need human
              health assistance.
            </div>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        HealthSathi • Personal Health Support Companion • Non-Diagnostic Health Triage
      </footer>
    </div>
  );
};
