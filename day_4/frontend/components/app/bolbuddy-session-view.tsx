'use client';

import React, { useEffect, useRef, useState } from 'react';
import {
  BookOpen,
  Brain,
  Briefcase,
  Coffee,
  Database,
  GraduationCap,
  MapPin,
  MessageSquare,
  Mic,
  MicOff,
  PhoneOff,
  ShieldAlert,
  Sparkles,
  Trash2,
  User,
  X,
} from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';
import {
  useAgent,
  useLocalParticipant,
  useSessionContext,
  useSessionMessages,
  useVoiceAssistant,
} from '@livekit/components-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/shadcn/utils';
import { resetPersistentUserId } from '@/lib/utils';

export function BolBuddySessionView() {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const { state: agentState } = useAgent();
  const { localParticipant } = useLocalParticipant();
  const { state: voiceState } = useVoiceAssistant();
  const isMuted = localParticipant ? !localParticipant.isMicrophoneEnabled : false;
  const [showTranscript, setShowTranscript] = useState(true);
  const [showMemoryDrawer, setShowMemoryDrawer] = useState(false);
  const [isForgetting, setIsForgetting] = useState(false);
  const [isForgotten, setIsForgotten] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const handleForgetMyData = async () => {
    try {
      setIsForgetting(true);
      const userId = localParticipant?.identity || '';

      await fetch('/api/forget', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId }),
      }).catch((e) => console.warn('Forget API call warning:', e));

      resetPersistentUserId();
      setIsForgotten(true);

      setTimeout(() => {
        setIsForgetting(false);
        setShowMemoryDrawer(false);
      }, 1500);
    } catch (err) {
      console.error('Forget data error:', err);
      setIsForgetting(false);
    }
  };

  // Toggle microphone
  const toggleMicrophone = async () => {
    if (localParticipant) {
      await localParticipant.setMicrophoneEnabled(isMuted);
    }
  };

  // End call
  const endCall = () => {
    session.end();
  };

  // Auto scroll transcript
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  // Determine current active status
  const currentStatus = voiceState || agentState || 'idle';

  // Orb animation classes & glowing styles
  const getOrbStateClass = () => {
    switch (currentStatus) {
      case 'listening':
        return 'orb-listening ring-4 ring-purple-500/30 scale-105';
      case 'thinking':
        return 'orb-thinking ring-4 ring-indigo-500/40';
      case 'speaking':
        return 'orb-speaking ring-8 ring-emerald-500/30 scale-110';
      default:
        return 'orb-idle ring-2 ring-indigo-500/20';
    }
  };

  const getStatusText = () => {
    switch (currentStatus) {
      case 'listening':
        return 'Listening... Speak freely in English or Hinglish';
      case 'thinking':
        return 'BolBuddy is processing...';
      case 'speaking':
        return 'BolBuddy is speaking...';
      default:
        return 'BolBuddy is ready • Start speaking anytime';
    }
  };

  const getStatusBadgeColor = () => {
    switch (currentStatus) {
      case 'listening':
        return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'thinking':
        return 'bg-indigo-100 text-indigo-700 border-indigo-200';
      case 'speaking':
        return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const topicPrompts = [
    {
      icon: GraduationCap,
      label: 'School & Campus',
      text: 'Tell me about your favorite subjects in school.',
    },
    {
      icon: Briefcase,
      label: 'Job Interview',
      text: 'Let us practice answering "Tell me about yourself".',
    },
    {
      icon: User,
      label: 'Self Introduction',
      text: 'Help me practice introducing myself confidently.',
    },
    { icon: Coffee, label: 'Daily Life', text: 'What did you have for breakfast today?' },
    { icon: MapPin, label: 'Travel', text: 'How do I ask for directions to the nearest bus stop?' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex flex-col justify-between overflow-hidden bg-[#FAFAF8] text-slate-900 selection:bg-indigo-100">
      {/* Top Bar */}
      <header className="z-20 flex items-center justify-between border-b border-slate-200/60 bg-white/80 px-6 py-4 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-purple-700 text-white shadow-sm">
            <Mic className="size-4 animate-pulse" />
          </div>
          <div>
            <h1 className="text-base font-extrabold tracking-tight text-slate-900">BolBuddy</h1>
            <p className="text-[11px] font-medium text-slate-500">
              Voice for Bharat • Learning &amp; Literacy
            </p>
          </div>
        </div>

        {/* Connection & Mode Badge */}
        <div className="flex items-center gap-3">
          <span
            className={cn(
              'flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold transition-all',
              getStatusBadgeColor()
            )}
          >
            <span className="size-2 animate-ping rounded-full bg-current" />
            <span>{getStatusText()}</span>
          </span>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowTranscript(!showTranscript)}
            className="text-xs font-semibold text-slate-600 hover:text-slate-900"
          >
            <MessageSquare className="mr-1.5 size-4" />
            {showTranscript ? 'Hide Transcript' : 'Show Transcript'}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowMemoryDrawer(true)}
            className="border-indigo-200 bg-indigo-50/50 text-xs font-semibold text-indigo-700 hover:bg-indigo-100/70 hover:text-indigo-900"
          >
            <Brain className="mr-1.5 size-4 text-indigo-600" />
            Memory &amp; Knowledge
          </Button>
        </div>
      </header>

      {/* Main Conversation Experience Area */}
      <main className="relative mx-auto flex w-full max-w-4xl flex-1 flex-col items-center justify-center px-6 py-4">
        {/* Centered Animated Conversation Orb */}
        <div className="my-auto flex flex-col items-center justify-center space-y-6">
          <div className="relative flex items-center justify-center">
            {/* Outer Glow Halo */}
            <div
              className={cn(
                'absolute size-64 rounded-full opacity-60 blur-2xl transition-all duration-700 md:size-80',
                currentStatus === 'speaking' && 'bg-emerald-400/40',
                currentStatus === 'listening' && 'bg-purple-500/40',
                currentStatus === 'thinking' && 'bg-indigo-500/40',
                currentStatus === 'idle' && 'bg-indigo-300/30'
              )}
            />

            {/* Core Animated Orb */}
            <div
              className={cn(
                'relative flex size-44 cursor-pointer items-center justify-center rounded-full bg-gradient-to-tr from-indigo-600 via-purple-600 to-indigo-800 shadow-2xl transition-all duration-500 md:size-56',
                getOrbStateClass()
              )}
              onClick={toggleMicrophone}
            >
              <div className="absolute inset-2 rounded-full border border-white/20 bg-white/10 backdrop-blur-xs" />
              <div className="relative flex flex-col items-center gap-2 text-white">
                {isMuted ? (
                  <MicOff className="size-10 text-rose-300" />
                ) : (
                  <Mic className="size-10 animate-pulse text-white" />
                )}
                <span className="text-[11px] font-bold tracking-wider text-white/80 uppercase">
                  {isMuted ? 'Muted' : currentStatus}
                </span>
              </div>
            </div>
          </div>

          {/* Subtitle status guidance */}
          <p className="max-w-md text-center text-xs font-medium text-slate-500">
            {isMuted
              ? 'Your microphone is muted. Click the orb or mic button to resume.'
              : 'Speak naturally in English or Hinglish. BolBuddy is listening!'}
          </p>
        </div>

        {/* Turn 0 Conversation Starters (When transcript is empty) */}
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 w-full max-w-2xl space-y-3 text-center"
          >
            <p className="text-xs font-bold tracking-wider text-slate-400 uppercase">
              Need inspiration? Try starting with:
            </p>
            <div className="flex flex-wrap items-center justify-center gap-2">
              {topicPrompts.map((topic, i) => {
                const Icon = topic.icon;
                return (
                  <div
                    key={i}
                    className="flex cursor-pointer items-center gap-2 rounded-xl border border-slate-200/80 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-2xs transition-all hover:border-indigo-300 hover:shadow-md"
                  >
                    <Icon className="size-3.5 text-indigo-600" />
                    <span>{topic.label}</span>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}

        {/* Clean Live Transcript Stream */}
        {showTranscript && messages.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 flex h-48 w-full max-w-2xl flex-col rounded-2xl border border-slate-200/80 bg-white/90 p-4 shadow-lg backdrop-blur-md md:h-56"
          >
            <div className="mb-3 flex items-center justify-between border-b border-slate-100 pb-2">
              <span className="flex items-center gap-1.5 text-xs font-bold text-slate-700">
                <MessageSquare className="size-3.5 text-indigo-600" />
                Live Conversation Transcript
              </span>
              <span className="text-[10px] font-medium text-slate-400">
                {messages.length} Turns
              </span>
            </div>

            <div
              ref={scrollAreaRef}
              className="scrollbar-thin scrollbar-thumb-slate-200 flex-1 space-y-3 overflow-y-auto pr-2"
            >
              {messages.map((msg, idx) => {
                const isUser = msg.from?.isLocal;

                return (
                  <div
                    key={idx}
                    className={cn(
                      'flex max-w-[85%] items-start gap-2.5 text-xs leading-relaxed',
                      isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
                    )}
                  >
                    <div
                      className={cn(
                        'flex size-6 shrink-0 items-center justify-center rounded-full text-[10px] font-bold',
                        isUser
                          ? 'bg-slate-200 text-slate-700'
                          : 'bg-gradient-to-br from-indigo-600 to-purple-700 text-white'
                      )}
                    >
                      {isUser ? 'You' : 'BB'}
                    </div>
                    <div
                      className={cn(
                        'rounded-2xl border p-3',
                        isUser
                          ? 'rounded-tr-xs border-indigo-600 bg-indigo-600 text-white'
                          : 'rounded-tl-xs border-slate-200/60 bg-slate-100 text-slate-900'
                      )}
                    >
                      {msg.message}
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </main>

      {/* Slide-over Memory & Knowledge Drawer */}
      <AnimatePresence>
        {showMemoryDrawer && (
          <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-xs">
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="flex h-full w-full max-w-md flex-col border-l border-slate-200 bg-white p-6 shadow-2xl"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <div className="flex items-center gap-2">
                  <div className="flex size-8 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600">
                    <Brain className="size-4" />
                  </div>
                  <div>
                    <h2 className="text-sm font-bold text-slate-900">Memory &amp; Knowledge</h2>
                    <p className="text-[11px] text-slate-500">
                      BolBuddy features &amp; data privacy
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowMemoryDrawer(false)}
                  className="size-8 rounded-full text-slate-400 hover:text-slate-600"
                >
                  <X className="size-4" />
                </Button>
              </div>

              <div className="mt-4 flex-1 space-y-6 overflow-y-auto pr-1">
                {/* Personal Memory Card */}
                <div className="space-y-3 rounded-2xl border border-indigo-100 bg-indigo-50/50 p-4">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-xs font-bold text-indigo-900">
                      <Database className="size-3.5 text-indigo-600" />
                      Persistent User Memory (SQLite)
                    </span>
                    <span className="rounded-full border border-indigo-200 bg-indigo-100 px-2 py-0.5 text-[10px] font-bold text-indigo-700">
                      Persistent Active
                    </span>
                  </div>
                  <p className="text-xs leading-relaxed text-slate-600">
                    BolBuddy automatically remembers your preferred name, English level, learning
                    goals, and topics practiced across calls on this device.
                  </p>
                  <div className="space-y-1.5 rounded-xl border border-indigo-100 bg-white p-3 text-[11px]">
                    <div className="flex items-center justify-between text-slate-700">
                      <span className="font-medium">Device Memory Identity:</span>
                      <span className="font-mono font-semibold text-indigo-600">Saved</span>
                    </div>
                    <div className="flex items-center justify-between text-slate-700">
                      <span className="font-medium">Explicit Verbal Consent:</span>
                      <span className="font-semibold text-emerald-600">Required</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 pt-1 text-[11px] font-semibold text-indigo-700">
                    <Sparkles className="size-3 text-indigo-600" />
                    <span>Try asking: &quot;What do you remember about me?&quot;</span>
                  </div>
                </div>

                {/* Curated Knowledge Base (RAG) */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-xs font-bold text-slate-900">
                      <BookOpen className="size-3.5 text-purple-600" />
                      Learning Resource Library (RAG)
                    </span>
                    <span className="text-[10px] text-slate-400">5 Curated Guides</span>
                  </div>
                  <div className="space-y-2">
                    {[
                      { title: 'Beginner Grammar Guide', tag: 'Grammar Tips' },
                      { title: 'Job Interview Answers', tag: 'Career Prep' },
                      { title: 'College Viva & Academic Q&A', tag: 'Viva Prep' },
                      { title: 'Everyday Conversation Phrases', tag: 'Fluency' },
                      { title: 'Pronunciation & Accent Guide', tag: 'Pronunciation' },
                    ].map((guide, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/70 p-3 text-xs text-slate-800"
                      >
                        <span className="font-medium">{guide.title}</span>
                        <span className="rounded-md border border-purple-200 bg-purple-50 px-2 py-0.5 text-[10px] font-semibold text-purple-700">
                          {guide.tag}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Privacy & Data Consent Card */}
                <div className="space-y-3 rounded-2xl border border-rose-100 bg-rose-50/40 p-4">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-rose-900">
                    <ShieldAlert className="size-3.5 text-rose-600" />
                    Privacy &amp; Data Control
                  </div>
                  <p className="text-xs leading-relaxed text-slate-600">
                    You have complete ownership of your data. You can request BolBuddy to
                    permanently delete all saved memory at any time.
                  </p>
                  <div className="pt-1">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={isForgetting || isForgotten}
                      onClick={handleForgetMyData}
                      className={cn(
                        'w-full border-rose-200 text-xs font-semibold transition-all',
                        isForgotten
                          ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
                          : 'bg-white text-rose-600 hover:bg-rose-100/50 hover:text-rose-700'
                      )}
                    >
                      {isForgetting ? (
                        <div className="flex items-center justify-center gap-2">
                          <span className="size-3 animate-spin rounded-full border-2 border-rose-600 border-t-transparent" />
                          <span>Deleting Memory...</span>
                        </div>
                      ) : isForgotten ? (
                        <div className="flex items-center justify-center gap-1.5">
                          <Sparkles className="size-3.5 text-emerald-600" />
                          <span>Memory Deleted &amp; Data Forgotten</span>
                        </div>
                      ) : (
                        <div className="flex items-center justify-center gap-1.5">
                          <Trash2 className="size-3.5" />
                          <span>Ask BolBuddy to &quot;Forget My Data&quot;</span>
                        </div>
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Glassmorphism Control Bar */}
      <footer className="z-20 flex items-center justify-center gap-4 border-t border-slate-200/60 bg-white/90 p-4 backdrop-blur-md">
        <Button
          size="lg"
          variant={isMuted ? 'destructive' : 'outline'}
          onClick={toggleMicrophone}
          className="size-12 cursor-pointer rounded-full shadow-sm"
        >
          {isMuted ? <MicOff className="size-5" /> : <Mic className="size-5 text-indigo-600" />}
        </Button>

        <Button
          size="lg"
          variant="destructive"
          onClick={endCall}
          className="flex cursor-pointer items-center gap-2 rounded-full bg-rose-600 px-6 text-xs font-semibold text-white shadow-md hover:bg-rose-700"
        >
          <PhoneOff className="size-4" />
          <span>End Conversation</span>
        </Button>
      </footer>
    </div>
  );
}
