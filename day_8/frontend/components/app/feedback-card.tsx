'use client';

import React from 'react';
import { ArrowLeft, CheckCircle2, Lightbulb, RefreshCw, Sparkles, Star } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface EvaluationFeedback {
  score?: number;
  strength?: string;
  improvement?: string;
  example?: string;
}

interface FeedbackCardProps {
  feedback: EvaluationFeedback | null;
  onTryAgain: () => void;
  onBackHome: () => void;
  onPracticeWithFeedback?: () => void;
}

export function FeedbackCard({
  feedback,
  onTryAgain,
  onBackHome,
  onPracticeWithFeedback,
}: FeedbackCardProps) {
  const hasScore = typeof feedback?.score === 'number';

  if (hasScore && feedback) {
    return (
      <div className="w-full max-w-lg space-y-5 rounded-3xl border border-indigo-100 bg-white p-6 shadow-xl">
        {/* Card Header */}
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <span className="text-xs font-bold tracking-wider text-slate-400 uppercase">
              Evaluation Feedback
            </span>
            <h3 className="text-lg font-extrabold text-slate-900">Your Speaking Practice</h3>
          </div>
          <div className="flex items-center gap-1.5 rounded-2xl bg-indigo-600 px-4 py-2 text-white shadow-md shadow-indigo-600/20">
            <Star className="size-4 fill-amber-300 text-amber-300" />
            <span className="text-base font-extrabold">{feedback.score} / 10</span>
          </div>
        </div>

        {/* Strength Section */}
        {feedback.strength && (
          <div className="space-y-1.5 rounded-2xl border border-emerald-100 bg-emerald-50/50 p-4 text-xs">
            <span className="flex items-center gap-1.5 font-bold text-emerald-900">
              <CheckCircle2 className="size-4 text-emerald-600" />
              What Went Well
            </span>
            <p className="leading-relaxed font-medium text-slate-700 capitalize">
              {feedback.strength}
            </p>
          </div>
        )}

        {/* Improvement Section */}
        {feedback.improvement && (
          <div className="space-y-1.5 rounded-2xl border border-indigo-100 bg-indigo-50/50 p-4 text-xs">
            <span className="flex items-center gap-1.5 font-bold text-indigo-900">
              <Lightbulb className="size-4 text-indigo-600" />
              Try This Next
            </span>
            <p className="leading-relaxed font-medium text-slate-700 capitalize">
              {feedback.improvement}
            </p>
          </div>
        )}

        {/* Example Corrected Phrase */}
        {feedback.example && (
          <div className="space-y-1.5 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs">
            <span className="flex items-center gap-1.5 font-bold text-slate-900">
              <Sparkles className="size-3.5 text-purple-600" />
              Try Saying:
            </span>
            <p className="font-mono text-sm font-semibold text-indigo-700 italic">
              &quot;{feedback.example}&quot;
            </p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center gap-3 pt-2">
          <Button
            onClick={onTryAgain}
            className="flex-1 rounded-2xl bg-indigo-600 py-5 text-xs font-bold text-white shadow-md hover:bg-indigo-700"
          >
            <RefreshCw className="mr-1.5 size-4" />
            Try Again
          </Button>
          <Button
            variant="outline"
            onClick={onBackHome}
            className="flex-1 rounded-2xl border-slate-300 py-5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            <ArrowLeft className="mr-1.5 size-4" />
            Back to Home
          </Button>
        </div>
      </div>
    );
  }

  // Fallback view when no score was generated during the session
  return (
    <div className="w-full max-w-md space-y-4 rounded-3xl border border-slate-200/80 bg-white p-6 text-center shadow-lg">
      <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
        <Sparkles className="size-6" />
      </div>
      <div>
        <h3 className="text-lg font-extrabold text-slate-900">Nice Conversation!</h3>
        <p className="mt-1 text-xs text-slate-500">
          Want to practice an answer and get instant speaking feedback?
        </p>
      </div>

      <div className="flex flex-col gap-2 pt-2 sm:flex-row">
        <Button
          onClick={onPracticeWithFeedback || onTryAgain}
          className="flex-1 rounded-2xl bg-indigo-600 py-5 text-xs font-bold text-white shadow-md hover:bg-indigo-700"
        >
          <Sparkles className="mr-1.5 size-4" />
          Practice &amp; Get Feedback
        </Button>
        <Button
          variant="outline"
          onClick={onBackHome}
          className="flex-1 rounded-2xl border-slate-300 py-5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
        >
          <ArrowLeft className="mr-1.5 size-4" />
          Back to Home
        </Button>
      </div>
    </div>
  );
}
