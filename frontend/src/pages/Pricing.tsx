import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Check, Sparkles, Briefcase, Users, Loader2, AlertTriangle, RotateCcw } from "lucide-react";
import { Layout } from "@/components/Layout";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useTheme } from "@/hooks/use-theme";
import { usePageMeta } from "@/hooks/use-seo";
import { getPublicPlans, type Plan } from "@/services/pricing";

function limitLabel(v: number, isAr: boolean, unit: string, unitAr: string): string {
  if (!v || v <= 0) return isAr ? "غير محدود" : "Unlimited";
  return `${v} ${isAr ? unitAr : unit}`;
}

function PlanCard({ plan, isAr }: { plan: Plan; isAr: boolean }) {
  const features: string[] = [
    limitLabel(plan.job_posting_limit, isAr, "job postings", "إعلان وظيفة"),
    limitLabel(plan.candidate_search_limit, isAr, "candidate searches / mo", "بحث مرشحين شهريًا"),
    plan.ai_features_enabled
      ? (isAr ? "أدوات الذكاء الاصطناعي مفعّلة" : "AI features included")
      : (isAr ? "بدون أدوات الذكاء الاصطناعي" : "No AI features"),
  ];

  return (
    <Card className="surface-card-interactive flex flex-col">
      <CardHeader>
        <CardTitle className="text-heading-3">{plan.name}</CardTitle>
        {plan.description && <p className="text-body text-muted-foreground mt-1">{plan.description}</p>}
      </CardHeader>
      <CardContent className="flex flex-1 flex-col">
        <ul className="space-y-2 mb-6">
          {features.map((f, i) => (
            <li key={i} className="flex items-start gap-2 text-body">
              <Check className="h-4 w-4 text-success mt-0.5 shrink-0" />
              <span>{f}</span>
            </li>
          ))}
          {plan.ai_features_enabled && (
            <li className="flex items-start gap-2">
              <Badge variant="soft" className="gap-1"><Sparkles className="h-3 w-3" /> AI</Badge>
            </li>
          )}
        </ul>
        <Button asChild className="mt-auto w-full">
          {/* No public payment provider yet — route to employer registration / contact. */}
          <Link to="/app/employer/register">{isAr ? "ابدأ الآن" : "Get started"}</Link>
        </Button>
      </CardContent>
    </Card>
  );
}

export default function Pricing() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  usePageMeta(
    isAr ? "الأسعار والباقات" : "Pricing & Plans",
    isAr ? "باقات التوظيف على منصة USAM" : "USAM hiring plans and packages",
  );

  const { data: plans, isLoading, isError, refetch } = useQuery({
    queryKey: ["public-plans"],
    queryFn: getPublicPlans,
  });

  return (
    <Layout>
      <div className="container py-12">
        <PageHeader
          title={isAr ? "باقات التوظيف" : "Hiring Plans"}
          subtitle={
            isAr
              ? "اختر الباقة المناسبة لاحتياجات شركتك. كل الباقات قابلة للتخصيص من فريقنا."
              : "Choose the plan that fits your hiring needs. All plans are configurable by our team."
          }
        />

        {isLoading && (
          <div className="flex items-center justify-center py-24" role="status" aria-live="polite">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <span className="sr-only">{isAr ? "جاري التحميل" : "Loading"}</span>
          </div>
        )}

        {isError && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="rounded-full bg-destructive/10 p-3 mb-4">
              <AlertTriangle className="h-6 w-6 text-destructive" />
            </div>
            <h2 className="text-heading-3 mb-1">{isAr ? "تعذّر تحميل الباقات" : "Couldn't load plans"}</h2>
            <Button onClick={() => refetch()} className="gap-2 mt-2">
              <RotateCcw className="h-4 w-4" /> {isAr ? "إعادة المحاولة" : "Try again"}
            </Button>
          </div>
        )}

        {!isLoading && !isError && plans && plans.length === 0 && (
          <div className="surface-card p-12 text-center max-w-lg mx-auto">
            <Briefcase className="h-10 w-10 text-muted-foreground mx-auto mb-4" />
            <h2 className="text-heading-3 mb-2">{isAr ? "الباقات قيد الإعداد" : "Plans coming into place"}</h2>
            <p className="text-body text-muted-foreground mb-4">
              {isAr
                ? "تواصل مع فريقنا لإعداد باقة مخصصة لشركتك."
                : "Talk to our team to set up a plan tailored to your company."}
            </p>
            <Button asChild><Link to="/app/employer/register">{isAr ? "تواصل معنا" : "Contact us"}</Link></Button>
          </div>
        )}

        {!isLoading && !isError && plans && plans.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
            {plans.map((p) => (
              <PlanCard key={p.uuid} plan={p} isAr={isAr} />
            ))}
          </div>
        )}

        {/* Candidate note */}
        <div className="surface-card mt-10 p-6 flex items-start gap-4 max-w-3xl mx-auto">
          <div className="rounded-lg bg-primary-muted p-2.5">
            <Users className="h-5 w-5 text-primary" />
          </div>
          <div>
            <p className="text-body font-medium">{isAr ? "للباحثين عن عمل" : "For job seekers"}</p>
            <p className="text-body text-muted-foreground">
              {isAr
                ? "البحث عن الوظائف والتقديم المباشر ومساعد رشيد المهني — مجانًا."
                : "Job search, direct apply, and the Rasheed career assistant are free."}
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
