'use client';

import React, { useState } from 'react';
import {
  Activity,
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Heart,
  HelpCircle,
  Menu,
  MessageSquare,
  PhoneCall,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  X,
} from 'lucide-react';
import { motion } from 'motion/react';
import { OutboundCallCard } from '@/components/app/outbound-call-card';
import { Button } from '@/components/ui/button';

interface WelcomeViewProps {
  startButtonText?: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText = 'Talk to HealthSaathi',
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div
      ref={ref}
      className="relative flex min-h-screen flex-col justify-between bg-gradient-to-b from-[#F0F7FF] via-[#F4F9F8] to-[#FFFFFF] font-sans text-slate-800 selection:bg-teal-100 selection:text-teal-900"
    >
      {/* Soft organic ambient shapes in background */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -top-32 -left-20 size-[420px] rounded-full bg-sky-200/40 blur-3xl" />
        <div className="absolute top-1/4 -right-24 size-[480px] rounded-full bg-teal-200/35 blur-3xl" />
        <div className="absolute bottom-1/3 -left-32 size-[400px] rounded-full bg-emerald-100/50 blur-3xl" />
      </div>

      {/* ============================================================ */}
      {/* 1. NAVIGATION                                                */}
      {/* ============================================================ */}
      <header className="sticky top-0 z-40 border-b border-teal-100/70 bg-[#F0F7FF]/85 px-4 py-4 backdrop-blur-md sm:px-8">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          {/* Logo & Brand Name */}
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-600 to-sky-600 text-white shadow-sm shadow-teal-600/20">
              <Activity className="size-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-bold tracking-tight text-slate-900">HealthSaathi</span>
              <span className="text-[10px] font-semibold tracking-wider text-teal-700 uppercase">
                AI Health Companion
              </span>
            </div>
          </div>

          {/* Desktop Links & CTA */}
          <nav className="hidden items-center gap-8 md:flex">
            <a
              href="#outbound-calling"
              className="rounded-full border border-teal-200/80 bg-teal-50 px-3.5 py-1.5 text-sm font-semibold text-teal-800 transition-colors hover:bg-teal-100"
            >
              Day 6 Outbound Call
            </a>
            <a
              href="#how-it-works"
              className="text-sm font-medium text-slate-600 transition-colors hover:text-teal-700"
            >
              How It Works
            </a>

            <a
              href="#safety"
              className="text-sm font-medium text-slate-600 transition-colors hover:text-teal-700"
            >
              Safety
            </a>
            <a
              href="#about"
              className="text-sm font-medium text-slate-600 transition-colors hover:text-teal-700"
            >
              About
            </a>
            <Button
              onClick={onStartCall}
              className="rounded-full bg-teal-700 px-6 py-2.5 text-sm font-semibold text-white shadow-md shadow-teal-700/20 transition-all hover:bg-teal-800 hover:shadow-lg hover:shadow-teal-700/30"
            >
              {startButtonText}
            </Button>
          </nav>

          {/* Mobile Hamburger Toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="flex size-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 md:hidden"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-teal-100 bg-white/95 px-6 py-4 backdrop-blur-md md:hidden"
          >
            <div className="flex flex-col gap-4">
              <a
                href="#how-it-works"
                onClick={() => setMobileMenuOpen(false)}
                className="py-2 text-base font-medium text-slate-700 hover:text-teal-700"
              >
                How It Works
              </a>
              <a
                href="#safety"
                onClick={() => setMobileMenuOpen(false)}
                className="py-2 text-base font-medium text-slate-700 hover:text-teal-700"
              >
                Safety
              </a>
              <a
                href="#about"
                onClick={() => setMobileMenuOpen(false)}
                className="py-2 text-base font-medium text-slate-700 hover:text-teal-700"
              >
                About
              </a>
              <Button
                onClick={() => {
                  setMobileMenuOpen(false);
                  onStartCall();
                }}
                className="w-full rounded-2xl bg-teal-700 py-3 text-base font-semibold text-white shadow-md shadow-teal-700/20"
              >
                {startButtonText}
              </Button>
            </div>
          </motion.div>
        )}
      </header>

      {/* Main Container */}
      <main className="relative z-10 mx-auto flex max-w-6xl flex-1 flex-col gap-20 px-4 py-8 sm:px-8 sm:py-14">
        {/* ============================================================ */}
        {/* 2. HERO SECTION (Editorial Split Layout)                    */}
        {/* ============================================================ */}
        <section className="grid grid-cols-1 items-center gap-12 lg:grid-cols-12">
          {/* Left Column: Headline, Copy, Primary CTA */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex flex-col items-start gap-6 lg:col-span-7"
          >
            <div className="inline-flex items-center gap-2 rounded-full border border-teal-200/80 bg-teal-50 px-3.5 py-1.5 text-xs font-semibold text-teal-800">
              <Sparkles className="size-3.5 text-teal-600" />
              <span>Your AI Health Companion</span>
            </div>

            <div className="space-y-4">
              <h1 className="text-4xl leading-[1.15] font-extrabold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
                Understand your health. <br />
                <span className="bg-gradient-to-r from-teal-700 via-sky-700 to-teal-800 bg-clip-text text-transparent">
                  Without the medical jargon.
                </span>
              </h1>
              <p className="max-w-xl text-lg leading-relaxed text-slate-600 sm:text-xl">
                HealthSaathi helps you explore general health information through simple, natural
                conversations — whenever you need a clearer explanation.
              </p>
            </div>

            <div className="flex flex-col gap-3 pt-2 sm:flex-row sm:items-center">
              <Button
                onClick={onStartCall}
                size="lg"
                className="flex items-center justify-center gap-3 rounded-2xl bg-teal-700 px-8 py-6 text-base font-bold text-white shadow-lg shadow-teal-700/25 transition-all hover:scale-[1.01] hover:bg-teal-800"
              >
                <span>Talk to HealthSaathi</span>
                <ArrowRight className="size-5" />
              </Button>

              <a
                href="#outbound-calling"
                className="flex items-center justify-center gap-2.5 rounded-2xl border border-teal-200 bg-teal-50 px-6 py-4 text-base font-bold text-teal-800 shadow-sm transition-all hover:bg-teal-100 hover:text-teal-900"
              >
                <PhoneCall className="size-5 text-teal-700" />
                <span>Day 6 Outbound Call</span>
              </a>
            </div>

            {/* Reassurance text */}
            <div className="flex items-center gap-4 pt-1 text-xs font-medium text-slate-500">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="size-4 text-teal-600" />
                Simple language
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="size-4 text-teal-600" />
                Natural conversation
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="size-4 text-teal-600" />
                No judgment
              </span>
            </div>
          </motion.div>

          {/* Right Column: Abstract Health Conversation Panel (NOT a Voice Orb) */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="relative flex items-center justify-center py-4 lg:col-span-5"
          >
            {/* Background Organic Floating Shapes */}
            <div className="relative w-full max-w-md">
              <div className="absolute -top-4 -right-4 size-24 rounded-3xl bg-teal-100/70 blur-xl" />
              <div className="absolute -bottom-6 -left-6 size-32 rounded-full bg-sky-100/70 blur-xl" />

              {/* Health Conversation Panel Card */}
              <div className="relative rounded-3xl border border-teal-100/90 bg-white/90 p-6 shadow-xl shadow-teal-900/5 backdrop-blur-sm sm:p-8">
                {/* Header of Card */}
                <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                  <div className="flex items-center gap-3">
                    <div className="flex size-11 items-center justify-center rounded-2xl border border-teal-100 bg-teal-50 text-teal-700">
                      <Heart className="size-5 fill-teal-600/20 text-teal-600" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-slate-900">HealthSaathi</h3>
                      <p className="text-xs text-slate-500">Ready for conversation</p>
                    </div>
                  </div>
                  <span className="flex items-center gap-1.5 rounded-full border border-emerald-100 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                    <span className="size-2 animate-pulse rounded-full bg-emerald-500" />
                    Active
                  </span>
                </div>

                {/* Main Speech Bubble Content inside panel */}
                <div className="my-6 rounded-2xl border border-sky-100/80 bg-gradient-to-br from-sky-50 to-teal-50/60 p-5">
                  <p className="text-sm font-semibold text-slate-800">
                    &quot;How are you feeling today? You can ask me any health questions in simple
                    English or Hinglish.&quot;
                  </p>

                  {/* Abstract Heartbeat Line SVG */}
                  <div className="mt-4 flex items-center gap-2 border-t border-teal-100/60 pt-2">
                    <svg
                      className="h-6 w-full text-teal-600/70"
                      viewBox="0 0 200 40"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M 0 20 H 40 L 50 10 L 60 30 L 75 5 L 90 35 L 100 20 H 200" />
                    </svg>
                  </div>
                </div>

                {/* Interactive Card Action */}
                <button
                  onClick={onStartCall}
                  className="flex w-full items-center justify-center gap-2.5 rounded-xl bg-slate-900 py-3.5 text-sm font-bold text-white transition-colors hover:bg-teal-800"
                >
                  <MessageSquare className="size-4" />
                  <span>Start Conversation</span>
                </button>

                {/* Floating Healthcare Wellness Shapes around Card */}
                <motion.div
                  animate={{ y: [-4, 4, -4] }}
                  transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
                  className="absolute -top-5 -left-4 flex items-center gap-1.5 rounded-2xl border border-teal-100 bg-white px-3 py-1.5 text-xs font-semibold text-teal-800 shadow-md"
                >
                  <Stethoscope className="size-3.5 text-teal-600" />
                  <span>Doctor Prep</span>
                </motion.div>

                <motion.div
                  animate={{ y: [4, -4, 4] }}
                  transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut', delay: 0.5 }}
                  className="absolute -right-4 -bottom-4 flex items-center gap-1.5 rounded-2xl border border-sky-100 bg-white px-3 py-1.5 text-xs font-semibold text-sky-800 shadow-md"
                >
                  <ShieldCheck className="size-3.5 text-sky-600" />
                  <span>No Diagnosis Limit</span>
                </motion.div>
              </div>
            </div>
          </motion.div>
        </section>

        {/* Outbound Calling Section (Day 6) */}
        <section id="outbound-calling" className="py-2">
          <OutboundCallCard />
        </section>

        {/* ============================================================ */}
        {/* 3. HEALTH ACCESS CONTEXT                                    */}
        {/* ============================================================ */}
        <section id="about" className="space-y-8 pt-4">
          <div className="mx-auto max-w-2xl space-y-3 text-center">
            <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
              Health information shouldn&apos;t feel complicated.
            </h2>
            <p className="text-base leading-relaxed text-slate-600">
              Medical terms can be difficult to understand, especially when you&apos;re worried,
              short on time, or trying to help someone in your family.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            {/* UNDERSTAND */}
            <div className="flex flex-col gap-4 rounded-3xl border border-teal-100 bg-white p-7 shadow-sm transition-all hover:border-teal-200 hover:shadow-md">
              <div className="flex size-12 items-center justify-center rounded-2xl border border-sky-100 bg-sky-50 font-bold text-sky-700">
                01
              </div>
              <h3 className="text-xl font-bold text-slate-900">UNDERSTAND</h3>
              <p className="text-sm leading-relaxed text-slate-600">
                Get general health information explained in simpler language.
              </p>
            </div>

            {/* PREPARE */}
            <div className="flex flex-col gap-4 rounded-3xl border border-teal-100 bg-white p-7 shadow-sm transition-all hover:border-teal-200 hover:shadow-md">
              <div className="flex size-12 items-center justify-center rounded-2xl border border-teal-100 bg-teal-50 font-bold text-teal-700">
                02
              </div>
              <h3 className="text-xl font-bold text-slate-900">PREPARE</h3>
              <p className="text-sm leading-relaxed text-slate-600">
                Know what questions you may want to ask a healthcare professional.
              </p>
            </div>

            {/* KNOW WHEN TO SEEK HELP */}
            <div className="flex flex-col gap-4 rounded-3xl border border-teal-100 bg-white p-7 shadow-sm transition-all hover:border-teal-200 hover:shadow-md">
              <div className="flex size-12 items-center justify-center rounded-2xl border border-emerald-100 bg-emerald-50 font-bold text-emerald-700">
                03
              </div>
              <h3 className="text-xl font-bold text-slate-900">KNOW WHEN TO SEEK HELP</h3>
              <p className="text-sm leading-relaxed text-slate-600">
                Recognize situations where professional medical attention may be important.
              </p>
            </div>
          </div>
        </section>

        {/* ============================================================ */}
        {/* 4. VOICE CTA SECTION                                        */}
        {/* ============================================================ */}
        <section className="relative overflow-hidden rounded-3xl border border-teal-200/80 bg-gradient-to-r from-teal-800 via-teal-900 to-sky-900 p-8 text-white shadow-xl sm:p-12">
          <div className="relative z-10 mx-auto flex max-w-3xl flex-col items-center space-y-6 text-center">
            <span className="rounded-full border border-teal-500/30 bg-teal-700/60 px-4 py-1.5 text-xs font-semibold tracking-wide text-teal-200">
              Voice-First Convenience
            </span>

            <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl lg:text-5xl">
              Sometimes, it&apos;s easier to ask.
            </h2>

            <p className="max-w-xl text-base leading-relaxed text-teal-100 sm:text-lg">
              Talk naturally instead of searching through pages of medical information. Speak the
              way you&apos;re comfortable.
            </p>

            {/* Language badges */}
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <span className="rounded-xl border border-white/15 bg-white/10 px-4 py-2 text-xs font-semibold text-white">
                English
              </span>
              <span className="rounded-xl border border-white/15 bg-white/10 px-4 py-2 text-xs font-semibold text-white">
                Hindi
              </span>
              <span className="rounded-xl border border-teal-400/30 bg-teal-500/20 px-4 py-2 text-xs font-bold text-teal-200">
                Hindi + English
              </span>
            </div>

            <div className="pt-4">
              <Button
                onClick={onStartCall}
                size="lg"
                className="rounded-2xl bg-white px-8 py-6 text-base font-bold text-teal-900 shadow-lg transition-all hover:scale-[1.02] hover:bg-teal-50"
              >
                Start a Conversation
              </Button>
            </div>

            <p className="text-xs text-teal-200/80">
              Speak in English, Hindi, or a natural mix of both.
            </p>
          </div>
        </section>

        {/* ============================================================ */}
        {/* 5. TRUST / SAFETY SECTION                                   */}
        {/* ============================================================ */}
        <section id="safety" className="space-y-8 pt-4">
          <div className="mx-auto max-w-2xl space-y-3 text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-3.5 py-1.5 text-xs font-semibold text-sky-800">
              <ShieldCheck className="size-4 text-sky-600" />
              <span>Safety & Transparency</span>
            </div>

            <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
              HealthSaathi has limits. And that&apos;s intentional.
            </h2>

            <p className="text-base leading-relaxed text-slate-600">
              HealthSaathi provides general educational information. It does not diagnose illnesses
              or prescribe medicines.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            {/* NO DIAGNOSIS */}
            <div className="space-y-3 rounded-3xl border border-slate-200/80 bg-white p-7 shadow-sm">
              <div className="flex size-10 items-center justify-center rounded-xl bg-slate-100 text-slate-700">
                <HelpCircle className="size-5" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">NO DIAGNOSIS</h3>
              <p className="text-sm leading-relaxed text-slate-600">
                HealthSaathi does not determine what condition you have.
              </p>
            </div>

            {/* NO PRESCRIPTIONS */}
            <div className="space-y-3 rounded-3xl border border-slate-200/80 bg-white p-7 shadow-sm">
              <div className="flex size-10 items-center justify-center rounded-xl bg-slate-100 text-slate-700">
                <ShieldCheck className="size-5" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">NO PRESCRIPTIONS</h3>
              <p className="text-sm leading-relaxed text-slate-600">
                HealthSaathi does not recommend or prescribe medication.
              </p>
            </div>

            {/* PROFESSIONAL CARE */}
            <div className="space-y-3 rounded-3xl border border-slate-200/80 bg-white p-7 shadow-sm">
              <div className="flex size-10 items-center justify-center rounded-xl bg-slate-100 text-slate-700">
                <Stethoscope className="size-5" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">PROFESSIONAL CARE</h3>
              <p className="text-sm leading-relaxed text-slate-600">
                When symptoms may require medical attention, HealthSaathi encourages you to seek
                appropriate professional help.
              </p>
            </div>
          </div>

          {/* ============================================================ */}
          {/* 6. SUBTLE EMERGENCY NOTICE                                   */}
          {/* ============================================================ */}
          <div className="space-y-2 rounded-2xl border border-slate-200 bg-slate-50 p-5 text-slate-700 sm:p-6">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
              <AlertCircle className="size-4 text-amber-600" />
              <span>Need urgent medical help?</span>
            </div>
            <p className="max-w-3xl text-xs leading-relaxed text-slate-600">
              HealthSaathi is not an emergency service. If someone is experiencing a serious or
              life-threatening situation, contact local emergency services or seek immediate medical
              attention.
            </p>
          </div>
        </section>

        {/* ============================================================ */}
        {/* 7. SIMPLE HOW IT WORKS                                      */}
        {/* ============================================================ */}
        <section id="how-it-works" className="space-y-8 pt-4">
          <div className="mx-auto max-w-2xl space-y-3 text-center">
            <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">
              Simple 3-step conversation
            </h2>
            <p className="text-base text-slate-600">
              How to use HealthSaathi to explore your health questions.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="flex flex-col gap-3 rounded-3xl border border-teal-100/70 bg-white p-7 shadow-sm">
              <span className="text-3xl font-extrabold text-teal-700">01</span>
              <h3 className="text-lg font-bold text-slate-900">ASK</h3>
              <p className="text-sm leading-relaxed text-slate-600">
                Tell HealthSaathi what you&apos;d like to understand.
              </p>
            </div>

            <div className="flex flex-col gap-3 rounded-3xl border border-teal-100/70 bg-white p-7 shadow-sm">
              <span className="text-3xl font-extrabold text-teal-700">02</span>
              <h3 className="text-lg font-bold text-slate-900">LISTEN</h3>
              <p className="text-sm leading-relaxed text-slate-600">
                Have a natural voice conversation in a language you&apos;re comfortable using.
              </p>
            </div>

            <div className="flex flex-col gap-3 rounded-3xl border border-teal-100/70 bg-white p-7 shadow-sm">
              <span className="text-3xl font-extrabold text-teal-700">03</span>
              <h3 className="text-lg font-bold text-slate-900">ACT</h3>
              <p className="text-sm leading-relaxed text-slate-600">
                Use the information to prepare for the next step, including speaking with a
                healthcare professional when needed.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* ============================================================ */}
      {/* FOOTER                                                       */}
      {/* ============================================================ */}
      <footer className="mt-16 border-t border-teal-100/80 bg-white px-4 py-8 text-xs text-slate-500 sm:px-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <Activity className="size-4 text-teal-600" />
            <span className="font-bold text-slate-900">HealthSaathi</span>
            <span>— AI Voice Companion for Health Access</span>
          </div>

          <p className="text-center text-slate-500 sm:text-right">
            © {new Date().getFullYear()} HealthSaathi • Educational Information Only • Not a Doctor
          </p>
        </div>
      </footer>
    </div>
  );
};
