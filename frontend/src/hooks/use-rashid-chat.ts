/**
 * useRashidChat Hook
 * Manages Rashid chat interactions across the app
 */

import { useState, useCallback } from 'react';
import { useRashidWidget } from '@/hooks/use-rashid-widget';

export type RashidTool = 
  | 'cv_review'
  | 'cover_letter'
  | 'interview_prep'
  | 'linkedin_optimizer'
  | 'course_advisor'
  | 'analyze_job'
  | 'career_path';

export interface RashidChatOptions {
  tool?: RashidTool;
  context?: Record<string, any>;
}

export function useRashidChat() {
  const { openWidget } = useRashidWidget();
  const [currentTool, setCurrentTool] = useState<RashidTool | null>(null);
  const [context, setContext] = useState<Record<string, any> | null>(null);

  const openRashidChat = useCallback((tool: RashidTool, contextData?: Record<string, any>) => {
    setCurrentTool(tool);
    setContext(contextData || {});
    openWidget();
  }, [openWidget]);

  const closeRashidChat = useCallback(() => {
    setCurrentTool(null);
    setContext(null);
  }, []);

  return {
    currentTool,
    context,
    openRashidChat,
    closeRashidChat,
  };
}