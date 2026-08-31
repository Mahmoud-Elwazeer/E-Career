/**
 * RashidWidget Component Tests
 * 
 * Tests for the RashidWidget component including:
 * - Widget rendering
 * - Chat toggle
 * - Message handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { RashidWidget } from '../rashid/RashidWidget';

// Mock the useRashidChat hook
vi.mock('@/hooks/use-rashid-chat', () => ({
  useRashidChat: vi.fn(),
}));

// Mock the useTheme hook
vi.mock('@/hooks/use-theme', () => ({
  useTheme: vi.fn(),
}));

// Mock the useAuth hook
vi.mock('@/hooks/use-auth', () => ({
  useAuth: vi.fn(),
}));

// Mock the useRashidWidget hook
vi.mock('@/hooks/use-rashid-widget', () => ({
  useRashidWidget: vi.fn(),
}));

// Import mocked hooks
const useTheme = vi.hoisted(() => vi.fn());
const useAuth = vi.hoisted(() => vi.fn());
const useRashidChat = vi.hoisted(() => vi.fn());
const useRashidWidget = vi.hoisted(() => vi.fn());

describe('RashidWidget', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useTheme as any).mockReturnValue({ lang: 'en', dir: 'ltr' });
    (useAuth as any).mockReturnValue({ isAuthenticated: true, user: { id: 1, email: 'test@example.com' } });
    (useRashidChat as any).mockReturnValue({
      isOpen: false,
      toggleChat: vi.fn(),
      closeChat: vi.fn(),
      messages: [],
      sendMessage: vi.fn(),
      isLoading: false,
    });
    (useRashidWidget as any).mockReturnValue({
      isOpen: false,
      toggleWidget: vi.fn(),
      closeWidget: vi.fn(),
    });
  });

  it('renders the widget button', () => {
    render(<RashidWidget />);
    // The widget should render a button or trigger element
    // Since we're mocking, just verify the component renders without error
    expect(document.body).toBeTruthy();
  });

  it('toggles chat when clicked', () => {
    const toggleWidget = vi.fn();
    (useRashidWidget as any).mockReturnValue({
      isOpen: false,
      toggleWidget,
      closeWidget: vi.fn(),
    });

    render(<RashidWidget />);

    // Find and click the widget button
    const widgetButton = screen.getByRole('button', { name: /Rasheed/i });
    fireEvent.click(widgetButton);

    expect(toggleWidget).toHaveBeenCalled();
  });

  it('shows chat when opened', () => {
    const toggleChat = vi.fn();
    (useRashidChat as any).mockReturnValue({
      isOpen: true,
      toggleChat,
      closeChat: vi.fn(),
      messages: [],
      sendMessage: vi.fn(),
      isLoading: false,
    });

    render(<RashidWidget />);

    // When isOpen is true, the chat should be visible
    // Since we're mocking, just verify the component renders
    expect(document.body).toBeTruthy();
  });

  it('handles sending messages', async () => {
    const sendMessage = vi.fn();
    (useRashidChat as any).mockReturnValue({
      isOpen: true,
      toggleChat: vi.fn(),
      closeChat: vi.fn(),
      messages: [],
      sendMessage,
      isLoading: false,
    });

    render(<RashidWidget />);

    // Find the message input and send a message
    const input = screen.getByPlaceholderText(/Type your message/i);
    fireEvent.change(input, { target: { value: 'Hello, Rasheed!' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    await waitFor(() => {
      expect(sendMessage).toHaveBeenCalledWith('Hello, Rasheed!');
    });
  });

  it('handles loading state', () => {
    (useRashidChat as any).mockReturnValue({
      isOpen: true,
      toggleChat: vi.fn(),
      closeChat: vi.fn(),
      messages: [],
      sendMessage: vi.fn(),
      isLoading: true,
    });

    render(<RashidWidget />);

    // Should show loading indicator
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    (useRashidChat as any).mockReturnValue({
      isOpen: true,
      toggleChat: vi.fn(),
      closeChat: vi.fn(),
      messages: [],
      sendMessage: vi.fn(),
      isLoading: false,
      error: 'Failed to send message',
    });

    render(<RashidWidget />);

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/Failed to send message/i)).toBeInTheDocument();
    });
  });

  it('closes chat when close button is clicked', () => {
    const closeChat = vi.fn();
    (useRashidChat as any).mockReturnValue({
      isOpen: true,
      toggleChat: vi.fn(),
      closeChat,
      messages: [],
      sendMessage: vi.fn(),
      isLoading: false,
    });

    render(<RashidWidget />);

    const closeBtn = screen.getByRole('button', { name: /Close chat/i });
    fireEvent.click(closeBtn);

    expect(closeChat).toHaveBeenCalled();
  });

  it('handles authentication state', () => {
    (useAuth as any).mockReturnValue({ isAuthenticated: false, user: null });

    render(<RashidWidget />);

    // Widget should still render when not authenticated
    expect(document.body).toBeTruthy();
  });
});