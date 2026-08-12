'use client';

import React, { useState } from 'react';
import { Brain, CheckCircle2, ShieldCheck, Sparkles, Trash2, UserCheck, X } from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/shadcn/utils';
import { resetPersistentUserId } from '@/lib/utils';

export interface UserMemoryData {
  userId?: string;
  name?: string | null;
  reminderPreference?: string | null;
  contactPreference?: string | null;
  languagePreference?: string | null;
  interactionPreferences?: string[] | null;
}

interface MemoryPanelProps {
  isOpen: boolean;
  memory: UserMemoryData | null;
  onClose: () => void;
  onMemoryCleared: () => void;
}

export function MemoryPanel({ isOpen, memory, onClose, onMemoryCleared }: MemoryPanelProps) {
  const [isForgetting, setIsForgetting] = useState(false);
  const [isForgotten, setIsForgotten] = useState(false);

  const hasMemory = Boolean(
    memory && (memory.name || memory.learningGoal || memory.lastPracticedTopic)
  );

  const handleForgetMyData = async () => {
    try {
      setIsForgetting(true);
      const userId = memory?.userId || '';

      await fetch('/api/forget', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId }),
      }).catch((e) => console.warn('Forget API call warning:', e));

      resetPersistentUserId();
      setIsForgotten(true);
      onMemoryCleared();

      setTimeout(() => {
        setIsForgetting(false);
        onClose();
      }, 1400);
    } catch (err) {
      console.error('Forget data error:', err);
      setIsForgetting(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-xs">
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="flex h-full w-full max-w-md flex-col border-l border-slate-200 bg-white p-6 shadow-2xl"
          >
            {/* Drawer Header */}
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="flex size-9 items-center justify-center rounded-xl bg-teal-100 text-teal-600">
                  <Brain className="size-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900">Memory &amp; Privacy</h2>
                  <p className="text-xs text-slate-500">Manage saved health profile details</p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="size-8 rounded-full text-slate-400 hover:text-slate-600"
              >
                <X className="size-4" />
              </Button>
            </div>

            {/* Main Content Body */}
            <div className="mt-6 flex-1 space-y-6 overflow-y-auto pr-1">
              {/* Memory Summary Card */}
              <div className="space-y-4 rounded-2xl border border-teal-100 bg-gradient-to-br from-teal-50/70 to-emerald-50/40 p-4">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-xs font-bold text-teal-900">
                    <UserCheck className="size-4 text-teal-600" />
                    Saved Health Profile
                  </span>
                  <span className="rounded-full border border-teal-200 bg-white px-2.5 py-0.5 text-[10px] font-bold text-teal-700 shadow-2xs">
                    {hasMemory ? 'Profile Saved' : 'New User'}
                  </span>
                </div>

                {hasMemory ? (
                  <div className="space-y-2.5 rounded-xl border border-teal-100 bg-white p-3 text-xs">
                    {memory?.name && (
                      <div className="flex items-center justify-between text-slate-700">
                        <span className="text-slate-500">Name:</span>
                        <span className="font-bold text-slate-900">{memory.name}</span>
                      </div>
                    )}
                    {memory?.languagePreference && (
                      <div className="flex items-center justify-between text-slate-700">
                        <span className="text-slate-500">Language:</span>
                        <span className="font-semibold text-teal-700 capitalize">
                          {memory.languagePreference}
                        </span>
                      </div>
                    )}
                    {memory?.reminderPreference && (
                      <div className="flex items-center justify-between text-slate-700">
                        <span className="text-slate-500">Reminder:</span>
                        <span className="font-medium text-slate-800">
                          {memory.reminderPreference}
                        </span>
                      </div>
                    )}
                    {memory?.contactPreference && (
                      <div className="flex items-center justify-between text-slate-700">
                        <span className="text-slate-500">Contact:</span>
                        <span className="font-medium text-slate-800 capitalize">
                          {memory.contactPreference}
                        </span>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-xs text-slate-600">
                    HealthSathi remembers your name, language, and health preferences when you share
                    them during a voice conversation.
                  </p>
                )}

                <div className="flex items-center gap-2 pt-1 text-[11px] font-medium text-teal-700">
                  <Sparkles className="size-3.5 text-teal-600" />
                  <span>Ask HealthSathi: &quot;What do you remember about me?&quot;</span>
                </div>
              </div>

              {/* Privacy Guarantee */}
              <div className="space-y-2 rounded-2xl border border-slate-200/80 bg-slate-50/60 p-4 text-xs">
                <span className="flex items-center gap-1.5 font-bold text-slate-900">
                  <ShieldCheck className="size-4 text-emerald-600" />
                  Privacy Guarantee
                </span>
                <p className="leading-relaxed text-slate-600">
                  Your voice conversations are private and used solely to build your speaking
                  confidence. You can erase all saved details anytime.
                </p>
              </div>

              {/* Forget My Data Control */}
              <div className="space-y-3 rounded-2xl border border-rose-100 bg-rose-50/30 p-4">
                <div className="flex items-center gap-1.5 text-xs font-bold text-rose-900">
                  <Trash2 className="size-4 text-rose-600" />
                  Data Control
                </div>
                <p className="text-xs text-slate-600">
                  Permanently delete all saved health memory and reset your health profile.
                </p>

                <Button
                  variant="outline"
                  size="sm"
                  disabled={isForgetting || isForgotten}
                  onClick={handleForgetMyData}
                  className={cn(
                    'w-full rounded-xl border-rose-200 text-xs font-semibold transition-all',
                    isForgotten
                      ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
                      : 'bg-white text-rose-600 hover:bg-rose-100/60 hover:text-rose-700'
                  )}
                >
                  {isForgetting ? (
                    <div className="flex items-center justify-center gap-2">
                      <span className="size-3.5 animate-spin rounded-full border-2 border-rose-600 border-t-transparent" />
                      <span>Erasing Memory...</span>
                    </div>
                  ) : isForgotten ? (
                    <div className="flex items-center justify-center gap-1.5">
                      <CheckCircle2 className="size-4 text-emerald-600" />
                      <span>Data Cleared</span>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center gap-1.5">
                      <Trash2 className="size-3.5" />
                      <span>Forget My Data</span>
                    </div>
                  )}
                </Button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
