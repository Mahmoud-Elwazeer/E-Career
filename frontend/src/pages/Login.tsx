import { useNavigate, useLocation, Link } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import { Bookmark, Bell, FileText, ExternalLink, Shield, Lock, DollarSign, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LoginCareerGuide } from "@/components/LoginCareerGuide";
import { useAuth } from "@/hooks/use-auth";
import { useTheme } from "@/hooks/use-theme";
import { WatermarkBackground } from "@/components/WatermarkBackground";
import { useEffect, useState } from "react";
import { MOTION } from "@/lib/motion-tokens";
import { useToast } from "@/hooks/use-toast";

const BENEFITS = [
  { icon: FileText, en: "Full job details & salary ranges", ar: "تفاصيل الوظائف الكاملة ونطاق الراتب" },
  { icon: DollarSign, en: "Unlock salary & match score", ar: "اطلع على الراتب ونسبة التوافق" },
  { icon: Bookmark, en: "Save jobs & track applications", ar: "حفظ الوظائف ومتابعة الطلبات" },
  { icon: Bell, en: "Custom job alerts", ar: "تنبيهات وظائف مخصصة" },
  { icon: ExternalLink, en: "Direct apply to original source", ar: "تقديم مباشر للمصدر الأصلي" },
];

type AuthMode = "login" | "register";

export default function Login() {
  const { signIn, signUp, signInWithGoogle, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const reduced = useReducedMotion();
  const { toast } = useToast();
  const from = (location.state as any)?.from || "/app/jobs";

  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) navigate(from, { replace: true });
  }, [isAuthenticated, navigate, from]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (mode === "login") {
        await signIn(email, password);
      } else {
        await signUp(email, password, firstName, lastName);
      }
      navigate(from, { replace: true });
    } catch (err: any) {
      toast({
        title: mode === "login" ? "Login failed" : "Registration failed",
        description: err?.message ?? "Please check your details and try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const cardVariants = reduced
    ? { hidden: { opacity: 0 }, visible: { opacity: 1 } }
    : {
        hidden: { opacity: 0, y: 24, scale: 0.97 },
        visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.5, ease: MOTION.ease.default } },
      };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-background">
      <WatermarkBackground variant="shimmer" opacity={0.03} />
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-secondary/5" />

      <motion.div
        className="relative z-10 w-full max-w-4xl mx-auto px-4 py-8 flex flex-col lg:flex-row items-stretch gap-6"
        variants={cardVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Left: Career Guide teaser */}
        <div className="hidden lg:flex flex-col flex-1">
          <LoginCareerGuide />
        </div>

        {/* Right: Auth form */}
        <div className="flex-1 bg-card rounded-2xl border shadow-xl p-8 flex flex-col justify-center">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-foreground">
              {mode === "login"
                ? (isAr ? "تسجيل الدخول" : "Sign in")
                : (isAr ? "إنشاء حساب" : "Create account")}
            </h1>
            <p className="text-muted-foreground text-sm mt-1">
              {mode === "login"
                ? (isAr ? "مرحباً بك مجدداً" : "Welcome back to USAM Career Compass")
                : (isAr ? "انضم إلى USAM اليوم" : "Join thousands of MENA professionals")}
            </p>
          </div>

          {/* Google OAuth */}
          <Button
            type="button"
            variant="outline"
            className="w-full mb-4 gap-2"
            onClick={signInWithGoogle}
          >
            <svg className="h-4 w-4" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            {isAr ? "المتابعة مع Google" : "Continue with Google"}
          </Button>

          <div className="flex items-center gap-2 mb-4">
            <div className="flex-1 h-px bg-border" />
            <span className="text-xs text-muted-foreground">{isAr ? "أو" : "or"}</span>
            <div className="flex-1 h-px bg-border" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === "register" && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label htmlFor="firstName">{isAr ? "الاسم الأول" : "First name"}</Label>
                  <Input id="firstName" value={firstName} onChange={(e) => setFirstName(e.target.value)} required className="mt-1" />
                </div>
                <div>
                  <Label htmlFor="lastName">{isAr ? "اسم العائلة" : "Last name"}</Label>
                  <Input id="lastName" value={lastName} onChange={(e) => setLastName(e.target.value)} required className="mt-1" />
                </div>
              </div>
            )}

            <div>
              <Label htmlFor="email">{isAr ? "البريد الإلكتروني" : "Email"}</Label>
              <Input
                id="email" type="email" value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com" required className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="password">{isAr ? "كلمة المرور" : "Password"}</Label>
              <div className="relative mt-1">
                <Input
                  id="password" type={showPassword ? "text" : "password"}
                  value={password} onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••" required minLength={8}
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {mode === "login" && (
                <div className="text-right mt-1">
                  <Link to="/reset-password" className="text-xs text-primary hover:underline">
                    {isAr ? "نسيت كلمة المرور؟" : "Forgot password?"}
                  </Link>
                </div>
              )}
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading
                ? (isAr ? "جاري التحميل..." : "Loading...")
                : mode === "login"
                  ? (isAr ? "تسجيل الدخول" : "Sign in")
                  : (isAr ? "إنشاء الحساب" : "Create account")}
            </Button>
          </form>

          <p className="text-center text-sm text-muted-foreground mt-4">
            {mode === "login" ? (
              <>
                {isAr ? "ليس لديك حساب؟ " : "Don't have an account? "}
                <button onClick={() => setMode("register")} className="text-primary hover:underline font-medium">
                  {isAr ? "سجّل الآن" : "Sign up"}
                </button>
              </>
            ) : (
              <>
                {isAr ? "لديك حساب بالفعل؟ " : "Already have an account? "}
                <button onClick={() => setMode("login")} className="text-primary hover:underline font-medium">
                  {isAr ? "تسجيل الدخول" : "Sign in"}
                </button>
              </>
            )}
          </p>

          {/* Benefits list */}
          <div className="mt-6 pt-4 border-t">
            <div className="flex items-center gap-2 mb-2">
              <Lock className="h-3.5 w-3.5 text-primary" />
              <p className="text-xs font-medium">{isAr ? "لماذا تسجيل الدخول؟" : "Why sign in?"}</p>
            </div>
            <ul className="space-y-1.5">
              {BENEFITS.map((b, i) => (
                <li key={i} className="flex items-center gap-2 text-xs text-muted-foreground">
                  <div className="rounded bg-primary/10 p-1 shrink-0">
                    <b.icon className="h-3 w-3 text-primary" />
                  </div>
                  {isAr ? b.ar : b.en}
                </li>
              ))}
            </ul>
          </div>

          <div className="mt-4 pt-3 border-t text-center">
            <div className="flex items-center justify-center gap-1.5 text-xs text-muted-foreground">
              <Shield className="h-3 w-3" />
              {isAr ? "بياناتك آمنة ومشفرة" : "Your data is safe & encrypted"}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
