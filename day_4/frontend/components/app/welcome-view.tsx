'use client';

import React from 'react';
import {
  ArrowRight,
  Bell,
  BookOpen,
  Briefcase,
  CheckCircle2,
  Clock,
  Coffee,
  GraduationCap,
  Info,
  MapPin,
  Mic,
  ShieldCheck,
  Sparkles,
  Sun,
  User,
  Users,
} from 'lucide-react';
import { motion } from 'motion/react';
import { Button } from '@/components/ui/button';

interface WelcomeViewProps {
  startButtonText?: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText = '🎙 Talk to BolBuddy',
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  // Conversation Starter Cards for BolBuddy (Learning & Literacy)
  const conversationStarters = [
    {
      id: 'school',
      emoji: '🎓',
      icon: GraduationCap,
      title: 'School & Campus',
      description:
        'Practice discussing your favorite subjects, classes, and student life in English.',
      badge: 'Campus Life',
      bgGradient: 'from-purple-500/10 to-indigo-500/10 border-purple-200/60 text-purple-900',
      iconBg: 'bg-purple-100 text-purple-600',
    },
    {
      id: 'interview',
      emoji: '💼',
      icon: Briefcase,
      title: 'Job Interview Prep',
      description: 'Practice answering common interview questions like "Tell me about yourself".',
      badge: 'Career',
      bgGradient: 'from-blue-500/10 to-indigo-500/10 border-blue-200/60 text-blue-900',
      iconBg: 'bg-blue-100 text-blue-600',
    },
    {
      id: 'intro',
      emoji: '🙋‍♂️',
      icon: User,
      title: 'Self Introduction',
      description: 'Build confidence introducing yourself comfortably to new people.',
      badge: 'Confidence',
      bgGradient: 'from-teal-500/10 to-emerald-500/10 border-teal-200/60 text-teal-900',
      iconBg: 'bg-teal-100 text-teal-600',
    },
    {
      id: 'daily',
      emoji: '☕',
      icon: Coffee,
      title: 'Daily Life Chit-Chat',
      description: 'Chat about daily routines, hobbies, food, and everyday life naturally.',
      badge: 'Everyday Talk',
      bgGradient: 'from-amber-500/10 to-orange-500/10 border-amber-200/60 text-amber-900',
      iconBg: 'bg-amber-100 text-amber-600',
    },
    {
      id: 'travel',
      emoji: '📍',
      icon: MapPin,
      title: 'Travel & Directions',
      description: 'Learn how to ask for directions, bus routes, and travel help easily.',
      badge: 'Travel Prep',
      bgGradient: 'from-emerald-500/10 to-green-500/10 border-emerald-200/60 text-emerald-900',
      iconBg: 'bg-emerald-100 text-emerald-600',
    },
  ];

  // Future Ready Feature Cards for BolBuddy Roadmap
  const futureFeatures = [
    {
      icon: Clock,
      title: 'Practice History',
      description: 'Review your past voice conversations and spoken feedback anytime.',
      badge: 'Coming Soon',
    },
    {
      icon: BookOpen,
      title: 'Vocabulary Builder',
      description: 'Track daily new words, idioms, and natural phrasing learned.',
      badge: 'Coming Soon',
    },
    {
      icon: Sun,
      title: 'Daily Speaking Tips',
      description: 'Receive morning audio tips on fluency, accent, and confidence.',
      badge: 'Coming Soon',
    },
    {
      icon: Bell,
      title: 'Daily Reminder',
      description: 'Set gentle daily reminders to spend 5 minutes practicing speech.',
      badge: 'Coming Soon',
    },
    {
      icon: MapPin,
      title: 'Real World Scenarios',
      description: 'Practice interactive role-play scenarios at banks, stores, and offices.',
      badge: 'Coming Soon',
    },
    {
      icon: Users,
      title: 'Group Conversations',
      description: 'Practice English conversations with peers and study partners.',
      badge: 'Coming Soon',
    },
  ];

  const handleStarterClick = (_id: string) => {
    onStartCall();
  };

  return (
    <div
      ref={ref}
      className="flex min-h-screen flex-col justify-between bg-[#F8FAFC] font-sans text-slate-900 selection:bg-indigo-100 selection:text-indigo-900"
    >
      {/* Header */}
      <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-[#F8FAFC]/90 px-4 py-4 backdrop-blur-md sm:px-8">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-600 text-white shadow-lg shadow-indigo-500/25">
              <Mic className="size-6 animate-pulse text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-extrabold tracking-tight text-slate-900">
                  BolBuddy
                </span>
                <span className="rounded-full border border-indigo-200/80 bg-indigo-50 px-2 py-0.5 text-[10px] font-bold tracking-wider text-indigo-700 uppercase">
                  Learning &amp; Literacy
                </span>
              </div>
              <p className="hidden text-xs text-slate-500 sm:block">
                Voice for Bharat Challenge • AI Speaking Companion
              </p>
            </div>
          </div>

          <nav className="flex items-center gap-6">
            <a
              href="#about"
              className="hidden text-sm font-medium text-slate-600 transition-colors hover:text-indigo-600 md:block"
            >
              About
            </a>
            <a
              href="#how-it-works"
              className="hidden text-sm font-medium text-slate-600 transition-colors hover:text-indigo-600 md:block"
            >
              How It Works
            </a>
            <a
              href="#privacy"
              className="hidden text-sm font-medium text-slate-600 transition-colors hover:text-indigo-600 md:block"
            >
              Privacy
            </a>
            <Button
              onClick={onStartCall}
              className="rounded-full bg-indigo-600 px-5 py-2 text-sm font-semibold text-white shadow-md shadow-indigo-600/25 transition-all hover:scale-[1.02] hover:bg-indigo-700"
            >
              {startButtonText}
            </Button>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="mx-auto flex max-w-6xl flex-1 flex-col gap-16 px-4 py-8 sm:px-8 sm:py-12">
        {/* Welcome Card */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex flex-col items-center justify-between gap-4 rounded-2xl border border-indigo-200/70 bg-gradient-to-r from-indigo-50 via-purple-50/60 to-blue-50/40 p-4 shadow-sm sm:flex-row sm:p-5"
        >
          <div className="flex items-center gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-indigo-600/10 text-indigo-600">
              <ShieldCheck className="size-5" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900">
                &quot;I&apos;m here to help you practice, not judge your mistakes.&quot;
              </p>
              <p className="mt-0.5 text-xs text-slate-600">
                Natural Indian English &amp; Hinglish practice. Safe, encouraging, and
                judgment-free.
              </p>
            </div>
          </div>
          <span className="rounded-full border border-indigo-200 bg-white px-3 py-1 text-xs font-semibold whitespace-nowrap text-indigo-700 shadow-2xs">
            ✨ Voice-First English Practice
          </span>
        </motion.div>

        {/* Hero Section */}
        <section className="grid grid-cols-1 items-center gap-12 lg:grid-cols-12">
          {/* Left Column */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="flex flex-col gap-6 text-left lg:col-span-7"
          >
            <div className="inline-flex w-fit items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-bold text-indigo-700">
              <Sparkles className="size-3.5 text-indigo-600" />
              <span>Voice for Bharat • Learning &amp; Literacy Track</span>
            </div>

            <div className="space-y-3">
              <h1 className="text-4xl leading-[1.15] font-extrabold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
                BolBuddy
              </h1>
              <p className="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-xl font-bold text-transparent sm:text-2xl">
                Helping you speak English with confidence, one conversation at a time.
              </p>
            </div>

            <p className="max-w-xl text-base leading-relaxed text-slate-600 sm:text-lg">
              BolBuddy is your AI speaking companion that helps you practice conversational English,
              prepare for job interviews, and build real-world speaking confidence through natural
              voice conversations.
            </p>

            {/* CTAs */}
            <div className="flex flex-col items-stretch gap-4 pt-2 sm:flex-row sm:items-center">
              <Button
                onClick={onStartCall}
                size="lg"
                className="flex items-center justify-center gap-3 rounded-2xl bg-indigo-600 px-8 py-6 text-base font-bold text-white shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.02] hover:bg-indigo-700"
              >
                <span>🎙 Talk to BolBuddy</span>
                <ArrowRight className="size-5" />
              </Button>

              <a href="#how-it-works" className="w-full sm:w-auto">
                <Button
                  variant="outline"
                  size="lg"
                  className="w-full rounded-2xl border-slate-300 px-6 py-6 text-base font-semibold text-slate-700 transition-all hover:border-indigo-400 hover:bg-slate-50"
                >
                  Learn More
                </Button>
              </a>
            </div>

            {/* Micro Trust Stats */}
            <div className="grid max-w-md grid-cols-3 gap-4 border-t border-slate-200/80 pt-6">
              <div>
                <p className="text-lg font-bold text-slate-900">100% Free</p>
                <p className="text-xs text-slate-500">No sign-up required</p>
              </div>
              <div>
                <p className="text-lg font-bold text-slate-900">Friendly AI</p>
                <p className="text-xs text-slate-500">Zero judgment</p>
              </div>
              <div>
                <p className="text-lg font-bold text-slate-900">Voice-First</p>
                <p className="text-xs text-slate-500">English &amp; Hinglish</p>
              </div>
            </div>
          </motion.div>

          {/* Right Column: Hero Orb */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="relative flex flex-col items-center justify-center py-8 lg:col-span-5"
          >
            <div className="relative flex size-72 items-center justify-center sm:size-80">
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
                className="absolute inset-0 rounded-full bg-gradient-to-tr from-indigo-500/20 via-purple-400/20 to-blue-400/20 blur-2xl"
              />

              {/* Rotating Outer Gradient Ring */}
              <motion.div
                animate={{
                  rotate: [0, 360],
                }}
                transition={{
                  duration: 25,
                  repeat: Infinity,
                  ease: 'linear',
                }}
                className="absolute inset-4 rounded-full bg-gradient-to-br from-indigo-600 via-purple-600 to-blue-500 p-1 shadow-2xl shadow-indigo-500/35 sm:inset-6"
              />

              {/* Static Inner Orb Container (Pulsing scale, NO rotation) */}
              <motion.div
                animate={{
                  scale: [1, 1.05, 1],
                }}
                transition={{
                  duration: 3.5,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
                className="group relative flex size-52 cursor-pointer items-center justify-center rounded-full p-1 sm:size-60"
                onClick={onStartCall}
              >
                <div className="relative flex size-full flex-col items-center justify-center overflow-hidden rounded-full bg-gradient-to-br from-indigo-600/90 via-indigo-700 to-purple-700 p-6 text-white backdrop-blur-md">
                  <Mic className="mb-2 size-12 animate-pulse text-white drop-shadow-md" />
                  <span className="text-base font-extrabold tracking-wide text-white drop-shadow">
                    BolBuddy
                  </span>
                  <span className="text-[11px] font-medium text-indigo-100 opacity-90">
                    Tap to speak
                  </span>
                </div>
              </motion.div>

              {/* Floating Emojis */}
              <motion.div
                animate={{ y: [-6, 6, -6], x: [-3, 3, -3] }}
                transition={{ duration: 3.2, repeat: Infinity, ease: 'easeInOut' }}
                className="absolute -top-2 left-4 flex size-12 items-center justify-center rounded-2xl border border-indigo-100 bg-white text-indigo-600 shadow-lg"
              >
                <span className="text-xl">🎙️</span>
              </motion.div>

              <motion.div
                animate={{ y: [6, -6, 6], x: [3, -3, 3] }}
                transition={{ duration: 3.8, repeat: Infinity, ease: 'easeInOut', delay: 0.5 }}
                className="absolute top-4 -right-2 flex size-12 items-center justify-center rounded-2xl border border-purple-100 bg-white text-purple-600 shadow-lg"
              >
                <span className="text-xl">💬</span>
              </motion.div>

              <motion.div
                animate={{ y: [5, -5, 5], x: [-4, 4, -4] }}
                transition={{ duration: 4.1, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
                className="absolute bottom-4 -left-2 flex size-12 items-center justify-center rounded-2xl border border-blue-100 bg-white text-blue-600 shadow-lg"
              >
                <span className="text-xl">🎓</span>
              </motion.div>

              <motion.div
                animate={{ y: [-5, 5, -5], x: [4, -4, 4] }}
                transition={{ duration: 3.6, repeat: Infinity, ease: 'easeInOut', delay: 1.5 }}
                className="absolute right-4 -bottom-2 flex size-12 items-center justify-center rounded-2xl border border-emerald-100 bg-white text-emerald-600 shadow-lg"
              >
                <span className="text-xl">✨</span>
              </motion.div>
            </div>

            <p className="mt-4 flex items-center gap-1.5 text-center text-xs font-semibold text-slate-500">
              <span className="size-2 animate-ping rounded-full bg-indigo-500" />
              AI Voice Companion Ready • Tap Orb or Button to Begin
            </p>
          </motion.div>
        </section>

        {/* Conversation Starters Cards */}
        <section className="space-y-6 pt-4">
          <div className="flex flex-col justify-between gap-2 border-b border-slate-200/80 pb-4 sm:flex-row sm:items-end">
            <div>
              <h2 className="text-2xl font-extrabold tracking-tight text-slate-900 sm:text-3xl">
                What would you like to practice today?
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                Select any topic card below to start your natural voice conversation immediately:
              </p>
            </div>
            <span className="w-fit rounded-full border border-indigo-200/80 bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-600">
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
                className="group relative flex cursor-pointer flex-col justify-between gap-4 overflow-hidden rounded-2xl border bg-white p-6 shadow-sm transition-all hover:shadow-md"
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
                  <h3 className="text-lg font-extrabold text-slate-900 transition-colors group-hover:text-indigo-600">
                    {starter.title}
                  </h3>
                  <p className="text-xs leading-relaxed text-slate-600">{starter.description}</p>
                </div>

                <div className="flex items-center border-t border-slate-100 pt-2 text-xs font-bold text-indigo-600 transition-transform group-hover:translate-x-1">
                  <span>Start Conversation</span>
                  <ArrowRight className="ml-1 size-4" />
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Companion Philosophy Card */}
        <section
          id="about"
          className="space-y-4 rounded-3xl border border-slate-200/80 bg-white p-6 shadow-sm sm:p-8"
        >
          <div className="flex items-start gap-4">
            <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
              <Info className="size-6" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-extrabold text-slate-900">
                Speaking Companion Philosophy
              </h3>
              <p className="text-sm leading-relaxed text-slate-600">
                BolBuddy is designed to be an AI speaking companion—not a strict English teacher.{' '}
                <strong className="font-semibold text-slate-900">
                  It helps learners become confident English speakers through natural
                  conversations—not dry lessons.
                </strong>{' '}
                Feel free to speak in Hinglish or simple English whenever you are practicing.
              </p>
              <div className="flex flex-wrap gap-3 pt-2">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
                  <CheckCircle2 className="size-3.5" /> Practice Before Explanation
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-purple-200 bg-purple-50 px-3 py-1 text-xs font-semibold text-purple-700">
                  <CheckCircle2 className="size-3.5" /> Gentle Feedback
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
                  <CheckCircle2 className="size-3.5" /> Code-Mixing Encouraged
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works Section */}
        <section id="how-it-works" className="space-y-8 pt-4">
          <div className="mx-auto max-w-2xl space-y-2 text-center">
            <h2 className="text-2xl font-extrabold tracking-tight text-slate-900 sm:text-3xl">
              How BolBuddy Works
            </h2>
            <p className="text-sm text-slate-600">
              Three simple steps to build your spoken English confidence:
            </p>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="flex flex-col gap-3 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
              <div className="flex size-10 items-center justify-center rounded-xl bg-indigo-100 text-base font-extrabold text-indigo-700">
                1
              </div>
              <h3 className="text-base font-bold text-slate-900">Tap &amp; Speak</h3>
              <p className="text-xs leading-relaxed text-slate-600">
                Tap the microphone button and speak naturally in English or Hinglish about your day
                or practice topic.
              </p>
            </div>

            <div className="flex flex-col gap-3 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
              <div className="flex size-10 items-center justify-center rounded-xl bg-purple-100 text-base font-extrabold text-purple-700">
                2
              </div>
              <h3 className="text-base font-bold text-slate-900">Listen &amp; Respond</h3>
              <p className="text-xs leading-relaxed text-slate-600">
                Listen to clear, warm responses in simple English, with gentle phrasing suggestions
                when helpful.
              </p>
            </div>

            <div className="flex flex-col gap-3 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
              <div className="flex size-10 items-center justify-center rounded-xl bg-emerald-100 text-base font-extrabold text-emerald-700">
                3
              </div>
              <h3 className="text-base font-bold text-slate-900">Build Confidence</h3>
              <p className="text-xs leading-relaxed text-slate-600">
                Overcome fear of speaking, expand your active vocabulary, and converse naturally in
                daily life.
              </p>
            </div>
          </div>
        </section>

        {/* Future Ready Section */}
        <section className="space-y-6 border-t border-slate-200/80 pt-4">
          <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
            <div>
              <div className="mb-2 inline-flex items-center gap-1.5 rounded-full border border-purple-200 bg-purple-50 px-2.5 py-1 text-xs font-bold text-purple-700">
                <Sparkles className="size-3" />
                <span>Product Roadmap</span>
              </div>
              <h2 className="text-2xl font-extrabold tracking-tight text-slate-900 sm:text-3xl">
                Built for the Future of Language Accessibility
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                Upcoming modules designed to expand conversational literacy across India:
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

      {/* Footer */}
      <footer
        id="privacy"
        className="mt-12 border-t border-slate-200 bg-white px-4 py-8 text-center text-xs text-slate-500 sm:px-8"
      >
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <Mic className="size-4 text-indigo-600" />
            <span className="font-bold text-slate-900">BolBuddy</span>
            <span>— Voice for Bharat Challenge (Learning &amp; Literacy Track)</span>
          </div>

          <p className="text-slate-500">
            © {new Date().getFullYear()} BolBuddy • AI Speaking Companion • Voice for Bharat
          </p>
        </div>
      </footer>
    </div>
  );
};
