'use client';

import React from 'react';
import { Flame, MessageSquare, Target } from 'lucide-react';

interface ProgressSummaryProps {
  sessionCount?: number;
  topicsPracticedCount?: number;
  streakDays?: number;
}

export function ProgressSummary({
  sessionCount = 3,
  topicsPracticedCount = 2,
  streakDays = 2,
}: ProgressSummaryProps) {
  return (
    <div className="flex items-center justify-around rounded-2xl border border-slate-200/70 bg-white/90 p-3.5 text-slate-800 shadow-2xs">
      <div className="flex items-center gap-2.5">
        <div className="flex size-8 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
          <MessageSquare className="size-4" />
        </div>
        <div>
          <p className="text-xs font-bold text-slate-900">{sessionCount} Sessions</p>
          <p className="text-[10px] text-slate-500">Spoken practice</p>
        </div>
      </div>

      <div className="h-6 w-px bg-slate-200" />

      <div className="flex items-center gap-2.5">
        <div className="flex size-8 items-center justify-center rounded-lg bg-purple-50 text-purple-600">
          <Target className="size-4" />
        </div>
        <div>
          <p className="text-xs font-bold text-slate-900">{topicsPracticedCount} Topics</p>
          <p className="text-[10px] text-slate-500">Covered so far</p>
        </div>
      </div>

      <div className="h-6 w-px bg-slate-200" />

      <div className="flex items-center gap-2.5">
        <div className="flex size-8 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
          <Flame className="size-4" />
        </div>
        <div>
          <p className="text-xs font-bold text-slate-900">{streakDays} Day Streak</p>
          <p className="text-[10px] text-slate-500">Keep it up!</p>
        </div>
      </div>
    </div>
  );
}
