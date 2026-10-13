import { useEffect, useState } from "react";
import { AppShell } from "@/components/shells/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { useTheme } from "@/hooks/use-theme";
import {
  Download, Trash2, ShieldCheck, Eye, Megaphone, Loader2, FileText, Clock, Ban,
} from "lucide-react";
import { apiRequest } from "@/services/client";
import {
  requestDataExport, getDataExportStatus, requestAccountDeletionGrace,
  cancelAccountDeletionGrace, getAccountDeletionStatus,
  type DataExportRequestStatus, type DeletionStatus,
} from "@/services/auth";
import {
  listConsentPurposes, setConsent, getMarketingPreference, updateMarketingPreference,
  openPrivacyRequest, listPrivacyRequests,
  type ConsentPurpose, type MarketingPreference, type PrivacyRequest,
} from "@/services/legal";

const DSR_TYPES: { key: string; en: string; ar: string }[] = [
  { key: "access", en: "Access my data", ar: "الوصول إلى بياناتي" },
  { key: "correct", en: "Correct my data", ar: "تصحيح بياناتي" },
  { key: "restrict", en: "Restrict processing", ar: "تقييد المعالجة" },
  { key: "object", en: "Object to processing", ar: "الاعتراض على المعالجة" },
  { key: "complaint", en: "File a complaint", ar: "تقديم شكوى" },
];

export default function PrivacyCenter() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const { toast } = useToast();

  // Data export
  const [exportStatus, setExportStatus] = useState<DataExportRequestStatus | null>(null);
  const [exportLoading, setExportLoading] = useState(false);

  // Deletion grace period
  const [deletionStatus, setDeletionStatus] = useState<DeletionStatus | null>(null);
  const [deletionLoading, setDeletionLoading] = useState(false);
  const [confirmDeletion, setConfirmDeletion] = useState(false);

  // Consent purposes
  const [purposes, setPurposes] = useState<ConsentPurpose[]>([]);
  const [savingPurpose, setSavingPurpose] = useState<string | null>(null);

  // Marketing preference
  const [marketing, setMarketing] = useState<MarketingPreference | null>(null);
  const [savingMarketing, setSavingMarketing] = useState(false);

  // Talent pool (reusing the same discoverability endpoint Settings uses)
  const [discoverable, setDiscoverable] = useState<boolean | null>(null);
  const [savingDiscover, setSavingDiscover] = useState(false);

  // DSR requests
  const [requests, setRequests] = useState<PrivacyRequest[]>([]);
  const [dsrType, setDsrType] = useState("access");
  const [dsrDetails, setDsrDetails] = useState("");
  const [submittingDsr, setSubmittingDsr] = useState(false);

  useEffect(() => {
    getAccountDeletionStatus().then(setDeletionStatus).catch(() => {});
    listConsentPurposes().then(setPurposes).catch(() => {});
    getMarketingPreference().then(setMarketing).catch(() => {});
    apiRequest<{ is_discoverable: boolean }>("/career/discoverability/")
      .then((d) => setDiscoverable(!!d?.is_discoverable)).catch(() => setDiscoverable(false));
    listPrivacyRequests().then(setRequests).catch(() => {});
  }, []);

  const handleExport = async () => {
    setExportLoading(true);
    try {
      const res = await requestDataExport();
      const polled = await getDataExportStatus(res.request_id);
      setExportStatus(polled);
      toast({ title: isAr ? "تم الطلب" : "Requested", description: isAr ? "سيتم إعداد ملف بياناتك." : "Your data export is being prepared." });
    } catch {
      toast({ title: isAr ? "خطأ" : "Error", description: isAr ? "فشل طلب التصدير" : "Failed to request export.", variant: "destructive" });
    } finally {
      setExportLoading(false);
    }
  };

  const handleRequestDeletion = async () => {
    setDeletionLoading(true);
    try {
      const res = await requestAccountDeletionGrace();
      setDeletionStatus({ pending: true, scheduled_for: res.scheduled_for, request_id: res.request_id });
      setConfirmDeletion(false);
      toast({
        title: isAr ? "تم جدولة الحذف" : "Deletion scheduled",
        description: isAr ? "لديك 30 يوماً للإلغاء." : "You have 30 days to cancel.",
      });
    } catch {
      toast({ title: isAr ? "خطأ" : "Error", description: isAr ? "فشل الطلب" : "Request failed.", variant: "destructive" });
    } finally {
      setDeletionLoading(false);
    }
  };

  const handleCancelDeletion = async () => {
    setDeletionLoading(true);
    try {
      await cancelAccountDeletionGrace();
      setDeletionStatus({ pending: false });
      toast({ title: isAr ? "تم الإلغاء" : "Cancelled" });
    } catch {
      toast({ title: isAr ? "خطأ" : "Error", variant: "destructive" });
    } finally {
      setDeletionLoading(false);
    }
  };

  const togglePurpose = async (purpose: ConsentPurpose, granted: boolean) => {
    setSavingPurpose(purpose.key);
    setPurposes((prev) => prev.map((p) => (p.key === purpose.key ? { ...p, granted } : p)));
    try {
      await setConsent(purpose.key, granted, "privacy_center");
    } catch {
      setPurposes((prev) => prev.map((p) => (p.key === purpose.key ? { ...p, granted: !granted } : p)));
      toast({ title: isAr ? "خطأ" : "Error", description: isAr ? "فشل التحديث" : "Failed to update.", variant: "destructive" });
    } finally {
      setSavingPurpose(null);
    }
  };

  const toggleDiscoverable = async (next: boolean) => {
    setSavingDiscover(true);
    const prev = discoverable;
    setDiscoverable(next);
    try {
      await apiRequest("/career/discoverability/", { method: "PATCH", body: { is_discoverable: next } });
    } catch {
      setDiscoverable(prev);
      toast({ title: isAr ? "خطأ" : "Error", variant: "destructive" });
    } finally {
      setSavingDiscover(false);
    }
  };

  const toggleMarketing = async (field: "email_marketing_opt_in" | "sms_marketing_opt_in", value: boolean) => {
    if (!marketing) return;
    setSavingMarketing(true);
    const prev = marketing;
    setMarketing({ ...marketing, [field]: value });
    try {
      const updated = await updateMarketingPreference({ [field]: value });
      setMarketing(updated);
    } catch {
      setMarketing(prev);
      toast({ title: isAr ? "خطأ" : "Error", variant: "destructive" });
    } finally {
      setSavingMarketing(false);
    }
  };

  const submitDsr = async () => {
    setSubmittingDsr(true);
    try {
      const req = await openPrivacyRequest(dsrType, dsrDetails);
      setRequests((prev) => [req, ...prev]);
      setDsrDetails("");
      toast({ title: isAr ? "تم تقديم الطلب" : "Request submitted" });
    } catch {
      toast({ title: isAr ? "خطأ" : "Error", variant: "destructive" });
    } finally {
      setSubmittingDsr(false);
    }
  };

  return (
    <AppShell>
      <div className="container max-w-4xl py-8 space-y-6">
        <PageHeader
          title={isAr ? "مركز الخصوصية" : "Privacy Center"}
          subtitle={isAr
            ? "تصدير بياناتك، إدارة الموافقات، وطلبات الخصوصية — كل إجراء هنا موثّق وقابل للتدقيق."
            : "Export your data, manage consent, and submit privacy requests — every action here is logged and auditable."}
        />

        {/* Data export */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2"><Download className="h-5 w-5" /><CardTitle>{isAr ? "تصدير بياناتك" : "Export your data"}</CardTitle></div>
            <CardDescription>{isAr ? "احصل على نسخة من بياناتك الشخصية بصيغة JSON." : "Get a copy of your personal data as a JSON file."}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button onClick={handleExport} disabled={exportLoading}>
              {exportLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isAr ? "طلب تصدير البيانات" : "Request data export"}
            </Button>
            {exportStatus && (
              <p className="text-caption text-muted-foreground">
                {isAr ? "الحالة: " : "Status: "}{exportStatus.status}
                {exportStatus.download_url && (
                  <> — <a href={exportStatus.download_url} className="text-primary link-underline">{isAr ? "تحميل" : "Download"}</a></>
                )}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Consent purposes */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2"><ShieldCheck className="h-5 w-5" /><CardTitle>{isAr ? "الموافقات" : "Consent"}</CardTitle></div>
            <CardDescription>
              {isAr ? "كل موافقة مستقلة ويمكن سحبها في أي وقت دون التأثير على الأخرى." : "Each consent is independent and can be withdrawn at any time without affecting the others."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {purposes.length === 0 && <p className="text-caption text-muted-foreground">{isAr ? "لا توجد موافقات مُعرّفة بعد." : "No consent purposes configured yet."}</p>}
            {purposes.map((p) => (
              <div key={p.key} className="flex items-center justify-between rounded-xl border border-border p-3">
                <div className="pe-4">
                  <p className="text-body font-medium">{p.label}</p>
                  {p.description && <p className="text-caption text-muted-foreground">{p.description}</p>}
                </div>
                <Switch
                  checked={!!p.granted}
                  disabled={p.is_required || savingPurpose === p.key}
                  onCheckedChange={(v) => togglePurpose(p, v)}
                  aria-label={p.label}
                />
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Talent Pool visibility (explicit, opt-in) */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2"><Eye className="h-5 w-5" /><CardTitle>{isAr ? "الظهور في قاعدة المواهب" : "Talent Pool visibility"}</CardTitle></div>
            <CardDescription>{isAr ? "غير مفعّل تلقائياً — أنت من يقرر." : "Off by default — you decide."}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between rounded-xl border border-border p-3">
              <p className="text-body">{isAr ? "مرئي لأصحاب العمل الموثقين" : "Discoverable by verified employers"}</p>
              {discoverable === null ? <Loader2 className="h-4 w-4 animate-spin" /> : (
                <Switch checked={discoverable} disabled={savingDiscover} onCheckedChange={toggleDiscoverable} />
              )}
            </div>
          </CardContent>
        </Card>

        {/* Marketing preference (separate from transactional notifications) */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2"><Megaphone className="h-5 w-5" /><CardTitle>{isAr ? "تفضيلات التسويق" : "Marketing preferences"}</CardTitle></div>
            <CardDescription>
              {isAr ? "منفصلة تماماً عن إشعارات الحساب الأساسية (تذكيرات، تحديثات الطلبات)." : "Fully separate from core account notifications (reminders, application updates)."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {!marketing ? <Loader2 className="h-4 w-4 animate-spin" /> : (
              <>
                <div className="flex items-center justify-between rounded-xl border border-border p-3">
                  <p className="text-body">{isAr ? "رسائل بريد تسويقية" : "Marketing emails"}</p>
                  <Switch checked={marketing.email_marketing_opt_in} disabled={savingMarketing}
                    onCheckedChange={(v) => toggleMarketing("email_marketing_opt_in", v)} />
                </div>
                <div className="flex items-center justify-between rounded-xl border border-border p-3">
                  <p className="text-body">{isAr ? "رسائل نصية تسويقية" : "Marketing SMS"}</p>
                  <Switch checked={marketing.sms_marketing_opt_in} disabled={savingMarketing}
                    onCheckedChange={(v) => toggleMarketing("sms_marketing_opt_in", v)} />
                </div>
              </>
            )}
          </CardContent>
        </Card>

        {/* DSR requests */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2"><FileText className="h-5 w-5" /><CardTitle>{isAr ? "طلبات الخصوصية" : "Privacy requests"}</CardTitle></div>
            <CardDescription>{isAr ? "قدّم طلباً وتابع حالته." : "Submit a request and track its status."}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <Label>{isAr ? "نوع الطلب" : "Request type"}</Label>
                <select
                  value={dsrType}
                  onChange={(e) => setDsrType(e.target.value)}
                  className="mt-1 h-10 w-full rounded-md border border-input bg-background px-3 text-body"
                >
                  {DSR_TYPES.map((t) => <option key={t.key} value={t.key}>{isAr ? t.ar : t.en}</option>)}
                </select>
              </div>
            </div>
            <Textarea
              placeholder={isAr ? "تفاصيل إضافية (اختياري)" : "Additional details (optional)"}
              value={dsrDetails} onChange={(e) => setDsrDetails(e.target.value)} rows={3}
            />
            <Button onClick={submitDsr} disabled={submittingDsr}>
              {submittingDsr && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isAr ? "تقديم الطلب" : "Submit request"}
            </Button>

            {requests.length > 0 && (
              <div className="space-y-2 pt-2">
                {requests.map((r) => (
                  <div key={r.uuid} className="flex items-center justify-between rounded-lg border border-border p-3 text-caption">
                    <div className="flex items-center gap-2">
                      <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                      <span className="font-medium">{r.request_type}</span>
                      <span className="text-muted-foreground">{new Date(r.created_at).toLocaleDateString()}</span>
                    </div>
                    <Badge variant={r.status === "completed" ? "success" : r.status === "rejected" ? "destructive" : "soft"}>
                      {r.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Account deletion grace period */}
        <Card className="border-destructive/50">
          <CardHeader>
            <div className="flex items-center gap-2"><Trash2 className="h-5 w-5 text-destructive" /><CardTitle className="text-destructive">{isAr ? "حذف الحساب" : "Delete account"}</CardTitle></div>
            <CardDescription>{isAr ? "فترة سماح 30 يوماً — يمكنك الإلغاء خلالها." : "30-day grace period — you can cancel at any time during it."}</CardDescription>
          </CardHeader>
          <CardContent>
            {deletionStatus?.pending ? (
              <div className="flex items-center justify-between rounded-xl border border-destructive/30 p-3">
                <p className="text-body">
                  {isAr ? "مجدول للحذف في: " : "Scheduled for: "}
                  {deletionStatus.scheduled_for && new Date(deletionStatus.scheduled_for).toLocaleDateString()}
                </p>
                <Button variant="outline" onClick={handleCancelDeletion} disabled={deletionLoading} className="gap-1.5">
                  <Ban className="h-3.5 w-3.5" /> {isAr ? "إلغاء" : "Cancel"}
                </Button>
              </div>
            ) : !confirmDeletion ? (
              <Button variant="destructive" onClick={() => setConfirmDeletion(true)}>
                {isAr ? "حذف الحساب" : "Delete account"}
              </Button>
            ) : (
              <div className="flex gap-2">
                <Button variant="destructive" onClick={handleRequestDeletion} disabled={deletionLoading}>
                  {deletionLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {isAr ? "تأكيد الحذف" : "Confirm deletion"}
                </Button>
                <Button variant="ghost" onClick={() => setConfirmDeletion(false)}>{isAr ? "إلغاء" : "Cancel"}</Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
