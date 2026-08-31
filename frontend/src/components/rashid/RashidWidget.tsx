/**
 * Rashid Widget Component
 * Main floating character widget that appears on all pages
 */

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/hooks/use-auth';
import { useTheme } from '@/hooks/use-theme';
import { useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { RashidBubble } from './RashidBubble';
import { RashidMiniChat } from './RashidMiniChat';
import { RashidCharacter } from './character';

type RashidTool = 
  | 'cv_review'
  | 'cover_letter'
  | 'interview_prep'
  | 'linkedin_optimizer'
  | 'course_advisor'
  | 'analyze_job'
  | 'career_path';

interface RashidToolContext {
  tool?: RashidTool;
  context?: Record<string, any>;
}

export function RashidWidget() {
  const { isAuthenticated } = useAuth();
  const { lang } = useTheme();
  const location = useLocation();

  const [isExpanded, setIsExpanded] = useState(false);
  const [showBubble, setShowBubble] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
   const [isMobile, setIsMobile] = useState(false);
   const [toolToOpen, setToolToOpen] = useState<RashidTool | null>(null);
   const [toolContext, setToolContext] = useState<Record<string, any> | null>(null);
   const [widgetState, setWidgetState] = useState<'idle' | 'talking' | 'thinking' | 'listening'>('idle');
   const widgetRef = useRef<HTMLDivElement>(null);

  // Check if mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

   // Listen for custom events to open with specific tool
   useEffect(() => {
     const handleRashidOpen = (event: CustomEvent<RashidToolContext>) => {
       const { tool, context } = event.detail || {};
       if (tool) {
         setToolToOpen(tool);
         setToolContext(context || {});
         setIsExpanded(true);
       }
     };

     window.addEventListener('rashid:open', handleRashidOpen as EventListener);
     return () => window.removeEventListener('rashid:open', handleRashidOpen as EventListener);
   }, []);

   // Listen for tool-specific events from AskRashidButton
   useEffect(() => {
     const handleRashidOpenTool = (event: CustomEvent) => {
       const { tool, context } = event.detail || {};
       if (tool) {
         setToolToOpen(tool);
         setToolContext(context || {});
         setIsExpanded(true);
       }
     };

     window.addEventListener('rashid:open-tool', handleRashidOpenTool as EventListener);
     return () => window.removeEventListener('rashid:open-tool', handleRashidOpenTool as EventListener);
   }, []);

   // Show bubble after delay on page load (only once per day)
   useEffect(() => {
     if (!isAuthenticated || isMobile) return;

     const lastDismissed = localStorage.getItem('rashid_last_dismissed');
     const now = Date.now();
     const oneDay = 24 * 60 * 60 * 1000;

     if (!lastDismissed || now - parseInt(lastDismissed) > oneDay) {
       const timer = setTimeout(() => {
         setShowBubble(true);
         // Show wave pose briefly on first appearance
         setWidgetState('talking');
         setTimeout(() => setWidgetState('idle'), 3000);
       }, 2000);
       return () => clearTimeout(timer);
     }
   }, [isAuthenticated, isMobile]);

  // Persist conversation ID
  useEffect(() => {
    const savedConvId = localStorage.getItem('rashid_conversation_id');
    if (savedConvId) {
      setConversationId(savedConvId);
    }
  }, []);

  const handleWidgetClick = () => {
    if (isMobile) {
      // On mobile, expand to full screen
      setIsExpanded(true);
    } else {
      // On desktop, toggle mini chat
      setIsExpanded(!isExpanded);
    }
  };

  const handleOpenFullChat = () => {
    setIsExpanded(false);
    window.location.href = '/app/rashid';
  };

  const handleBubbleClose = () => {
    setShowBubble(false);
    localStorage.setItem('rashid_last_dismissed', Date.now().toString());
  };

  // Pass tool to mini chat when opening
  const getInitialTool = () => {
    if (toolToOpen) {
      const tool = toolToOpen;
      const context = toolContext;
      setToolToOpen(null);
      setToolContext(null);
      return { tool, context };
    }
    return null;
  };

  const handleConversationStart = (id: string) => {
    setConversationId(id);
    localStorage.setItem('rashid_conversation_id', id);
  };

  if (!isAuthenticated) return null;

  return (
    <>
      {/* Floating Widget */}
      <motion.div
        initial={{ opacity: 0, scale: 0.8, y: 50 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ type: 'spring', duration: 0.5 }}
        className="fixed bottom-6 right-6 z-50"
      >
        <div className="relative">
          {/* Chat Panel (Desktop) */}
          {!isMobile && (
            <RashidMiniChat
              isOpen={isExpanded}
              onClose={() => setIsExpanded(false)}
              onOpenFullChat={handleOpenFullChat}
              conversationId={conversationId}
              initialTool={getInitialTool()}
            />
          )}

          {/* Chat Panel (Mobile - Full Screen) */}
          {isMobile && (
            <motion.div
              initial={{ opacity: 0, y: '100%' }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: '100%' }}
              className="fixed inset-0 bg-white dark:bg-gray-900 z-[60] flex flex-col"
            >
              <div className="bg-blue-600 p-4 flex items-center justify-between">
                <h2 className="text-white font-semibold text-lg">راشد</h2>
                <button
                  onClick={() => setIsExpanded(false)}
                  className="text-white hover:bg-white/20 rounded-full p-2"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-4">
                <RashidMiniChat
                  isOpen={true}
                  onClose={() => setIsExpanded(false)}
                  onOpenFullChat={handleOpenFullChat}
                  conversationId={conversationId}
                  initialTool={getInitialTool()}
                />
              </div>
            </motion.div>
          )}

          {/* Speech Bubble */}
          <RashidBubble show={showBubble} onClose={handleBubbleClose} />

           {/* Character Avatar */}
           <motion.button
             onClick={handleWidgetClick}
             className="relative group"
             whileHover={{ scale: 1.1 }}
             whileTap={{ scale: 0.95 }}
           >
             <RashidCharacter 
               pose={isExpanded ? 'listening' : widgetState === 'talking' ? 'wave' : 'bust'}
               size={isMobile ? 'sm' : 'md'}
               className="w-12 h-12 md:w-16 md:h-16"
             />
             
             {/* Tooltip */}
             <div className="absolute -top-12 right-0 bg-gray-900 text-white text-xs px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50">
               {lang === 'ar' ? 'راشد - مساعدك المهني' : 'Rasheed - Your Career Advisor'}
             </div>
           </motion.button>
        </div>
      </motion.div>
    </>
  );
}