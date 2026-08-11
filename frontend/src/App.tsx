import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import { ThemeProvider } from "@/hooks/use-theme";
import { AuthProvider } from "@/hooks/use-auth";
import { RequireAuth } from "@/components/RequireAuth";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import Index from "./pages/Index";
import Login from "./pages/Login";
import Jobs from "./pages/Jobs";
import JobDetail from "./pages/JobDetail";
import CompanyProfile from "./pages/CompanyProfile";
import Profile from "./pages/Profile";
import AdminDashboard from "./pages/AdminDashboard";
import About from "./pages/About";
import NotFound from "./pages/NotFound";
import ResetPassword from "./pages/ResetPassword";
import Alerts from "./pages/Alerts";
import ApiDocs from "./pages/ApiDocs";
import Recommendations from "./pages/Recommendations";
import RashidChat from "./pages/RashidChat";
import InterviewPractice from "./pages/InterviewPractice";
import ResumeBuilder from "./pages/ResumeBuilder";
import NotificationPreferences from "./pages/NotificationPreferences";
import Applications from "./pages/Applications";
import { EmployerDashboard, EmployerRegister, JobPostingForm } from "./pages/employer";
import { RashidWidget } from "./components/rashid/RashidWidget";
import { RashidOnboarding } from "./components/rashid/RashidOnboarding";
import { OnboardingFlow } from "./components/landing/OnboardingFlow";
import { useI18nSync } from "@/hooks/use-i18n";
import { useAuth } from "@/hooks/use-auth";
import { useState, useEffect } from "react";

const queryClient = new QueryClient();

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait" initial={false}>
      <Routes location={location} key={location.pathname}>
        {/* Public routes */}
        <Route path="/" element={<Index />} />
        <Route path="/about" element={<About />} />
        <Route path="/login" element={<Login />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        {/* Auth-protected app routes */}
        <Route path="/app/jobs" element={<RequireAuth><Jobs /></RequireAuth>} />
        <Route path="/app/jobs/:id" element={<RequireAuth><JobDetail /></RequireAuth>} />
        <Route path="/app/companies/:id" element={<RequireAuth><CompanyProfile /></RequireAuth>} />
        <Route path="/app/profile" element={<RequireAuth><Profile /></RequireAuth>} />
        <Route path="/app/saved" element={<RequireAuth><Profile /></RequireAuth>} />
        <Route path="/app/alerts" element={<RequireAuth><Alerts /></RequireAuth>} />
        <Route path="/app/recommendations" element={<RequireAuth><Recommendations /></RequireAuth>} />
        <Route path="/app/rashid" element={<RequireAuth><RashidChat /></RequireAuth>} />
        <Route path="/app/interviews" element={<RequireAuth><InterviewPractice /></RequireAuth>} />
        <Route path="/app/resume" element={<RequireAuth><ResumeBuilder /></RequireAuth>} />
        <Route path="/app/notifications" element={<RequireAuth><NotificationPreferences /></RequireAuth>} />
        <Route path="/app/applications" element={<RequireAuth><Applications /></RequireAuth>} />
        <Route path="/admin" element={<RequireAuth><AdminDashboard /></RequireAuth>} />
        <Route path="/api-docs" element={<ApiDocs />} />
        
        {/* Employer routes */}
        <Route path="/app/employer/dashboard" element={<RequireAuth><EmployerDashboard /></RequireAuth>} />
        <Route path="/app/employer/register" element={<RequireAuth><EmployerRegister /></RequireAuth>} />
        <Route path="/app/employer/post-job" element={<RequireAuth><JobPostingForm /></RequireAuth>} />

        {/* Legacy redirects */}
        <Route path="/jobs" element={<RequireAuth><Jobs /></RequireAuth>} />
        <Route path="/jobs/:id" element={<RequireAuth><JobDetail /></RequireAuth>} />
        <Route path="/companies/:id" element={<RequireAuth><CompanyProfile /></RequireAuth>} />
        <Route path="/profile" element={<RequireAuth><Profile /></RequireAuth>} />
        <Route path="/saved" element={<RequireAuth><Profile /></RequireAuth>} />
        <Route path="/alerts" element={<RequireAuth><Profile /></RequireAuth>} />

        <Route path="*" element={<NotFound />} />
      </Routes>
    </AnimatePresence>
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

  const handleOnboardingComplete = (preferences: { track: string; mode: string; location: string }) => {
    console.log("User preferences:", preferences);
    // TODO: Send preferences to backend API
    setShowOnboarding(false);
  };

  if (!showOnboarding) return null;
  return <OnboardingFlow onComplete={handleOnboardingComplete} />;
}

function AppContent() {
  useI18nSync();

  return (
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <AnimatedRoutes />
          <RashidWidget />
          <RashidOnboarding />
          <OnboardingWrapper />
        </BrowserRouter>
      </TooltipProvider>
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
