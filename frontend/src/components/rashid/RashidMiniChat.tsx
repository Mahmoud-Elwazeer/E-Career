/**
 * Rashid Mini Chat Component
 * Embedded chat panel that appears when widget is clicked
 */

import { useState, useEffect, useRef } from 'react';
import { Send, X, MessageSquare, ChevronDown, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/hooks/use-auth';
import { useTheme } from '@/hooks/use-theme';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface Message {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

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

interface RashidMiniChatProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenFullChat: () => void;
  conversationId?: string;
  initialTool?: RashidToolContext;
}

export function RashidMiniChat({ 
  isOpen, 
  onClose, 
  onOpenFullChat,
  conversationId,
  initialTool
}: RashidMiniChatProps) {
  const { isAuthenticated } = useAuth();
  const { lang } = useTheme();
  const isAr = lang === 'ar';
  const dir = isAr ? 'rtl' : 'ltr';

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showMessages, setShowMessages] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch existing messages if conversation exists
  useEffect(() => {
    if (conversationId && isAuthenticated) {
      // In a real app, fetch messages from API
      // For now, show a welcome message
      setMessages([
        {
          role: 'assistant',
          content: isAr 
            ? 'أهلاً! أنا راشد، مستشارك المهني. كيف يمكنني مساعدتك اليوم؟'
            : "Hi! I'm Rashid, your career advisor. How can I help you today?",
          timestamp: new Date().toISOString(),
        },
      ]);
    }
  }, [conversationId, isAuthenticated, isAr]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (showMessages) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, showMessages]);

  // WebSocket connection
  useEffect(() => {
    if (!isAuthenticated || !isOpen) return;

    const wsUrl = conversationId
      ? `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/rashid/${conversationId}/`
      : `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/rashid/`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'message') {
        setMessages((prev) => [
          ...prev,
          {
            role: data.role as 'user' | 'assistant',
            content: data.content,
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [isAuthenticated, isOpen, conversationId]);

  const handleSendMessage = () => {
    if (!inputMessage.trim() || !isConnected) return;

    const userMessage: Message = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setIsProcessing(true);

    // Send to WebSocket
    wsRef.current?.send(JSON.stringify({ type: 'message', content: userMessage.content }));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 100, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 100, scale: 0.95 }}
      transition={{ type: 'spring', duration: 0.4 }}
      className="fixed bottom-24 right-4 md:right-8 w-[380px] md:w-[400px] h-[550px] md:h-[600px] bg-white dark:bg-gray-900 rounded-2xl shadow-2xl overflow-hidden z-50 border border-gray-200 dark:border-gray-700 flex flex-col"
    >
      {/* Header */}
      <div className="bg-blue-600 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
            <span className="text-xl">👋</span>
          </div>
          <div>
            <h3 className="text-white font-semibold text-lg">راشد</h3>
            <p className="text-blue-100 text-xs flex items-center gap-1">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              {isConnected ? (isAr ? 'متصل' : 'Online') : (isAr ? 'يتصل' : 'Connecting...')}
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-white/80 hover:text-white hover:bg-white/20 rounded-full p-1 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-gray-950">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
            <MessageSquare className="w-12 h-12 mb-2 opacity-50" />
            <p>{isAr ? 'ابدأ المحادثة' : 'Start the conversation'}</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.timestamp + Math.random()}
              className={cn(
                'max-w-[85%] p-3 rounded-2xl text-sm',
                msg.role === 'user'
                  ? 'bg-blue-600 text-white ml-auto rounded-br-none'
                  : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 mr-auto rounded-bl-none border border-gray-200 dark:border-gray-700'
              )}
            >
              {msg.content}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-3 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isAr ? 'اكتب رسالتك...' : 'Type your message...'}
            className="flex-1 px-4 py-2 bg-gray-100 dark:bg-gray-800 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
            disabled={isProcessing || !isConnected}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isProcessing || !isConnected}
            className="p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isProcessing ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
        <button
          onClick={onOpenFullChat}
          className="mt-2 text-xs text-blue-600 dark:text-blue-400 hover:underline w-full text-center"
        >
          {isAr ? 'فتح المحادثة الكاملة' : 'Open full chat'}
        </button>
      </div>
    </motion.div>
  );
}