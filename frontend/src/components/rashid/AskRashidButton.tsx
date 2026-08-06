/**
 * Ask Rashid Button Component
 * Shows a card with Rashid avatar and action buttons for job-related assistance
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { MessageCircle, FileText, Briefcase } from 'lucide-react';
import { motion } from 'framer-motion';

interface AskRashidButtonProps {
  jobSlug: string;
  isAr: boolean;
}

export function AskRashidButton({ jobSlug, isAr }: AskRashidButtonProps) {
  const [expanded, setExpanded] = useState(false);

  const handleAnalyzeJob = () => {
    // Open Rashid widget with analyze_job tool
    const event = new CustomEvent('rashid:open', { detail: { tool: 'analyze_job', context: { jobSlug } } });
    window.dispatchEvent(event);
  };

  const handleWriteCoverLetter = () => {
    // Open Rashid widget with cover_letter tool
    const event = new CustomEvent('rashid:open', { detail: { tool: 'cover_letter', context: { jobSlug } } });
    window.dispatchEvent(event);
  };

  const handlePrepInterview = () => {
    // Open Rashid widget with interview_prep tool
    const event = new CustomEvent('rashid:open', { detail: { tool: 'interview_prep', context: { jobSlug } } });
    window.dispatchEvent(event);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="bg-card rounded-2xl p-5 border border-border shadow-sm"
    >
      <div className="flex items-start gap-4">
        {/* Rashid Avatar */}
        <div className="flex-shrink-0 w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
          <span className="text-2xl">👋</span>
        </div>

        <div className="flex-1">
          <h3 className="text-base font-semibold text-foreground mb-2">
            {isAr ? 'عايز أساعدك في الوظيفة دي؟' : 'Want help with this job?'}
          </h3>

          {expanded ? (
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-start gap-2 h-10 text-sm"
                onClick={handleAnalyzeJob}
              >
                <MessageCircle className="w-4 h-4" />
                {isAr ? 'حلل الوظيفة' : 'Analyze Job'}
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start gap-2 h-10 text-sm"
                onClick={handleWriteCoverLetter}
              >
                <FileText className="w-4 h-4" />
                {isAr ? 'اكتب Cover Letter' : 'Write Cover Letter'}
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start gap-2 h-10 text-sm"
                onClick={handlePrepInterview}
              >
                <Briefcase className="w-4 h-4" />
                {isAr ? 'حضرني للمقابلة' : 'Prep for Interview'}
              </Button>
            </div>
          ) : (
            <Button
              variant="default"
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