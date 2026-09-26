import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { AppShell } from "@/components/shells/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/hooks/use-auth";
import { updateMe, changePassword, deleteAccount } from "@/services/auth";
import { apiRequest } from "@/services/client";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { Bell, User, Shield, Loader2, ChevronRight, Eye } from "lucide-react";

export default function Settings() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const { user, refreshUser, signOut } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [saving, setSaving] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [changingPw, setChangingPw] = useState(false);
  const [showPwForm, setShowPwForm] = useState(false);

  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  // Talent-pool discoverability (individual consent)
  const [discoverable, setDiscoverable] = useState<boolean | null>(null);
  const [savingDiscover, setSavingDiscover] = useState(false);
  const isEmployer = user?.role === "employer";

  useEffect(() => {
    if (isEmployer) return;
    apiRequest<{ is_discoverable: boolean }>("/career/discoverability/")
      .then((d) => setDiscoverable(!!d?.is_discoverable))
      .catch(() => setDiscoverable(false));
  }, [isEmployer]);

  const toggleDiscoverable = async (next: boolean) => {
    setSavingDiscover(true);
    const prev = discoverable;
    setDiscoverable(next); // optimistic
    try {
      await apiRequest("/career/discoverability/", { method: "PATCH", body: { is_discoverable: next } });
      toast({ title: isAr ? "تم التحديث" : "Updated", description: next
        ? (isAr ? "أصبح ملفك مرئياً لأصحاب العمل." : "You're now discoverable by employers.")
        : (isAr ? "لم يعد ملفك مرئياً لأصحاب العمل." : "You're no longer discoverable.") });
    } catch {
      setDiscoverable(prev); // revert
      toast({ title: isAr ? "خطأ" : "Error", description: isAr ? "فشل التحديث" : "Failed to update.", variant: "destructive" });
    } finally {
      setSavingDiscover(false);
    }
  };

  useEffect(() => {
    if (user) {
      setName(user.name || "");
      setEmail(user.email || "");
    }
  }, [user]);

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      const [first_name, ...rest] = name.trim().split(" ");
      await updateMe({ first_name, last_name: rest.join(" ") });
      await refreshUser();
      toast({ title: isAr ? "تم الحفظ" : "Saved", description: isAr ? "تم تحديث بياناتك" : "Profile updated." });
    } catch {
      toast({ title: isAr ? "خطأ" : "Error", description: isAr ? "فشل التحديث" : "Failed to update profile.", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      toast({ title: isAr ? "خطأ" : "Error", description: isAr ? "كلمات المرور غير متطابقة" : "Passwords do not match.", variant: "destructive" });
      return;
    }
    setChangingPw(true);
    try {
      await changePassword(currentPassword, newPassword, confirmPassword);
      toast({ title: isAr ? "تم التحديث" : "Updated", description: isAr ? "تم تغيير كلمة المرور" : "Password changed." });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setShowPwForm(false);
    } catch {
      toast({ title: isAr ? "خطأ" : "Error", description: isAr ? "فشل تغيير كلمة المرور" : "Failed to change password.", variant: "destructive" });
    } finally {
      setChangingPw(false);
    }
  };

  const handleDeleteAccount = async () => {
    setDeleting(true);
    try {
      await deleteAccount();
      await signOut();
      navigate("/");
    } catch {
      toast({ title: isAr ? "خطأ" : "Error", description: isAr ? "فشل حذف الحساب" : "Failed to delete account.", variant: "destructive" });
      setDeleting(false);
      setConfirmDelete(false);
    }
  };

  return (
    <AppShell>
      <div className="container max-w-4xl py-8">
        <PageHeader
          title={isAr ? "الإعدادات" : "Settings"}
          subtitle={isAr ? "إدارة تفضيلاتك وإعدادات الحساب" : "Manage your preferences and account settings"}
        />

        <div className="space-y-6">
          {/* Account Settings */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <User className="h-5 w-5" />
                <CardTitle>{isAr ? "الحساب" : "Account"}</CardTitle>
              </div>
              <CardDescription>
                {isAr ? "معلومات حسابك الشخصية" : "Your personal account information"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>{isAr ? "الاسم" : "Name"}</Label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder={isAr ? "اسمك الكامل" : "Your full name"}
                />
              </div>
              <div className="space-y-2">
                <Label>{isAr ? "البريد الإلكتروني" : "Email"}</Label>
                <Input type="email" value={email} disabled />
              </div>
              <Button onClick={handleSaveProfile} disabled={saving}>
                {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isAr ? "حفظ التغييرات" : "Save Changes"}
              </Button>
            </CardContent>
          </Card>

          {/* Notification Settings — delegate to the dedicated, fully-wired page
              instead of duplicating toggles that could drift out of sync. */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                <CardTitle>{isAr ? "الإشعارات" : "Notifications"}</CardTitle>
              </div>
              <CardDescription>
                {isAr ? "إدارة تفضيلات الإشعارات والقنوات والتكرار" : "Manage channels, frequency, and notification types"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link
                to="/app/notification-preferences"
                className="surface-card-interactive flex items-center justify-between p-4 group"
              >
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-primary-muted p-2">
                    <Bell className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-body font-medium">
                      {isAr ? "تفضيلات الإشعارات" : "Notification preferences"}
                    </p>
                    <p className="text-caption text-muted-foreground">
                      {isAr ? "البريد، داخل التطبيق، التكرار، وساعات الهدوء" : "Email, in-app, frequency & quiet hours"}
                    </p>
                  </div>
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors rtl:rotate-180" />
              </Link>
            </CardContent>
          </Card>

          {/* Talent Pool visibility — individual consent to be discovered by
              employers. Job-seeker only. */}
          {!isEmployer && (
            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Eye className="h-5 w-5" />
                  <CardTitle>{isAr ? "الظهور في قاعدة المواهب" : "Talent Pool Visibility"}</CardTitle>
                </div>
                <CardDescription>
                  {isAr
                    ? "اسمح لأصحاب العمل الموثقين باكتشاف ملفك وإضافتك إلى قوائم المواهب."
                    : "Let verified employers discover your profile and add you to talent pools."}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between rounded-xl border border-border p-4">
                  <div className="pe-4">
                    <p className="text-body font-medium">
                      {isAr ? "مرئي لأصحاب العمل" : "Discoverable by employers"}
                    </p>
                    <p className="text-caption text-muted-foreground">
                      {isAr
                        ? "عند التفعيل، يمكن لأصحاب العمل العثور عليك في البحث عن المواهب."
                        : "When on, employers can find you in talent search. You can turn this off anytime."}
                    </p>
                  </div>
                  {discoverable === null ? (
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  ) : (
                    <Switch
                      checked={discoverable}
                      disabled={savingDiscover}
                      onCheckedChange={toggleDiscoverable}
                      aria-label={isAr ? "الظهور في قاعدة المواهب" : "Talent pool visibility"}
                    />
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Privacy & Security */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                <CardTitle>{isAr ? "الخصوصية والأمان" : "Privacy & Security"}</CardTitle>
              </div>
              <CardDescription>
                {isAr ? "إعدادات الأمان والخصوصية" : "Security and privacy settings"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>{isAr ? "تغيير كلمة المرور" : "Change Password"}</Label>
                {!showPwForm ? (
                  <Button variant="outline" onClick={() => setShowPwForm(true)}>
                    {isAr ? "تحديث كلمة المرور" : "Update Password"}
                  </Button>
                ) : (
                  <div className="space-y-3 max-w-sm">
                    <Input
                      type="password"
                      placeholder={isAr ? "كلمة المرور الحالية" : "Current password"}
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                    />
                    <Input
                      type="password"
                      placeholder={isAr ? "كلمة المرور الجديدة" : "New password"}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                    />
                    <Input
                      type="password"
                      placeholder={isAr ? "تأكيد كلمة المرور" : "Confirm new password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                    />
                    <div className="flex gap-2">
                      <Button onClick={handleChangePassword} disabled={changingPw || !currentPassword || !newPassword}>
                        {changingPw && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        {isAr ? "تغيير" : "Change"}
                      </Button>
                      <Button variant="ghost" onClick={() => { setShowPwForm(false); setCurrentPassword(""); setNewPassword(""); setConfirmPassword(""); }}>
                        {isAr ? "إلغاء" : "Cancel"}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Danger Zone */}
          <Card className="border-destructive/50">
            <CardHeader>
              <CardTitle className="text-destructive">{isAr ? "منطقة الخطر" : "Danger Zone"}</CardTitle>
              <CardDescription>
                {isAr ? "إجراءات لا يمكن التراجع عنها" : "Irreversible actions"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>{isAr ? "حذف الحساب" : "Delete Account"}</Label>
                  <p className="text-sm text-muted-foreground">
                    {isAr ? "حذف حسابك وجميع بياناتك نهائياً" : "Permanently delete your account and all data"}
                  </p>
                </div>
                {!confirmDelete ? (
                  <Button variant="destructive" onClick={() => setConfirmDelete(true)}>
                    {isAr ? "حذف" : "Delete"}
                  </Button>
                ) : (
                  <div className="flex gap-2">
                    <Button variant="destructive" onClick={handleDeleteAccount} disabled={deleting}>
                      {deleting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      {isAr ? "تأكيد الحذف" : "Confirm Delete"}
                    </Button>
                    <Button variant="ghost" onClick={() => setConfirmDelete(false)}>
                      {isAr ? "إلغاء" : "Cancel"}
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
