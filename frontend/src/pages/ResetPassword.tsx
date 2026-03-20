import { useState, useEffect } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useTheme } from "@/hooks/use-theme";
import { useToast } from "@/hooks/use-toast";
import { Lock, Mail } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { resetPasswordConfirm } from "@/services/auth";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const uid = searchParams.get("uid");
  const token = searchParams.get("token");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [done, setDone] = useState(false);
  const navigate = useNavigate();
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const { toast } = useToast();
  const { resetPassword } = useAuth();

  const isConfirmMode = !!(uid && token);

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await resetPassword(email);
      setSent(true);
    } catch {
      toast({ title: "Error", description: "Something went wrong. Please try again.", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirm) {
      toast({ title: "Passwords don't match", variant: "destructive" });
      return;
    }
    setLoading(true);
    try {
      await resetPasswordConfirm(uid!, token!, password, confirm);
      setDone(true);
      setTimeout(() => navigate("/login"), 2000);
    } catch (err: any) {
      toast({ title: "Reset failed", description: err?.message ?? "Invalid or expired link.", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md bg-card rounded-2xl border shadow-xl p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="rounded-xl bg-primary/10 p-2.5">
            <Lock className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold">
              {isConfirmMode
                ? (isAr ? "كلمة مرور جديدة" : "Set new password")
                : (isAr ? "إعادة تعيين كلمة المرور" : "Reset your password")}
            </h1>
            <p className="text-sm text-muted-foreground">
              {isConfirmMode
                ? (isAr ? "اختر كلمة مرور قوية" : "Choose a strong password")
                : (isAr ? "أدخل بريدك لاستلام الرابط" : "Enter your email to receive a reset link")}
            </p>
          </div>
        </div>

        {done ? (
          <div className="text-center py-6">
            <p className="text-green-600 font-medium">✅ {isAr ? "تم تغيير كلمة المرور!" : "Password changed!"}</p>
            <p className="text-sm text-muted-foreground mt-1">{isAr ? "جاري التحويل..." : "Redirecting to login..."}</p>
          </div>
        ) : sent && !isConfirmMode ? (
          <div className="text-center py-6">
            <Mail className="h-10 w-10 text-primary mx-auto mb-3" />
            <p className="font-medium">{isAr ? "تحقق من بريدك الإلكتروني" : "Check your inbox"}</p>
            <p className="text-sm text-muted-foreground mt-1">
              {isAr ? "إذا كان الحساب موجوداً، سيصلك رابط إعادة التعيين." : "If that email exists, a reset link is on its way."}
            </p>
            <Link to="/login" className="text-primary text-sm hover:underline mt-4 block">
              {isAr ? "العودة لتسجيل الدخول" : "Back to login"}
            </Link>
          </div>
        ) : isConfirmMode ? (
          <form onSubmit={handleConfirmReset} className="space-y-4">
            <div>
              <Label>{isAr ? "كلمة المرور الجديدة" : "New password"}</Label>
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required className="mt-1" />
            </div>
            <div>
              <Label>{isAr ? "تأكيد كلمة المرور" : "Confirm password"}</Label>
              <Input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required className="mt-1" />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "..." : (isAr ? "حفظ كلمة المرور" : "Save password")}
            </Button>
          </form>
        ) : (
          <form onSubmit={handleRequestReset} className="space-y-4">
            <div>
              <Label>{isAr ? "البريد الإلكتروني" : "Email address"}</Label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="mt-1" placeholder="you@example.com" />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "..." : (isAr ? "إرسال رابط الاسترداد" : "Send reset link")}
            </Button>
            <Link to="/login" className="block text-center text-sm text-primary hover:underline">
              {isAr ? "العودة لتسجيل الدخول" : "Back to login"}
            </Link>
          </form>
        )}
      </div>
    </div>
  );
}
