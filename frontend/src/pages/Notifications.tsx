import { AppLayout } from "@/components/layout/AppLayout";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useTheme } from "@/hooks/use-theme";
import {
  Bell,
  Briefcase,
  CheckCircle,
  Star,
  TrendingUp,
  Calendar,
  Settings,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { EmptyStates } from "@/components/EmptyState";

// Mock notification types
type NotificationType = "job_match" | "application_update" | "interview" | "recommendation" | "system";

interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  actionUrl?: string;
}

const NOTIFICATION_ICONS: Record<NotificationType, typeof Briefcase> = {
  job_match: Briefcase,
  application_update: CheckCircle,
  interview: Calendar,
  recommendation: Star,
  system: Bell,
};

const NOTIFICATION_COLORS: Record<NotificationType, string> = {
  job_match: "text-blue-600",
  application_update: "text-green-600",
  interview: "text-purple-600",
  recommendation: "text-yellow-600",
  system: "text-gray-600",
};

// Mock data
const mockNotifications: Notification[] = [];

export default function Notifications() {
  const { lang } = useTheme();
  const isAr = lang === "ar";

  const unreadCount = mockNotifications.filter(n => !n.read).length;

  if (mockNotifications.length === 0) {
    return (
      <AppLayout>
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
      </AppLayout>
    );
  }

  return (
    <AppLayout>
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
              <Button variant="outline" size="sm">
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
          {mockNotifications.map((notification) => {
            const Icon = NOTIFICATION_ICONS[notification.type];
            const iconColor = NOTIFICATION_COLORS[notification.type];

            return (
              <Card
                key={notification.id}
                className={`cursor-pointer transition-colors hover:bg-accent ${
                  !notification.read ? "bg-blue-50/50 dark:bg-blue-950/20 border-blue-200/50" : ""
                }`}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-4">
                    <div className={`p-2 rounded-full bg-background ${iconColor}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-start justify-between gap-2">
                        <p className="font-medium text-sm">{notification.title}</p>
                        {!notification.read && (
                          <span className="h-2 w-2 rounded-full bg-blue-600 shrink-0 mt-1.5" />
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">{notification.message}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatDistanceToNow(notification.timestamp, { addSuffix: true })}
                      </p>
                    </div>
                  </div>
                  {notification.actionUrl && (
                    <div className="mt-3 pl-14">
                      <Button size="sm" variant="outline" asChild>
                        <a href={notification.actionUrl}>
                          {isAr ? "عرض" : "View"}
                        </a>
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </AppLayout>
  );
}
