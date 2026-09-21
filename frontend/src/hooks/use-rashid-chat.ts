/**
 * useRashidChat Hook
 * Opens the live RasheedCompanion assistant (globally mounted) via custom
 * events. `rashid:open-tool` carries a tool + context; `rashid:open` just
 * opens the chat. RasheedCompanion listens for both.
 */

import { useState, useCallback } from 'react';

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
  context?: Record<string, unknown>;
}

export function useRashidChat() {
  const [currentTool, setCurrentTool] = useState<RashidTool | null>(null);
  const [context, setContext] = useState<Record<string, unknown> | null>(null);

  const openRashidChat = useCallback((tool: RashidTool, contextData?: Record<string, unknown>) => {
    setCurrentTool(tool);
    setContext(contextData || {});
    window.dispatchEvent(
      new CustomEvent('rashid:open-tool', { detail: { tool, context: contextData || {} } }),
    );
  }, []);

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
