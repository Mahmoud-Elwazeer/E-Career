import { Bookmark, Loader2 } from "lucide-react";
import { Layout } from "@/components/Layout";
import { JobCard } from "@/components/JobCard";
import { useSavedJobs } from "@/hooks/use-saved-jobs";
import { useTheme } from "@/hooks/use-theme";

export default function SavedJobs() {
  const { savedJobs, isSaved, save, remove, loading } = useSavedJobs();
  const { lang } = useTheme();
  const isAr = lang === "ar";

  return (
    <Layout>
      <div className="container py-8 max-w-3xl">
        <h1 className="text-2xl font-medium mb-1 flex items-center gap-2">
          <Bookmark className="h-6 w-6 text-primary" />
          {isAr ? "الوظائف المحفوظة" : "Saved Jobs"}
        </h1>
        <p className="text-sm text-muted-foreground mb-6">
          {savedJobs.length} {isAr ? "وظيفة محفوظة" : `saved job${savedJobs.length !== 1 ? "s" : ""}`}
        </p>

        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
          </div>
        ) : savedJobs.length === 0 ? (
          <div className="text-center py-20 text-muted-foreground">
            <Bookmark className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p className="font-medium">{isAr ? "لا توجد وظائف محفوظة" : "No saved jobs yet"}</p>
            <p className="text-sm mt-1">{isAr ? "انقر على أيقونة الإشارة المرجعية لأي وظيفة لحفظها" : "Click the bookmark icon on any job to save it here"}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {savedJobs.map(({ job }) => (
              <JobCard
                key={job.id}
                job={job}
                isSaved={isSaved(job.id)}
                onToggleSave={(jid) => (isSaved(jid) ? remove(jid) : save(Number(jid)))}
              />
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
