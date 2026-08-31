import { Link, useLocation } from "react-router-dom";
import {
  Briefcase, Info, Menu, User, LogOut, CheckCircle2,
  MessageCircle, FileText, Mic, Sparkles,
  ClipboardList, Bookmark, Target, Bell,
  Settings as SettingsIcon, PlusCircle, Search,
  LayoutDashboard, DollarSign, Award,
} from "lucide-react";
import { NotificationBell } from "@/components/NotificationBell";
import { useState } from "react";
import { motion, useReducedMotion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "@/components/ui/sheet";
import { ThemeToggle, LangToggle } from "@/components/ThemeToggle";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/hooks/use-auth";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface NavItem {
  to: string;
  label: string;
  labelAr: string;
  icon: React.ComponentType<{ className?: string }>;
}

const publicNavItems: NavItem[] = [
  { to: "/", label: "Home", labelAr: "الرئيسية", icon: Briefcase },
  { to: "/about", label: "About", labelAr: "عن USAM", icon: Info },
];

const appPrimaryNav: NavItem[] = [
  { to: "/app/jobs", label: "Jobs", labelAr: "الوظائف", icon: Briefcase },
  { to: "/app/rashid", label: "Rasheed", labelAr: "رشيد", icon: MessageCircle },
  { to: "/app/resume", label: "Resume", labelAr: "السيرة الذاتية", icon: FileText },
  { to: "/app/interviews", label: "Interviews", labelAr: "المقابلات", icon: Mic },
  { to: "/app/recommendations", label: "For You", labelAr: "مقترحة لك", icon: Sparkles },
];

const appSecondaryNav: NavItem[] = [
  { to: "/app/applications", label: "Applications", labelAr: "طلباتي", icon: ClipboardList },
  { to: "/app/saved", label: "Saved Jobs", labelAr: "المحفوظات", icon: Bookmark },
  { to: "/app/talent-score", label: "Talent Score", labelAr: "نقاط الموهبة", icon: Target },
  { to: "/app/alerts", label: "Job Alerts", labelAr: "تنبيهات الوظائف", icon: Bell },
  { to: "/app/salary", label: "Salary Insights", labelAr: "رؤى الرواتب", icon: DollarSign },
  { to: "/app/assessments", label: "Assessments", labelAr: "التقييمات", icon: Award },
  { to: "/app/settings", label: "Settings", labelAr: "الإعدادات", icon: SettingsIcon },
];

const employerPrimaryNav: NavItem[] = [
  { to: "/app/employer/dashboard", label: "Dashboard", labelAr: "لوحة التحكم", icon: LayoutDashboard },
  { to: "/app/employer/post-job", label: "Post Job", labelAr: "نشر وظيفة", icon: PlusCircle },
  { to: "/app/employer/talent-search", label: "Talent Search", labelAr: "بحث المواهب", icon: Search },
];

const employerSecondaryNav: NavItem[] = [
  { to: "/app/jobs", label: "Browse Jobs", labelAr: "تصفح الوظائف", icon: Briefcase },
  { to: "/app/settings", label: "Settings", labelAr: "الإعدادات", icon: SettingsIcon },
];

export function AuthNavbar() {
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const { lang } = useTheme();
  const { user, isAuthenticated, signOut } = useAuth();
  const isAr = lang === "ar";
  const reduced = useReducedMotion();

  const isEmployer = user?.role === 'employer';
  const primaryNav = !isAuthenticated ? publicNavItems : isEmployer ? employerPrimaryNav : appPrimaryNav;
  const secondaryNav = isEmployer ? employerSecondaryNav : appSecondaryNav;
  const mobileNav = !isAuthenticated ? publicNavItems : [...primaryNav, ...secondaryNav];

  return (
    <header className="sticky top-0 z-50 border-b bg-card/95 glass supports-[backdrop-filter]:bg-card/80">
      <div className="container flex h-14 items-center justify-between">
        <Link to="/" className="flex items-center gap-2 press-feedback">
          <img src="/logo-dark.png" alt="USAM" className="h-8 dark:invert" style={{ minWidth: 70 }} />
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-0.5">
          {primaryNav.map((item) => {
            const active = item.to === "/" ? location.pathname === "/" : location.pathname.startsWith(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-body font-medium transition-all duration-fast ${
                  active
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-foreground/60 hover:text-foreground hover:bg-accent"
                }`}
              >
                <item.icon className="h-3.5 w-3.5" />
                {isAr ? item.labelAr : item.label}
              </Link>
            );
          })}

          <div className="flex items-center gap-0.5 ms-2 border-s ps-2 border-border">
            <LangToggle />
            <ThemeToggle />
            {isAuthenticated && <NotificationBell />}

            {isAuthenticated && user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className="ms-1 rounded-lg gap-2 h-9 px-2.5">
                    <AnimatePresence>
                      <motion.span
                        className="hidden lg:flex items-center gap-1 text-caption font-medium text-foreground/70"
                        initial={reduced ? {} : { opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3, delay: 0.1 }}
                      >
                        {user.name.split(" ")[0]}
                        <CheckCircle2 className="h-3 w-3 text-success" />
                      </motion.span>
                    </AnimatePresence>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <div className="px-3 py-2.5">
                    <div className="flex items-center gap-2 mb-1">
                      <CheckCircle2 className="h-3.5 w-3.5 text-success shrink-0" />
                      <p className="text-body font-medium truncate">{user.name}</p>
                    </div>
                    <p className="text-caption text-muted-foreground truncate ps-5.5">{user.email}</p>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to="/app/profile" className="cursor-pointer">
                      <User className="h-3.5 w-3.5 me-2" />
                      {isAr ? "الملف الشخصي" : "Profile"}
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  {secondaryNav.map((item) => (
                    <DropdownMenuItem key={item.to} asChild>
                      <Link to={item.to} className="cursor-pointer">
                        <item.icon className="h-3.5 w-3.5 me-2" />
                        {isAr ? item.labelAr : item.label}
                      </Link>
                    </DropdownMenuItem>
                  ))}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={signOut} className="text-destructive cursor-pointer">
                    <LogOut className="h-3.5 w-3.5 me-2" />
                    {isAr ? "تسجيل الخروج" : "Sign out"}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Button asChild variant="default" size="sm" className="ms-2 rounded-lg press-feedback">
                <Link to="/login">{isAr ? "دخول" : "Sign in"}</Link>
              </Button>
            )}
          </div>
        </nav>

        {/* Mobile nav */}
        <div className="flex items-center gap-1 md:hidden">
          <ThemeToggle />
          {isAuthenticated && user && (
            <div className="flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3 text-success -ms-2 -mt-3" />
            </div>
          )}
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="Open menu" className="h-9 w-9">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side={isAr ? "left" : "right"} className="w-72 overflow-y-auto">
              <SheetTitle className="sr-only">Navigation</SheetTitle>
              <div className="flex items-center justify-between mt-2 mb-6">
                <img src="/logo-dark.png" alt="USAM" className="h-7 dark:invert" />
                <LangToggle />
              </div>

              {isAuthenticated && user && (
                <div className="flex items-center gap-3 mb-4 pb-4 border-b border-border">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <p className="text-body font-medium truncate">{user.name}</p>
                      <CheckCircle2 className="h-3.5 w-3.5 text-success shrink-0" />
                    </div>
                    <p className="text-caption text-muted-foreground truncate">{user.email}</p>
                  </div>
                </div>
              )}

              <nav className="flex flex-col gap-1">
                {mobileNav.map((item) => {
                  const active = item.to === "/" ? location.pathname === "/" : location.pathname.startsWith(item.to);
                  return (
                    <Link
                      key={item.to}
                      to={item.to}
                      onClick={() => setOpen(false)}
                      className={`flex items-center gap-2.5 px-4 py-3 rounded-lg text-body font-medium transition-all duration-fast ${
                        active
                          ? "bg-primary text-primary-foreground"
                          : "text-foreground/60 hover:text-foreground hover:bg-accent"
                      }`}
                    >
                      <item.icon className="h-4 w-4" />
                      {isAr ? item.labelAr : item.label}
                    </Link>
                  );
                })}

                {isAuthenticated && (
                  <>
                    <Link
                      to="/app/profile"
                      onClick={() => setOpen(false)}
                      className={`flex items-center gap-2.5 px-4 py-3 rounded-lg text-body font-medium transition-all duration-fast ${
                        location.pathname.startsWith("/app/profile")
                          ? "bg-primary text-primary-foreground"
                          : "text-foreground/60 hover:text-foreground hover:bg-accent"
                      }`}
                    >
                      <User className="h-4 w-4" />
                      {isAr ? "الملف الشخصي" : "Profile"}
                    </Link>
                    <div className="my-2 border-t border-border" />
                    <button
                      onClick={() => { signOut(); setOpen(false); }}
                      className="flex items-center gap-2.5 px-4 py-3 rounded-lg text-body font-medium text-destructive hover:bg-accent"
                    >
                      <LogOut className="h-4 w-4" />
                      {isAr ? "تسجيل الخروج" : "Sign out"}
                    </button>
                  </>
                )}

                {!isAuthenticated && (
                  <Link
                    to="/login"
                    onClick={() => setOpen(false)}
                    className="flex items-center gap-2.5 px-4 py-3 rounded-lg text-body font-medium bg-primary text-primary-foreground mt-2"
                  >
                    {isAr ? "تسجيل الدخول" : "Sign in"}
                  </Link>
                )}
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
