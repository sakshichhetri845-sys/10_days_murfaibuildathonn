'use client';

import React, { useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  Building2,
  ChevronDown,
  Heart,
  Leaf,
  MessageSquare,
  Mic,
  MicOff,
  PhoneCall,
  PhoneOff,
  Pill,
  ShieldCheck,
  Sparkles,
  TestTube,
  Thermometer,
  Volume2,
  VolumeX,
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

export function HealthSaathiSessionView() {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const { state: agentState } = useAgent();
  const { localParticipant } = useLocalParticipant();
  const { state: voiceState } = useVoiceAssistant();

  const [isMuted, setIsMuted] = useState(false);
  const [showTranscript, setShowTranscript] = useState(true);
  const [emergencyMode, setEmergencyMode] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Emergency keywords check
  const emergencyKeywords = [
    'chest pain',
    'difficulty breathing',
    'severe bleeding',
    'loss of consciousness',
    'stroke',
    'suicidal',
    'heart attack',
    'unconscious',
    'breathing problem',
    'heavy bleeding',
  ];

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

  // Auto scroll transcript and check for emergency keywords
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }

    // Check last messages for emergency keywords
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      const textContent =
        typeof lastMessage.message === 'string' ? lastMessage.message.toLowerCase() : '';

      const isEmergency = emergencyKeywords.some((keyword) => textContent.includes(keyword));
      if (isEmergency) {
        setEmergencyMode(true);
      }
    }
  }, [messages]);

  // Determine current active voice state
  const currentStatus = voiceState || agentState || 'idle';

  // Status text for voice state
  const getStatusText = () => {
    if (emergencyMode) {
      return '🚨 Emergency Mode Active • Seek Immediate Medical Care';
    }
    switch (currentStatus) {
      case 'listening':
        return 'Listening... Speak naturally in English or Hinglish';
      case 'thinking':
        return 'HealthSaathi is processing...';
      case 'speaking':
        return 'HealthSaathi is speaking...';
      default:
        return 'HealthSaathi is ready • Speak anytime';
    }
  };

  // Status badge styling
  const getStatusBadgeColor = () => {
    if (emergencyMode) {
      return 'bg-red-100 text-red-700 border-red-200';
    }
    switch (currentStatus) {
      case 'listening':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'thinking':
        return 'bg-teal-100 text-teal-700 border-teal-200';
      case 'speaking':
        return 'bg-emerald-100 text-emerald-700 border-emerald-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="flex min-h-screen flex-col justify-between bg-[#F8FAFC] font-sans text-slate-900 select-none">
      {/* Top Header Bar */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-200/80 bg-[#F8FAFC]/90 px-4 py-3.5 backdrop-blur-md sm:px-8">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-teal-600 text-white shadow-md shadow-blue-500/20">
            <Heart className="size-5 animate-pulse fill-white/20" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-extrabold text-slate-900">HealthSaathi</span>
              <span
                className={`rounded-full border px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase ${getStatusBadgeColor()}`}
              >
                {currentStatus}
              </span>
            </div>
            <p className="hidden text-xs text-slate-500 sm:block">
              AI Health Companion • Voice Session
            </p>
          </div>
        </div>

        {/* Top Controls */}
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowTranscript(!showTranscript)}
            className="rounded-full border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100"
          >
            <MessageSquare className="mr-1.5 size-3.5" />
            {showTranscript ? 'Hide Log' : 'Show Log'}
          </Button>

          <Button
            onClick={endCall}
            size="sm"
            className="flex items-center gap-1.5 rounded-full bg-red-500 px-4 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-red-600"
          >
            <PhoneOff className="size-3.5" />
            <span>End Session</span>
          </Button>
        </div>
      </header>

      {/* Main Voice Interface Area */}
      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col justify-between gap-6 px-4 py-6 sm:px-6">
        {/* Emergency Mode Card (Subtle Red Accents, No Panic) */}
        <AnimatePresence>
          {emergencyMode && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-3 rounded-2xl border border-red-200/90 bg-red-50/90 p-4 text-red-900 shadow-sm sm:p-5"
            >
              <div className="flex items-start gap-3">
                <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-red-100 text-red-600">
                  <AlertTriangle className="size-5" />
                </div>
                <div className="space-y-1">
                  <h3 className="flex items-center gap-2 text-sm font-extrabold text-red-900">
                    <span>🚨 Immediate Medical Attention May Be Required</span>
                  </h3>
                  <p className="text-xs leading-relaxed text-red-800">
                    If you or someone nearby is experiencing chest pain, difficulty breathing,
                    severe bleeding, loss of consciousness, or stroke symptoms, please contact local
                    emergency services immediately or visit the nearest hospital emergency room.
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3 border-t border-red-200/60 pt-1">
                <a
                  href="tel:108"
                  className="inline-flex items-center gap-2 rounded-xl bg-red-600 px-4 py-2 text-xs font-bold text-white shadow-sm transition-colors hover:bg-red-700"
                >
                  <PhoneCall className="size-4" />
                  <span>Call Emergency Ambulance (108)</span>
                </a>
                <button
                  onClick={() => setEmergencyMode(false)}
                  className="rounded-lg px-3 py-1.5 text-xs font-semibold text-red-700 transition-colors hover:bg-red-100/60 hover:text-red-900"
                >
                  Dismiss Warning
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Centered Voice Orb Container */}
        <div className="relative flex min-h-[260px] flex-1 flex-col items-center justify-center">
          {/* Animated Voice Orb with States */}
          <div className="relative flex size-64 items-center justify-center sm:size-72">
            {/* Listening State: Soft Blue Pulsing Rings */}
            {currentStatus === 'listening' && (
              <>
                <motion.div
                  animate={{ scale: [1, 1.3, 1], opacity: [0.4, 0.8, 0.4] }}
                  transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                  className="absolute inset-0 rounded-full bg-blue-500/20 blur-xl"
                />
                <motion.div
                  animate={{ scale: [1.1, 1.4, 1.1], opacity: [0.2, 0.5, 0.2] }}
                  transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut', delay: 0.3 }}
                  className="absolute inset-0 rounded-full bg-blue-600/15 blur-2xl"
                />
              </>
            )}

            {/* Thinking State: Gentle Breathing & Rotating Ring */}
            {currentStatus === 'thinking' && (
              <>
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
                  className="absolute inset-0 rounded-full border-2 border-dashed border-teal-500/50"
                />
                <motion.div
                  animate={{ scale: [1, 1.1, 1], opacity: [0.5, 0.9, 0.5] }}
                  transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
                  className="absolute inset-0 rounded-full bg-teal-500/20 blur-xl"
                />
              </>
            )}

            {/* Speaking State: Animated Waveform Glowing Pulsing Rings */}
            {currentStatus === 'speaking' && (
              <>
                <motion.div
                  animate={{ scale: [1, 1.25, 1], opacity: [0.5, 0.9, 0.5] }}
                  transition={{ duration: 1.2, repeat: Infinity, ease: 'easeInOut' }}
                  className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-500/30 via-teal-400/30 to-emerald-400/30 blur-2xl"
                />

                {/* Waveform Bar Circles */}
                <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center gap-1.5">
                  {[0.4, 0.9, 0.6, 1.0, 0.7, 0.5, 0.8].map((h, i) => (
                    <motion.div
                      key={i}
                      animate={{ height: [12, 48 * h, 12] }}
                      transition={{ duration: 0.8 + i * 0.1, repeat: Infinity, ease: 'easeInOut' }}
                      className="w-1.5 rounded-full bg-white/90 shadow-xs"
                    />
                  ))}
                </div>
              </>
            )}

            {/* Core Orb Body */}
            <motion.div
              animate={{
                scale: currentStatus === 'speaking' ? [1, 1.05, 1] : [1, 1.03, 1],
              }}
              transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
              className={`relative flex size-48 items-center justify-center rounded-full p-1 shadow-2xl transition-colors duration-500 sm:size-56 ${
                emergencyMode
                  ? 'bg-gradient-to-br from-red-500 via-rose-600 to-amber-600 shadow-red-500/30'
                  : currentStatus === 'speaking'
                    ? 'bg-gradient-to-br from-emerald-500 via-teal-600 to-blue-600 shadow-emerald-500/30'
                    : currentStatus === 'listening'
                      ? 'bg-gradient-to-br from-blue-600 via-indigo-600 to-teal-500 shadow-blue-500/35'
                      : 'bg-gradient-to-br from-blue-600 via-blue-700 to-teal-600 shadow-blue-500/25'
              }`}
            >
              <div className="relative flex size-full flex-col items-center justify-center overflow-hidden rounded-full bg-slate-900/90 p-4 text-white backdrop-blur-md">
                <Heart
                  className={`mb-2 size-10 animate-pulse ${emergencyMode ? 'text-red-400' : 'text-blue-400'}`}
                />
                <span className="text-sm font-extrabold tracking-wide text-white">
                  HealthSaathi
                </span>
                <span className="mt-0.5 text-[11px] font-medium text-slate-300">
                  {currentStatus.toUpperCase()}
                </span>
              </div>
            </motion.div>
          </div>

          {/* Status Indicator Pill */}
          <div className="mt-4 flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-1.5 shadow-xs">
            <span
              className={`size-2.5 rounded-full ${
                emergencyMode
                  ? 'animate-ping bg-red-500'
                  : currentStatus === 'listening'
                    ? 'animate-pulse bg-blue-500'
                    : currentStatus === 'speaking'
                      ? 'animate-pulse bg-emerald-500'
                      : 'bg-teal-500'
              }`}
            />
            <span className="text-xs font-semibold text-slate-700">{getStatusText()}</span>
          </div>
        </div>

        {/* Transcript Area */}
        {showTranscript && (
          <div className="flex max-h-[240px] flex-col gap-3 rounded-3xl border border-slate-200/80 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <span className="flex items-center gap-1.5 text-xs font-bold text-slate-700">
                <MessageSquare className="size-3.5 text-blue-600" /> Live Conversation Transcript
              </span>
              <span className="text-[10px] font-medium text-slate-600">Voice Optimized</span>
            </div>

            <div
              ref={scrollAreaRef}
              className="scrollbar-thin scrollbar-thumb-slate-200 flex-1 space-y-3 overflow-y-auto pr-2"
            >
              {messages.length === 0 ? (
                <div className="space-y-1 py-6 text-center text-xs text-slate-600">
                  <p className="font-semibold text-slate-600">
                    &quot;Hi! I&apos;m HealthSaathi, your AI health companion.&quot;
                  </p>
                  <p>Start speaking naturally about your health concern or question.</p>
                </div>
              ) : (
                messages.map((msg, idx) => {
                  const isUser = msg.from?.isLocal;
                  const text = typeof msg.message === 'string' ? msg.message : '';

                  return (
                    <div
                      key={idx}
                      className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
                    >
                      <span className="mb-0.5 px-1 text-[10px] font-bold text-slate-600">
                        {isUser ? 'You' : 'HealthSaathi'}
                      </span>
                      <div
                        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-xs leading-relaxed font-medium ${
                          isUser
                            ? 'rounded-br-none bg-blue-600 text-white shadow-xs'
                            : 'rounded-bl-none border border-slate-200/60 bg-slate-100 text-slate-800'
                        }`}
                      >
                        {text}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}

        {/* Quick Context Prompt Starters Bar during call */}
        <div className="scrollbar-none flex items-center gap-2 overflow-x-auto pb-1">
          <span className="shrink-0 text-[11px] font-bold text-slate-600">Quick Ask:</span>
          <button
            onClick={() => setEmergencyMode(true)}
            className="shrink-0 rounded-full border border-red-200 bg-red-50 px-3 py-1 text-[11px] font-semibold text-red-700 transition-colors hover:bg-red-100"
          >
            🚨 Emergency Symptoms
          </button>
          <button
            onClick={() => {}}
            className="shrink-0 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-[11px] font-semibold text-blue-700 transition-colors hover:bg-blue-100"
          >
            🤒 Fever &amp; Cold
          </button>
          <button
            onClick={() => {}}
            className="shrink-0 rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-[11px] font-semibold text-teal-700 transition-colors hover:bg-teal-100"
          >
            🧪 Blood Test Info
          </button>
          <button
            onClick={() => {}}
            className="shrink-0 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-[11px] font-semibold text-emerald-700 transition-colors hover:bg-emerald-100"
          >
            🏥 Doctor Questions
          </button>
        </div>

        {/* Trust Card Disclaimer Footer */}
        <div className="flex items-center justify-between rounded-xl border border-blue-200/70 bg-blue-50/70 p-3 text-xs text-blue-900">
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-4 shrink-0 text-blue-600" />
            <p className="text-[11px] font-medium">
              HealthSaathi provides educational health information. It does not replace qualified
              healthcare professionals.
            </p>
          </div>
        </div>

        {/* Bottom Call Controls Bar */}
        <div className="flex items-center justify-center gap-4 py-2">
          <Button
            onClick={toggleMicrophone}
            size="lg"
            className={`flex size-14 items-center justify-center rounded-full shadow-md transition-all ${
              isMuted
                ? 'bg-amber-500 text-white hover:bg-amber-600'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {isMuted ? <MicOff className="size-6" /> : <Mic className="size-6 animate-pulse" />}
          </Button>

          <Button
            onClick={endCall}
            size="lg"
            className="flex size-14 items-center justify-center rounded-full bg-red-600 text-white shadow-md transition-all hover:bg-red-700"
          >
            <PhoneOff className="size-6" />
          </Button>
        </div>
      </main>
    </div>
  );
}
