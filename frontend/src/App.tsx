import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import { ThemeProvider } from "@/hooks/use-theme";
import { AuthProvider } from "@/hooks/use-auth";
import { RequireAuth } from "@/components/RequireAuth";
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
        <Route path="/admin" element={<RequireAuth><AdminDashboard /></RequireAuth>} />
        <Route path="/api-docs" element={<ApiDocs />} />

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

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider>
      <AuthProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <AnimatedRoutes />
          </BrowserRouter>
        </TooltipProvider>
      </AuthProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
