import { Link, useLocation } from "react-router-dom";
import { Briefcase, Info, Menu, Building2, Code2, User, LogOut, CheckCircle2, Bell } from "lucide-react";
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

const publicNavItems = [
  { to: "/", label: "Home", labelAr: "الرئيسية", icon: Briefcase },
  { to: "/about", label: "About", labelAr: "عن USAM", icon: Info },
];

const appNavItems = [
  { to: "/app/jobs", label: "Jobs", labelAr: "وظائف", icon: Briefcase },
  { to: "/app/coding-practice", label: "Practice", labelAr: "تمرين", icon: Code2 },
  { to: "/app/profile", label: "Profile", labelAr: "الملف", icon: User },
  { to: "/about", label: "About", labelAr: "عن USAM", icon: Info },
];

const employerNavItems = [
  { to: "/app/employer/dashboard", label: "Dashboard", labelAr: "لوحة التحكم", icon: Building2 },
  { to: "/app/jobs", label: "Jobs", labelAr: "وظائف", icon: Briefcase },
  { to: "/about", label: "About", labelAr: "عن USAM", icon: Info },
];

export function AuthNavbar() {
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const { lang } = useTheme();
  const { user, isAuthenticated, signOut } = useAuth();
  const isAr = lang === "ar";
  const reduced = useReducedMotion();

  const isEmployer = user?.role === 'employer';
  const navItems = !isAuthenticated ? publicNavItems : isEmployer ? employerNavItems : appNavItems;

  return (
    <header className="sticky top-0 z-50 border-b bg-card/95 glass supports-[backdrop-filter]:bg-card/80">
      <div className="container flex h-14 items-center justify-between">
        <Link to="/" className="flex items-center gap-2 press-feedback">
          <img src="/logo-dark.png" alt="USAM" className="h-8 dark:invert" style={{ minWidth: 70 }} />
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-0.5">
          {navItems.map((item) => {
            const active = item.to === "/" ? location.pathname === "/" : location.pathname.startsWith(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-body font-medium transition-all duration-fast ${
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
                    {/* <img src={user.avatar} alt={user.name} className="h-6 w-6 rounded-full" /> */}
                    {/* Session badge */}
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
                <DropdownMenuContent align="end" className="w-52">
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
              {/* <img src={user.avatar} alt={user.name} className="h-7 w-7 rounded-full" /> */}
              <CheckCircle2 className="h-3 w-3 text-success -ms-2 -mt-3" />
            </div>
          )}
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="Open menu" className="h-9 w-9">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side={isAr ? "left" : "right"} className="w-72">
              <SheetTitle className="sr-only">Navigation</SheetTitle>
              <div className="flex items-center justify-between mt-2 mb-6">
                <img src="/logo-dark.png" alt="USAM" className="h-7 dark:invert" />
                <LangToggle />
              </div>

              {/* Session badge in mobile sheet */}
              {isAuthenticated && user && (
                <div className="flex items-center gap-3 mb-4 pb-4 border-b border-border">
                  {/* <img src={user.avatar} alt={user.name} className="h-9 w-9 rounded-full" /> */}
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
                {navItems.map((item) => {
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
                {!isAuthenticated && (
                  <Link
                    to="/login"
                    onClick={() => setOpen(false)}
                    className="flex items-center gap-2.5 px-4 py-3 rounded-lg text-body font-medium bg-primary text-primary-foreground mt-2"
                  >
                    {isAr ? "تسجيل الدخول" : "Sign in"}
                  </Link>
                )}
                {isAuthenticated && (
                  <button
                    onClick={() => { signOut(); setOpen(false); }}
                    className="flex items-center gap-2.5 px-4 py-3 rounded-lg text-body font-medium text-destructive hover:bg-accent mt-2"
                  >
                    <LogOut className="h-4 w-4" />
                    {isAr ? "تسجيل الخروج" : "Sign out"}
                  </button>
                )}
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
