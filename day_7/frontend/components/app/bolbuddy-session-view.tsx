'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Brain, LifeBuoy, MessageSquare, Mic, MicOff, PhoneOff } from 'lucide-react';
import { motion } from 'motion/react';
import {
  useAgent,
  useLocalParticipant,
  useSessionContext,
  useSessionMessages,
  useVoiceAssistant,
} from '@livekit/components-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/shadcn/utils';
import { EvaluationFeedback, FeedbackCard } from './feedback-card';
import { MemoryPanel, UserMemoryData } from './memory-panel';

export function BolBuddySessionView() {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const { state: agentState } = useAgent();
  const { localParticipant } = useLocalParticipant();
  const { state: voiceState } = useVoiceAssistant();
  const isMuted = localParticipant ? !localParticipant.isMicrophoneEnabled : false;

  const [showTranscript, setShowTranscript] = useState(false); // Transcript hidden by default
  const [showMemoryDrawer, setShowMemoryDrawer] = useState(false);
  const [memory, setMemory] = useState<UserMemoryData | null>(null);
  const [isCallEnded, setIsCallEnded] = useState(false);
  const [extractedFeedback, setExtractedFeedback] = useState<EvaluationFeedback | null>(null);
  const [activeTicketRef, setActiveTicketRef] = useState<string | null>(null);

  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Auto scroll transcript when visible
  useEffect(() => {
    if (showTranscript && scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages, showTranscript]);

  // Parse active ticket reference ID (ESC-XXXX) from messages
  useEffect(() => {
    for (const msg of messages) {
      if (!msg.from?.isLocal && msg.message) {
        const refMatch = msg.message.match(/ESC-[A-Z0-9]+/i);
        if (refMatch) {
          setActiveTicketRef(refMatch[0].toUpperCase());
        }
      }
    }
  }, [messages]);

  // Extract structured feedback if score_spoken_answer (JSON or natural spoken text) was returned in chat history
  useEffect(() => {
    for (const msg of messages) {
      if (!msg.from?.isLocal && msg.message) {
        // 1. Try JSON match first
        try {
          const match = msg.message.match(/\{[\s\S]*"score"[\s\S]*\}/);
          if (match) {
            const parsed = JSON.parse(match[0]);
            if (typeof parsed.score === 'number') {
              setExtractedFeedback({
                score: parsed.score,
                strength: parsed.strength || 'Clear ideas',
                improvement: parsed.improvement || 'Natural phrasing',
                example: parsed.example || '',
              });
              continue;
            }
          }
        } catch {
          // Ignore JSON parse errors
        }

        // 2. Fallback to spoken text pattern match (e.g., "7 out of 10")
        const spokenScoreMatch = msg.message.match(/(\d+)\s*out of\s*10/i);
        if (spokenScoreMatch) {
          const scoreNum = parseInt(spokenScoreMatch[1], 10);
          const lowerMsg = msg.message.toLowerCase();

          let strength = 'Clear ideas';
          if (lowerMsg.includes('ideas were clear') || lowerMsg.includes('clear ideas')) {
            strength = 'Clear ideas';
          } else if (lowerMsg.includes('clear and easy')) {
            strength = 'Clear delivery';
          } else if (lowerMsg.includes('structure')) {
            strength = 'Good structure';
          }

          let improvement = 'Natural phrasing';
          if (lowerMsg.includes('phrasing') || lowerMsg.includes('natural')) {
            improvement = 'Natural phrasing';
          } else if (lowerMsg.includes('filler')) {
            improvement = 'Reduce filler words';
          } else if (lowerMsg.includes('vocabulary')) {
            improvement = 'Varied vocabulary';
          }

          setExtractedFeedback({
            score: scoreNum,
            strength: strength,
            improvement: improvement,
          });
        }
      }
    }
  }, [messages]);

  // Determine current voice state label
  const currentStatus = voiceState || agentState || 'idle';

  const getStatusText = () => {
    if (isCallEnded) return 'Conversation ended';
    switch (currentStatus) {
      case 'connecting':
        return 'Connecting to BolBuddy...';
      case 'listening':
        return 'Listening to you';
      case 'thinking':
        return 'BolBuddy is thinking...';
      case 'speaking':
        return 'BolBuddy is speaking';
      default:
        return 'BolBuddy is ready';
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

  // Toggle microphone
  const toggleMicrophone = async () => {
    if (localParticipant) {
      await localParticipant.setMicrophoneEnabled(isMuted);
    }
  };

  // End conversation & show post-call feedback view
  const handleEndCall = () => {
    setIsCallEnded(true);
    session.end();
  };

  // Restart session
  const handleTryAgain = () => {
    setIsCallEnded(false);
    setExtractedFeedback(null);
    session.start();
  };

  // Return to home
  const handleBackHome = () => {
    session.end();
  };

  // Render Post-Call Feedback Card View
  if (isCallEnded) {
    return (
      <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-[#F8FAFC] p-6 text-slate-900">
        <FeedbackCard
          feedback={extractedFeedback}
          onTryAgain={handleTryAgain}
          onBackHome={handleBackHome}
        />
      </div>
    );
  }

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
            <p className="text-[11px] font-medium text-slate-500">Voice-First English Companion</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Voice State Badge */}
          <span
            className={cn(
              'flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold transition-all',
              getStatusBadgeColor()
            )}
          >
            <span className="size-2 animate-ping rounded-full bg-current" />
            <span>{getStatusText()}</span>
          </span>

          {/* Transcript Toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowTranscript(!showTranscript)}
            className="text-xs font-semibold text-slate-600 hover:text-slate-900"
          >
            <MessageSquare className="mr-1.5 size-4" />
            {showTranscript ? 'Hide Transcript' : 'Show Transcript'}
          </Button>

          {/* Memory Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowMemoryDrawer(true)}
            className="border-indigo-200 bg-indigo-50/50 text-xs font-semibold text-indigo-700 hover:bg-indigo-100/70 hover:text-indigo-900"
          >
            <Brain className="mr-1.5 size-4 text-indigo-600" />
            Memory
          </Button>
        </div>
      </header>

      {/* Main Voice Interaction Area */}
      <main className="relative mx-auto flex w-full max-w-4xl flex-1 flex-col items-center justify-center px-6 py-4">
        {/* Active Ticket Banner Card */}
        {activeTicketRef && (
          <motion.div
            initial={{ opacity: 0, y: -15 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 flex w-full max-w-md items-center justify-between gap-3 rounded-2xl border border-amber-200 bg-amber-50/90 px-4 py-3 shadow-sm backdrop-blur-md"
          >
            <div className="flex items-center gap-3">
              <div className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-amber-500/20 text-amber-700">
                <LifeBuoy className="size-5" />
              </div>
              <div className="text-left">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-slate-900">Support Request Created</span>
                  <span className="rounded bg-amber-200/80 px-1.5 py-0.5 text-[10px] font-extrabold text-amber-900">
                    {activeTicketRef}
                  </span>
                </div>
                <p className="text-[11px] font-medium text-slate-600">
                  A human teacher can review it through the support system. You can continue
                  practicing while you wait!
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Animated Voice Orb */}
        <div className="my-auto flex flex-col items-center justify-center space-y-6">
          <div className="relative flex items-center justify-center">
            {/* Ambient Glow */}
            <div
              className={cn(
                'absolute size-64 rounded-full opacity-50 blur-2xl transition-all duration-700 md:size-80',
                currentStatus === 'speaking' && 'bg-emerald-400/40',
                currentStatus === 'listening' && 'bg-purple-500/40',
                currentStatus === 'thinking' && 'bg-indigo-500/40',
                currentStatus === 'idle' && 'bg-indigo-300/30'
              )}
            />

            {/* Core Orb */}
            <div
              className={cn(
                'relative flex size-44 cursor-pointer items-center justify-center rounded-full bg-gradient-to-tr from-indigo-600 via-purple-600 to-indigo-800 shadow-2xl transition-all duration-500 md:size-56',
                currentStatus === 'listening' && 'scale-105 ring-4 ring-purple-500/30',
                currentStatus === 'thinking' && 'ring-4 ring-indigo-500/40',
                currentStatus === 'speaking' && 'scale-110 ring-8 ring-emerald-500/30'
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
                  {isMuted ? 'Muted' : getStatusText()}
                </span>
              </div>
            </div>
          </div>

          <p className="max-w-md text-center text-xs font-medium text-slate-500">
            {isMuted
              ? 'Microphone muted. Tap the orb to resume.'
              : 'Speak naturally in English or Hinglish. BolBuddy is listening!'}
          </p>
        </div>

        {/* Live Transcript Stream (Hidden by default) */}
        {showTranscript && messages.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 flex h-48 w-full max-w-2xl flex-col rounded-2xl border border-slate-200/80 bg-white/95 p-4 shadow-lg backdrop-blur-md md:h-56"
          >
            <div className="mb-2 flex items-center justify-between border-b border-slate-100 pb-2">
              <span className="flex items-center gap-1.5 text-xs font-bold text-slate-700">
                <MessageSquare className="size-3.5 text-indigo-600" />
                Live Conversation Transcript
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowTranscript(false)}
                className="h-6 text-[10px] text-slate-400 hover:text-slate-700"
              >
                Hide
              </Button>
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

      {/* Memory Control Drawer */}
      <MemoryPanel
        isOpen={showMemoryDrawer}
        memory={memory}
        onClose={() => setShowMemoryDrawer(false)}
        onMemoryCleared={() => setMemory(null)}
      />

      {/* Bottom Control Bar */}
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
          onClick={handleEndCall}
          className="flex cursor-pointer items-center gap-2 rounded-full bg-rose-600 px-6 text-xs font-bold text-white shadow-md hover:bg-rose-700"
        >
          <PhoneOff className="size-4" />
          <span>End Conversation</span>
        </Button>
      </footer>
    </div>
  );
}
