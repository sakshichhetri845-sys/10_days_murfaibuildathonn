'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Brain, Heart, LifeBuoy, Mic, MicOff, PhoneOff, ScrollText } from 'lucide-react';
import { motion } from 'motion/react';
import {
  useAgent,
  useLocalParticipant,
  useRoomContext,
  useSessionContext,
  useSessionMessages,
  useVoiceAssistant,
} from '@livekit/components-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/shadcn/utils';
import { MemoryPanel, UserMemoryData } from './memory-panel';

const VOICE_STATE_CONFIG: Record<
  string,
  { label: string; color: string; ring: string; pulse: boolean }
> = {
  disconnected: {
    label: 'Connecting…',
    color: 'text-slate-500',
    ring: 'ring-slate-200',
    pulse: false,
  },
  connecting: {
    label: 'Connecting…',
    color: 'text-teal-500',
    ring: 'ring-teal-200',
    pulse: true,
  },
  initializing: {
    label: 'Starting HealthSathi…',
    color: 'text-teal-500',
    ring: 'ring-teal-200',
    pulse: true,
  },
  idle: {
    label: 'HealthSathi Ready • Listening',
    color: 'text-emerald-600',
    ring: 'ring-emerald-300',
    pulse: true,
  },
  ready: {
    label: 'HealthSathi Ready • Listening',
    color: 'text-emerald-600',
    ring: 'ring-emerald-300',
    pulse: true,
  },
  listening: {
    label: 'Listening…',
    color: 'text-emerald-600',
    ring: 'ring-emerald-300',
    pulse: true,
  },
  thinking: {
    label: 'Thinking…',
    color: 'text-amber-600',
    ring: 'ring-amber-300',
    pulse: true,
  },
  speaking: {
    label: 'HealthSathi is speaking',
    color: 'text-teal-600',
    ring: 'ring-teal-400',
    pulse: true,
  },
};

export function HealthSathiSessionView() {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const { state: agentState } = useAgent();
  const { localParticipant } = useLocalParticipant();
  const { state: voiceState } = useVoiceAssistant();
  const isMuted = localParticipant ? !localParticipant.isMicrophoneEnabled : false;

  const [showTranscript, setShowTranscript] = useState(false);
  const [showMemoryDrawer, setShowMemoryDrawer] = useState(false);
  const [memory, setMemory] = useState<UserMemoryData | null>(null);
  const [activeTicketRef, setActiveTicketRef] = useState<string | null>(null);

  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (showTranscript && scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages, showTranscript]);

  // Parse escalation reference IDs from messages
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

  const rawVoiceState = String(
    voiceState ?? agentState ?? (session.isConnected ? 'idle' : 'disconnected')
  );
  let stateKey = Object.keys(VOICE_STATE_CONFIG).find((k) =>
    rawVoiceState.toLowerCase().includes(k)
  );

  if (!stateKey) {
    stateKey = session.isConnected ? 'idle' : 'disconnected';
  }

  const {
    label: stateLabel,
    color: stateColor,
    ring: stateRing,
    pulse: statePulse,
  } = VOICE_STATE_CONFIG[stateKey];

  const handleToggleMute = async () => {
    if (!localParticipant) return;
    try {
      await localParticipant.setMicrophoneEnabled(isMuted);
    } catch (e) {
      console.warn('Mute toggle error:', e);
    }
  };

  const room = useRoomContext();

  const handleEndCall = () => {
    try {
      const sessEnd = (session as unknown as { end?: () => void })?.end;
      if (typeof sessEnd === 'function') {
        sessEnd();
      }
    } catch (e) {
      console.warn('Session end warning:', e);
    }
    try {
      if (room && typeof room.disconnect === 'function') {
        room.disconnect();
      }
    } catch (e) {
      console.warn('Room disconnect warning:', e);
    }
  };

  const lastAgentMessage = [...messages].reverse().find((m) => !m.from?.isLocal)?.message ?? null;

  return (
    <div className="flex min-h-screen flex-col bg-[#F0FAFA] font-sans text-slate-900">
      {/* Header */}
      <header className="sticky top-0 z-30 border-b border-teal-100/80 bg-[#F0FAFA]/90 px-4 py-4 backdrop-blur-md sm:px-8">
        <div className="mx-auto flex max-w-3xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-teal-500 to-emerald-600 text-white shadow-md shadow-teal-500/30">
              <Heart className="size-4 text-white" />
            </div>
            <div>
              <span className="text-base font-extrabold tracking-tight text-slate-900">
                HealthSathi
              </span>
              <p className="text-[10px] font-medium text-teal-600">Active Session</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {activeTicketRef && (
              <div className="flex items-center gap-1.5 rounded-full border border-rose-200 bg-rose-50 px-3 py-1 text-xs font-bold text-rose-700">
                <LifeBuoy className="size-3.5 text-rose-500" />
                <span>{activeTicketRef}</span>
              </div>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowMemoryDrawer(true)}
              className="rounded-full border-teal-200 bg-teal-50/70 text-xs font-bold text-teal-700 hover:bg-teal-100"
            >
              <Brain className="mr-1.5 size-4 text-teal-600" />
              Memory
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowTranscript(!showTranscript)}
              className={cn(
                'rounded-full text-xs font-bold',
                showTranscript
                  ? 'border-slate-300 bg-slate-100 text-slate-700'
                  : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
              )}
            >
              <ScrollText className="mr-1.5 size-4" />
              Transcript
            </Button>
          </div>
        </div>
      </header>

      <MemoryPanel
        isOpen={showMemoryDrawer}
        memory={memory}
        onClose={() => setShowMemoryDrawer(false)}
        onMemoryCleared={() => setMemory(null)}
      />

      {/* Main session content */}
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8 sm:px-8">
        {/* Voice State Orb */}
        <motion.div
          className="flex flex-col items-center gap-6"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {/* Animated Orb */}
          <div className="relative flex items-center justify-center">
            {statePulse && (
              <motion.div
                className={cn('absolute size-32 rounded-full opacity-20', stateRing, 'ring-4')}
                animate={{ scale: [1, 1.15, 1] }}
                transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
              />
            )}
            <div
              className={cn(
                'flex size-28 items-center justify-center rounded-full shadow-xl transition-all duration-500',
                stateKey === 'listening' && 'bg-gradient-to-br from-emerald-400 to-teal-500',
                stateKey === 'speaking' && 'bg-gradient-to-br from-teal-400 to-cyan-500',
                stateKey === 'thinking' && 'bg-gradient-to-br from-amber-400 to-orange-400',
                (stateKey === 'connecting' || stateKey === 'initializing') &&
                  'bg-gradient-to-br from-teal-300 to-emerald-400',
                stateKey === 'disconnected' && 'bg-gradient-to-br from-slate-300 to-slate-400'
              )}
            >
              <Heart className="size-12 text-white drop-shadow" />
            </div>
          </div>

          {/* State Label */}
          <div className="text-center">
            <p className={cn('text-lg font-bold', stateColor)}>{stateLabel}</p>
            {lastAgentMessage && (
              <motion.p
                key={lastAgentMessage}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="mx-auto mt-2 max-w-sm text-center text-sm text-slate-600"
              >
                &ldquo;{lastAgentMessage}&rdquo;
              </motion.p>
            )}
          </div>

          {/* Call Controls */}
          <div className="flex items-center gap-4">
            <Button
              onClick={handleToggleMute}
              size="lg"
              variant="outline"
              className={cn(
                'size-14 rounded-full border-2 transition-all',
                isMuted
                  ? 'border-rose-300 bg-rose-50 text-rose-600 hover:bg-rose-100'
                  : 'border-teal-200 bg-teal-50 text-teal-600 hover:bg-teal-100'
              )}
            >
              {isMuted ? <MicOff className="size-6" /> : <Mic className="size-6" />}
            </Button>

            <Button
              onClick={handleEndCall}
              size="lg"
              className="size-16 rounded-full bg-rose-500 text-white shadow-lg shadow-rose-500/30 hover:bg-rose-600"
            >
              <PhoneOff className="size-7" />
            </Button>
          </div>

          {isMuted && (
            <p className="text-xs font-semibold text-rose-500">
              🎤 Microphone muted — tap to unmute
            </p>
          )}
        </motion.div>

        {/* Transcript */}
        {showTranscript && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <p className="text-xs font-bold tracking-wider text-slate-400 uppercase">
              Conversation
            </p>
            <div ref={scrollAreaRef} className="flex max-h-72 flex-col gap-2 overflow-y-auto pr-1">
              {messages.length === 0 && (
                <p className="text-center text-xs text-slate-400">
                  Your conversation will appear here.
                </p>
              )}
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={cn(
                    'max-w-[80%] rounded-xl px-3 py-2 text-sm',
                    msg.from?.isLocal
                      ? 'self-end bg-teal-600 text-white'
                      : 'self-start bg-slate-100 text-slate-800'
                  )}
                >
                  {msg.message}
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Health Safety Reminder */}
        <div className="rounded-2xl border border-teal-100 bg-teal-50/60 p-4 text-center text-xs text-teal-700">
          🏥 For medical emergencies, call <span className="font-bold text-rose-600">112</span> or
          visit your nearest hospital. HealthSathi is a voice companion, not a medical provider.
        </div>
      </main>
    </div>
  );
}
