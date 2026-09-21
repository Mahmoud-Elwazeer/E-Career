/**
 * Cover Letters — frontend for the previously-unused backend cover-letter API.
 * Lists the user's saved cover letters, lets them read/edit/save/delete one,
 * and points them to a job to generate a new one (generation is job-scoped on
 * the backend, so it starts from a job — surfaced via "Ask Rasheed" on Job
 * Detail and the browse-jobs CTA here). No backend changes.
 */
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  FileText, Loader2, AlertCircle, Trash2, Save, Copy, Check,
  Briefcase, PenLine, ArrowRight, ArrowLeft,
} from "lucide-react";
import { AppShell } from "@/components/shells/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { useTheme } from "@/hooks/use-theme";
import { MOTION } from "@/lib/motion-tokens";
import {
  listCoverLetters, getCoverLetter, updateCoverLetter, deleteCoverLetter,
  type CoverLetterListItem,
} from "@/services/coverLetters";

export default function CoverLetters() {
  const { lang, dir } = useTheme();
  const isAr = lang === "ar";
  const Arrow = dir === "rtl" ? ArrowLeft : ArrowRight;
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [copied, setCopied] = useState(false);

  const listQuery = useQuery({
    queryKey: ["cover-letters"],
    queryFn: listCoverLetters,
    retry: false,
  });

  const detailQuery = useQuery({
    queryKey: ["cover-letter", selectedId],
    queryFn: () => getCoverLetter(selectedId!),
    enabled: !!selectedId,
  });

  // The editor shows `draft` once the user types; until then it mirrors the
  // loaded content. Switching letters resets `draft` (see openLetter).
  const loadedContent = detailQuery.data?.content ?? "";

  const saveMutation = useMutation({
    mutationFn: (content: string) => updateCoverLetter(selectedId!, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cover-letters"] });
      queryClient.invalidateQueries({ queryKey: ["cover-letter", selectedId] });
      toast({ title: isAr ? "تم الحفظ" : "Saved", description: isAr ? "تم تحديث خطاب التغطية." : "Cover letter updated." });
    },
    onError: () =>
      toast({ title: isAr ? "خطأ" : "Error", description: isAr ? "فشل الحفظ." : "Failed to save.", variant: "destructive" }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteCoverLetter(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cover-letters"] });
      setSelectedId(null);
      setDraft("");
      toast({ title: isAr ? "تم الحذف" : "Deleted" });
    },
    onError: () =>
      toast({ title: isAr ? "خطأ" : "Error", description: isAr ? "فشل الحذف." : "Failed to delete.", variant: "destructive" }),
  });

  const openLetter = (item: CoverLetterListItem) => {
    setSelectedId(item.id);
    setDraft("");
  };

  const content = draft || loadedContent;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const letters = listQuery.data ?? [];

  return (
    <AppShell>
      <div className="page-shell">
        <PageHeader
          title={isAr ? "خطابات التغطية" : "Cover Letters"}
          subtitle={isAr ? "أنشئ وحرّر خطابات تغطية مخصصة لكل وظيفة" : "Generate and edit tailored cover letters per job"}
          actions={
            <Button asChild className="gap-2">
              <Link to="/app/jobs">
                <Briefcase className="h-4 w-4" />
                {isAr ? "خطاب لوظيفة" : "New for a job"}
              </Link>
            </Button>
          }
        />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* List */}
          <div className="lg:col-span-1 surface-card overflow-hidden">
            <div className="p-4 border-b border-border">
              <h2 className="text-heading-3">{isAr ? "خطاباتك" : "Your letters"}</h2>
            </div>
            {listQuery.isLoading ? (
              <div className="flex items-center justify-center py-12" role="status">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
              </div>
            ) : listQuery.isError ? (
              <div className="p-6 text-center">
                <AlertCircle className="h-8 w-8 text-destructive mx-auto mb-2" />
                <p className="text-body text-muted-foreground mb-3">
                  {isAr ? "تعذّر التحميل." : "Couldn't load letters."}
                </p>
                <Button variant="outline" size="sm" onClick={() => listQuery.refetch()}>
                  {isAr ? "إعادة المحاولة" : "Retry"}
                </Button>
              </div>
            ) : letters.length === 0 ? (
              <div className="p-6 text-center">
                <PenLine className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-body text-muted-foreground mb-1">
                  {isAr ? "لا توجد خطابات بعد." : "No cover letters yet."}
                </p>
                <p className="text-caption text-muted-foreground mb-4">
                  {isAr
                    ? "افتح أي وظيفة واطلب من رشيد كتابة خطاب تغطية."
                    : "Open any job and ask Rasheed to write a cover letter."}
                </p>
                <Button asChild variant="outline" size="sm" className="gap-1">
                  <Link to="/app/jobs">
                    {isAr ? "تصفح الوظائف" : "Browse jobs"}
                    <Arrow className="h-3.5 w-3.5" />
                  </Link>
                </Button>
              </div>
            ) : (
              <ul className="divide-y divide-border max-h-[70vh] overflow-y-auto">
                {letters.map((l) => (
                  <li key={l.id}>
                    <button
                      onClick={() => openLetter(l)}
                      className={`w-full text-start p-4 transition-colors hover:bg-accent/40 ${
                        selectedId === l.id ? "bg-accent/60" : ""
                      }`}
                    >
                      <p className="text-body font-medium text-foreground truncate">{l.job_title}</p>
                      <p className="text-caption text-muted-foreground truncate">{l.company}</p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <span className="pill-tag text-[10px] py-0.5">{l.tone}</span>
                        {l.is_edited && (
                          <Badge variant="outline" className="text-[10px]">
                            {isAr ? "معدّل" : "Edited"}
                          </Badge>
                        )}
                        <span className="text-caption text-muted-foreground font-mono-data">
                          {l.word_count}w
                        </span>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Editor */}
          <motion.div {...MOTION.presets.fadeUp} className="lg:col-span-2 surface-card overflow-hidden">
            {!selectedId ? (
              <div className="flex flex-col items-center justify-center text-center h-full min-h-[400px] p-8">
                <FileText className="h-12 w-12 text-muted-foreground mb-3" />
                <p className="text-body-lg font-medium text-foreground mb-1">
                  {isAr ? "اختر خطاباً لعرضه" : "Select a letter to view"}
                </p>
                <p className="text-body text-muted-foreground max-w-sm">
                  {isAr
                    ? "أو افتح وظيفة واطلب من رشيد إنشاء خطاب تغطية مخصص لها."
                    : "Or open a job and have Rasheed generate a tailored cover letter for it."}
                </p>
              </div>
            ) : detailQuery.isLoading ? (
              <div className="flex items-center justify-center min-h-[400px]" role="status">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
              </div>
            ) : detailQuery.isError ? (
              <div className="flex flex-col items-center justify-center min-h-[400px] text-center p-8">
                <AlertCircle className="h-10 w-10 text-destructive mb-3" />
                <p className="text-body text-muted-foreground mb-3">
                  {isAr ? "تعذّر تحميل الخطاب." : "Couldn't load this letter."}
                </p>
                <Button variant="outline" size="sm" onClick={() => detailQuery.refetch()}>
                  {isAr ? "إعادة المحاولة" : "Retry"}
                </Button>
              </div>
            ) : (
              <div className="flex flex-col h-full">
                <div className="flex items-center justify-between gap-3 p-4 border-b border-border">
                  <div className="min-w-0">
                    <p className="text-body font-medium text-foreground truncate">
                      {detailQuery.data?.job_title}
                    </p>
                    <p className="text-caption text-muted-foreground truncate">
                      {detailQuery.data?.company}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Button variant="outline" size="sm" className="gap-1.5" onClick={handleCopy}>
                      {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
                      {isAr ? "نسخ" : "Copy"}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5 text-destructive hover:text-destructive"
                      onClick={() => {
                        if (confirm(isAr ? "حذف هذا الخطاب؟" : "Delete this cover letter?")) {
                          deleteMutation.mutate(selectedId);
                        }
                      }}
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>

                <div className="p-4 flex-1">
                  <Textarea
                    value={content}
                    onChange={(e) => setDraft(e.target.value)}
                    className="min-h-[420px] resize-y leading-relaxed"
                    dir={isAr ? "rtl" : "ltr"}
                  />
                </div>

                <div className="flex items-center justify-between gap-3 p-4 border-t border-border">
                  <span className="text-caption text-muted-foreground font-mono-data">
                    {content.trim() ? content.trim().split(/\s+/).length : 0} {isAr ? "كلمة" : "words"}
                  </span>
                  <Button
                    className="gap-1.5"
                    onClick={() => saveMutation.mutate(content)}
                    disabled={saveMutation.isPending || !draft || draft === loadedContent}
                  >
                    {saveMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Save className="h-4 w-4" />
                    )}
                    {isAr ? "حفظ التغييرات" : "Save changes"}
                  </Button>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </AppShell>
  );
}
