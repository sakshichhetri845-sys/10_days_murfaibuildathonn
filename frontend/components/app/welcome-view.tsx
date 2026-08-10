'use client';

import React, { useEffect, useState } from 'react';
import { ArrowRight, Brain, Mic, ShieldCheck, Sparkles } from 'lucide-react';
import { motion } from 'motion/react';
import { Button } from '@/components/ui/button';
import { getPersistentUserId } from '@/lib/utils';
import { MemoryPanel, UserMemoryData } from './memory-panel';
import { PRACTICE_MODES, PracticeMode, PracticeSelector } from './practice-selector';
import { ProgressSummary } from './progress-summary';

interface WelcomeViewProps {
  startButtonText?: string;
  onStartCall: () => void;
  onSelectTopic?: (topic: string) => void;
}

export const WelcomeView = ({
  startButtonText = '🎙 Start Speaking',
  onStartCall,
  onSelectTopic,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [memory, setMemory] = useState<UserMemoryData | null>(null);
  const [isMemoryOpen, setIsMemoryOpen] = useState(false);
  const [selectedMode, setSelectedMode] = useState<PracticeMode>(PRACTICE_MODES[0]);

  // Fetch persistent memory facts on mount
  useEffect(() => {
    async function loadMemory() {
      const userId = getPersistentUserId();
      if (!userId) return;
      try {
        const res = await fetch(`/api/memory?userId=${encodeURIComponent(userId)}`);
        const data = await res.json();
        if (data.success && data.memory) {
          setMemory(data.memory);
        }
      } catch (err) {
        console.warn('Memory fetch warning:', err);
      }
    }
    loadMemory();
  }, []);

  const handleSelectMode = (mode: PracticeMode) => {
    setSelectedMode(mode);
    if (onSelectTopic) {
      onSelectTopic(mode.topicPrompt);
    }
  };

  const handleStartCallClick = () => {
    if (onSelectTopic) {
      onSelectTopic(selectedMode.topicPrompt);
    }
    onStartCall();
  };

  const handleMemoryCleared = () => {
    setMemory(null);
  };

  const greetingTitle = memory?.name
    ? `Welcome back, ${memory.name}.`
    : 'Ready for a little English practice?';

  const greetingSubtitle = memory?.learningGoal
    ? `Ready to continue your ${memory.learningGoal} practice?`
    : 'No perfect English required. Just start speaking.';

  return (
    <div
      ref={ref}
      className="flex min-h-screen flex-col justify-between bg-[#F8FAFC] font-sans text-slate-900 selection:bg-indigo-100 selection:text-indigo-900"
    >
      {/* Header */}
      <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-[#F8FAFC]/90 px-4 py-4 backdrop-blur-md sm:px-8">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-600 text-white shadow-md shadow-indigo-500/20">
              <Mic className="size-5 text-white" />
            </div>
            <div>
              <span className="text-xl font-extrabold tracking-tight text-slate-900">BolBuddy</span>
              <p className="text-[11px] font-medium text-slate-500">
                AI English Speaking Companion
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsMemoryOpen(true)}
              className="rounded-full border-indigo-200 bg-indigo-50/70 text-xs font-bold text-indigo-700 hover:bg-indigo-100/70 hover:text-indigo-900"
            >
              <Brain className="mr-1.5 size-4 text-indigo-600" />
              <span>Memory</span>
            </Button>

            <Button
              onClick={handleStartCallClick}
              size="sm"
              className="rounded-full bg-indigo-600 px-5 py-2 text-xs font-bold text-white shadow-md shadow-indigo-600/20 transition-all hover:bg-indigo-700"
            >
              {startButtonText}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto flex max-w-4xl flex-1 flex-col gap-10 px-4 py-8 sm:px-8 sm:py-12">
        {/* Memory Panel Drawer */}
        <MemoryPanel
          isOpen={isMemoryOpen}
          memory={memory}
          onClose={() => setIsMemoryOpen(false)}
          onMemoryCleared={handleMemoryCleared}
        />

        {/* Safe Judgement-Free Banner */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex items-center gap-3 rounded-2xl border border-indigo-200/60 bg-gradient-to-r from-indigo-50/80 via-purple-50/50 to-blue-50/30 p-4 text-xs font-medium text-slate-700 shadow-2xs"
        >
          <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-indigo-600/10 text-indigo-600">
            <ShieldCheck className="size-4" />
          </div>
          <div>
            <span className="font-bold text-slate-900">
              &quot;Speak freely without fear of mistakes.&quot;
            </span>
            <span className="ml-1 text-slate-600">
              Natural English &amp; Hinglish practice designed for Indian learners.
            </span>
          </div>
        </motion.div>

        {/* Hero Section */}
        <motion.section
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex flex-col gap-6 text-left"
        >
          <div className="inline-flex w-fit items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-3.5 py-1.5 text-xs font-bold text-indigo-700">
            <Sparkles className="size-3.5 text-indigo-600" />
            <span>Learning &amp; Literacy • Voice-First</span>
          </div>

          <div className="space-y-2">
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl lg:text-5xl">
              {greetingTitle}
            </h1>
            <p className="text-base font-semibold text-indigo-600 sm:text-lg">{greetingSubtitle}</p>
          </div>

          {/* Primary Action Button */}
          <div className="pt-2">
            <Button
              onClick={handleStartCallClick}
              size="lg"
              className="flex w-full items-center justify-center gap-3 rounded-2xl bg-indigo-600 py-7 text-base font-extrabold text-white shadow-xl shadow-indigo-600/25 transition-all hover:scale-[1.01] hover:bg-indigo-700 sm:w-auto sm:px-10"
            >
              <span>🎙 Start Speaking</span>
              <ArrowRight className="size-5" />
            </Button>
          </div>
        </motion.section>

        {/* Practice Selector */}
        <motion.section
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <PracticeSelector selectedModeId={selectedMode.id} onSelectMode={handleSelectMode} />
        </motion.section>

        {/* Light Progress Summary */}
        <motion.section
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <ProgressSummary
            sessionCount={memory?.topicsPracticed?.length ? memory.topicsPracticed.length + 2 : 1}
            topicsPracticedCount={memory?.topicsPracticed?.length || 1}
            streakDays={2}
          />
        </motion.section>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200/60 bg-white py-4 text-center text-xs text-slate-400">
        BolBuddy • AI English Speaking Companion for Indian Learners
      </footer>
    </div>
  );
};
