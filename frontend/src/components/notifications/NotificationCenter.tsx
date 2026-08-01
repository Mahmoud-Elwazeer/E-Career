/**
 * Notification Center Component
 * Displays and manages user notifications
 */

import { useState, useEffect } from 'react';
import api from '@/services/api';

export interface Notification {
  id: number;
  uuid: string;
  user_id: number;
  type: string;
  title: string;
  message: string;
  severity: 'high' | 'medium' | 'low';
  is_read: boolean;
  created_at: string;
  metadata?: any;
}

export function NotificationCenter() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const response = await api.get('/core/notifications/');
      setNotifications(response.data.data || []);
    } catch (err) {
      setError('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId: number) => {
    try {
      await api.patch(`/core/notifications/${notificationId}/read/`);
      setNotifications(prev =>
        prev.map(n =>
          n.id === notificationId ? { ...n, is_read: true } : n
        )
      );
    } catch (err) {
      console.error('Failed to mark notification as read');
    }
  };

  const markAllAsRead = async () => {
    try {
      await api.post('/core/notifications/read-all/');
      setNotifications(prev =>
        prev.map(n => ({ ...n, is_read: true }))
      );
    } catch (err) {
      console.error('Failed to mark all notifications as read');
    }
  };

  const deleteNotification = async (notificationId: number) => {
    try {
      await api.delete(`/core/notifications/${notificationId}/`);
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
    } catch (err) {
      console.error('Failed to delete notification');
    }
  };

  const getUnreadCount = () => {
    return notifications.filter(n => !n.is_read).length;
  };

  const getFilteredNotifications = () => {
    if (showAll) {
      return notifications;
    }
    return notifications.slice(0, 10);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  if (loading) {
    return (
      <div className="notification-center loading">
        <div className="spinner">Loading notifications...</div>
      </div>
    );
  }

  return (
    <div className="notification-center">
      <div className="notification-header">
        <h2>Notifications</h2>
        <span className="badge">{getUnreadCount()} unread</span>
        <button
          onClick={markAllAsRead}
          className="mark-all-read"
          disabled={getUnreadCount() === 0}
        >
          Mark all as read
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="notification-list">
        {getFilteredNotifications().length === 0 ? (
          <div className="empty-state">
            <p>No notifications yet</p>
          </div>
        ) : (
          getFilteredNotifications().map(notification => (
            <div
              key={notification.id}
              className={`notification-item ${notification.is_read ? 'read' : 'unread'}`}
            >
              <div className="notification-content">
                <div className="notification-header">
                  <span className={`severity-badge ${getSeverityColor(notification.severity)}`}>
                    {notification.severity}
                  </span>
                  <span className="notification-time">
                    {new Date(notification.created_at).toLocaleString()}
                  </span>
                </div>
                <h4>{notification.title}</h4>
                <p>{notification.message}</p>
              </div>
              <div className="notification-actions">
                {!notification.is_read && (
                  <button
                    onClick={() => markAsRead(notification.id)}
                    className="mark-read-btn"
                  >
                    ✓
                  </button>
                )}
                <button
                  onClick={() => deleteNotification(notification.id)}
                  className="delete-btn"
                >
                  ×
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {notifications.length > 10 && (
        <div className="notification-footer">
          <button onClick={() => setShowAll(!showAll)}>
            {showAll ? 'Show less' : 'Show all'}
          </button>
        </div>
      )}
    </div>
  );
}

export function NotificationBadge() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    // In production, this would fetch from the API
    // const fetchCount = async () => { ... }
    setCount(0);
  }, []);

  if (count === 0) return null;

  return (
    <div className="notification-badge">
      <span className="count">{count}</span>
    </div>
  );
}