/**
 * Rashid Mini Chat Component
 * Embedded chat panel that appears when widget is clicked
 * Uses REST API for production (WebSocket fallback for development)
 */

import { useState, useEffect, useRef } from 'react';
import { Send, X, MessageSquare, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/hooks/use-auth';
import { useTheme } from '@/hooks/use-theme';
import { getAccessToken } from '@/services/client';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

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

interface Message {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface RashidMiniChatProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenFullChat: () => void;
  conversationId?: string;
  initialTool?: RashidToolContext;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

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
  const queryClient = useQueryClient();

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [localConversationId, setLocalConversationId] = useState<string | undefined>(conversationId);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'error'>('connecting');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load messages when conversation exists
  const { data: messagesData, isLoading: messagesLoading } = useQuery({
    queryKey: ['rashid-messages', localConversationId],
    queryFn: async () => {
      if (!localConversationId) return [];
      const response = await fetch(`${API_BASE_URL}/rashid/conversations/${localConversationId}/messages/`, {
        headers: {
          'Authorization': `Bearer ${getAccessToken()}`,
        },
      });
      if (!response.ok) throw new Error('Failed to fetch messages');
      return response.json();
    },
    enabled: !!localConversationId && isOpen,
  });

  // Create conversation mutation
  const createConversationMutation = useMutation({
    mutationFn: async (mode: string = 'general') => {
      const response = await fetch(`${API_BASE_URL}/rashid/conversations/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAccessToken()}`,
        },
        body: JSON.stringify({ mode }),
      });
      if (!response.ok) throw new Error('Failed to create conversation');
      return response.json();
    },
    onSuccess: (data) => {
      setLocalConversationId(data.id);
      localStorage.setItem('rashid_conversation_id', data.id);
      setConnectionStatus('connected');
    },
  });

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: async ({ conversationId, content }: { conversationId: string; content: string }) => {
      const response = await fetch(`${API_BASE_URL}/rashid/conversations/${conversationId}/send_message/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAccessToken()}`,
        },
        body: JSON.stringify({ message: content }),
      });
      if (!response.ok) throw new Error('Failed to send message');
      return response.json();
    },
    onSuccess: (data, variables) => {
      // Add user message
      const userMessage: Message = {
        role: 'user',
        content: variables.content,
        timestamp: new Date().toISOString(),
      };

      // Add assistant response
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.assistant_response,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setInputMessage('');
      setIsProcessing(false);
    },
    onError: () => {
      setIsProcessing(false);
      setConnectionStatus('error');
    },
  });

  // Load initial messages
  useEffect(() => {
    if (messagesData && messagesData.length > 0) {
      setMessages(messagesData.map((msg: any) => ({
        role: msg.role as 'user' | 'assistant',
        content: msg.content,
        timestamp: msg.created_at || new Date().toISOString(),
      })));
    }
  }, [messagesData]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isProcessing]);

  // Initialize conversation on open
  useEffect(() => {
    if (isOpen && !localConversationId) {
      createConversationMutation.mutate('general');
    }
  }, [isOpen, localConversationId, createConversationMutation]);

  // Handle initial tool from widget
  useEffect(() => {
    if (initialTool && localConversationId && messages.length === 0) {
      // Send initial tool command
      const toolCommand = isAr 
        ? `استخدم أداة ${initialTool.tool}` 
        : `Use tool: ${initialTool.tool}`;
      
      sendMessageMutation.mutate({
        conversationId: localConversationId,
        content: toolCommand,
      });
    }
  }, [initialTool, localConversationId, messages.length, isAr, sendMessageMutation]);

  const handleSendMessage = () => {
    if (!inputMessage.trim() || !localConversationId || isProcessing) return;

    setIsProcessing(true);
    sendMessageMutation.mutate({
      conversationId: localConversationId,
      content: inputMessage,
    });
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
              <span className={`w-2 h-2 rounded-full ${connectionStatus === 'connected' ? 'bg-green-400' : connectionStatus === 'connecting' ? 'bg-yellow-400 animate-pulse' : 'bg-red-400'}`} />
              {connectionStatus === 'connected' ? (isAr ? 'متصل' : 'Online') : connectionStatus === 'connecting' ? (isAr ? 'يتصل' : 'Connecting...') : (isAr ? 'خطأ' : 'Error')}
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
        {messagesLoading ? (
          <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
            <MessageSquare className="w-12 h-12 mb-2 opacity-50" />
            <p>{isAr ? 'ابدأ المحادثة' : 'Start the conversation'}</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
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
        {isProcessing && (
          <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>{isAr ? 'جاري الرد...' : 'Typing...'}</span>
          </div>
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
            disabled={isProcessing || connectionStatus !== 'connected'}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isProcessing || connectionStatus !== 'connected'}
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