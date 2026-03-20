import { useState } from "react";
import { Bell, Plus, Trash2, Pause, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Layout } from "@/components/Layout";
import { useAlerts } from "@/hooks/use-alerts";
import { useTheme } from "@/hooks/use-theme";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDistanceToNow } from "date-fns";

export default function Alerts() {
  const { alerts, isLoading, addAlert, updateAlert, removeAlert } = useAlerts();
  const { toast } = useToast();
  const { lang } = useTheme();
  const isAr = lang === "ar";

  const [keyword, setKeyword] = useState("");
  const [workMode, setWorkMode] = useState("");
  const [industry, setIndustry] = useState("");
  const [frequency, setFrequency] = useState<"daily" | "weekly" | "instant">("daily");

  const handleCreate = async () => {
    if (!keyword.trim()) return;
    const result = await addAlert(keyword.trim(), workMode || undefined, industry || undefined, frequency);
    if (result?.error) {
      toast({ title: "Error", description: "Failed to create alert.", variant: "destructive" });
    } else {
      toast({ title: isAr ? "تم إنشاء التنبيه" : "Alert created", description: `"${keyword}" jobs will notify you.` });
      setKeyword(""); setWorkMode(""); setIndustry("");
    }
  };

  return (
    <Layout>
      <div className="container py-8 max-w-2xl">
        <h1 className="text-2xl font-medium mb-1 flex items-center gap-2">
          <Bell className="h-6 w-6 text-primary" />
          {isAr ? "تنبيهات الوظائف" : "Job Alerts"}
        </h1>
        <p className="text-sm text-muted-foreground mb-6">
          {isAr ? "احصل على إشعارات عند توفر وظائف جديدة" : "Get notified when new matching jobs are posted"}
        </p>

        {/* Create alert form */}
        <Card className="mb-6">
          <CardContent className="p-5 space-y-3">
            <h3 className="text-sm font-medium">{isAr ? "إنشاء تنبيه جديد" : "Create New Alert"}</h3>
            <Input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              placeholder={isAr ? "كلمة مفتاحية (مثل: React, تسويق)" : "Keyword (e.g. React, Marketing)"}
              className="rounded-xl"
            />
            <div className="grid grid-cols-3 gap-2">
              <Select value={workMode || "any"} onValueChange={(v) => setWorkMode(v === "any" ? "" : v)}>
                <SelectTrigger className="text-sm rounded-xl"><SelectValue placeholder={isAr ? "نوع الموقع" : "Work mode"} /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">{isAr ? "الكل" : "Any"}</SelectItem>
                  <SelectItem value="remote">{isAr ? "عن بعد" : "Remote"}</SelectItem>
                  <SelectItem value="hybrid">{isAr ? "هجين" : "Hybrid"}</SelectItem>
                  <SelectItem value="onsite">{isAr ? "في المقر" : "On-site"}</SelectItem>
                </SelectContent>
              </Select>
              <Select value={industry || "any"} onValueChange={(v) => setIndustry(v === "any" ? "" : v)}>
                <SelectTrigger className="text-sm rounded-xl"><SelectValue placeholder={isAr ? "القطاع" : "Industry"} /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">{isAr ? "الكل" : "Any"}</SelectItem>
                  <SelectItem value="technology">{isAr ? "التكنولوجيا" : "Technology"}</SelectItem>
                  <SelectItem value="finance">{isAr ? "المالية" : "Finance"}</SelectItem>
                  <SelectItem value="healthcare">{isAr ? "الرعاية الصحية" : "Healthcare"}</SelectItem>
                  <SelectItem value="design">{isAr ? "التصميم" : "Design"}</SelectItem>
                  <SelectItem value="marketing">{isAr ? "التسويق" : "Marketing"}</SelectItem>
                </SelectContent>
              </Select>
              <Select value={frequency} onValueChange={(v) => setFrequency(v as any)}>
                <SelectTrigger className="text-sm rounded-xl"><SelectValue placeholder={isAr ? "التكرار" : "Frequency"} /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">{isAr ? "يومي" : "Daily"}</SelectItem>
                  <SelectItem value="weekly">{isAr ? "أسبوعي" : "Weekly"}</SelectItem>
                  <SelectItem value="instant">{isAr ? "فوري" : "Instant"}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleCreate} disabled={!keyword.trim()} className="w-full rounded-xl">
              <Plus className="h-4 w-4 mr-1" /> {isAr ? "إنشاء تنبيه" : "Create Alert"}
            </Button>
          </CardContent>
        </Card>

        {/* Alert list */}
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => <Skeleton key={i} className="h-20 w-full rounded-xl" />)}
          </div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-16 text-muted-foreground">
            <Bell className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p className="font-medium">{isAr ? "لا توجد تنبيهات" : "No alerts yet"}</p>
            <p className="text-sm mt-1">{isAr ? "أنشئ تنبيهاً أعلاه لتبدأ" : "Create an alert above to get started"}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <Card key={alert.uuid} className={!alert.is_active ? "opacity-60" : ""}>
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">"{alert.keyword || (isAr ? "كل الوظائف" : "All jobs")}"</p>
                    <div className="flex gap-1.5 mt-1 flex-wrap">
                      {alert.work_mode && <Badge variant="outline" className="text-[10px]">{alert.work_mode}</Badge>}
                      {alert.industry && <Badge variant="outline" className="text-[10px]">{alert.industry}</Badge>}
                      <Badge variant="secondary" className="text-[10px]">{alert.frequency}</Badge>
                      {!alert.is_active && <Badge variant="destructive" className="text-[10px]">{isAr ? "متوقف" : "paused"}</Badge>}
                      <span className="text-[10px] text-muted-foreground">
                        {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost" size="icon"
                      onClick={() => updateAlert(alert.uuid, { is_active: !alert.is_active })}
                      title={alert.is_active ? "Pause" : "Resume"}
                    >
                      {alert.is_active ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => removeAlert(alert.uuid)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
