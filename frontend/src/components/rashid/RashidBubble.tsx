/**
 * Rashid Speech Bubble Component
 * Shows contextual hints based on current page
 */

import { motion } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { useTheme } from '@/hooks/use-theme';
import { useRashidChat } from '@/hooks/use-rashid-chat';

interface RashidBubbleProps {
  show: boolean;
  onClose?: () => void;
}

const getGreeting = (pathname: string, lang: string): string => {
  const isAr = lang === 'ar';
  
  const greetings: Record<string, { en: string; ar: string }> = {
    '/jobs': {
      en: 'Want me to help you find a suitable job?',
      ar: 'عايز أساعدك تلاقي وظيفة مناسبة؟',
    },
    '/app/jobs': {
      en: 'Want me to help you find a suitable job?',
      ar: 'عايز أساعدك تلاقي وظيفة مناسبة؟',
    },
    '/app/jobs/': {
      en: 'Want me to analyze this job for you?',
      ar: 'عايز أحللك الوظيفة دي؟',
    },
    '/profile': {
      en: 'Shall I review your CV?',
      ar: 'أراجعلك السيرة الذاتية؟',
    },
    '/app/profile': {
      en: 'Shall I review your CV?',
      ar: 'أراجعلك السيرة الذاتية؟',
    },
    '/app/employer': {
      en: 'Need help with hiring?',
      ar: 'محتاج مساعدة في التوظيف؟',
    },
    '/app/employer/': {
      en: 'Need help with hiring?',
      ar: 'محتاج مساعدة في التوظيف؟',
    },
    default: {
      en: "Hi! I'm Rasheed, your career advisor",
      ar: 'أهلاً! أنا راشد، مستشارك المهني',
    },
  };

  // Find matching route
  for (const [route, greeting] of Object.entries(greetings)) {
    if (route === 'default') continue;
    if (pathname.startsWith(route)) {
      return isAr ? greeting.ar : greeting.en;
    }
  }

  return isAr ? greetings.default.ar : greetings.default.en;
};

export function RashidBubble({ show, onClose }: RashidBubbleProps) {
  const location = useLocation();
  const { lang } = useTheme();
  const { openRashidChat } = useRashidChat();

  const greeting = getGreeting(location.pathname, lang);

  if (!show) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.8, y: 20 }}
      transition={{ type: 'spring', duration: 0.5 }}
      className="absolute -top-24 right-0 w-64 bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-4 z-50 border border-gray-200 dark:border-gray-700"
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
          <span className="text-2xl">👋</span>
        </div>
        <div className="flex-1">
          <p className="text-sm text-gray-700 dark:text-gray-200 font-medium">
            {greeting}
          </p>
          <button
            onClick={onClose}
            className="mt-2 text-xs text-blue-600 dark:text-blue-400 hover:underline"
          >
            {lang === 'ar' ? 'إغلاق' : 'Close'}
          </button>
          <button
            onClick={() => {
              openRashidChat('cv_review');
            }}
            className="mt-2 text-xs text-primary hover:underline"
          >
            {lang === 'ar' ? 'ابدأ المحادثة' : 'Start Chat'}
          </button>
        </div>
      </div>
      
      {/* Arrow pointing to the character */}
      <div className="absolute bottom-0 right-6 -mb-2 w-4 h-4 bg-white dark:bg-gray-800 rotate-45 border-b border-r border-gray-200 dark:border-gray-700" />
    </motion.div>
  );
}