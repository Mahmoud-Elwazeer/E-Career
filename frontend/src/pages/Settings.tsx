import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useTheme } from "@/hooks/use-theme";
import { useAuth } from "@/hooks/use-auth";
import { updateMe, changePassword, deleteAccount } from "@/services/auth";
import { useToast } from "@/hooks/use-toast";
import { Bell, Lock, User, Shield, Loader2 } from "lucide-react";

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

  useEffect(() => {
    if (user) {
      setName(user.full_name || "");
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
    <Layout>
      <div className="container max-w-4xl py-8">
        <div className="mb-8">
          <h1 className="text-heading-1 mb-2">
            {isAr ? "الإعدادات" : "Settings"}
          </h1>
          <p className="text-muted-foreground">
            {isAr ? "إدارة تفضيلاتك وإعدادات الحساب" : "Manage your preferences and account settings"}
          </p>
        </div>

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

          {/* Notification Settings */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                <CardTitle>{isAr ? "الإشعارات" : "Notifications"}</CardTitle>
              </div>
              <CardDescription>
                {isAr ? "إدارة تفضيلات الإشعارات" : "Manage your notification preferences"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>{isAr ? "فرص عمل جديدة" : "New Job Opportunities"}</Label>
                  <p className="text-sm text-muted-foreground">
                    {isAr ? "إشعارات عند نشر وظائف تطابق ملفك" : "Notify when jobs match your profile"}
                  </p>
                </div>
                <Switch defaultChecked />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>{isAr ? "تحديثات الطلبات" : "Application Updates"}</Label>
                  <p className="text-sm text-muted-foreground">
                    {isAr ? "إشعارات عند تغيير حالة الطلب" : "Notify on application status changes"}
                  </p>
                </div>
                <Switch defaultChecked />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>{isAr ? "نصائح مهنية" : "Career Tips"}</Label>
                  <p className="text-sm text-muted-foreground">
                    {isAr ? "نصائح أسبوعية لتطوير مسارك المهني" : "Weekly tips to improve your career"}
                  </p>
                </div>
                <Switch />
              </div>
            </CardContent>
          </Card>

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
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>{isAr ? "ملف شخصي عام" : "Public Profile"}</Label>
                  <p className="text-sm text-muted-foreground">
                    {isAr ? "السماح لأصحاب العمل برؤية ملفك" : "Allow employers to view your profile"}
                  </p>
                </div>
                <Switch defaultChecked />
              </div>
              <Separator />
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
    </Layout>
  );
}
