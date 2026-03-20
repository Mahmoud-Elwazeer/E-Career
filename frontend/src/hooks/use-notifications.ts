import { useState, useCallback, useEffect } from "react";
import { useAuth } from "@/hooks/use-auth";
import {
  fetchNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  type Notification,
} from "@/services/userdata";

export type { Notification };

export function useNotifications() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const load = useCallback(async () => {
    if (!user) { setNotifications([]); return; }
    setIsLoading(true);
    try { setNotifications(await fetchNotifications()); }
    catch { setNotifications([]); }
    finally { setIsLoading(false); }
  }, [user]);

  useEffect(() => { load(); }, [load]);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const markRead = useCallback(async (uuid: string) => {
    try {
      await markNotificationRead(uuid);
      setNotifications((prev) => prev.map((n) => (n.uuid === uuid ? { ...n, is_read: true } : n)));
    } catch {}
  }, []);

  const markAllRead = useCallback(async () => {
    try {
      await markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {}
  }, []);

  return { notifications, unreadCount, isLoading, markRead, markAllRead, reload: load };
}
