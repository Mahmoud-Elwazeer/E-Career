/**
 * Rashid AI Chat Page
 * Real-time WebSocket chat with the Egyptian Arabic AI career mentor
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Send, Loader2, Wifi, WifiOff, MessageSquare, Plus, Trash2, ChevronDown, Wrench } from 'lucide-react';
import { Layout } from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/use-auth';
import { useTheme } from '@/hooks/use-theme';
import { getAccessToken } from '@/services/client';
import { cn } from '@/lib/utils';
import ToolSelector from '@/components/rashid/ToolSelector';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

interface Message {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface Conversation {
  id: string;
  mode: string;
  title: string;
  last_message?: {
    role: string;
    preview: string;
    timestamp: string;
  };
}

const MODES = [
  { value: 'general', label: 'General Chat', labelAr: 'محادثة عامة' },
  { value: 'career_path', label: 'Career Path', labelAr: 'المسار المهني' },
  { value: 'cv_review', label: 'CV Review', labelAr: 'مراجعة السيرة الذاتية' },
  { value: 'interview_prep', label: 'Interview Prep', labelAr: 'التحضير للمقابلة' },
  { value: 'cover_letter', label: 'Cover Letter', labelAr: 'خطاب التقديم' },
  { value: 'linkedin', label: 'LinkedIn', labelAr: 'لينكد إن' },
  { value: 'course_advisor', label: 'Course Advisor', labelAr: 'استشارة الدورات' },
  { value: 'salary_negotiation', label: 'Salary', labelAr: 'التفاوض على الراتب' },
];

export default function RashidChat() {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { lang } = useTheme();
  const isAr = lang === 'ar';
  const dir = isAr ? 'rtl' : 'ltr';

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showModeSelect, setShowModeSelect] = useState(false);
  const [selectedMode, setSelectedMode] = useState('general');
   const [showTools, setShowTools] = useState(false);

   const wsRef = useRef<WebSocket | null>(null);
   const messagesEndRef = useRef<HTMLDivElement>(null);
   const inputRef = useRef<HTMLInputElement>(null);
   const [useWebSocket, setUseWebSocket] = useState(true);
   const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'rest' | 'error'>('connecting');
   const [restMessages, setRestMessages] = useState<Message[]>([]);
   const [restProcessing, setRestProcessing] = useState(false);
   const restIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: '/app/rashid' } });
    }
  }, [isAuthenticated, navigate]);

  // Fetch conversations
  useEffect(() => {
    if (isAuthenticated) {
      fetchConversations();
    }
  }, [isAuthenticated]);

   // WebSocket connection with REST fallback
   useEffect(() => {
     if (!isAuthenticated) return;

     // Try WebSocket first
     const wsUrl = conversationId
       ? `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/rashid/${conversationId}/`
       : `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/rashid/`;

     const ws = new WebSocket(wsUrl);
     wsRef.current = ws;

     let wsConnected = false;
     const wsConnectTimer = setTimeout(() => {
       if (!wsConnected && !useWebSocket) {
         // WebSocket failed, switch to REST
         setConnectionStatus('rest');
         setUseWebSocket(false);
         console.log('WebSocket failed, switching to REST API');
       }
     }, 3000);

     ws.onopen = () => {
       wsConnected = true;
       clearTimeout(wsConnectTimer);
       setConnectionStatus('connected');
       setUseWebSocket(true);
       console.log('WebSocket connected');
     };

     ws.onmessage = (event) => {
       const data = JSON.parse(event.data);

       if (data.type === 'message') {
         setMessages((prev) => [
           ...prev,
           {
             role: data.role,
             content: data.content,
             timestamp: data.timestamp,
           },
         ]);
         setIsProcessing(false);
       } else if (data.type === 'message_received') {
         setIsProcessing(true);
       } else if (data.type === 'tool_processing') {
         setIsProcessing(true);
         setMessages((prev) => [
           ...prev,
           {
             role: 'assistant',
             content: isAr ? `جاري تنفيذ ${data.tool}...` : `Executing ${data.tool}...`,
             timestamp: new Date().toISOString(),
           },
         ]);
       } else if (data.type === 'tool_result') {
         setMessages((prev) => [
           ...prev.slice(0, -1), // Remove processing message
           {
             role: 'assistant',
             content: data.result,
             timestamp: data.timestamp,
           },
         ]);
         setIsProcessing(false);
       } else if (data.type === 'error') {
         console.error('WebSocket error:', data.message);
         setIsProcessing(false);
       }
     };

     ws.onclose = () => {
       if (useWebSocket) {
         setConnectionStatus('error');
         console.log('WebSocket disconnected');
       }
     };

     ws.onerror = (error) => {
       if (useWebSocket) {
         setConnectionStatus('error');
         console.error('WebSocket error:', error);
       }
     };

     return () => {
       ws.close();
       clearTimeout(wsConnectTimer);
       if (restIntervalRef.current) {
         clearInterval(restIntervalRef.current);
       }
     };
   }, [conversationId, isAuthenticated, useWebSocket]);

   // REST API polling for messages (fallback mode)
   useEffect(() => {
     if (!useWebSocket && conversationId && connectionStatus === 'rest') {
       const fetchMessages = async () => {
         try {
           const response = await fetch(`${API_BASE_URL}/rashid/conversations/${conversationId}/messages/`, {
             headers: {
               Authorization: `Bearer ${getAccessToken()}`,
             },
           });
           if (response.ok) {
             const data = await response.json();
             const newMessages = data.map((msg: any) => ({
               role: msg.role as 'user' | 'assistant',
               content: msg.content,
               timestamp: msg.created_at || new Date().toISOString(),
             }));
             setRestMessages(newMessages);
           }
         } catch (error) {
           console.error('Error fetching messages via REST:', error);
         }
       };

       fetchMessages();
       restIntervalRef.current = setInterval(fetchMessages, 2000);
     }

     return () => {
       if (restIntervalRef.current) {
         clearInterval(restIntervalRef.current);
       }
     };
   }, [useWebSocket, conversationId, connectionStatus]);

   const fetchConversations = async () => {
     try {
       const response = await fetch(
         `${API_BASE_URL}/rashid/conversations/`,
         {
           headers: {
             Authorization: `Bearer ${getAccessToken()}`,
           },
         }
       );
       if (response.ok) {
         const data = await response.json();
         setConversations(data.results || data);
       }
     } catch (error) {
       console.error('Error fetching conversations:', error);
     }
   };

   const startNewConversation = async (mode: string = 'general') => {
     try {
       const response = await fetch(
         `${API_BASE_URL}/rashid/conversations/`,
         {
           method: 'POST',
           headers: {
             'Content-Type': 'application/json',
             Authorization: `Bearer ${getAccessToken()}`,
           },
           body: JSON.stringify({ mode }),
         }
       );

       if (response.ok) {
         const data = await response.json();
         setMessages([]);
         navigate(`/app/rashid/${data.id}`);
         fetchConversations();
       }
     } catch (error) {
       console.error('Error starting conversation:', error);
     }
   };

   const handleSendMessage = useCallback(() => {
     if (!inputMessage.trim()) return;

     const message = inputMessage.trim();
     setInputMessage('');

     if (useWebSocket && wsRef.current && connectionStatus === 'connected') {
       // Send via WebSocket
       setMessages((prev) => [
         ...prev,
         {
           role: 'user',
           content: message,
           timestamp: new Date().toISOString(),
         },
       ]);

       wsRef.current.send(
         JSON.stringify({
           type: 'message',
           message,
         })
       );

       setIsProcessing(true);
     } else {
       // Send via REST API
       setRestMessages((prev) => [
         ...prev,
         {
           role: 'user',
           content: message,
           timestamp: new Date().toISOString(),
         },
       ]);
       setRestProcessing(true);

       fetch(`${API_BASE_URL}/rashid/conversations/${conversationId}/send_message/`, {
         method: 'POST',
         headers: {
           'Content-Type': 'application/json',
           Authorization: `Bearer ${getAccessToken()}`,
         },
         body: JSON.stringify({ message }),
       })
         .then((res) => res.json())
         .then((data) => {
           setRestMessages((prev) => [
             ...prev,
             {
               role: 'assistant',
               content: data.assistant_response,
               timestamp: new Date().toISOString(),
             },
           ]);
           setRestProcessing(false);
         })
         .catch((err) => {
           console.error('REST send error:', err);
           setRestProcessing(false);
         });
     }

     inputRef.current?.focus();
   }, [inputMessage, useWebSocket, wsRef.current, connectionStatus, conversationId]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const deleteConversation = async (id: string) => {
    try {
      await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/rashid/conversations/${id}/`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${getAccessToken()}`,
          },
        }
      );
      fetchConversations();
      if (conversationId === id) {
        navigate('/app/rashid');
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  };

   const handleToolSelection = useCallback((toolName: string) => {
     setShowTools(false);

     if (useWebSocket && wsRef.current && connectionStatus === 'connected') {
       // Send via WebSocket
       wsRef.current.send(
         JSON.stringify({
           type: 'tool',
           tool: toolName,
           context: {}
         })
       );

       setMessages((prev) => [
         ...prev,
         {
           role: 'user',
           content: isAr ? `استخدام أداة: ${toolName}` : `Using tool: ${toolName}`,
           timestamp: new Date().toISOString(),
         },
       ]);

       setIsProcessing(true);
     } else {
       // Send via REST API
       setRestMessages((prev) => [
         ...prev,
         {
           role: 'user',
           content: isAr ? `استخدام أداة: ${toolName}` : `Using tool: ${toolName}`,
           timestamp: new Date().toISOString(),
         },
       ]);
       setRestProcessing(true);

       fetch(`${API_BASE_URL}/rashid/conversations/${conversationId}/send_message/`, {
         method: 'POST',
         headers: {
           'Content-Type': 'application/json',
           Authorization: `Bearer ${getAccessToken()}`,
         },
         body: JSON.stringify({ message: `Use tool: ${toolName}` }),
       })
         .then((res) => res.json())
         .then((data) => {
           setRestMessages((prev) => [
             ...prev,
             {
               role: 'assistant',
               content: data.assistant_response,
               timestamp: new Date().toISOString(),
             },
           ]);
           setRestProcessing(false);
         })
         .catch((err) => {
           console.error('REST tool error:', err);
           setRestProcessing(false);
         });
     }
   }, [useWebSocket, wsRef.current, connectionStatus, conversationId, isAr]);

  if (!isAuthenticated) {
    return null;
  }

  return (
    <Layout>
      <div className="flex h-[calc(100vh-4rem)] bg-surface-2">
        {/* Sidebar */}
        <aside
          className={cn(
            'w-64 bg-card border-e flex flex-col transition-all duration-300',
            showSidebar ? 'translate-x-0' : '-translate-x-full absolute'
          )}
          dir={dir}
        >
          {/* New Chat Button */}
          <div className="p-4 border-b">
            <Button
              onClick={() => startNewConversation(selectedMode)}
              className="w-full flex items-center justify-center gap-2"
            >
              <Plus className="h-4 w-4" />
              {isAr ? 'محادثة جديدة' : 'New Chat'}
            </Button>
          </div>

          {/* Mode Select */}
          <div className="px-4 pb-4 border-b">
            <div className="relative">
              <button
                onClick={() => setShowModeSelect(!showModeSelect)}
                className="w-full flex items-center justify-between px-3 py-2 text-sm border rounded-lg hover:bg-surface-1"
              >
                <span>
                  {MODES.find((m) => m.value === selectedMode)?.[isAr ? 'labelAr' : 'label']}
                </span>
                <ChevronDown className="h-4 w-4" />
              </button>
              {showModeSelect && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-card border rounded-lg shadow-lg z-10">
                  {MODES.map((mode) => (
                    <button
                      key={mode.value}
                      onClick={() => {
                        setSelectedMode(mode.value);
                        setShowModeSelect(false);
                      }}
                      className={cn(
                        'w-full px-3 py-2 text-sm text-start hover:bg-surface-1',
                        selectedMode === mode.value && 'bg-primary-muted'
                      )}
                    >
                      {isAr ? mode.labelAr : mode.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Conversations List */}
          <div className="flex-1 overflow-y-auto p-2">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                className={cn(
                  'group flex items-center justify-between p-2 rounded-lg cursor-pointer hover:bg-surface-1',
                  conversationId === conv.id && 'bg-primary-muted'
                )}
                onClick={() => navigate(`/app/rashid/${conv.id}`)}
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {conv.title || MODES.find((m) => m.value === conv.mode)?.[isAr ? 'labelAr' : 'label']}
                  </p>
                  {conv.last_message && (
                    <p className="text-xs text-muted-foreground truncate">
                      {conv.last_message.preview}
                    </p>
                  )}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteConversation(conv.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </aside>

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col" dir={dir}>
          {/* Header */}
          <header className="bg-card border-b px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowSidebar(!showSidebar)}
                className="p-2 hover:bg-surface-1 rounded-lg lg:hidden"
              >
                <MessageSquare className="h-5 w-5" />
              </button>
              <div>
                <h1 className="text-lg font-semibold">
                  {isAr ? 'رشيد - مستشارك المهني' : 'Rasheed - Your Career Mentor'}
                </h1>
                <p className="text-sm text-muted-foreground flex items-center gap-1">
                  {isConnected ? (
                    <>
                      <Wifi className="h-3 w-3 text-green-500" />
                      {isAr ? 'متصل' : 'Connected'}
                    </>
                  ) : (
                    <>
                      <WifiOff className="h-3 w-3 text-red-500" />
                      {isAr ? 'غير متصل' : 'Disconnected'}
                    </>
                  )}
                </p>
              </div>
            </div>
            <Button
              onClick={() => setShowTools(!showTools)}
              variant={showTools ? 'default' : 'outline'}
              className="flex items-center gap-2"
            >
              <Wrench className="h-4 w-4" />
              {isAr ? 'الأدوات' : 'Tools'}
            </Button>
          </header>

          {/* Tools Panel */}
          {showTools && (
            <ToolSelector
              onSelectTool={handleToolSelection}
              onClose={() => setShowTools(false)}
              isAr={isAr}
            />
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
                <MessageSquare className="h-12 w-12 mb-4 opacity-50" />
                <p className="text-lg font-medium">
                  {isAr ? 'ابدأ محادثة مع رشيد' : 'Start a conversation with Rasheed'}
                </p>
                <p className="text-sm">
                  {isAr
                    ? 'اسأل عن أي سؤال مهني - سيرتك الذاتية، المقابلات، أو المسار المهني'
                    : 'Ask about anything career-related - CVs, interviews, or career paths'}
                </p>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={cn('flex', msg.role === 'user' ? 'justify-end' : 'justify-start')}
              >
                <div
                  className={cn(
                    'max-w-[80%] px-4 py-3 rounded-2xl',
                    msg.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-card border'
                  )}
                >
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                </div>
              </div>
            ))}

            {isProcessing && (
              <div className="flex justify-start">
                <div className="bg-card border px-4 py-3 rounded-2xl">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">{isAr ? 'جاري التفكير...' : 'Thinking...'}</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="bg-card border-t p-4">
            <div className="max-w-4xl mx-auto flex gap-3">
              <input
                ref={inputRef}
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={isAr ? 'اكتب رسالتك...' : 'Type your message...'}
                className="flex-1 px-4 py-3 bg-surface-1 border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50"
                disabled={!isConnected || isProcessing}
                dir={dir}
              />
              <Button
                onClick={handleSendMessage}
                disabled={!isConnected || !inputMessage.trim() || isProcessing}
                size="icon"
                className="h-12 w-12 rounded-xl"
              >
                <Send className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </main>
      </div>
    </Layout>
  );
}