import { Link } from "react-router-dom";
import {
  User,
  Bell,
  Settings,
  LogOut,
  HelpCircle,
  Briefcase,
  Building2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/hooks/use-auth";
import { useTheme } from "@/hooks/use-theme";

interface UserMenuProps {
  unreadNotifications?: number;
}

export function UserMenu({ unreadNotifications = 0 }: UserMenuProps) {
  const { user, logout } = useAuth();
  const { lang } = useTheme();
  const isAr = lang === "ar";

  if (!user) return null;

  const userInitials = user.name
    ? user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "U";

  const handleLogout = async () => {
    await logout();
    window.location.href = "/login";
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="relative h-9 w-9 rounded-full"
          aria-label={isAr ? "قائمة المستخدم" : "User menu"}
        >
          <Avatar className="h-9 w-9">
            <AvatarImage src={user.avatar_url} alt={user.name} />
            <AvatarFallback className="bg-primary text-primary-foreground text-sm">
              {userInitials}
            </AvatarFallback>
          </Avatar>
          {unreadNotifications > 0 && (
            <span className="absolute -top-0.5 -right-0.5 h-4 w-4 rounded-full bg-destructive text-[10px] font-bold text-white flex items-center justify-center">
              {unreadNotifications > 9 ? "9+" : unreadNotifications}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        className="w-64"
        align={isAr ? "start" : "end"}
        sideOffset={8}
      >
        {/* User Info */}
        <DropdownMenuLabel>
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{user.name}</p>
            <p className="text-xs leading-none text-muted-foreground">
              {user.email}
            </p>
            {user.role && (
              <Badge variant="secondary" className="mt-1 w-fit text-xs">
                {user.role === "employer" ? (
                  <>
                    <Building2 className="mr-1 h-3 w-3" />
                    {isAr ? "صاحب عمل" : "Employer"}
                  </>
                ) : (
                  <>
                    <Briefcase className="mr-1 h-3 w-3" />
                    {isAr ? "باحث عن عمل" : "Job Seeker"}
                  </>
                )}
              </Badge>
            )}
          </div>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        {/* Profile */}
        <DropdownMenuItem asChild>
          <Link to="/app/profile" className="cursor-pointer">
            <User className="mr-2 h-4 w-4" />
            <span>{isAr ? "الملف الشخصي" : "Profile"}</span>
          </Link>
        </DropdownMenuItem>

        {/* Notifications */}
        <DropdownMenuItem asChild>
          <Link to="/app/notifications" className="cursor-pointer">
            <Bell className="mr-2 h-4 w-4" />
            <span className="flex-1">{isAr ? "الإشعارات" : "Notifications"}</span>
            {unreadNotifications > 0 && (
              <Badge variant="destructive" className="ml-auto text-xs h-5 px-1.5">
                {unreadNotifications}
              </Badge>
            )}
          </Link>
        </DropdownMenuItem>

        {/* Settings */}
        <DropdownMenuItem asChild>
          <Link to="/app/settings" className="cursor-pointer">
            <Settings className="mr-2 h-4 w-4" />
            <span>{isAr ? "الإعدادات" : "Settings"}</span>
          </Link>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        {/* Help */}
        <DropdownMenuItem asChild>
          <Link to="/help" className="cursor-pointer">
            <HelpCircle className="mr-2 h-4 w-4" />
            <span>{isAr ? "المساعدة" : "Help"}</span>
          </Link>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        {/* Logout */}
        <DropdownMenuItem
          onClick={handleLogout}
          className="cursor-pointer text-destructive focus:text-destructive"
        >
          <LogOut className="mr-2 h-4 w-4" />
          <span>{isAr ? "تسجيل الخروج" : "Logout"}</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
