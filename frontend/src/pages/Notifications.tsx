import { useState, useEffect } from "react";
import { Layout } from "@/components/Layout";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useTheme } from "@/hooks/use-theme";
import {
  Bell,
  Briefcase,
  CheckCircle,
  Star,
  Calendar,
  Settings,
  Loader2,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { EmptyStates } from "@/components/EmptyState";
import { apiRequest } from "@/services/client";

type NotificationType = "job_match" | "application_update" | "interview" | "recommendation" | "system";

interface Notification {
  id: number;
  uuid: string;
  type: string;
  title: string;
  message: string;
  created_at: string;
  is_read: boolean;
  metadata?: any;
}

const NOTIFICATION_ICONS: Record<string, typeof Briefcase> = {
  job_match: Briefcase,
  application_update: CheckCircle,
  interview: Calendar,
  recommendation: Star,
  system: Bell,
};

const NOTIFICATION_COLORS: Record<string, string> = {
  job_match: "text-blue-600",
  application_update: "text-green-600",
  interview: "text-purple-600",
  recommendation: "text-yellow-600",
  system: "text-gray-600",
};

export default function Notifications() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const data = await apiRequest<Notification[]>('/users/me/notifications/');
      setNotifications(Array.isArray(data) ? data : []);
    } catch {
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  };

  const markAllAsRead = async () => {
    try {
      await apiRequest('/users/me/notifications/mark-all-read/', { method: 'POST' });
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch {
      // silent
    }
  };

  const markAsRead = async (uuid: string) => {
    try {
      await apiRequest(`/users/me/notifications/${uuid}/`, {
        method: 'PATCH',
        body: { is_read: true },
      });
      setNotifications(prev =>
        prev.map(n => n.uuid === uuid ? { ...n, is_read: true } : n)
      );
    } catch {
      // silent
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  if (loading) {
    return (
      <Layout>
        <div className="container max-w-4xl py-8 flex justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </Layout>
    );
  }

  if (notifications.length === 0) {
    return (
      <Layout>
        <div className="container max-w-4xl py-8">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-heading-1 mb-2">
                {isAr ? "الإشعارات" : "Notifications"}
              </h1>
              <p className="text-muted-foreground">
                {isAr ? "ابق على اطلاع بآخر التحديثات" : "Stay updated with your latest activities"}
              </p>
            </div>
            <Button variant="outline" size="sm" asChild>
              <a href="/app/settings">
                <Settings className="h-4 w-4 mr-2" />
                {isAr ? "إعدادات" : "Settings"}
              </a>
            </Button>
          </div>

          <EmptyStates.NoNotifications />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="container max-w-4xl py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-heading-1 mb-2 flex items-center gap-2">
              {isAr ? "الإشعارات" : "Notifications"}
              {unreadCount > 0 && (
                <Badge variant="destructive" className="h-6 px-2">
                  {unreadCount}
                </Badge>
              )}
            </h1>
            <p className="text-muted-foreground">
              {isAr ? "ابق على اطلاع بآخر التحديثات" : "Stay updated with your latest activities"}
            </p>
          </div>
          <div className="flex gap-2">
            {unreadCount > 0 && (
              <Button variant="outline" size="sm" onClick={markAllAsRead}>
                {isAr ? "تعليم الكل كمقروء" : "Mark All Read"}
              </Button>
            )}
            <Button variant="outline" size="sm" asChild>
              <a href="/app/settings">
                <Settings className="h-4 w-4 mr-2" />
                {isAr ? "إعدادات" : "Settings"}
              </a>
            </Button>
          </div>
        </div>

        <div className="space-y-2">
          {notifications.map((notification) => {
            const Icon = NOTIFICATION_ICONS[notification.type] || Bell;
            const iconColor = NOTIFICATION_COLORS[notification.type] || "text-gray-600";

            return (
              <Card
                key={notification.uuid}
                className={`cursor-pointer transition-colors hover:bg-accent ${
                  !notification.is_read ? "bg-blue-50/50 dark:bg-blue-950/20 border-blue-200/50" : ""
                }`}
                onClick={() => !notification.is_read && markAsRead(notification.uuid)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-4">
                    <div className={`p-2 rounded-full bg-background ${iconColor}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-start justify-between gap-2">
                        <p className="font-medium text-sm">{notification.title}</p>
                        {!notification.is_read && (
                          <span className="h-2 w-2 rounded-full bg-blue-600 shrink-0 mt-1.5" />
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">{notification.message}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </Layout>
  );
}
