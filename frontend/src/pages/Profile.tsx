import { useState, useRef } from "react";
import { User, Bookmark, Bell, Settings, Plus, Trash2, Camera, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StaggerContainer, StaggerItem } from "@/components/motion";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Layout } from "@/components/Layout";
import { JobCard } from "@/components/JobCard";
import { EmptyState } from "@/components/EmptyState";
import { useSavedJobs } from "@/hooks/use-saved-jobs";
import { useAlerts } from "@/hooks/use-alerts";
import { useAuth } from "@/hooks/use-auth";
import { useTheme } from "@/hooks/use-theme";
import { useToast } from "@/hooks/use-toast";
import { uploadAvatar } from "@/services/auth";
import { formatDistanceToNow } from "date-fns";
import { usePageMeta } from "@/hooks/use-seo";

export default function Profile() {
  usePageMeta("My Profile", "Manage your saved jobs, alerts, and preferences on USAM Jobs.");
  const { user, refreshUser } = useAuth();
  const { savedJobs, isSaved, save, remove } = useSavedJobs();
  const { alerts, addAlert, removeAlert } = useAlerts();
  const { lang, theme, setTheme } = useTheme();
  const { toast } = useToast();
  const isAr = lang === "ar";
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || "");

  const [keyword, setKeyword] = useState("");
  const [alertLocType, setAlertLocType] = useState("");
  const [alertIndustry, setAlertIndustry] = useState("");

  const handleCreateAlert = () => {
    if (!keyword.trim()) return;
    addAlert(keyword.trim(), alertLocType || undefined, alertIndustry || undefined);
    toast({
      title: isAr ? "تم إنشاء التنبيه" : "Alert created",
      description: isAr ? `ستتلقى إشعاراً عند توفر وظائف "${keyword}"` : `You'll be notified for "${keyword}" jobs.`,
    });
    setKeyword("");
    setAlertLocType("");
    setAlertIndustry("");
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const allowed = ["image/jpeg", "image/png", "image/webp"];
    if (!allowed.includes(file.type)) {
      toast({ title: "Invalid file type", description: "Use JPG, PNG, or WebP.", variant: "destructive" });
      return;
    }
    setUploading(true);
    try {
      const updated = await uploadAvatar(file);
      const url = updated.avatar_url || "";
      setAvatarUrl(url);
      await refreshUser?.();
      toast({ title: isAr ? "تم تحديث الصورة" : "Avatar updated" });
    } catch (err: any) {
      toast({ title: "Upload failed", description: err?.message, variant: "destructive" });
    } finally {
      setUploading(false);
    }
  };

  return (
    <Layout>
      <section className="bg-surface-2 border-b">
        <div className="container py-8 max-w-3xl">
          <div className="flex items-center gap-4 animate-fade-in">
            <div className="relative group">
              {avatarUrl ? (
                <img src={avatarUrl} alt="Avatar" className="h-16 w-16 rounded-2xl object-cover" />
              ) : (
                <div className="h-16 w-16 rounded-2xl bg-primary flex items-center justify-center">
                  <User className="h-7 w-7 text-primary-foreground" />
                </div>
              )}
              <button
                onClick={() => fileRef.current?.click()}
                disabled={uploading}
                className="absolute inset-0 rounded-2xl bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
              >
                {uploading ? <Loader2 className="h-5 w-5 text-white animate-spin" /> : <Camera className="h-5 w-5 text-white" />}
              </button>
              <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp"
                onChange={handleAvatarUpload} className="hidden" />
            </div>
            <div>
              <h1 className="text-heading-2">{user?.full_name || user?.first_name || (isAr ? "مرحباً" : "Welcome back")}</h1>
              <p className="text-body text-muted-foreground">{user?.email}</p>
            </div>
          </div>
        </div>
      </section>

      <div className="container py-8 max-w-3xl">
        <Tabs defaultValue="saved">
          <TabsList className="mb-6">
            <TabsTrigger value="saved" className="gap-1.5">
              <Bookmark className="h-3.5 w-3.5" />
              {isAr ? `المحفوظة (${savedJobs.length})` : `Saved (${savedJobs.length})`}
            </TabsTrigger>
            <TabsTrigger value="alerts" className="gap-1.5">
              <Bell className="h-3.5 w-3.5" />
              {isAr ? `التنبيهات (${alerts.length})` : `Alerts (${alerts.length})`}
            </TabsTrigger>
            <TabsTrigger value="preferences" className="gap-1.5">
              <Settings className="h-3.5 w-3.5" />
              {isAr ? "التفضيلات" : "Preferences"}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="saved">
            {savedJobs.length > 0 ? (
              <StaggerContainer className="space-y-3">
                {savedJobs.map(({ job }) => (
                  <StaggerItem key={job.id}>
                    <JobCard job={job} isSaved={isSaved(job.id)}
                      onToggleSave={(jid) => (isSaved(jid) ? remove(jid) : save(Number(jid)))} />
                  </StaggerItem>
                ))}
              </StaggerContainer>
            ) : (
              <EmptyState icon={Bookmark}
                title={isAr ? "لا توجد وظائف محفوظة" : "No saved jobs yet"}
                description={isAr ? "انقر على أيقونة الحفظ في أي وظيفة لإضافتها هنا" : "Click the bookmark icon on any job to save it here"}
                actionLabel={isAr ? "تصفح الوظائف" : "Browse jobs"} actionHref="/app/jobs" />
            )}
          </TabsContent>

          <TabsContent value="alerts">
            <Card className="mb-6">
              <CardContent className="p-5 space-y-3">
                <h3 className="text-body font-medium">{isAr ? "إنشاء تنبيه جديد" : "Create New Alert"}</h3>
                <Input value={keyword} onChange={(e) => setKeyword(e.target.value)}
                  placeholder={isAr ? "كلمة مفتاحية (مثل: React, تسويق)" : "Keyword (e.g. React, Marketing)"}
                  className="rounded-xl" />
                <div className="grid grid-cols-2 gap-3">
                  <Select value={alertLocType || "any"} onValueChange={(v) => setAlertLocType(v === "any" ? "" : v)}>
                    <SelectTrigger className="text-body rounded-xl"><SelectValue placeholder={isAr ? "نوع الموقع" : "Location type"} /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="any">{isAr ? "الكل" : "Any"}</SelectItem>
                      <SelectItem value="remote">{isAr ? "عن بعد" : "Remote"}</SelectItem>
                      <SelectItem value="hybrid">{isAr ? "هجين" : "Hybrid"}</SelectItem>
                      <SelectItem value="onsite">{isAr ? "في المقر" : "On-site"}</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={alertIndustry || "any"} onValueChange={(v) => setAlertIndustry(v === "any" ? "" : v)}>
                    <SelectTrigger className="text-body rounded-xl"><SelectValue placeholder={isAr ? "القطاع" : "Industry"} /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="any">{isAr ? "الكل" : "Any"}</SelectItem>
                      <SelectItem value="technology">{isAr ? "التكنولوجيا" : "Technology"}</SelectItem>
                      <SelectItem value="finance">{isAr ? "المالية" : "Finance"}</SelectItem>
                      <SelectItem value="healthcare">{isAr ? "الرعاية الصحية" : "Healthcare"}</SelectItem>
                      <SelectItem value="design">{isAr ? "التصميم" : "Design"}</SelectItem>
                      <SelectItem value="marketing">{isAr ? "التسويق" : "Marketing"}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={handleCreateAlert} disabled={!keyword.trim()} className="w-full rounded-xl">
                  <Plus className="h-4 w-4 me-1" /> {isAr ? "إنشاء تنبيه" : "Create Alert"}
                </Button>
              </CardContent>
            </Card>

            {alerts.length > 0 ? (
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <Card key={alert.uuid} className="animate-fade-in">
                    <CardContent className="p-4 flex items-center justify-between">
                      <div>
                        <p className="text-body font-medium">"{alert.keyword || "All jobs"}"</p>
                        <div className="flex gap-1.5 mt-1 flex-wrap">
                          {alert.work_mode && <Badge variant="outline" className="text-[10px]">{alert.work_mode}</Badge>}
                          {alert.industry && <Badge variant="outline" className="text-[10px]">{alert.industry}</Badge>}
                          <span className="text-[10px] text-muted-foreground">
                            {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
                          </span>
                        </div>
                      </div>
                      <Button variant="ghost" size="icon" onClick={() => removeAlert(alert.uuid)}>
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <EmptyState icon={Bell}
                title={isAr ? "لا توجد تنبيهات" : "No alerts yet"}
                description={isAr ? "أنشئ تنبيهاً أعلاه لتبدأ" : "Create an alert above to get started"} />
            )}
          </TabsContent>

          <TabsContent value="preferences">
            <div className="space-y-6 animate-fade-in">
              <Card>
                <CardContent className="p-5 space-y-4">
                  <h3 className="text-body font-medium">{isAr ? "المظهر" : "Theme"}</h3>
                  <div className="flex gap-2">
                    {(["light", "dark", "night"] as const).map((t) => (
                      <Button key={t} variant={theme === t ? "default" : "outline"} size="sm"
                        className="rounded-xl capitalize flex-1" onClick={() => setTheme(t)}>
                        {t === "light" ? "☀️" : t === "dark" ? "🌙" : "🌑"} {t}
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-5">
                  <h3 className="text-body font-medium mb-3">{isAr ? "عن التطبيق" : "About"}</h3>
                  <p className="text-caption text-muted-foreground">
                    USAM Career Compass v1.0<br />
                    {isAr ? "بحث واحد. كل الفرص." : "One search. Every opportunity."}
                  </p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}
