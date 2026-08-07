/**
 * useAuth Hook Tests
 * 
 * Tests for the useAuth hook including:
 * - Login/logout flow
 * - Authentication state
 * - User data handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '../use-auth';
import { getAccessToken, getRefreshToken, clearTokens } from '@/services/client';

// Mock the auth service
vi.mock('@/services/auth', () => ({
  login: vi.fn(),
  logout: vi.fn(),
  register: vi.fn(),
  resetPassword: vi.fn(),
  getMe: vi.fn(),
}));

// Mock the client service
vi.mock('@/services/client', () => ({
  getAccessToken: vi.fn(),
  getRefreshToken: vi.fn(),
  clearTokens: vi.fn(),
}));

// Import mocked functions
const login = vi.hoisted(() => vi.fn());
const logout = vi.hoisted(() => vi.fn());
const register = vi.hoisted(() => vi.fn());
const resetPassword = vi.hoisted(() => vi.fn());
const getMe = vi.hoisted(() => vi.fn());

// Mock window event listener
const addEventListenerMock = vi.fn();
const removeEventListenerMock = vi.fn();
Object.defineProperty(window, 'addEventListener', { value: addEventListenerMock });
Object.defineProperty(window, 'removeEventListener', { value: removeEventListenerMock });

describe('useAuth Hook', () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <AuthProvider>{children}</AuthProvider>
  );

  beforeEach(() => {
    vi.clearAllMocks();
    (getAccessToken as any).mockReturnValue(null);
    (getRefreshToken as any).mockReturnValue(null);
  });

  it('returns initial state when not authenticated', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(result.current.isLoading).toBe(true);
  });

  it('returns authenticated state when user has token', async () => {
    (getAccessToken as any).mockReturnValue('fake-token');
    (getMe as any).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).not.toBeNull();
      expect(result.current.user?.email).toBe('test@example.com');
    });
  });

  it('handles login successfully', async () => {
    (login as any).mockResolvedValue({
      user: {
        id: 1,
        email: 'test@example.com',
        first_name: 'Test',
        last_name: 'User',
      },
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    // Wait for initial load to complete
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Perform login
    await act(async () => {
      await result.current.signIn('test@example.com', 'password123');
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.email).toBe('test@example.com');
    expect(result.current.user?.full_name).toBe('Test User');
  });

  it('handles logout successfully', async () => {
    (getAccessToken as any).mockReturnValue('fake-token');
    (getMe as any).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
    });
    (logout as any).mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth(), { wrapper });

    // Wait for initial load to complete
    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    // Perform logout
    await act(async () => {
      await result.current.signOut();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    expect(clearTokens).toHaveBeenCalled();
  });

  it('handles registration successfully', async () => {
    (register as any).mockResolvedValue({
      user: {
        id: 1,
        email: 'newuser@example.com',
        first_name: 'New',
        last_name: 'User',
      },
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    // Perform registration
    await act(async () => {
      await result.current.signUp(
        'newuser@example.com',
        'password123',
        'New',
        'User'
      );
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.email).toBe('newuser@example.com');
  });

  it('handles password reset', async () => {
    (resetPassword as any).mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth(), { wrapper });

    const response = await act(async () => {
      return await result.current.resetPassword('test@example.com');
    });

    expect(response.error).toBeNull();
  });

  it('handles password reset error', async () => {
    (resetPassword as any).mockRejectedValue(new Error('User not found'));

    const { result } = renderHook(() => useAuth(), { wrapper });

    const response = await act(async () => {
      return await result.current.resetPassword('nonexistent@example.com');
    });

    expect(response.error).not.toBeNull();
    expect(response.error?.message).toBe('User not found');
  });

  it('handles auth:logout event', async () => {
    (getAccessToken as any).mockReturnValue('fake-token');
    (getMe as any).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    // Wait for initial load to complete
    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });

    // Simulate logout event
    await act(async () => {
      window.dispatchEvent(new Event('auth:logout'));
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
  });

  it('normalizes user name correctly', async () => {
    (getAccessToken as any).mockReturnValue('fake-token');
    (getMe as any).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      name: 'Full Name',
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
    expect(result.current.user?.full_name).toBe('Full Name');
    });
  });

  it('handles missing user data gracefully', async () => {
    (getAccessToken as any).mockReturnValue('fake-token');
    (getMe as any).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
    });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
    expect(result.current.user?.full_name).toBe('test');
    });
  });
});