import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, useLocation, useParams } from "react-router-dom";
import { RouteTransition } from "@/components/motion/RouteTransition";
import { ThemeProvider } from "@/hooks/use-theme";
import { AuthProvider } from "@/hooks/use-auth";
import { RasheedProvider } from "@/components/rashid/rasheed-state";
import { apiRequest } from "@/services/client";
import { RequireAuth } from "@/components/RequireAuth";
import { RequireAdmin, RequireEmployer } from "@/components/RequireRole";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Loader2 } from "lucide-react";

// First-paint critical routes stay eager.
import Index from "./pages/Index";
import Login from "./pages/Login";
import Jobs from "./pages/Jobs";
import JobDetail from "./pages/JobDetail";
import NotFound from "./pages/NotFound";

// Everything else is code-split so the initial bundle stays small.
import { lazy, Suspense, useState, useEffect } from "react";
const CompanyProfile = lazy(() => import("./pages/CompanyProfile"));
const ProfilePage = lazy(() => import("./pages/ProfilePage"));
const SavedJobs = lazy(() => import("./pages/SavedJobs"));
const TalentScore = lazy(() => import("./pages/TalentScore"));
const AdminDashboard = lazy(() => import("./pages/AdminDashboard"));
const About = lazy(() => import("./pages/About"));
const ResetPassword = lazy(() => import("./pages/ResetPassword"));
const Alerts = lazy(() => import("./pages/Alerts"));
const ApiDocs = lazy(() => import("./pages/ApiDocs"));
const Recommendations = lazy(() => import("./pages/Recommendations"));
const RashidChat = lazy(() => import("./pages/RashidChat"));
const InterviewPractice = lazy(() => import("./pages/InterviewPractice"));
const ResumeBuilder = lazy(() => import("./pages/ResumeBuilder"));
const NotificationPreferences = lazy(() => import("./pages/NotificationPreferences"));
const Notifications = lazy(() => import("./pages/Notifications"));
const Settings = lazy(() => import("./pages/Settings"));
const Applications = lazy(() => import("./pages/Applications"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const CoverLetters = lazy(() => import("./pages/CoverLetters"));
const IntelligenceDashboard = lazy(() => import("./pages/IntelligenceDashboard"));
const EmployerDashboard = lazy(() => import("./pages/employer/EmployerDashboard"));
const EmployerRegister = lazy(() => import("./pages/employer/EmployerRegister"));
const JobPostingForm = lazy(() => import("./pages/employer/JobPostingForm"));
const TalentSearch = lazy(() => import("./pages/employer/TalentSearch"));
const CodingPractice = lazy(() => import("./pages/CodingPractice"));
const SalaryInsights = lazy(() => import("./pages/SalaryInsights"));
const Assessments = lazy(() => import("./pages/Assessments"));
const Pricing = lazy(() => import("./pages/Pricing"));
const Companies = lazy(() => import("./pages/Companies"));
const CareerGraph = lazy(() => import("./pages/CareerGraph"));
const SkillsExplorer = lazy(() => import("./pages/SkillsExplorer"));
const ForIndividuals = lazy(() => import("./pages/AudiencePage"));
const ForBusinesses = lazy(() => import("./pages/AudiencePage").then((m) => ({ default: m.ForBusinessesPage })));
// Dev/QA-only: Rasheed 3D asset validation overlay (?rasheedCheck=1).
const RasheedGlbCheck = lazy(() =>
  import("@/components/rashid/RasheedGlbCheck").then((m) => ({ default: m.RasheedGlbCheck })),
);

import { RasheedCompanion } from "./components/rashid/RasheedCompanion";
import { OnboardingTour } from "./components/OnboardingTour";
import { OnboardingFlow } from "./components/landing/OnboardingFlow";
import { useI18nSync } from "@/hooks/use-i18n";
import { useAuth } from "@/hooks/use-auth";

const queryClient = new QueryClient();

function RouteFallback() {
  return (
    <div className="flex items-center justify-center py-32" role="status" aria-live="polite">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
      <span className="sr-only">Loading…</span>
    </div>
  );
}

/** Wraps JobPostingForm for the edit route, passing the numeric job id from the URL. */
function EditJobPosting() {
  const { id } = useParams<{ id: string }>();
  const jobId = id ? Number(id) : undefined;
  return <JobPostingForm jobId={Number.isFinite(jobId) ? jobId : undefined} />;
}

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <RouteTransition>
      <Suspense fallback={<RouteFallback />}>
      <Routes location={location}>
        {/* Public routes */}
        <Route path="/" element={<Index />} />
        <Route path="/for-individuals" element={<ForIndividuals />} />
        <Route path="/for-businesses" element={<ForBusinesses />} />
        <Route path="/about" element={<About />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        {/* Auth-protected app routes */}
        <Route path="/app/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
        <Route path="/app/cover-letters" element={<RequireAuth><CoverLetters /></RequireAuth>} />
        <Route path="/app/jobs" element={<RequireAuth><Jobs /></RequireAuth>} />
        <Route path="/app/jobs/:id" element={<RequireAuth><JobDetail /></RequireAuth>} />
        <Route path="/app/companies" element={<RequireAuth><Companies /></RequireAuth>} />
        <Route path="/app/companies/:id" element={<RequireAuth><CompanyProfile /></RequireAuth>} />
        <Route path="/app/career-graph" element={<RequireAuth><CareerGraph /></RequireAuth>} />
        <Route path="/app/skills" element={<RequireAuth><SkillsExplorer /></RequireAuth>} />
        <Route path="/app/profile" element={<RequireAuth><ProfilePage /></RequireAuth>} />
        <Route path="/app/career" element={<RequireAuth><TalentScore /></RequireAuth>} />
        <Route path="/app/talent-score" element={<RequireAuth><TalentScore /></RequireAuth>} />
        <Route path="/app/saved" element={<RequireAuth><SavedJobs /></RequireAuth>} />
        <Route path="/app/alerts" element={<RequireAuth><Alerts /></RequireAuth>} />
        <Route path="/app/recommendations" element={<RequireAuth><Recommendations /></RequireAuth>} />
        <Route path="/app/rashid" element={<RequireAuth><RashidChat /></RequireAuth>} />
        <Route path="/app/interviews" element={<RequireAuth><InterviewPractice /></RequireAuth>} />
        <Route path="/app/resume" element={<RequireAuth><ResumeBuilder /></RequireAuth>} />
        <Route path="/app/notification-preferences" element={<RequireAuth><NotificationPreferences /></RequireAuth>} />
        <Route path="/app/notifications" element={<RequireAuth><Notifications /></RequireAuth>} />
        <Route path="/app/settings" element={<RequireAuth><Settings /></RequireAuth>} />
        <Route path="/app/applications" element={<RequireAuth><Applications /></RequireAuth>} />
        <Route path="/admin" element={<RequireAdmin><AdminDashboard /></RequireAdmin>} />
        <Route path="/admin/intelligence" element={<RequireAdmin><IntelligenceDashboard /></RequireAdmin>} />
        <Route path="/api-docs" element={<ApiDocs />} />
        
        {/* Employer routes */}
        <Route path="/app/employer/dashboard" element={<RequireEmployer><EmployerDashboard /></RequireEmployer>} />
        <Route path="/app/employer/register" element={<RequireAuth><EmployerRegister /></RequireAuth>} />
        <Route path="/app/coding-practice" element={<RequireAuth><CodingPractice /></RequireAuth>} />
        <Route path="/app/salary" element={<RequireAuth><SalaryInsights /></RequireAuth>} />
        <Route path="/app/assessments" element={<RequireAuth><Assessments /></RequireAuth>} />
        <Route path="/app/employer/post-job" element={<RequireEmployer><JobPostingForm /></RequireEmployer>} />
        <Route path="/app/employer/jobs/:id/edit" element={<RequireEmployer><EditJobPosting /></RequireEmployer>} />
        <Route path="/app/employer/talent-search" element={<RequireEmployer><TalentSearch /></RequireEmployer>} />

        {/* Legacy redirects */}
        <Route path="/jobs" element={<RequireAuth><Jobs /></RequireAuth>} />
        <Route path="/jobs/:id" element={<RequireAuth><JobDetail /></RequireAuth>} />
        <Route path="/companies/:id" element={<RequireAuth><CompanyProfile /></RequireAuth>} />
        <Route path="/profile" element={<RequireAuth><ProfilePage /></RequireAuth>} />
        <Route path="/saved" element={<RequireAuth><SavedJobs /></RequireAuth>} />
        <Route path="/alerts" element={<RequireAuth><Alerts /></RequireAuth>} />

        <Route path="*" element={<NotFound />} />
      </Routes>
      </Suspense>
    </RouteTransition>
  );
}

function OnboardingWrapper() {
  const { user } = useAuth();
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    // Show onboarding for new authenticated users
    if (user) {
      const hasCompletedOnboarding = localStorage.getItem("usam_onboarding_complete");
      if (!hasCompletedOnboarding) {
        setShowOnboarding(true);
      }
    }
  }, [user]);

  const handleOnboardingComplete = async (preferences: { track: string; mode: string; location: string }) => {
    // Persist the job-search preferences the flow actually collects (track/mode/
    // location) so they can drive the initial jobs query. We mark the backend
    // "preferences" onboarding step complete with a VALID step_id — we do NOT
    // jam these into career_stage/primary_interest (different enums/concepts).
    try {
      localStorage.setItem("usam_job_prefs", JSON.stringify(preferences));
      await apiRequest("/career/onboarding/", {
        method: "PATCH",
        body: { step_id: "preferences" },
      });
    } catch {
      // Non-fatal: onboarding UX shouldn't block the user if the step write fails.
    } finally {
      localStorage.setItem("usam_onboarding_complete", "true");
      setShowOnboarding(false);
      // Kick off the guided section tour right after preferences.
      localStorage.removeItem("usam_tour_done");
      window.dispatchEvent(new CustomEvent("usam:start-tour"));
    }
  };

  if (!showOnboarding) return null;
  return <OnboardingFlow onComplete={handleOnboardingComplete} />;
}

function AppContent() {
  useI18nSync();

  const showRasheedCheck =
    typeof window !== "undefined" && new URLSearchParams(window.location.search).has("rasheedCheck");

  return (
    <AuthProvider>
      <RasheedProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <AnimatedRoutes />
            <RasheedCompanion />
            <OnboardingWrapper />
            <OnboardingTour />
          </BrowserRouter>
          {showRasheedCheck && (
            <Suspense fallback={null}>
              <RasheedGlbCheck />
            </Suspense>
          )}
        </TooltipProvider>
      </RasheedProvider>
    </AuthProvider>
  );
}

const App = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <AppContent />
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
