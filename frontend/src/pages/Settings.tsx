import { Layout } from "@/components/Layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { useTheme } from "@/hooks/use-theme";
import { Bell, Lock, User, Globe, Palette, Shield } from "lucide-react";

export default function Settings() {
  const { lang } = useTheme();
  const isAr = lang === "ar";

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
                <Input placeholder={isAr ? "اسمك الكامل" : "Your full name"} />
              </div>
              <div className="space-y-2">
                <Label>{isAr ? "البريد الإلكتروني" : "Email"}</Label>
                <Input type="email" placeholder={isAr ? "بريدك الإلكتروني" : "Your email"} />
              </div>
              <Button>{isAr ? "حفظ التغييرات" : "Save Changes"}</Button>
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
                <Button variant="outline">{isAr ? "تحديث كلمة المرور" : "Update Password"}</Button>
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
                <Button variant="destructive">{isAr ? "حذف" : "Delete"}</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
