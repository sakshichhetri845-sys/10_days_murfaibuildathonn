'use client';

import React, { useState } from 'react';
import {
  Activity,
  ArrowRight,
  Bell,
  BookOpen,
  Building2,
  CheckCircle2,
  ChevronDown,
  Clock,
  Heart,
  Info,
  Leaf,
  MapPin,
  MessageCircle,
  PhoneCall,
  Pill,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  Sun,
  TestTube,
  Thermometer,
  Users,
} from 'lucide-react';
import { motion } from 'motion/react';
import { Button } from '@/components/ui/button';

interface WelcomeViewProps {
  startButtonText?: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText = '🎙 Talk to HealthSaathi',
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);

  // Conversation Starter Cards
  const conversationStarters = [
    {
      id: 'symptom',
      emoji: '🤒',
      icon: Thermometer,
      title: 'Understand a symptom',
      description: 'Explain what your symptoms might mean in simple terms before seeing a doctor.',
      badge: 'Symptom Help',
      bgGradient: 'from-amber-500/10 to-orange-500/10 border-amber-200/60 text-amber-900',
      iconBg: 'bg-amber-100 text-amber-600',
    },
    {
      id: 'medicine',
      emoji: '💊',
      icon: Pill,
      title: 'Medicine information',
      description: 'Understand prescription usage, timing, and dosage instructions safely.',
      badge: 'Prescriptions',
      bgGradient: 'from-blue-500/10 to-indigo-500/10 border-blue-200/60 text-blue-900',
      iconBg: 'bg-blue-100 text-blue-600',
    },
    {
      id: 'doctor',
      emoji: '🏥',
      icon: Building2,
      title: 'Prepare for a doctor visit',
      description: 'Organize your questions and symptom notes for your next clinic appointment.',
      badge: 'Doctor Prep',
      bgGradient: 'from-teal-500/10 to-emerald-500/10 border-teal-200/60 text-teal-900',
      iconBg: 'bg-teal-100 text-teal-600',
    },
    {
      id: 'test',
      emoji: '🧪',
      icon: TestTube,
      title: 'Understand a medical test',
      description: 'Learn what common blood tests, X-rays, or lab scans check for in plain words.',
      badge: 'Lab Tests',
      bgGradient: 'from-purple-500/10 to-violet-500/10 border-purple-200/60 text-purple-900',
      iconBg: 'bg-purple-100 text-purple-600',
    },
    {
      id: 'habits',
      emoji: '🌿',
      icon: Leaf,
      title: 'Healthy habits',
      description:
        'Discover practical advice on diet, hydration, exercise, and preventive wellness.',
      badge: 'Wellness',
      bgGradient: 'from-emerald-500/10 to-green-500/10 border-emerald-200/60 text-emerald-900',
      iconBg: 'bg-emerald-100 text-emerald-600',
    },
  ];

  // Future Ready Feature Cards
  const futureFeatures = [
    {
      icon: Clock,
      title: 'Conversation History',
      description: 'Review past voice summaries and doctor visit preparation notes anytime.',
      badge: 'Coming Soon',
    },
    {
      icon: BookOpen,
      title: 'Health Journal',
      description: 'Track daily symptoms, mood, and vital wellness milestones over time.',
      badge: 'Coming Soon',
    },
    {
      icon: Sun,
      title: 'Daily Wellness Tips',
      description: 'Receive personalized preventive health and nutrition advice every morning.',
      badge: 'Coming Soon',
    },
    {
      icon: Bell,
      title: 'Medication Reminder',
      description: 'Gentle voice & push alerts for scheduled daily doctor prescriptions.',
      badge: 'Coming Soon',
    },
    {
      icon: MapPin,
      title: 'Nearby Healthcare Resources',
      description:
        'Locate verified local primary health centers, clinics, and government hospitals.',
      badge: 'Coming Soon',
    },
    {
      icon: Users,
      title: 'Family Profiles',
      description: 'Manage health guidance and visit notes for elderly parents and family members.',
      badge: 'Coming Soon',
    },
  ];

  const handleStarterClick = (id: string) => {
    setSelectedTopic(id);
    onStartCall();
  };

  return (
    <div
      ref={ref}
      className="flex min-h-screen flex-col justify-between bg-[#F8FAFC] font-sans text-slate-900 selection:bg-blue-100 selection:text-blue-900"
    >
      {/* Minimal Header */}
      <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-[#F8FAFC]/90 px-4 py-4 backdrop-blur-md sm:px-8">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 via-blue-700 to-teal-600 text-white shadow-lg shadow-blue-500/25">
              <Heart className="size-6 animate-pulse fill-white/20" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-extrabold tracking-tight text-slate-900">
                  HealthSaathi
                </span>
                <span className="rounded-full border border-blue-200/80 bg-blue-50 px-2 py-0.5 text-[10px] font-bold tracking-wider text-blue-700 uppercase">
                  Health Access
                </span>
              </div>
              <p className="hidden text-xs text-slate-500 sm:block">
                Voice for Bharat Challenge • AI Health Companion
              </p>
            </div>
          </div>

          <nav className="flex items-center gap-6">
            <a
              href="#about"
              className="hidden text-sm font-medium text-slate-600 transition-colors hover:text-blue-600 md:block"
            >
              About
            </a>
            <a
              href="#how-it-works"
              className="hidden text-sm font-medium text-slate-600 transition-colors hover:text-blue-600 md:block"
            >
              How It Works
            </a>
            <a
              href="#privacy"
              className="hidden text-sm font-medium text-slate-600 transition-colors hover:text-blue-600 md:block"
            >
              Privacy
            </a>
            <Button
              onClick={onStartCall}
              className="rounded-full bg-blue-600 px-5 py-2 text-sm font-semibold text-white shadow-md shadow-blue-600/25 transition-all hover:scale-[1.02] hover:bg-blue-700"
            >
              {startButtonText}
            </Button>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="mx-auto flex max-w-6xl flex-1 flex-col gap-16 px-4 py-8 sm:px-8 sm:py-12">
        {/* Reassuring Target User Welcome Card */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex flex-col items-center justify-between gap-4 rounded-2xl border border-blue-200/70 bg-gradient-to-r from-blue-50 via-teal-50/60 to-emerald-50/40 p-4 shadow-sm sm:flex-row sm:p-5"
        >
          <div className="flex items-center gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-blue-600/10 text-blue-600">
              <ShieldCheck className="size-5" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900">
                &quot;I&apos;m here to help you understand, not judge you.&quot;
              </p>
              <p className="mt-0.5 text-xs text-slate-600">
                Simple Indian English & Hinglish support for you and your family. Free, safe, and
                confidential.
              </p>
            </div>
          </div>
          <span className="rounded-full border border-blue-200 bg-white px-3 py-1 text-xs font-semibold whitespace-nowrap text-blue-700 shadow-2xs">
            🌿 Voice First Healthcare Guidance
          </span>
        </motion.div>

        {/* Hero Section */}
        <section className="grid grid-cols-1 items-center gap-12 lg:grid-cols-12">
          {/* Left Column: Text & Hero Info */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="flex flex-col gap-6 text-left lg:col-span-7"
          >
            <div className="inline-flex w-fit items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-bold text-blue-700">
              <Sparkles className="size-3.5 text-blue-600" />
              <span>Voice for Bharat • Health Access Track</span>
            </div>

            <div className="space-y-3">
              <h1 className="text-4xl leading-[1.15] font-extrabold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
                HealthSaathi
              </h1>
              <p className="bg-gradient-to-r from-blue-600 to-teal-600 bg-clip-text text-xl font-bold text-transparent sm:text-2xl">
                Helping you understand your health, one conversation at a time.
              </p>
            </div>

            <p className="max-w-xl text-base leading-relaxed text-slate-600 sm:text-lg">
              HealthSaathi is your AI health companion that explains health information in simple
              language, prepares you for doctor visits, and answers general health questions through
              natural voice conversations.
            </p>

            {/* CTAs */}
            <div className="flex flex-col items-stretch gap-4 pt-2 sm:flex-row sm:items-center">
              <Button
                onClick={onStartCall}
                size="lg"
                className="flex items-center justify-center gap-3 rounded-2xl bg-blue-600 px-8 py-6 text-base font-bold text-white shadow-lg shadow-blue-600/30 transition-all hover:scale-[1.02] hover:bg-blue-700"
              >
                <span>🎙 Talk to HealthSaathi</span>
                <ArrowRight className="size-5" />
              </Button>

              <a href="#how-it-works" className="w-full sm:w-auto">
                <Button
                  variant="outline"
                  size="lg"
                  className="w-full rounded-2xl border-slate-300 px-6 py-6 text-base font-semibold text-slate-700 transition-all hover:border-blue-400 hover:bg-slate-50"
                >
                  Learn More
                </Button>
              </a>
            </div>

            {/* Micro Trust Stats */}
            <div className="grid max-w-md grid-cols-3 gap-4 border-t border-slate-200/80 pt-6">
              <div>
                <p className="text-lg font-bold text-slate-900">100% Free</p>
                <p className="text-xs text-slate-500">No registration needed</p>
              </div>
              <div>
                <p className="text-lg font-bold text-slate-900">Simple Words</p>
                <p className="text-xs text-slate-500">No medical jargon</p>
              </div>
              <div>
                <p className="text-lg font-bold text-slate-900">Voice-First</p>
                <p className="text-xs text-slate-500">English & Hinglish</p>
              </div>
            </div>
          </motion.div>

          {/* Right Column: Hero Illustration — Animated Voice Orb */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="relative flex flex-col items-center justify-center py-8 lg:col-span-5"
          >
            {/* Orb Outer Glowing Container */}
            <div className="relative flex size-72 items-center justify-center sm:size-80">
              {/* Outer Pulsing Glow Ring 1 */}
              <motion.div
                animate={{
                  scale: [1, 1.15, 1],
                  opacity: [0.3, 0.6, 0.3],
                }}
                transition={{
                  duration: 4,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
                className="absolute inset-0 rounded-full bg-gradient-to-tr from-blue-500/20 via-teal-400/20 to-emerald-400/20 blur-2xl"
              />

              {/* Outer Pulsing Glow Ring 2 */}
              <motion.div
                animate={{
                  scale: [1.1, 1.25, 1.1],
                  opacity: [0.2, 0.4, 0.2],
                }}
                transition={{
                  duration: 5,
                  repeat: Infinity,
                  ease: 'easeInOut',
                  delay: 1,
                }}
                className="absolute inset-0 rounded-full bg-blue-600/15 blur-3xl"
              />

              {/* Core Breathing Voice Orb */}
              <motion.div
                animate={{
                  scale: [1, 1.06, 1],
                  rotate: [0, 90, 180, 270, 360],
                }}
                transition={{
                  scale: { duration: 3.5, repeat: Infinity, ease: 'easeInOut' },
                  rotate: { duration: 25, repeat: Infinity, ease: 'linear' },
                }}
                className="group relative flex size-52 cursor-pointer items-center justify-center rounded-full bg-gradient-to-br from-blue-600 via-teal-500 to-emerald-400 p-1 shadow-2xl shadow-blue-500/35 sm:size-60"
                onClick={onStartCall}
              >
                {/* Inner Glowing Orb Surface */}
                <div className="relative flex size-full flex-col items-center justify-center overflow-hidden rounded-full bg-gradient-to-br from-blue-600/90 via-blue-700 to-teal-700 p-6 text-white backdrop-blur-md">
                  <div className="pointer-events-none absolute inset-0 bg-radial from-white/20 via-transparent to-transparent opacity-60" />

                  <Heart className="mb-2 size-12 animate-pulse text-white drop-shadow-md" />
                  <span className="text-base font-extrabold tracking-wide text-white drop-shadow">
                    HealthSaathi
                  </span>
                  <span className="text-[11px] font-medium text-teal-100 opacity-90">
                    Tap to speak
                  </span>
                </div>
              </motion.div>

              {/* Floating Health-Inspired Icons around the Orb */}
              {/* Icon 1: Heart ❤️ (Top Left) */}
              <motion.div
                animate={{
                  y: [-6, 6, -6],
                  x: [-3, 3, -3],
                }}
                transition={{ duration: 3.2, repeat: Infinity, ease: 'easeInOut' }}
                className="absolute -top-2 left-4 flex size-12 items-center justify-center rounded-2xl border border-red-100 bg-white text-red-500 shadow-lg"
              >
                <span className="text-xl">❤️</span>
              </motion.div>

              {/* Icon 2: Voice Chat 💬 (Top Right) */}
              <motion.div
                animate={{
                  y: [6, -6, 6],
                  x: [3, -3, 3],
                }}
                transition={{ duration: 3.8, repeat: Infinity, ease: 'easeInOut', delay: 0.5 }}
                className="absolute top-4 -right-2 flex size-12 items-center justify-center rounded-2xl border border-blue-100 bg-white text-blue-500 shadow-lg"
              >
                <span className="text-xl">💬</span>
              </motion.div>

              {/* Icon 3: Stethoscope 🩺 (Bottom Left) */}
              <motion.div
                animate={{
                  y: [5, -5, 5],
                  x: [-4, 4, -4],
                }}
                transition={{ duration: 4.1, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
                className="absolute bottom-4 -left-2 flex size-12 items-center justify-center rounded-2xl border border-teal-100 bg-white text-teal-600 shadow-lg"
              >
                <span className="text-xl">🩺</span>
              </motion.div>

              {/* Icon 4: Herb 🌿 (Bottom Right) */}
              <motion.div
                animate={{
                  y: [-5, 5, -5],
                  x: [4, -4, 4],
                }}
                transition={{ duration: 3.6, repeat: Infinity, ease: 'easeInOut', delay: 1.5 }}
                className="absolute right-4 -bottom-2 flex size-12 items-center justify-center rounded-2xl border border-emerald-100 bg-white text-emerald-600 shadow-lg"
              >
                <span className="text-xl">🌿</span>
              </motion.div>
            </div>

            <p className="mt-4 flex items-center gap-1.5 text-center text-xs font-semibold text-slate-500">
              <span className="size-2 animate-ping rounded-full bg-emerald-500" />
              AI Voice Companion Ready • Tap Orb or Button to Begin
            </p>
          </motion.div>
        </section>

        {/* Conversation Starters Cards Section */}
        <section className="space-y-6 pt-4">
          <div className="flex flex-col justify-between gap-2 border-b border-slate-200/80 pb-4 sm:flex-row sm:items-end">
            <div>
              <h2 className="text-2xl font-extrabold tracking-tight text-slate-900 sm:text-3xl">
                How can HealthSaathi help today?
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                Select any topic card below to start your natural voice conversation immediately:
              </p>
            </div>
            <span className="w-fit rounded-full border border-blue-200/80 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-600">
              Tap any topic to talk
            </span>
          </div>

          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {conversationStarters.map((starter) => (
              <motion.div
                key={starter.id}
                whileHover={{ y: -4, scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleStarterClick(starter.id)}
                className={`group relative flex cursor-pointer flex-col justify-between gap-4 overflow-hidden rounded-2xl border bg-white p-6 shadow-sm transition-all hover:shadow-md`}
              >
                <div className="flex items-start justify-between">
                  <div
                    className={`size-12 rounded-2xl ${starter.iconBg} flex items-center justify-center text-2xl shadow-2xs`}
                  >
                    {starter.emoji}
                  </div>
                  <span className="rounded-full border border-slate-200 bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-700">
                    {starter.badge}
                  </span>
                </div>

                <div className="space-y-1.5">
                  <h3 className="text-lg font-extrabold text-slate-900 transition-colors group-hover:text-blue-600">
                    {starter.title}
                  </h3>
                  <p className="text-xs leading-relaxed text-slate-600">{starter.description}</p>
                </div>

                <div className="flex items-center border-t border-slate-100 pt-2 text-xs font-bold text-blue-600 transition-transform group-hover:translate-x-1">
                  <span>Start Conversation</span>
                  <ArrowRight className="ml-1 size-4" />
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Trust Card (Medical Disclaimer & Reassurance) */}
        <section
          id="about"
          className="space-y-4 rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm sm:p-8"
        >
          <div className="flex items-start gap-4">
            <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-teal-50 text-teal-600">
              <Info className="size-6" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-extrabold text-slate-900">
                Educational Companion Disclaimer
              </h3>
              <p className="text-sm leading-relaxed text-slate-600">
                HealthSaathi provides educational health information to help you understand general
                health topics, prepare for doctor visits, and clarify medical terms.{' '}
                <strong className="font-semibold text-slate-900">
                  It is not a doctor and does not replace qualified healthcare professionals.
                </strong>{' '}
                HealthSaathi does not diagnose illnesses or prescribe medicines.
              </p>
              <div className="flex flex-wrap gap-3 pt-2">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-700">
                  <CheckCircle2 className="size-3.5" /> No Prescriptions
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                  <CheckCircle2 className="size-3.5" /> No Medical Diagnoses
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                  <CheckCircle2 className="size-3.5" /> Simple Language
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works Section */}
        <section id="how-it-works" className="space-y-8 pt-4">
          <div className="mx-auto max-w-2xl space-y-2 text-center">
            <h2 className="text-2xl font-extrabold tracking-tight text-slate-900 sm:text-3xl">
              How HealthSaathi Works
            </h2>
            <p className="text-sm text-slate-600">
              Three simple steps to clarify your health questions through natural voice
              conversations:
            </p>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="flex flex-col gap-3 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
              <div className="flex size-10 items-center justify-center rounded-xl bg-blue-100 text-base font-extrabold text-blue-700">
                1
              </div>
              <h3 className="text-base font-bold text-slate-900">Tap &amp; Speak</h3>
              <p className="text-xs leading-relaxed text-slate-600">
                Tap the microphone button and speak naturally in Indian English or Hinglish about
                your health concern or doctor visit.
              </p>
            </div>

            <div className="flex flex-col gap-3 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
              <div className="flex size-10 items-center justify-center rounded-xl bg-teal-100 text-base font-extrabold text-teal-700">
                2
              </div>
              <h3 className="text-base font-bold text-slate-900">Listen &amp; Learn</h3>
              <p className="text-xs leading-relaxed text-slate-600">
                Receive calm, empathetic explanations in simple everyday words without confusing
                medical jargon or dry lectures.
              </p>
            </div>

            <div className="flex flex-col gap-3 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
              <div className="flex size-10 items-center justify-center rounded-xl bg-emerald-100 text-base font-extrabold text-emerald-700">
                3
              </div>
              <h3 className="text-base font-bold text-slate-900">Prepare &amp; Decide</h3>
              <p className="text-xs leading-relaxed text-slate-600">
                Organize your symptoms, prepare questions for your doctor, and make confident health
                decisions for your family.
              </p>
            </div>
          </div>
        </section>

        {/* Future Ready Section (Architected for Scalability) */}
        <section className="space-y-6 border-t border-slate-200/80 pt-4">
          <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
            <div>
              <div className="mb-2 inline-flex items-center gap-1.5 rounded-full border border-purple-200 bg-purple-50 px-2.5 py-1 text-xs font-bold text-purple-700">
                <Sparkles className="size-3" />
                <span>Product Roadmap</span>
              </div>
              <h2 className="text-2xl font-extrabold tracking-tight text-slate-900 sm:text-3xl">
                Built for the Future of Healthcare Access
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                Upcoming modules designed to expand healthcare accessibility across India:
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {futureFeatures.map((feature, idx) => {
              const FeatureIcon = feature.icon;
              return (
                <div
                  key={idx}
                  className="flex flex-col justify-between gap-3 rounded-2xl border border-slate-200/70 bg-white/80 p-5 opacity-85 shadow-2xs transition-opacity hover:opacity-100"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex size-10 items-center justify-center rounded-xl bg-slate-100 text-slate-700">
                      <FeatureIcon className="size-5" />
                    </div>
                    <span className="rounded-full border border-slate-200 bg-slate-100 px-2.5 py-0.5 text-[10px] font-bold tracking-wider text-slate-600 uppercase">
                      {feature.badge}
                    </span>
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{feature.title}</h4>
                    <p className="mt-1 text-xs leading-relaxed text-slate-500">
                      {feature.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </main>

      {/* Minimal Footer */}
      <footer
        id="privacy"
        className="mt-12 border-t border-slate-200 bg-white px-4 py-8 text-center text-xs text-slate-500 sm:px-8"
      >
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <Heart className="size-4 fill-blue-600/20 text-blue-600" />
            <span className="font-bold text-slate-900">HealthSaathi</span>
            <span>— Voice for Bharat Challenge (Health Access Track)</span>
          </div>

          <p className="text-slate-500">
            © {new Date().getFullYear()} HealthSaathi • Educational AI Health Companion • Not a
            Doctor
          </p>
        </div>
      </footer>
    </div>
  );
};
