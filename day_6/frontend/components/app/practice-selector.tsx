'use client';

import React from 'react';
import { Briefcase, Coffee, GraduationCap, Sparkles } from 'lucide-react';
import { cn } from '@/lib/shadcn/utils';

export interface PracticeMode {
  id: string;
  title: string;
  subtitle: string;
  topicPrompt: string;
  icon: React.ElementType;
  color: string;
}

export const PRACTICE_MODES: PracticeMode[] = [
  {
    id: 'interview',
    title: 'Interview',
    subtitle: 'Job & Internship Prep',
    topicPrompt: 'job interview practice',
    icon: Briefcase,
    color: 'border-blue-200 bg-blue-50/60 text-blue-900 hover:border-blue-400 hover:bg-blue-100/70',
  },
  {
    id: 'viva',
    title: 'College Viva',
    subtitle: 'Academic Q&A & Projects',
    topicPrompt: 'college viva practice',
    icon: GraduationCap,
    color:
      'border-purple-200 bg-purple-50/60 text-purple-900 hover:border-purple-400 hover:bg-purple-100/70',
  },
  {
    id: 'everyday',
    title: 'Everyday English',
    subtitle: 'Daily Life & Chit-Chat',
    topicPrompt: 'everyday English practice',
    icon: Coffee,
    color:
      'border-amber-200 bg-amber-50/60 text-amber-900 hover:border-amber-400 hover:bg-amber-100/70',
  },
  {
    id: 'presentation',
    title: 'Presentation',
    subtitle: 'Campus Speech & Talk',
    topicPrompt: 'campus presentation practice',
    icon: Sparkles,
    color:
      'border-emerald-200 bg-emerald-50/60 text-emerald-900 hover:border-emerald-400 hover:bg-emerald-100/70',
  },
];

interface PracticeSelectorProps {
  selectedModeId: string;
  onSelectMode: (mode: PracticeMode) => void;
}

export function PracticeSelector({ selectedModeId, onSelectMode }: PracticeSelectorProps) {
  return (
    <div className="w-full space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold tracking-wider text-slate-500 uppercase">
          Choose Practice Goal
        </h3>
        <span className="text-[11px] font-medium text-slate-400">Select one to start</span>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {PRACTICE_MODES.map((mode) => {
          const Icon = mode.icon;
          const isSelected = selectedModeId === mode.id;

          return (
            <button
              key={mode.id}
              type="button"
              onClick={() => onSelectMode(mode)}
              className={cn(
                'flex flex-col items-start gap-2.5 rounded-2xl border p-4 text-left transition-all duration-200 focus:ring-2 focus:ring-indigo-500/40 focus:outline-none',
                mode.color,
                isSelected
                  ? 'scale-[1.02] border-indigo-600 bg-white shadow-md ring-2 ring-indigo-600/30'
                  : 'bg-white/80 hover:scale-[1.01]'
              )}
            >
              <div className="flex size-9 items-center justify-center rounded-xl bg-white shadow-2xs">
                <Icon className="size-4 text-indigo-600" />
              </div>
              <div>
                <p className="text-sm font-bold text-slate-900">{mode.title}</p>
                <p className="mt-0.5 text-[11px] text-slate-500">{mode.subtitle}</p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
