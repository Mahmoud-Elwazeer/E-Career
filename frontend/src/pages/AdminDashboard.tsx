import { useState, useRef } from "react";
import { Link } from "react-router-dom";
import {
  BarChart3, Briefcase, Search, Link2, ArrowLeft, ImageIcon, Settings, ScrollText,
  TrendingUp, TrendingDown, Minus, Clock, RefreshCw, AlertTriangle,
  Users, Eye, MousePointerClick, Loader2, Upload, PieChart,
  LayoutDashboard, Building2, Star, ShieldCheck, Database, Globe,
  GitCompare, Brain, Bot, Mic, Zap, Bell, Package, Lock, Activity
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { ScrollReveal, StaggerContainer, StaggerItem } from "@/components/motion";
import { AdminJobsTable } from "@/components/admin/AdminJobsTable";
import { AdminSourcesManager } from "@/components/admin/AdminSourcesManager";
import { AdminMediaManager } from "@/components/admin/AdminMediaManager";
import { useAdminStats, fetchActivityLogs } from "@/hooks/use-admin-stats";
import { useFeatureFlags } from "@/hooks/use-feature-flags";
import { useTheme } from "@/hooks/use-theme";
import { usePageMeta } from "@/hooks/use-seo";
import { useToast } from "@/hooks/use-toast";
import { adminCsvImport, fetchClickAnalytics, fetchSearchAnalytics, fetchConversionAnalytics } from "@/lib/admin-api";
import { apiRequest } from "@/services/client";
import { formatDistanceToNow } from "date-fns";
import { useEffect } from "react";

type AdminTab =
  | 'overview' | 'users' | 'companies' | 'talent'
  | 'jobs' | 'verification' | 'sources' | 'scraping'
  | 'matching' | 'ai-center' | 'rashid' | 'interviews'
  | 'automations' | 'notifications' | 'analytics'
  | 'packages' | 'security' | 'search-admin' | 'system-health' | 'settings';

function AnalyticsTab() {
  const { toast } = useToast();
  const [clickData, setClickData] = useState<any>(null);
  const [searchData, setSearchData] = useState<any>(null);
  const [conversionData, setConversionData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchClickAnalytics().catch(() => null),
      fetchSearchAnalytics().catch(() => null),
      fetchConversionAnalytics().catch(() => null),
    ]).then(([c, s, cv]) => {
      setClickData(c);
      setSearchData(s);
      setConversionData(cv);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;

  return (
    <div className="space-y-6">
      {conversionData && (
        <StaggerContainer className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StaggerItem><Card><CardContent className="p-5">
            <p className="text-caption text-muted-foreground">Total Views</p>
            <p className="text-heading-1">{conversionData.total_views}</p>
          </CardContent></Card></StaggerItem>
          <StaggerItem><Card><CardContent className="p-5">
            <p className="text-caption text-muted-foreground">Total Clicks</p>
            <p className="text-heading-1">{conversionData.total_clicks}</p>
          </CardContent></Card></StaggerItem>
          <StaggerItem><Card><CardContent className="p-5">
            <p className="text-caption text-muted-foreground">Conversion Rate</p>
            <p className="text-heading-1">{conversionData.conversion_rate}</p>
          </CardContent></Card></StaggerItem>
        </StaggerContainer>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {clickData && (
          <Card><CardContent className="p-5">
            <h3 className="text-body font-medium mb-4">Top Jobs by Clicks</h3>
            <div className="space-y-2">
              {clickData.by_job.slice(0, 10).map((j: any) => (
                <div key={j.slug} className="flex items-center justify-between text-caption">
                  <span className="truncate max-w-[200px]">{j.title}</span>
                  <Badge variant="secondary">{j.count}</Badge>
                </div>
              ))}
              {clickData.by_job.length === 0 && <p className="text-caption text-muted-foreground">No clicks yet</p>}
            </div>
          </CardContent></Card>
        )}
        {searchData && (
          <Card><CardContent className="p-5">
            <h3 className="text-body font-medium mb-4">Top Searches ({searchData.total_searches} total)</h3>
            <div className="space-y-2">
              {searchData.top_queries.map((s: any) => (
                <div key={s.query} className="flex items-center justify-between text-caption">
                  <span>"{s.query}"</span>
                  <Badge variant="secondary">{s.count}</Badge>
                </div>
              ))}
              {searchData.top_queries.length === 0 && <p className="text-caption text-muted-foreground">No searches yet</p>}
            </div>
            {searchData.zero_result_queries.length > 0 && (
              <div className="mt-4 pt-4 border-t">
                <h4 className="text-caption font-medium mb-2 text-destructive">Zero-Result Queries</h4>
                <div className="flex flex-wrap gap-1.5">
                  {searchData.zero_result_queries.map((q: string) => (
                    <Badge key={q} variant="outline" className="text-[10px] text-destructive">{q}</Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent></Card>
        )}
        {clickData && (
          <Card><CardContent className="p-5">
            <h3 className="text-body font-medium mb-4">Clicks by Source</h3>
            <div className="space-y-2">
              {clickData.by_source.map((s: any) => (
                <div key={s.name} className="flex items-center justify-between text-caption">
                  <span>{s.name}</span>
                  <Badge variant="secondary">{s.count}</Badge>
                </div>
              ))}
              {clickData.by_source.length === 0 && <p className="text-caption text-muted-foreground">No data</p>}
            </div>
          </CardContent></Card>
        )}
      </div>
    </div>
  );
}

function CsvImportTab() {
  const { toast } = useToast();
  const fileRef = useRef<HTMLInputElement>(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<{ imported: number; skipped: number; total: number; errors: string[] } | null>(null);

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith(".csv")) {
      toast({ title: "Invalid file", description: "Please upload a .csv file", variant: "destructive" });
      return;
    }
    setImporting(true);
    setResult(null);
    try {
      const data = await adminCsvImport(file);
      setResult(data);
      toast({ title: `Imported ${data.imported} of ${data.total} jobs` });
    } catch (err: any) {
      toast({ title: "Import failed", description: err.message, variant: "destructive" });
    } finally {
      setImporting(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  return (
    <div className="max-w-2xl space-y-6">
      <Card><CardContent className="p-6 space-y-4">
        <h3 className="text-body font-medium">CSV Job Import</h3>
        <p className="text-caption text-muted-foreground">
          Upload a CSV with columns: <code className="bg-muted px-1 rounded text-[11px]">title</code> (required),{" "}
          <code className="bg-muted px-1 rounded text-[11px]">company, description, location, work_mode, seniority, industry, salary_min, salary_max, currency, apply_url, source, tags</code> (optional).
          Tags use semicolons. Jobs import as "review" status.
        </p>
        <Button onClick={() => fileRef.current?.click()} disabled={importing} className="rounded-xl gap-1.5">
          {importing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
          {importing ? "Importing..." : "Select CSV File"}
        </Button>
        <input ref={fileRef} type="file" accept=".csv" onChange={handleImport} className="hidden" />
      </CardContent></Card>
      {result && (
        <Card><CardContent className="p-5 space-y-3">
          <h4 className="text-body font-medium">Import Results</h4>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div><p className="text-heading-2 text-primary">{result.imported}</p><p className="text-caption text-muted-foreground">Imported</p></div>
            <div><p className="text-heading-2 text-destructive">{result.skipped}</p><p className="text-caption text-muted-foreground">Skipped</p></div>
            <div><p className="text-heading-2">{result.total}</p><p className="text-caption text-muted-foreground">Total</p></div>
          </div>
          {result.errors.length > 0 && (
            <div className="p-3 bg-destructive/10 rounded-lg">
              <p className="text-caption font-medium text-destructive mb-1">Errors:</p>
              {result.errors.map((e, i) => <p key={i} className="text-[11px] text-destructive">{e}</p>)}
            </div>
          )}
        </CardContent></Card>
      )}
    </div>
  );
}

function PlaceholderTab({ icon: Icon, title, description }: { icon: React.ComponentType<{ className?: string }>; title: string; description: string }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Icon className="h-5 w-5 text-primary" />
        <h2 className="text-heading-3">{title}</h2>
      </div>
      <Card>
        <CardContent className="p-8 text-center">
          <Icon className="h-10 w-10 text-muted-foreground/40 mx-auto mb-3" />
          <p className="text-body font-medium">{title}</p>
          <p className="text-caption text-muted-foreground mt-1">{description}</p>
        </CardContent>
      </Card>
    </div>
  );
}

function SystemHealthTab() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    apiRequest<any>("/admin-api/system-health/")
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Activity className="h-5 w-5 text-primary" />
        <h2 className="text-heading-3">System Health</h2>
      </div>
      {data ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(data).map(([key, value]) => (
            <Card key={key}>
              <CardContent className="p-5">
                <p className="text-caption text-muted-foreground capitalize">{key.replace(/_/g, " ")}</p>
                <p className="text-heading-2 mt-1">{typeof value === "object" ? JSON.stringify(value) : String(value)}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card><CardContent className="p-8 text-center">
          <Activity className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
          <p className="text-body text-muted-foreground">{error ? "Unable to load system health data" : "No data available"}</p>
        </CardContent></Card>
      )}
    </div>
  );
}

function ScrapingDashboardTab() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    apiRequest<any>("/admin-api/scraper-dashboard/")
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Globe className="h-5 w-5 text-primary" />
        <h2 className="text-heading-3">Scraping Dashboard</h2>
      </div>
      {data ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(data).map(([key, value]) => (
            <Card key={key}>
              <CardContent className="p-5">
                <p className="text-caption text-muted-foreground capitalize">{key.replace(/_/g, " ")}</p>
                <p className="text-heading-2 mt-1">{typeof value === "object" ? JSON.stringify(value) : String(value)}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card><CardContent className="p-8 text-center">
          <Globe className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
          <p className="text-body text-muted-foreground">{error ? "Unable to load scraper data" : "No scraping data available"}</p>
        </CardContent></Card>
      )}
    </div>
  );
}

function AiCenterTab() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    apiRequest<any>("/admin-api/ai-costs/")
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Brain className="h-5 w-5 text-primary" />
        <h2 className="text-heading-3">AI Center</h2>
      </div>
      {data ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(data).map(([key, value]) => (
            <Card key={key}>
              <CardContent className="p-5">
                <p className="text-caption text-muted-foreground capitalize">{key.replace(/_/g, " ")}</p>
                <p className="text-heading-2 mt-1">{typeof value === "object" ? JSON.stringify(value) : String(value)}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card><CardContent className="p-8 text-center">
          <Brain className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
          <p className="text-body text-muted-foreground">{error ? "Unable to load AI cost data" : "No AI cost data available"}</p>
        </CardContent></Card>
      )}
    </div>
  );
}

function GdprDashboardTab({ logs, logsLoading }: { logs: any[]; logsLoading: boolean }) {
  const [gdprData, setGdprData] = useState<any>(null);
  const [gdprLoading, setGdprLoading] = useState(true);

  useEffect(() => {
    apiRequest<any>("/admin-api/gdpr/dashboard/")
      .then(setGdprData)
      .catch(() => null)
      .finally(() => setGdprLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Lock className="h-5 w-5 text-primary" />
        <h2 className="text-heading-3">Security & Compliance</h2>
      </div>

      {/* GDPR Dashboard */}
      {gdprLoading ? (
        <div className="flex justify-center py-6"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>
      ) : gdprData ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(gdprData).map(([key, value]) => (
            <Card key={key}>
              <CardContent className="p-5">
                <p className="text-caption text-muted-foreground capitalize">{key.replace(/_/g, " ")}</p>
                <p className="text-heading-2 mt-1">{typeof value === "object" ? JSON.stringify(value) : String(value)}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card><CardContent className="p-5 text-center">
          <p className="text-caption text-muted-foreground">GDPR dashboard data unavailable</p>
        </CardContent></Card>
      )}

      {/* Activity Logs (moved from old logs tab) */}
      <div className="space-y-4">
        <h3 className="text-body font-medium">Activity Logs</h3>
        {logsLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : logs.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <ScrollText className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-body text-muted-foreground">No activity logs recorded yet</p>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full text-caption">
                <thead>
                  <tr className="border-b">
                    <th className="text-start p-3 font-medium">Action</th>
                    <th className="text-start p-3 font-medium">Entity</th>
                    <th className="text-start p-3 font-medium">Details</th>
                    <th className="text-start p-3 font-medium">When</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log: any) => (
                    <tr key={log.id} className="border-b last:border-0">
                      <td className="p-3">
                        <Badge variant="outline" className="text-[10px]">{log.action}</Badge>
                      </td>
                      <td className="p-3 text-muted-foreground">
                        {log.entity_type || "—"}
                      </td>
                      <td className="p-3 text-muted-foreground truncate max-w-[200px]">
                        {log.details ? JSON.stringify(log.details).slice(0, 80) : "—"}
                      </td>
                      <td className="p-3 text-muted-foreground whitespace-nowrap">
                        {formatDistanceToNow(new Date(log.created_at), { addSuffix: true })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

export default function AdminDashboard() {

  usePageMeta("Admin Dashboard", "USAM Jobs admin panel — manage jobs, sources, and platform settings.");
  const { lang } = useTheme();
  const { toast } = useToast();
  const isAr = lang === "ar";
  const [activeTab, setActiveTab] = useState<AdminTab>("overview");
  const [tableSearch, setTableSearch] = useState("");

  const { stats, charts, isLoading: statsLoading, reload: reloadStats } = useAdminStats();
  const { flags, isLoading: flagsLoading, toggleFlag } = useFeatureFlags();

  // Activity logs state
  const [logs, setLogs] = useState<any[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);

  useEffect(() => {
    if (activeTab === "security") {
      setLogsLoading(true);
      fetchActivityLogs(1).then(setLogs).catch(() => {}).finally(() => setLogsLoading(false));
    }
  }, [activeTab]);

  const kpis = [
    { label: "Total Jobs", value: stats?.total_jobs ?? "—", trend: `+${stats?.jobs_this_week ?? 0} this week`, icon: Briefcase, up: true },
    { label: "Pending Review", value: stats?.pending_review ?? "—", trend: "", icon: Search, up: null },
    { label: "Active Sources", value: stats?.active_sources ?? "—", trend: "", icon: Link2, up: null },
    { label: "Total Users", value: stats?.total_users ?? "—", trend: "", icon: Users, up: null },
    { label: "Total Saves", value: stats?.total_saves ?? "—", trend: "", icon: TrendingUp, up: true },
    { label: "Apply Clicks", value: stats?.total_clicks ?? "—", trend: "", icon: MousePointerClick, up: null },
    { label: "Job Views", value: stats?.total_views ?? "—", trend: "", icon: Eye, up: null },
  ];

  const navGroups = [
    {
      label: "Platform",
      items: [
        { icon: LayoutDashboard, label: "Overview", tab: "overview" as AdminTab },
        { icon: Users, label: "Users", tab: "users" as AdminTab },
        { icon: Building2, label: "Companies", tab: "companies" as AdminTab },
        { icon: Star, label: "Talent", tab: "talent" as AdminTab },
      ],
    },
    {
      label: "Content",
      items: [
        { icon: Briefcase, label: "Jobs", tab: "jobs" as AdminTab },
        { icon: ShieldCheck, label: "Verification", tab: "verification" as AdminTab },
        { icon: Database, label: "Sources", tab: "sources" as AdminTab },
        { icon: Globe, label: "Scraping", tab: "scraping" as AdminTab },
      ],
    },
    {
      label: "Intelligence",
      items: [
        { icon: GitCompare, label: "Matching", tab: "matching" as AdminTab },
        { icon: Brain, label: "AI Center", tab: "ai-center" as AdminTab },
        { icon: Bot, label: "Rashid", tab: "rashid" as AdminTab },
        { icon: Mic, label: "Interviews", tab: "interviews" as AdminTab },
      ],
    },
    {
      label: "Operations",
      items: [
        { icon: Zap, label: "Automations", tab: "automations" as AdminTab },
        { icon: Bell, label: "Notifications", tab: "notifications" as AdminTab },
        { icon: BarChart3, label: "Analytics", tab: "analytics" as AdminTab },
      ],
    },
    {
      label: "Administration",
      items: [
        { icon: Package, label: "Packages", tab: "packages" as AdminTab },
        { icon: Lock, label: "Security", tab: "security" as AdminTab },
        { icon: Search, label: "Search", tab: "search-admin" as AdminTab },
        { icon: Activity, label: "System Health", tab: "system-health" as AdminTab },
        { icon: Settings, label: "Settings", tab: "settings" as AdminTab },
      ],
    },
  ];

  const allNavItems = navGroups.flatMap(g => g.items);
  const activeNavItem = allNavItems.find(item => item.tab === activeTab);

  const handleToggleFlag = async (id: string, enabled: boolean, label: string) => {
    const { error } = await toggleFlag(id, enabled);
    if (error) {
      toast({ title: "Failed to update", description: (error as any).message, variant: "destructive" });
    } else {
      toast({ title: `${label} ${enabled ? "enabled" : "disabled"}` });
    }
  };

  return (
    <div className="min-h-screen flex bg-background">
      {/* Sidebar */}
      <aside className="hidden lg:flex w-60 border-e bg-surface-1 flex-col shrink-0 sticky top-0 h-screen">
        <div className="p-5 border-b">
          <img src="/logo-dark.png" alt="USAM" className="h-8 dark:invert" />
          <p className="text-caption text-muted-foreground mt-1">Admin Panel</p>
        </div>
        <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
          {navGroups.map((group) => (
            <div key={group.label}>
              <p className="px-3 pt-4 pb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/60 first:pt-1">
                {group.label}
              </p>
              {group.items.map((item) => (
                <button
                  key={item.tab}
                  onClick={() => setActiveTab(item.tab)}
                  className={`flex items-center gap-2.5 w-full px-3 py-2 rounded-lg text-caption font-medium transition-colors ${
                    activeTab === item.tab
                      ? "bg-primary text-primary-foreground"
                      : "text-foreground/70 hover:bg-accent hover:text-foreground"
                  }`}
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </button>
              ))}
            </div>
          ))}
        </nav>
        <div className="p-3 border-t">
          <Button variant="ghost" size="sm" className="w-full justify-start gap-2 text-caption" asChild>
            <Link to="/">
              <ArrowLeft className="h-3.5 w-3.5" /> Back to site
            </Link>
          </Button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">
        <header className="border-b bg-card/95 glass sticky top-0 z-40">
          <div className="flex items-center justify-between px-6 h-14">
            <div className="flex items-center gap-4">
              <div className="flex lg:hidden gap-1 overflow-x-auto">
                {allNavItems.map((item) => (
                  <Button
                    key={item.tab}
                    variant={activeTab === item.tab ? "default" : "ghost"}
                    size="sm"
                    onClick={() => setActiveTab(item.tab)}
                    className="text-caption rounded-lg shrink-0"
                  >
                    {item.label}
                  </Button>
                ))}
              </div>
              <h1 className="text-heading-3 hidden lg:block">{activeNavItem?.label ?? activeTab}</h1>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" className="rounded-lg" onClick={reloadStats}>
                <RefreshCw className="h-3.5 w-3.5 me-1" /> Refresh
              </Button>
              <Button variant="outline" size="sm" className="rounded-lg" asChild>
                <Link to="/">Public Site</Link>
              </Button>
            </div>
          </div>
        </header>

        <div className="p-6">
          {/* OVERVIEW */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              {statsLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <>
                  <StaggerContainer className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    {kpis.map((kpi) => (
                      <StaggerItem key={kpi.label}>
                        <Card>
                          <CardContent className="p-5">
                            <div className="flex items-center justify-between mb-3">
                              <div className="rounded-lg bg-primary-muted p-2">
                                <kpi.icon className="h-4 w-4 text-primary" />
                              </div>
                              {kpi.trend && (
                                <span className="text-caption font-medium text-muted-foreground">
                                  {kpi.trend}
                                </span>
                              )}
                            </div>
                            <p className="text-heading-1">{kpi.value}</p>
                            <p className="text-caption text-muted-foreground mt-1">{kpi.label}</p>
                          </CardContent>
                        </Card>
                      </StaggerItem>
                    ))}
                  </StaggerContainer>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Jobs by Source */}
                    <ScrollReveal>
                      <Card>
                        <CardContent className="p-5">
                          <h3 className="text-body font-medium mb-4">Jobs by Source</h3>
                          {charts?.jobs_by_source.length ? (
                            <div className="space-y-3">
                              {charts.jobs_by_source.map((s) => {
                                const total = charts.jobs_by_source.reduce((a, b) => a + b.count, 0);
                                const pct = total > 0 ? Math.round((s.count / total) * 100) : 0;
                                return (
                                  <div key={s.name}>
                                    <div className="flex items-center justify-between text-caption mb-1">
                                      <span>{s.name}</span>
                                      <span className="text-muted-foreground">{s.count} ({pct}%)</span>
                                    </div>
                                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                                      <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${pct}%` }} />
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          ) : (
                            <p className="text-caption text-muted-foreground">No data yet</p>
                          )}
                        </CardContent>
                      </Card>
                    </ScrollReveal>

                    {/* Jobs by Industry */}
                    <ScrollReveal delay={0.1}>
                      <Card>
                        <CardContent className="p-5">
                          <h3 className="text-body font-medium mb-4">Jobs by Industry</h3>
                          {charts?.jobs_by_industry.length ? (
                            <div className="space-y-3">
                              {charts.jobs_by_industry.map((ind) => {
                                const total = charts.jobs_by_industry.reduce((a, b) => a + b.count, 0);
                                const pct = total > 0 ? Math.round((ind.count / total) * 100) : 0;
                                return (
                                  <div key={ind.name}>
                                    <div className="flex items-center justify-between text-caption mb-1">
                                      <span className="capitalize">{ind.name}</span>
                                      <span className="text-muted-foreground">{ind.count} ({pct}%)</span>
                                    </div>
                                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                                      <div className="h-full bg-accent-foreground/30 rounded-full transition-all" style={{ width: `${pct}%` }} />
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          ) : (
                            <p className="text-caption text-muted-foreground">No data yet</p>
                          )}
                        </CardContent>
                      </Card>
                    </ScrollReveal>

                    {/* Recent Activity */}
                    <ScrollReveal delay={0.2} className="lg:col-span-2">
                      <Card>
                        <CardContent className="p-5">
                          <h3 className="text-body font-medium mb-4">Recent Activity</h3>
                          {(charts?.recent_activity ?? []).length ? (
                            <div className="space-y-3">
                              {(charts?.recent_activity ?? []).slice(0, 10).map((log: any) => (
                                <div key={log.id} className="flex items-start gap-3">
                                  <div className="rounded-lg p-1.5 mt-0.5 bg-primary-muted">
                                    <Clock className="h-3.5 w-3.5 text-primary" />
                                  </div>
                                  <div className="flex-1">
                                    <p className="text-caption">
                                      <Badge variant="outline" className="text-[10px] me-1.5">{log.action}</Badge>
                                      {log.entity_type && <span className="text-muted-foreground">{log.entity_type}</span>}
                                    </p>
                                    <p className="text-[10px] text-muted-foreground">
                                      {formatDistanceToNow(new Date(log.created_at), { addSuffix: true })}
                                    </p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-caption text-muted-foreground">No activity logged yet</p>
                          )}
                        </CardContent>
                      </Card>
                    </ScrollReveal>
                  </div>
                </>
              )}
            </div>
          )}

          {/* JOBS TABLE */}
          {activeTab === "jobs" && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <Search className="absolute start-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    value={tableSearch}
                    onChange={(e) => setTableSearch(e.target.value)}
                    placeholder="Search jobs..."
                    className="ps-10 rounded-xl"
                  />
                </div>
              </div>
              <AdminJobsTable />
            </div>
          )}

          {/* SOURCES */}
          {activeTab === "sources" && <AdminSourcesManager />}

          {/* SETTINGS - Feature Flags + Media + Import */}
          {activeTab === "settings" && (
            <div className="space-y-8">
              <div className="max-w-2xl">
                <Card>
                  <CardContent className="p-5">
                    <h3 className="text-body font-medium mb-4">Feature Flags</h3>
                    {flagsLoading ? (
                      <div className="flex justify-center py-6">
                        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {flags.map((flag) => (
                          <div key={flag.id} className="flex items-center justify-between py-2 border-b last:border-0">
                            <div>
                              <p className="text-body font-medium">{flag.label}</p>
                              {flag.description && (
                                <p className="text-caption text-muted-foreground">{flag.description}</p>
                              )}
                              <Badge variant="outline" className="text-[10px] mt-1">{flag.key}</Badge>
                            </div>
                            <Switch
                              checked={flag.is_enabled}
                              onCheckedChange={(checked) => handleToggleFlag(flag.uuid, checked, flag.label)}
                            />
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Media Library (moved from standalone media tab) */}
              <div>
                <h3 className="text-body font-medium mb-4 flex items-center gap-2">
                  <ImageIcon className="h-4 w-4 text-muted-foreground" /> Media Library
                </h3>
                <AdminMediaManager />
              </div>

              {/* CSV Import (moved from standalone import tab) */}
              <div>
                <h3 className="text-body font-medium mb-4 flex items-center gap-2">
                  <Upload className="h-4 w-4 text-muted-foreground" /> CSV Import
                </h3>
                <CsvImportTab />
              </div>
            </div>
          )}

          {/* ANALYTICS */}
          {activeTab === "analytics" && <AnalyticsTab />}

          {/* SECURITY (includes GDPR dashboard + activity logs) */}
          {activeTab === "security" && <GdprDashboardTab logs={logs} logsLoading={logsLoading} />}

          {/* SYSTEM HEALTH */}
          {activeTab === "system-health" && <SystemHealthTab />}

          {/* SCRAPING */}
          {activeTab === "scraping" && <ScrapingDashboardTab />}

          {/* AI CENTER */}
          {activeTab === "ai-center" && <AiCenterTab />}

          {/* PLACEHOLDER TABS */}
          {activeTab === "users" && (
            <PlaceholderTab icon={Users} title="User Management" description="Manage platform users, roles, and permissions. Coming soon." />
          )}
          {activeTab === "companies" && (
            <PlaceholderTab icon={Building2} title="Company Management" description="Review and manage registered companies and employer accounts. Coming soon." />
          )}
          {activeTab === "talent" && (
            <PlaceholderTab icon={Star} title="Talent Pool" description="Browse and manage candidate profiles, talent rankings, and skill assessments. Coming soon." />
          )}
          {activeTab === "verification" && (
            <PlaceholderTab icon={ShieldCheck} title="Verification Center" description="Review and verify job listings, company profiles, and user identities. Coming soon." />
          )}
          {activeTab === "matching" && (
            <PlaceholderTab icon={GitCompare} title="Job Matching" description="Configure and monitor the AI-powered job matching engine. Coming soon." />
          )}
          {activeTab === "rashid" && (
            <PlaceholderTab icon={Bot} title="Rashid AI Assistant" description="Manage the Rashid conversational AI assistant, training data, and conversation logs. Coming soon." />
          )}
          {activeTab === "interviews" && (
            <PlaceholderTab icon={Mic} title="Interview Management" description="Manage AI-assisted interview scheduling, templates, and evaluation criteria. Coming soon." />
          )}
          {activeTab === "automations" && (
            <PlaceholderTab icon={Zap} title="Automations" description="Configure automated workflows for job processing, notifications, and data pipelines. Coming soon." />
          )}
          {activeTab === "notifications" && (
            <PlaceholderTab icon={Bell} title="Notification Center" description="Manage notification templates, delivery channels, and broadcast messages. Coming soon." />
          )}
          {activeTab === "packages" && (
            <PlaceholderTab icon={Package} title="Packages & Billing" description="Manage subscription packages, pricing tiers, and billing configurations. Coming soon." />
          )}
          {activeTab === "search-admin" && (
            <PlaceholderTab icon={Search} title="Search Administration" description="Configure search indexing, relevance tuning, synonyms, and search analytics. Coming soon." />
          )}
        </div>
      </main>
    </div>
  );
}
