/**
 * Ask Rashid Button Component
 * Shows a card with Rashid avatar and action buttons for job-related assistance
 * Uses RashidCharacter component with proper pose animations
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { MessageCircle, FileText, Briefcase, User, GraduationCap } from 'lucide-react';
import { motion } from 'framer-motion';
import { RashidCharacter } from './character';

type RashidTool = 
  | 'analyze_job'
  | 'cover_letter'
  | 'interview_prep'
  | 'cv_review'
  | 'linkedin_optimizer'
  | 'course_advisor'
  | 'career_path';

interface AskRashidButtonProps {
  tool: RashidTool;
  context?: Record<string, any>;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const TOOL_ICONS = {
  analyze_job: MessageCircle,
  cover_letter: FileText,
  interview_prep: Briefcase,
  cv_review: User,
  linkedin_optimizer: MessageCircle,
  course_advisor: GraduationCap,
  career_path: Briefcase,
};

const TOOL_LABELS = {
  analyze_job: { en: 'Analyze Job', ar: 'حلل الوظيفة' },
  cover_letter: { en: 'Cover Letter', ar: 'اكتب Cover Letter' },
  interview_prep: { en: 'Interview Prep', ar: 'حضرني للمقابلة' },
  cv_review: { en: 'Review CV', ar: 'راجع السيرة الذاتية' },
  linkedin_optimizer: { en: 'Optimize LinkedIn', ar: 'تحسين لينكد إن' },
  course_advisor: { en: 'Course Advisor', ar: 'استشارة الدورات' },
  career_path: { en: 'Career Path', ar: 'المسار المهني' },
};

export function AskRashidButton({ 
  tool, 
  context = {}, 
  label,
  size = 'md',
  className = '' 
}: AskRashidButtonProps) {
  const [isProcessing, setIsProcessing] = useState(false);

  const handleOpenRashid = () => {
    setIsProcessing(true);
    
    // Dispatch custom event that RashidWidget listens for
    const event = new CustomEvent('rashid:open-tool', { 
      detail: { tool, context } 
    });
    window.dispatchEvent(event);
    
    // Close expanded state after a short delay
    setTimeout(() => setIsProcessing(false), 500);
  };

  const Icon = TOOL_ICONS[tool];
  const labelText = (label && typeof label === 'string') ? label : TOOL_LABELS[tool].en;

  const sizeClasses = {
    sm: 'h-8 px-3 text-xs',
    md: 'h-10 px-4 text-sm',
    lg: 'h-12 px-6 text-base',
  };

  return (
    <motion.button
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={handleOpenRashid}
      disabled={isProcessing}
      className={`
        ${sizeClasses[size]}
        ${className}
        flex items-center justify-center gap-2
        bg-blue-600 hover:bg-blue-700 text-white
        rounded-lg font-medium transition-all
        disabled:opacity-50 disabled:cursor-not-allowed
      `}
    >
      {isProcessing ? (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 1 }}
        >
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
        </motion.div>
      ) : (
        <>
          <Icon className="w-4 h-4" />
          <span>{labelText}</span>
        </>
      )}
    </motion.button>
  );
}

// Full card component for job detail page
export function AskRashidCard({ jobSlug, isAr }: { jobSlug: string; isAr: boolean }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="bg-blue-50/50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800/30 rounded-2xl p-5"
    >
      <div className="flex items-start gap-4">
        <RashidCharacter pose="presenting" size="sm" className="w-12 h-12" />
        
        <div className="flex-1">
          <h3 className="text-base font-semibold text-foreground mb-2">
            {isAr ? 'عايز أساعدك في الوظيفة دي؟' : 'Need help with this job?'}
          </h3>

          {expanded ? (
            <div className="space-y-2">
              <AskRashidButton 
                tool="analyze_job" 
                context={{ jobSlug }}
                label="Analyze Job"
                size="sm"
              />
              <AskRashidButton 
                tool="cover_letter" 
                context={{ jobSlug }}
                label="Cover Letter"
                size="sm"
              />
              <AskRashidButton 
                tool="interview_prep" 
                context={{ jobSlug }}
                label="Interview Prep"
                size="sm"
              />
            </div>
          ) : (
            <Button
              variant="outline"
              className="mt-2 w-full"
              onClick={() => setExpanded(true)}
            >
              {isAr ? 'عرض الخيارات' : 'Show Options'}
            </Button>
          )}
        </div>
      </div>
    </motion.div>
  );
}