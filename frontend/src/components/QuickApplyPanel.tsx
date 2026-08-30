import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Zap, Loader2, ExternalLink, CheckCircle, Copy, Check } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { prepareQuickApply, recordQuickApply } from "@/services/phase5";
import type { QuickApplyData } from "@/services/phase5";

interface QuickApplyPanelProps {
  jobId: string;
  jobTitle: string;
  atsPlatform?: string;
  applyUrl?: string;
  isAr?: boolean;
}

export function QuickApplyPanel({ jobId, jobTitle, atsPlatform, applyUrl, isAr }: QuickApplyPanelProps) {
  const [showReview, setShowReview] = useState(false);
  const [data, setData] = useState<QuickApplyData | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  const prepareMutation = useMutation({
    mutationFn: () => prepareQuickApply(jobId),
    onSuccess: (result) => {
      setData(result);
      setShowReview(true);
    },
  });

  const recordMutation = useMutation({
    mutationFn: () => recordQuickApply(jobId),
  });

  if (!atsPlatform) return null;

  const handleApplyClick = () => {
    if (data?.apply_url) {
      recordMutation.mutate();
      window.open(data.apply_url, "_blank", "noopener,noreferrer");
    }
    setShowReview(false);
  };

  const copyField = (field: string, value: string) => {
    navigator.clipboard.writeText(value);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const fields = data?.prepared_data
    ? Object.entries(data.prepared_data).filter(([, v]) => v)
    : [];

  return (
    <>
      <Card className="border-orange-200 dark:border-orange-800 bg-orange-50/50 dark:bg-orange-950/50">
        <CardContent className="p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-10 w-10 rounded-full bg-orange-100 dark:bg-orange-900 flex items-center justify-center">
              <Zap className="h-5 w-5 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
              <h3 className="text-body font-semibold text-orange-800 dark:text-orange-200">
                {isAr ? "تقديم سريع" : "Quick Apply"}
              </h3>
              <p className="text-caption text-orange-600 dark:text-orange-400">
                {isAr ? "عبر" : "via"} {atsPlatform}
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            className="w-full rounded-xl press-feedback border-orange-300 dark:border-orange-700"
            onClick={() => prepareMutation.mutate()}
            disabled={prepareMutation.isPending}
          >
            {prepareMutation.isPending ? (
              <Loader2 className="h-4 w-4 me-2 animate-spin" />
            ) : (
              <Zap className="h-4 w-4 me-2" />
            )}
            {isAr ? "جهّز بياناتي" : "Prepare My Application"}
          </Button>
          {prepareMutation.isError && (
            <p className="text-caption text-destructive mt-2">
              {isAr ? "فشل التحضير" : "Preparation failed. Please try again."}
            </p>
          )}
        </CardContent>
      </Card>

      <Dialog open={showReview} onOpenChange={setShowReview}>
        <DialogContent className="max-w-md max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {isAr ? "مراجعة طلبك" : "Review Your Application"}
            </DialogTitle>
            <DialogDescription>
              {isAr
                ? `تحقق من بياناتك قبل التقديم لـ ${jobTitle}`
                : `Verify your information before applying to ${jobTitle}`}
            </DialogDescription>
          </DialogHeader>

          {data && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="rounded-lg">
                  {data.ats_provider}
                </Badge>
                {!data.can_auto_submit && (
                  <span className="text-caption text-muted-foreground">
                    {isAr ? "تقديم يدوي" : "Manual submit required"}
                  </span>
                )}
              </div>

              <div className="space-y-2 bg-muted/50 rounded-xl p-3">
                {fields.map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="text-caption text-muted-foreground capitalize">
                        {key.replace(/_/g, " ")}
                      </p>
                      <p className="text-caption font-medium truncate">{String(value)}</p>
                    </div>
                    <button
                      onClick={() => copyField(key, String(value))}
                      className="shrink-0 p-1.5 rounded-lg hover:bg-muted transition-colors"
                    >
                      {copiedField === key ? (
                        <Check className="h-3.5 w-3.5 text-emerald-500" />
                      ) : (
                        <Copy className="h-3.5 w-3.5 text-muted-foreground" />
                      )}
                    </button>
                  </div>
                ))}
              </div>

              {data.provider_info?.note && (
                <p className="text-caption text-muted-foreground italic">
                  {data.provider_info.note}
                </p>
              )}
            </div>
          )}

          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowReview(false)} className="rounded-xl">
              {isAr ? "إلغاء" : "Cancel"}
            </Button>
            <Button onClick={handleApplyClick} className="rounded-xl gap-2">
              <ExternalLink className="h-4 w-4" />
              {isAr ? "التقديم الآن" : "Apply Now"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
