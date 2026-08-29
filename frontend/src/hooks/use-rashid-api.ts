/**
 * Rashid REST API Hook
 * Provides REST API methods for Rashid chat (fallback for production without WebSocket)
 */

import { useState } from 'react';
import { getAccessToken } from '@/services/client';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

interface Conversation {
  id: string;
  mode: string;
  messages: Message[];
  created_at: string;
}

export function useRashidAPI() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getAuthHeaders = () => {
    const token = getAccessToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : '',
    };
  };

  const createConversation = async (mode: string = 'general'): Promise<Conversation> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/rashid/conversations/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ mode }),
      });

      if (!response.ok) {
        throw new Error(`Failed to create conversation: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create conversation';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (
    conversationId: string,
    content: string
  ): Promise<{ user_message: Message; assistant_message: Message }> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE_URL}/rashid/conversations/${conversationId}/send_message/`,
        {
          method: 'POST',
          headers: getAuthHeaders(),
          body: JSON.stringify({ content }),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to send message';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getMessages = async (conversationId: string): Promise<Message[]> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE_URL}/rashid/conversations/${conversationId}/messages/`,
        {
          method: 'GET',
          headers: getAuthHeaders(),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to get messages: ${response.statusText}`);
      }

      const data = await response.json();
      return data.results || data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get messages';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getConversations = async (): Promise<Conversation[]> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/rashid/conversations/`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error(`Failed to get conversations: ${response.statusText}`);
      }

      const data = await response.json();
      return data.results || data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get conversations';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    error,
    createConversation,
    sendMessage,
    getMessages,
    getConversations,
  };
}
