'use client';

import React, { useEffect, useRef, useState } from 'react';
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Heart,
  MessageSquare,
  Mic,
  MicOff,
  PhoneOff,
} from 'lucide-react';
import { motion } from 'motion/react';
import {
  useAgent,
  useLocalParticipant,
  useSessionContext,
  useSessionMessages,
  useVoiceAssistant,
} from '@livekit/components-react';
import { Button } from '@/components/ui/button';

interface HealthSaathiSessionViewProps {
  onBackToLanding?: () => void;
}

export function HealthSaathiSessionView({ onBackToLanding }: HealthSaathiSessionViewProps) {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const { state: agentState } = useAgent();
  const { localParticipant } = useLocalParticipant();
  const { state: voiceState } = useVoiceAssistant();

  const [isMuted, setIsMuted] = useState(false);
  const [showTranscript, setShowTranscript] = useState(true);
  const [callEndedState, setCallEndedState] = useState(false);
  const [micErrorState, setMicErrorState] = useState(false);
  const [connErrorState, setConnErrorState] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Check microphone permissions
  const checkMicPermissions = async () => {
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        setMicErrorState(false);
      }
    } catch (err) {
      console.warn('Microphone permission error:', err);
      setMicErrorState(true);
    }
  };

  useEffect(() => {
    checkMicPermissions();
  }, []);

  // Handle call termination
  const handleEndCall = () => {
    try {
      session.end();
    } catch (e) {
      console.warn('Error ending session:', e);
    }
    setCallEndedState(true);
  };

  const handleRestartCall = async () => {
    setCallEndedState(false);
    setConnErrorState(false);
    try {
      await session.start();
    } catch (e) {
      console.error('Failed to restart session:', e);
      setConnErrorState(true);
    }
  };

  // Toggle mic
  const toggleMicrophone = async () => {
    if (localParticipant) {
      try {
        const enabled = localParticipant.isMicrophoneEnabled;
        await localParticipant.setMicrophoneEnabled(!enabled);
        setIsMuted(enabled);
      } catch (err) {
        console.warn('Mic toggle failed:', err);
        setMicErrorState(true);
      }
    }
  };

  // Auto-scroll transcript
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  // Determine actual connection / voice state
  const isConnecting = !session.isConnected && !callEndedState && !connErrorState && !micErrorState;

  const currentStatus = voiceState || agentState || 'ready';

  // Render CALL ENDED state
  if (callEndedState) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-[#F0F7FF] via-[#F4F9F8] to-[#FFFFFF] px-4 font-sans text-slate-800">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md space-y-6 rounded-3xl border border-teal-100 bg-white p-8 text-center shadow-xl shadow-teal-900/5"
        >
          <div className="mx-auto flex size-16 items-center justify-center rounded-3xl border border-teal-100 bg-teal-50 text-teal-700">
            <Activity className="size-8 text-teal-600" />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-extrabold text-slate-900">Conversation ended.</h2>
            <p className="text-sm leading-relaxed text-slate-600">
              We hope the conversation helped you understand things a little more clearly.
            </p>
          </div>

          <div className="flex flex-col gap-3 pt-2">
            <Button
              onClick={handleRestartCall}
              className="w-full rounded-2xl bg-teal-700 py-3.5 text-base font-bold text-white shadow-md shadow-teal-700/20 hover:bg-teal-800"
            >
              Talk Again
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                if (onBackToLanding) onBackToLanding();
                else handleRestartCall();
              }}
              className="w-full rounded-2xl border-slate-200 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Back to HealthSaathi
            </Button>
          </div>
        </motion.div>
      </div>
    );
  }

  // Render MICROPHONE ERROR state
  if (micErrorState) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-[#F0F7FF] via-[#F4F9F8] to-[#FFFFFF] px-4 font-sans text-slate-800">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md space-y-6 rounded-3xl border border-amber-200/80 bg-white p-8 text-center shadow-xl"
        >
          <div className="mx-auto flex size-16 items-center justify-center rounded-3xl border border-amber-100 bg-amber-50 text-amber-600">
            <MicOff className="size-8 text-amber-600" />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-extrabold text-slate-900">Microphone access is needed.</h2>
            <p className="text-sm leading-relaxed text-slate-600">
              HealthSaathi needs access to your microphone so it can hear you.
            </p>
            <p className="pt-1 text-xs text-slate-500">
              Please allow microphone access in your browser settings and try again.
            </p>
          </div>

          <Button
            onClick={() => {
              setMicErrorState(false);
              checkMicPermissions();
            }}
            className="w-full rounded-2xl bg-teal-700 py-3.5 text-base font-bold text-white shadow-md hover:bg-teal-800"
          >
            Try Again
          </Button>
        </motion.div>
      </div>
    );
  }

  // Render CONNECTION ERROR state
  if (connErrorState) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-[#F0F7FF] via-[#F4F9F8] to-[#FFFFFF] px-4 font-sans text-slate-800">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md space-y-6 rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-xl"
        >
          <div className="mx-auto flex size-16 items-center justify-center rounded-3xl border border-sky-100 bg-sky-50 text-sky-700">
            <AlertCircle className="size-8 text-sky-600" />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-extrabold text-slate-900">
              Couldn&apos;t connect to HealthSaathi.
            </h2>
            <p className="text-sm leading-relaxed text-slate-600">
              Please check your internet connection and try again.
            </p>
          </div>

          <Button
            onClick={handleRestartCall}
            className="w-full rounded-2xl bg-teal-700 py-3.5 text-base font-bold text-white shadow-md hover:bg-teal-800"
          >
            Try Again
          </Button>
        </motion.div>
      </div>
    );
  }

  // Render CONNECTING state
  if (isConnecting) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-[#F0F7FF] via-[#ECFDF5] to-[#FFFFFF] px-4 font-sans text-slate-800">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-md space-y-6 rounded-3xl border border-teal-100 bg-white/90 p-8 text-center shadow-xl backdrop-blur-sm"
        >
          {/* Calm Loading Wave Ring Animation */}
          <div className="relative mx-auto flex size-24 items-center justify-center">
            <motion.div
              animate={{ scale: [1, 1.25, 1], opacity: [0.3, 0.7, 0.3] }}
              transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
              className="absolute inset-0 rounded-full bg-teal-200/60 blur-md"
            />
            <div className="relative flex size-16 items-center justify-center rounded-2xl bg-teal-700 text-white shadow-md">
              <Activity className="size-8 animate-pulse text-white" />
            </div>
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-extrabold text-slate-900">
              Connecting to HealthSaathi...
            </h2>
            <p className="text-sm font-medium text-slate-500">Please wait a moment.</p>
          </div>
        </motion.div>
      </div>
    );
  }

  // ACTIVE VOICE INTERFACE (READY, LISTENING, SPEAKING)
  return (
    <div className="flex min-h-screen flex-col justify-between bg-gradient-to-b from-[#F0F7FF] via-[#F4F9F8] to-[#FFFFFF] font-sans text-slate-800 select-none">
      {/* Top Bar */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-teal-100/70 bg-[#F0F7FF]/85 px-4 py-3.5 backdrop-blur-md sm:px-8">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-600 to-sky-600 text-white shadow-sm">
            <Activity className="size-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-slate-900">HealthSaathi</span>
              <span className="rounded-full border border-teal-100 bg-teal-50 px-2.5 py-0.5 text-[11px] font-bold text-teal-700 uppercase">
                Voice Session
              </span>
            </div>
            <p className="hidden text-xs text-slate-500 sm:block">
              Clear health information • Natural conversation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowTranscript(!showTranscript)}
            className="rounded-full border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            <MessageSquare className="mr-1.5 size-3.5 text-teal-600" />
            {showTranscript ? 'Hide Transcript' : 'Show Transcript'}
          </Button>

          <Button
            onClick={handleEndCall}
            size="sm"
            className="flex items-center gap-1.5 rounded-full bg-slate-900 px-4 py-1.5 text-xs font-semibold text-white shadow-sm transition-colors hover:bg-red-700"
          >
            <PhoneOff className="size-3.5" />
            <span>End Session</span>
          </Button>
        </div>
      </header>

      {/* Main Container */}
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-between gap-6 px-4 py-6 sm:px-6">
        {/* Soft Health Conversation Panel */}
        <div className="relative flex flex-1 flex-col items-center justify-center py-6">
          <div className="w-full max-w-lg space-y-6 rounded-3xl border border-teal-100/90 bg-white/90 p-8 text-center shadow-xl shadow-teal-900/5 backdrop-blur-sm">
            {/* Header Emblem */}
            <div className="mx-auto flex size-14 items-center justify-center rounded-2xl border border-teal-100 bg-teal-50 text-teal-700">
              <Heart className="size-7 fill-teal-600/20 text-teal-600" />
            </div>

            {/* Dynamic State Headlines & Text Labels */}
            {currentStatus === 'speaking' ? (
              <div className="space-y-2">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">
                  <span className="size-2 animate-pulse rounded-full bg-emerald-500" />
                  HealthSaathi is speaking...
                </span>
                <h2 className="text-2xl font-extrabold text-slate-900">
                  Explaining in simple words...
                </h2>
              </div>
            ) : currentStatus === 'listening' ? (
              <div className="space-y-2">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-sky-100 bg-sky-50 px-3 py-1 text-xs font-bold text-sky-700">
                  <span className="size-2 animate-pulse rounded-full bg-sky-500" />
                  Listening...
                </span>
                <h2 className="text-2xl font-extrabold text-slate-900">
                  Take your time. Tell me what&apos;s on your mind.
                </h2>
              </div>
            ) : (
              <div className="space-y-2">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-teal-100 bg-teal-50 px-3 py-1 text-xs font-bold text-teal-700">
                  <CheckCircle2 className="size-3.5 text-teal-600" />
                  Ready
                </span>
                <h2 className="text-2xl font-extrabold text-slate-900">
                  How can I help you understand your health today?
                </h2>
                <p className="text-xs text-slate-500">
                  Talk naturally. You can speak in English, Hindi, or a mix of both.
                </p>
              </div>
            )}

            {/* Audio Indicator Visualiser */}
            <div className="flex items-center justify-center gap-2 py-4">
              {currentStatus === 'speaking' ? (
                <div className="flex items-center gap-1.5">
                  {[0.5, 1, 0.7, 1.2, 0.6, 0.9, 0.4].map((h, i) => (
                    <motion.div
                      key={i}
                      animate={{ height: [12, 36 * h, 12] }}
                      transition={{ duration: 0.7 + i * 0.1, repeat: Infinity, ease: 'easeInOut' }}
                      className="w-1.5 rounded-full bg-teal-600"
                    />
                  ))}
                </div>
              ) : currentStatus === 'listening' ? (
                <div className="flex items-center gap-2">
                  <motion.div
                    animate={{ scale: [1, 1.2, 1], opacity: [0.4, 0.8, 0.4] }}
                    transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
                    className="flex size-12 items-center justify-center rounded-full bg-sky-100 text-sky-600"
                  >
                    <Mic className="size-6" />
                  </motion.div>
                </div>
              ) : (
                <div className="flex items-center justify-center pt-2">
                  <Button
                    onClick={toggleMicrophone}
                    className="rounded-full bg-teal-700 px-6 py-2.5 text-sm font-bold text-white shadow-md hover:bg-teal-800"
                  >
                    Start Talking
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Live Transcript Log */}
        {showTranscript && (
          <div className="flex max-h-[220px] flex-col gap-3 rounded-3xl border border-teal-100 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <span className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                <MessageSquare className="size-3.5 text-teal-600" /> Live Transcript
              </span>
              <span className="text-[10px] font-medium text-slate-500">
                English / Hindi Code-mixing
              </span>
            </div>

            <div
              ref={scrollAreaRef}
              className="scrollbar-thin scrollbar-thumb-slate-200 flex-1 space-y-3 overflow-y-auto pr-2"
            >
              {messages.length === 0 ? (
                <div className="py-4 text-center text-xs text-slate-500">
                  <p className="font-semibold text-slate-700">
                    &quot;Namaste! I&apos;m HealthSaathi.&quot;
                  </p>
                  <p className="mt-0.5">
                    Start speaking about your health concern or doctor visit preparation.
                  </p>
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
                      <span className="mb-0.5 px-1 text-[10px] font-bold text-slate-500">
                        {isUser ? 'You' : 'HealthSaathi'}
                      </span>
                      <div
                        className={`max-w-[85%] rounded-2xl px-4 py-2 text-xs leading-relaxed font-medium ${
                          isUser
                            ? 'rounded-br-none bg-teal-700 text-white'
                            : 'rounded-bl-none border border-teal-100 bg-teal-50/60 text-slate-800'
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

        {/* Trust Reminder */}
        <div className="flex items-center justify-center rounded-2xl border border-teal-100 bg-teal-50/60 p-3 text-center text-xs text-teal-900">
          <p className="text-[11px] font-medium">
            HealthSaathi provides general educational information. It does not replace qualified
            healthcare professionals.
          </p>
        </div>

        {/* Bottom Call Controls */}
        <div className="flex items-center justify-center gap-4 py-2">
          <Button
            onClick={toggleMicrophone}
            size="lg"
            className={`flex size-14 items-center justify-center rounded-full shadow-md transition-all ${
              isMuted
                ? 'bg-amber-500 text-white hover:bg-amber-600'
                : 'bg-teal-700 text-white hover:bg-teal-800'
            }`}
            aria-label={isMuted ? 'Unmute microphone' : 'Mute microphone'}
          >
            {isMuted ? <MicOff className="size-6" /> : <Mic className="size-6" />}
          </Button>

          <Button
            onClick={handleEndCall}
            size="lg"
            className="flex size-14 items-center justify-center rounded-full bg-slate-900 text-white shadow-md transition-colors hover:bg-red-700"
            aria-label="End session"
          >
            <PhoneOff className="size-6" />
          </Button>
        </div>
      </main>
    </div>
  );
}
