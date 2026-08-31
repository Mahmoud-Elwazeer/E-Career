/**
 * Rashid Onboarding Component
 * Full-screen overlay for new users to set up their preferences
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '@/hooks/use-theme';
import { useAuth } from '@/hooks/use-auth';
import { RashidCharacter } from './character';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';
import { apiRequest } from '@/services/client';

interface OnboardingStep {
  question: { en: string; ar: string };
  options?: { value: string; label: { en: string; ar: string } }[];
  type: 'select' | 'text';
}

const STEPS: OnboardingStep[] = [
  {
    question: { en: "What's your career level?", ar: "إيه مستواك المهني؟" },
    options: [
      { value: 'junior', label: { en: 'Junior (0-2 years)', ar: 'مبتدئ (٠-٢ سنة)' } },
      { value: 'mid', label: { en: 'Mid (2-5 years)', ar: 'متوسط (٢-٥ سنوات)' } },
      { value: 'senior', label: { en: 'Senior (5+ years)', ar: 'خبير (٥+ سنوات)' } },
    ],
    type: 'select',
  },
  {
    question: { en: "What field do you work in?", ar: "إيه المجال اللي بتشتغل فيه؟" },
    type: 'text',
  },
  {
    question: { en: "What's your goal right now?", ar: "إيه هدفك دلوقتي؟" },
    options: [
      { value: 'find_job', label: { en: 'Find a job', ar: 'ألاقي شغل' } },
      { value: 'promotion', label: { en: 'Get promoted', ar: 'أترقى' } },
      { value: 'switch', label: { en: 'Switch career', ar: 'أغير مجالي' } },
      { value: 'learn', label: { en: 'Learn new skills', ar: 'أتعلم مهارات جديدة' } },
    ],
    type: 'select',
  },
];

export function RashidOnboarding() {
  const { lang } = useTheme();
  const { isAuthenticated } = useAuth();
  const isAr = lang === 'ar';

  // All hooks MUST be declared before any early return (React rules of hooks)
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);

  // Check if user has already been onboarded
  const hasOnboarded = typeof window !== 'undefined' && localStorage.getItem('rashid_onboarded') === 'true';

  // Don't show if not authenticated or already onboarded
  if (!isAuthenticated || hasOnboarded) {
    return null;
  }

  const handleSelectOption = (value: string) => {
    setAnswers(prev => ({ ...prev, [`step_${currentStep}`]: value }));
    
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(prev => prev + 1);
    } else {
      handleSubmit();
    }
  };

  const handleTextAnswer = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const value = formData.get('textAnswer') as string;
    
    if (value.trim()) {
      setAnswers(prev => ({ ...prev, [`step_${currentStep}`]: value }));
      
      if (currentStep < STEPS.length - 1) {
        setCurrentStep(prev => prev + 1);
      } else {
        handleSubmit();
      }
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      await apiRequest('/rashid/profile/complete_onboarding/', {
        method: 'POST',
        body: { answers },
      });

      localStorage.setItem('rashid_onboarded', 'true');
      setShowCelebration(true);
      setTimeout(() => {
        setShowCelebration(false);
      }, 3000);
    } catch (error) {
      console.error('Failed to submit onboarding:', error);
      // Even if API fails, mark as onboarded
      localStorage.setItem('rashid_onboarded', 'true');
      setShowCelebration(true);
      setTimeout(() => {
        setShowCelebration(false);
      }, 3000);
    } finally {
      setIsSubmitting(false);
    }
  };

  const currentStepData = STEPS[currentStep];
  const question = currentStepData.question[isAr ? 'ar' : 'en'];

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-md w-full mx-4 overflow-hidden"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-center">
          <h2 className="text-2xl font-bold text-white">
            {isAr ? 'مرحباً بك في رشيد!' : 'Welcome to Rasheed!'}
          </h2>
          <p className="text-blue-100 mt-2">
            {isAr ? 'دعني أتعلم أكثر عنك' : 'Let me learn more about you'}
          </p>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Progress */}
          <div className="flex justify-center gap-2 mb-6">
            {STEPS.map((_, index) => (
              <div
                key={index}
                className={`h-2 rounded-full transition-all duration-300 ${
                  index <= currentStep ? 'w-8 bg-blue-600' : 'w-2 bg-gray-200 dark:bg-gray-700'
                }`}
              />
            ))}
          </div>

          {/* Rashid Character */}
          <div className="flex justify-center mb-6">
            <RashidCharacter
              pose={showCelebration ? 'celebrating' : 'thinking'}
              size="md"
              className="w-32 h-64"
            />
          </div>

          {/* Question */}
          <div className="text-center mb-6">
            <h3 className="text-xl font-semibold text-foreground mb-2">
              {question}
            </h3>
            <p className="text-sm text-muted-foreground">
              {isAr ? 'اختر إجابة أو أدخل معلوماتك' : 'Choose an answer or enter your info'}
            </p>
          </div>

          {/* Content based on step type */}
          {showCelebration ? (
            <div className="text-center py-8">
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 0.5 }}
              >
                <div className="text-6xl mb-4">🎉</div>
              </motion.div>
              <h3 className="text-xl font-bold text-foreground mb-2">
                {isAr ? 'تم التسجيل بنجاح!' : 'Registration Complete!'}
              </h3>
              <p className="text-muted-foreground">
                {isAr ? 'رشيد جاهز لمساعدتك' : 'Rasheed is ready to help you'}
              </p>
            </div>
          ) : currentStepData.type === 'select' ? (
            <div className="space-y-3">
              {currentStepData.options?.map((option) => (
                <Button
                  key={option.value}
                  variant="outline"
                  className="w-full py-4 text-lg"
                  onClick={() => handleSelectOption(option.value)}
                  disabled={isSubmitting}
                >
                  {option.label[isAr ? 'ar' : 'en']}
                </Button>
              ))}
            </div>
          ) : (
            <form onSubmit={handleTextAnswer} className="space-y-4">
              <input
                type="text"
                name="textAnswer"
                placeholder={isAr ? 'أدخل إجابتك...' : 'Enter your answer...'}
                className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground focus:ring-2 focus:ring-blue-500 focus:outline-none"
                required
              />
              <Button
                type="submit"
                className="w-full py-3"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : isAr ? 'التالي' : 'Next'}
              </Button>
            </form>
          )}

          {/* Skip button */}
          <div className="mt-6 text-center">
            <button
              onClick={() => {
                localStorage.setItem('rashid_onboarded', 'true');
              }}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              {isAr ? 'تخطي الآن' : 'Skip for now'}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}