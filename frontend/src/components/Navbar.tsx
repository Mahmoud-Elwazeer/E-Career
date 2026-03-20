import { Link, useLocation } from "react-router-dom";
import { Briefcase, Bookmark, Bell, Info, Menu, Building2, User } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "@/components/ui/sheet";
import { ThemeToggle, LangToggle } from "@/components/ThemeToggle";
import { useTheme } from "@/hooks/use-theme";

const navItems = [
  { to: "/jobs", label: "Jobs", labelAr: "وظائف", icon: Briefcase },
  { to: "/companies", label: "Companies", labelAr: "الشركات", icon: Building2 },
  { to: "/profile", label: "Profile", labelAr: "الملف", icon: User },
  { to: "/about", label: "About", labelAr: "عن USAM", icon: Info },
];

export function Navbar() {
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const { lang } = useTheme();

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
                {lang === "ar" ? item.labelAr : item.label}
              </Link>
            );
          })}
          <div className="flex items-center gap-0.5 ms-2 border-s ps-2 border-border">
            <LangToggle />
            <ThemeToggle />
          </div>
        </nav>

        {/* Mobile nav */}
        <div className="flex items-center gap-1 md:hidden">
          <ThemeToggle />
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="Open menu" className="h-9 w-9">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side={lang === "ar" ? "left" : "right"} className="w-72">
              <SheetTitle className="sr-only">Navigation</SheetTitle>
              <div className="flex items-center justify-between mt-2 mb-6">
                <img src="/logo-dark.png" alt="USAM" className="h-7 dark:invert" />
                <LangToggle />
              </div>
              <nav className="flex flex-col gap-1 stagger-children">
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
                      {lang === "ar" ? item.labelAr : item.label}
                    </Link>
                  );
                })}
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
