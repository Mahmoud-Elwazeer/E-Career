/**
 * Company Settings — the employer's own company profile (jobs.Company).
 *
 * Reads/edits the real company record via /employer/profile/company/.
 * Write access is enforced server-side (owner/admin only); a 403 is surfaced
 * as a read-only notice rather than a crash. No frontend-only permissions —
 * the button is a convenience, the backend is authoritative.
 */
import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Building2, Loader2, AlertCircle, RotateCcw, Save, ShieldCheck, Clock } from "lucide-react";
import {
  getManagedCompany, updateManagedCompany,
  type ManagedCompany, type ManagedCompanyUpdate, type OrgType,
} from "@/services/employer";
import { AppShell } from "@/components/shells/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { useTheme } from "@/hooks/use-theme";

const EDITABLE_TEXT: Array<{ key: keyof ManagedCompanyUpdate; en: string; ar: string; textarea?: boolean }> = [
  { key: "name", en: "Company name", ar: "اسم الشركة" },
  { key: "website", en: "Website", ar: "الموقع الإلكتروني" },
  { key: "domain", en: "Domain (e.g. acme.com)", ar: "النطاق" },
  { key: "headquarters", en: "Headquarters", ar: "المقر الرئيسي" },
  { key: "size", en: "Company size (e.g. 11-50)", ar: "حجم الشركة" },
  { key: "logo_url", en: "Logo URL", ar: "رابط الشعار" },
  { key: "linkedin_url", en: "LinkedIn URL", ar: "رابط لينكدإن" },
  { key: "careers_page_url", en: "Careers page URL", ar: "رابط صفحة الوظائف" },
  { key: "github_org", en: "GitHub org handle", ar: "معرّف منظمة جيت هب" },
  { key: "snippet", en: "Short description", ar: "وصف مختصر" },
  { key: "about", en: "About the company", ar: "عن الشركة", textarea: true },
];

export default function CompanySettings() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["managed-company"],
    queryFn: getManagedCompany,
    retry: false,
  });

  const [form, setForm] = useState<ManagedCompanyUpdate>({});

  // Seed the form once the company loads.
  useEffect(() => {
    if (data) {
      setForm({
        name: data.name, org_type: data.org_type, website: data.website, domain: data.domain,
        headquarters: data.headquarters, size: data.size, logo_url: data.logo_url,
        linkedin_url: data.linkedin_url, careers_page_url: data.careers_page_url,
        github_org: data.github_org, snippet: data.snippet, about: data.about,
        industry: data.industry,
      });
    }
  }, [data]);

  const ORG_TYPES: Array<{ value: OrgType; en: string; ar: string }> = [
    { value: "business", en: "Business", ar: "شركة" },
    { value: "government", en: "Government", ar: "جهة حكومية" },
    { value: "university", en: "University", ar: "جامعة" },
    { value: "ngo", en: "NGO / Non-profit", ar: "منظمة غير ربحية" },
  ];

  const save = useMutation({
    mutationFn: (payload: ManagedCompanyUpdate) => updateManagedCompany(payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(["managed-company"], updated);
      queryClient.invalidateQueries({ queryKey: ["employer-profile"] });
      toast({ title: isAr ? "تم حفظ ملف الشركة" : "Company profile saved" });
    },
    onError: (e: { status?: number; message?: string }) => {
      if (e?.status === 403) {
        toast({
          title: isAr ? "صلاحيات غير كافية" : "Not allowed",
          description: isAr
            ? "فقط مالك الشركة أو المسؤول يمكنه التعديل."
            : "Only a company owner or admin can edit the company profile.",
          variant: "destructive",
        });
      } else {
        toast({ title: isAr ? "تعذّر الحفظ" : "Could not save", variant: "destructive" });
      }
    },
  });

  // No employer company at all -> send to onboarding.
  if (isError && (error as { status?: number } | null)?.status === 404) {
    return <Navigate to="/app/employer/register" replace />;
  }

  if (isLoading) {
    return (
      <AppShell>
        <div className="page-shell flex items-center justify-center py-24" role="status" aria-live="polite">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="sr-only">{isAr ? "جاري التحميل" : "Loading"}</span>
        </div>
      </AppShell>
    );
  }

  if (isError) {
    return (
      <AppShell>
        <div className="page-shell flex flex-col items-center justify-center py-24 text-center">
          <div className="rounded-full bg-destructive/10 p-3 mb-4">
            <AlertCircle className="h-6 w-6 text-destructive" />
          </div>
          <h2 className="text-heading-2 mb-1">{isAr ? "تعذّر التحميل" : "Couldn't load company"}</h2>
          <Button onClick={() => refetch()} className="gap-2 mt-2">
            <RotateCcw className="h-4 w-4" />
            {isAr ? "إعادة المحاولة" : "Try again"}
          </Button>
        </div>
      </AppShell>
    );
  }

  const company = data as ManagedCompany;

  return (
    <AppShell>
      <div className="page-shell max-w-3xl">
        <PageHeader
          title={isAr ? "ملف الشركة" : "Company Profile"}
          subtitle={company.name}
          actions={
            company.is_verified ? (
              <Badge variant="outline" className="gap-1 bg-success/15 text-success border-success/30">
                <ShieldCheck className="h-3.5 w-3.5" /> {isAr ? "موثّقة" : "Verified"}
              </Badge>
            ) : (
              <Badge variant="outline" className="gap-1 bg-warning/15 text-warning-foreground border-warning/30">
                <Clock className="h-3.5 w-3.5" /> {isAr ? "قيد التحقق" : "Unverified"}
              </Badge>
            )
          }
        />

        <form
          onSubmit={(e) => {
            e.preventDefault();
            save.mutate(form);
          }}
          className="surface-card p-6 space-y-5"
        >
          <div className="flex items-center gap-3 pb-2">
            {company.logo_url ? (
              <img src={company.logo_url} alt={company.name} className="h-12 w-12 rounded-lg object-cover border" />
            ) : (
              <div className="h-12 w-12 rounded-lg bg-muted flex items-center justify-center">
                <Building2 className="h-6 w-6 text-muted-foreground" />
              </div>
            )}
            <p className="text-caption text-muted-foreground">
              {isAr
                ? "هذه البيانات تظهر للمرشحين على صفحة شركتك العامة."
                : "This information is shown to candidates on your public company page."}
            </p>
          </div>

          <div>
            <label htmlFor="org_type" className="block text-caption font-medium text-foreground mb-1">
              {isAr ? "نوع المؤسسة" : "Organization type"}
            </label>
            <select
              id="org_type"
              value={(form.org_type as OrgType) ?? "business"}
              onChange={(e) => setForm((f) => ({ ...f, org_type: e.target.value as OrgType }))}
              className="w-full sm:w-1/2 px-3 py-2 border border-input rounded-lg focus:ring-2 focus:ring-ring text-body bg-background"
            >
              {ORG_TYPES.map((o) => (
                <option key={o.value} value={o.value}>{isAr ? o.ar : o.en}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {EDITABLE_TEXT.map(({ key, en, ar, textarea }) => (
              <div key={key} className={textarea ? "sm:col-span-2" : ""}>
                <label htmlFor={key} className="block text-caption font-medium text-foreground mb-1">
                  {isAr ? ar : en}
                </label>
                {textarea ? (
                  <textarea
                    id={key}
                    rows={4}
                    value={(form[key] as string) ?? ""}
                    onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                    className="w-full px-3 py-2 border border-input rounded-lg focus:ring-2 focus:ring-ring text-body"
                  />
                ) : (
                  <input
                    id={key}
                    type="text"
                    value={(form[key] as string) ?? ""}
                    onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                    className="w-full px-3 py-2 border border-input rounded-lg focus:ring-2 focus:ring-ring text-body"
                  />
                )}
              </div>
            ))}
          </div>

          <div className="flex items-center gap-3 pt-2">
            <Button type="submit" className="gap-2" disabled={save.isPending}>
              {save.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              {isAr ? "حفظ التغييرات" : "Save changes"}
            </Button>
            <p className="text-caption text-muted-foreground">
              {isAr
                ? "التحقق وحالة التفعيل يديرهما المسؤول."
                : "Verification and activation are managed by an admin."}
            </p>
          </div>
        </form>
      </div>
    </AppShell>
  );
}
