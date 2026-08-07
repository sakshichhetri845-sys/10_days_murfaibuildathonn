'use client';

import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  useAgent,
  useSessionContext,
  useSessionMessages,
  useLocalParticipant,
  useVoiceAssistant,
} from '@livekit/components-react';
import {
  Mic,
  MicOff,
  PhoneOff,
  MessageSquare,
  Sparkles,
  GraduationCap,
  Briefcase,
  User,
  Coffee,
  MapPin,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/shadcn/utils';

export function BolBuddySessionView() {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const { state: agentState } = useAgent();
  const { localParticipant } = useLocalParticipant();
  const { state: voiceState } = useVoiceAssistant();

  const [isMuted, setIsMuted] = useState(false);
  const [showTranscript, setShowTranscript] = useState(true);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Toggle microphone
  const toggleMicrophone = async () => {
    if (localParticipant) {
      const enabled = localParticipant.isMicrophoneEnabled;
      await localParticipant.setMicrophoneEnabled(!enabled);
      setIsMuted(enabled);
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
    { icon: GraduationCap, label: 'School & Campus', text: 'Tell me about your favorite subjects in school.' },
    { icon: Briefcase, label: 'Job Interview', text: 'Let us practice answering "Tell me about yourself".' },
    { icon: User, label: 'Self Introduction', text: 'Help me practice introducing myself confidently.' },
    { icon: Coffee, label: 'Daily Life', text: 'What did you have for breakfast today?' },
    { icon: MapPin, label: 'Travel', text: 'How do I ask for directions to the nearest bus stop?' },
  ];

  return (
    <div className="fixed inset-0 bg-[#FAFAF8] text-slate-900 flex flex-col justify-between overflow-hidden selection:bg-indigo-100 z-50">
      {/* Top Bar */}
      <header className="px-6 py-4 bg-white/80 backdrop-blur-md border-b border-slate-200/60 flex items-center justify-between z-20">
        <div className="flex items-center gap-3">
          <div className="size-9 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-700 flex items-center justify-center text-white shadow-sm">
            <Mic className="size-4 animate-pulse" />
          </div>
          <div>
            <h1 className="font-extrabold text-base tracking-tight text-slate-900">BolBuddy</h1>
            <p className="text-[11px] text-slate-500 font-medium">Voice for Bharat • Learning & Literacy</p>
          </div>
        </div>

        {/* Connection & Mode Badge */}
        <div className="flex items-center gap-3">
          <span
            className={cn(
              'px-3 py-1 rounded-full text-xs font-semibold border transition-all flex items-center gap-1.5',
              getStatusBadgeColor()
            )}
          >
            <span className="size-2 rounded-full bg-current animate-ping" />
            <span>{getStatusText()}</span>
          </span>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowTranscript(!showTranscript)}
            className="text-xs font-semibold text-slate-600 hover:text-slate-900"
          >
            <MessageSquare className="size-4 mr-1.5" />
            {showTranscript ? 'Hide Transcript' : 'Show Transcript'}
          </Button>
        </div>
      </header>

      {/* Main Conversation Experience Area */}
      <main className="flex-1 flex flex-col items-center justify-center relative px-6 py-4 max-w-4xl mx-auto w-full">
        {/* Centered Animated Conversation Orb */}
        <div className="flex flex-col items-center justify-center my-auto space-y-6">
          <div className="relative flex items-center justify-center">
            {/* Outer Glow Halo */}
            <div
              className={cn(
                'absolute size-64 md:size-80 rounded-full transition-all duration-700 blur-2xl opacity-60',
                currentStatus === 'speaking' && 'bg-emerald-400/40',
                currentStatus === 'listening' && 'bg-purple-500/40',
                currentStatus === 'thinking' && 'bg-indigo-500/40',
                currentStatus === 'idle' && 'bg-indigo-300/30'
              )}
            />

            {/* Core Animated Orb */}
            <div
              className={cn(
                'relative size-44 md:size-56 rounded-full bg-gradient-to-tr from-indigo-600 via-purple-600 to-indigo-800 flex items-center justify-center shadow-2xl transition-all duration-500 cursor-pointer',
                getOrbStateClass()
              )}
              onClick={toggleMicrophone}
            >
              <div className="absolute inset-2 rounded-full bg-white/10 backdrop-blur-xs border border-white/20" />
              <div className="relative text-white flex flex-col items-center gap-2">
                {isMuted ? (
                  <MicOff className="size-10 text-rose-300" />
                ) : (
                  <Mic className="size-10 text-white animate-pulse" />
                )}
                <span className="text-[11px] font-bold uppercase tracking-wider text-white/80">
                  {isMuted ? 'Muted' : currentStatus}
                </span>
              </div>
            </div>
          </div>

          {/* Subtitle status guidance */}
          <p className="text-xs text-slate-500 font-medium text-center max-w-md">
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
            className="w-full max-w-2xl mb-4 space-y-3 text-center"
          >
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Need inspiration? Try starting with:
            </p>
            <div className="flex flex-wrap items-center justify-center gap-2">
              {topicPrompts.map((topic, i) => {
                const Icon = topic.icon;
                return (
                  <div
                    key={i}
                    className="px-3.5 py-2 rounded-xl bg-white border border-slate-200/80 shadow-2xs text-xs font-semibold text-slate-700 flex items-center gap-2 hover:border-indigo-300 hover:shadow-md transition-all cursor-pointer"
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
            className="w-full max-w-2xl h-48 md:h-56 bg-white/90 backdrop-blur-md rounded-2xl border border-slate-200/80 shadow-lg p-4 flex flex-col mb-4"
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-3">
              <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                <MessageSquare className="size-3.5 text-indigo-600" />
                Live Conversation Transcript
              </span>
              <span className="text-[10px] text-slate-400 font-medium">{messages.length} Turns</span>
            </div>

            <div
              ref={scrollAreaRef}
              className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin scrollbar-thumb-slate-200"
            >
              {messages.map((msg, idx) => {
                const isUser = msg.from?.isLocal;

                return (
                  <div
                    key={idx}
                    className={cn(
                      'flex items-start gap-2.5 text-xs leading-relaxed max-w-[85%]',
                      isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'
                    )}
                  >
                    <div
                      className={cn(
                        'size-6 rounded-full flex items-center justify-center shrink-0 text-[10px] font-bold',
                        isUser
                          ? 'bg-slate-200 text-slate-700'
                          : 'bg-gradient-to-br from-indigo-600 to-purple-700 text-white'
                      )}
                    >
                      {isUser ? 'You' : 'BB'}
                    </div>
                    <div
                      className={cn(
                        'p-3 rounded-2xl border',
                        isUser
                          ? 'bg-indigo-600 text-white border-indigo-600 rounded-tr-xs'
                          : 'bg-slate-100 text-slate-900 border-slate-200/60 rounded-tl-xs'
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

      {/* Glassmorphism Control Bar */}
      <footer className="p-4 bg-white/90 backdrop-blur-md border-t border-slate-200/60 flex items-center justify-center gap-4 z-20">
        <Button
          size="lg"
          variant={isMuted ? 'destructive' : 'outline'}
          onClick={toggleMicrophone}
          className="rounded-full size-12 shadow-sm cursor-pointer"
        >
          {isMuted ? <MicOff className="size-5" /> : <Mic className="size-5 text-indigo-600" />}
        </Button>

        <Button
          size="lg"
          variant="destructive"
          onClick={endCall}
          className="rounded-full px-6 bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs shadow-md cursor-pointer flex items-center gap-2"
        >
          <PhoneOff className="size-4" />
          <span>End Conversation</span>
        </Button>
      </footer>
    </div>
  );
}
