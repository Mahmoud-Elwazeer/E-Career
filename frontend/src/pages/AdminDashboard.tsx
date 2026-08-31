import { useState, useRef } from "react";
import { Link } from "react-router-dom";
import {
  BarChart3, Briefcase, Search, Link2, ArrowLeft, ImageIcon, Settings, ScrollText,
  TrendingUp, TrendingDown, Minus, Clock, RefreshCw, AlertTriangle,
  Users, Eye, MousePointerClick, Loader2, Upload, PieChart,
  LayoutDashboard, Building2, Star, ShieldCheck, Database, Globe,
  GitCompare, Brain, Bot, Mic, Zap, Bell, Package, Lock, Activity,
  MessageSquare, Send
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
  | 'packages' | 'security' | 'search-admin' | 'system-health' | 'settings'
  | 'copilot';

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

function UsersTab() {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [searching, setSearching] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [timeline, setTimeline] = useState<any[] | null>(null);
  const [timelineLoading, setTimelineLoading] = useState(false);

  const fetchUsers = async (search?: string) => {
    setSearching(true);
    try {
      const params = search ? `?search=${encodeURIComponent(search)}` : "";
      const data = await apiRequest<any>(`/admin-api/users/${params}`);
      setUsers(Array.isArray(data) ? data : data?.results || []);
    } catch {
      setUsers([]);
    } finally {
      setSearching(false);
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  const handleSearch = () => {
    if (searchTerm.length < 2 && searchTerm.length > 0) return;
    fetchUsers(searchTerm || undefined);
  };

  const loadTimeline = async (userId: string) => {
    setSelectedUserId(userId);
    setTimelineLoading(true);
    try {
      const data = await apiRequest<any>(`/admin-api/users/${userId}/timeline/`);
      setTimeline(Array.isArray(data) ? data : data?.events || []);
    } catch {
      setTimeline([]);
    } finally {
      setTimelineLoading(false);
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Users className="h-5 w-5 text-primary" />
        <h2 className="text-heading-3">User Management</h2>
      </div>

      <Card><CardContent className="p-5 space-y-4">
        <h3 className="text-body font-medium">Search Users</h3>
        <div className="flex gap-2 max-w-lg">
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by name or email..."
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="rounded-xl"
          />
          <Button onClick={handleSearch} disabled={searching}>
            {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          </Button>
        </div>
      </CardContent></Card>

      <Card><CardContent className="p-5">
        <h3 className="text-body font-medium mb-4">Users ({users.length})</h3>
        {users.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-caption">
              <thead><tr className="border-b">
                <th className="text-start p-3 font-medium">Email</th>
                <th className="text-start p-3 font-medium">Name</th>
                <th className="text-start p-3 font-medium">Role</th>
                <th className="text-start p-3 font-medium">Active</th>
                <th className="text-start p-3 font-medium">Joined</th>
                <th className="text-start p-3 font-medium">Actions</th>
              </tr></thead>
              <tbody>
                {users.map((user: any, i: number) => (
                  <tr key={user.id || i} className="border-b last:border-0 hover:bg-muted/50">
                    <td className="p-3">{user.email}</td>
                    <td className="p-3 text-muted-foreground">{[user.first_name, user.last_name].filter(Boolean).join(" ") || "—"}</td>
                    <td className="p-3"><Badge variant="outline" className="text-[10px]">{user.role}</Badge></td>
                    <td className="p-3">{user.is_active ? "Yes" : "No"}</td>
                    <td className="p-3 text-muted-foreground whitespace-nowrap">
                      {user.date_joined ? formatDistanceToNow(new Date(user.date_joined), { addSuffix: true }) : "—"}
                    </td>
                    <td className="p-3">
                      <Button variant="ghost" size="sm" onClick={() => loadTimeline(String(user.id))}>
                        Timeline
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-caption text-muted-foreground">No users found</p>
        )}
      </CardContent></Card>

      {selectedUserId && (
        <Card><CardContent className="p-5">
          <h3 className="text-body font-medium mb-3">User Timeline</h3>
          {timelineLoading ? (
            <div className="flex justify-center py-6"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>
          ) : timeline && timeline.length > 0 ? (
            <div className="space-y-2">
              {timeline.map((event: any, i: number) => (
                <div key={i} className="flex items-start gap-3 py-2 border-b last:border-0">
                  <Clock className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <div>
                    <p className="text-caption font-medium">{event.action || event.type || "Event"}</p>
                    <p className="text-[10px] text-muted-foreground">{event.detail || event.description || ""}</p>
                    {event.created_at && (
                      <p className="text-[10px] text-muted-foreground">{formatDistanceToNow(new Date(event.created_at), { addSuffix: true })}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-caption text-muted-foreground">No timeline data available</p>
          )}
        </CardContent></Card>
      )}
    </div>
  );
}

function CompaniesTab() {
  const [companies, setCompanies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [selectedCompany, setSelectedCompany] = useState<any>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    apiRequest<any>("/admin-api/companies/")
      .then((data) => setCompanies(data?.results || []))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  const loadDetail = async (uuid: string) => {
    setDetailLoading(true);
    try {
      const data = await apiRequest<any>(`/admin-api/companies/${uuid}/`);
      setSelectedCompany(data);
    } catch {
      setSelectedCompany(null);
    } finally {
      setDetailLoading(false);
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;
  if (error) return <div className="text-center p-8 text-muted-foreground">Failed to load companies.</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Building2 className="h-5 w-5 text-primary" />
        <h2 className="text-heading-3">Company Management</h2>
        <Badge variant="secondary">{companies.length} companies</Badge>
      </div>

      {companies.length > 0 ? (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-caption">
              <thead>
                <tr className="border-b">
                  <th className="text-start p-3 font-medium">Name</th>
                  <th className="text-start p-3 font-medium">Industry</th>
                  <th className="text-start p-3 font-medium">Size</th>
                  <th className="text-start p-3 font-medium">Jobs</th>
                  <th className="text-start p-3 font-medium">Status</th>
                  <th className="text-start p-3 font-medium">Created</th>
                </tr>
              </thead>
              <tbody>
                {companies.map((c: any) => (
                  <tr key={c.uuid} className="border-b last:border-0 hover:bg-muted/50 cursor-pointer" onClick={() => loadDetail(c.uuid)}>
                    <td className="p-3 font-medium">{c.name}</td>
                    <td className="p-3 text-muted-foreground">{c.industry || "—"}</td>
                    <td className="p-3 text-muted-foreground">{c.size || "—"}</td>
                    <td className="p-3"><Badge variant="secondary">{c.job_count ?? 0}</Badge></td>
                    <td className="p-3">
                      <Badge variant={c.status === "active" ? "default" : "outline"} className="capitalize">{c.status || "unknown"}</Badge>
                    </td>
                    <td className="p-3 text-muted-foreground whitespace-nowrap">
                      {c.created_at ? formatDistanceToNow(new Date(c.created_at), { addSuffix: true }) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        <Card><CardContent className="p-8 text-center">
          <Building2 className="h-8 w-8 text-muted-foreground/40 mx-auto mb-2" />
          <p className="text-body text-muted-foreground">No companies registered yet</p>
        </CardContent></Card>
      )}

      {detailLoading && (
        <div className="flex justify-center py-6"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>
      )}
      {selectedCompany && !detailLoading && (
        <Card><CardContent className="p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-body font-medium">{selectedCompany.name}</h3>
            <Button variant="ghost" size="sm" onClick={() => setSelectedCompany(null)}>Close</Button>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {Object.entries(selectedCompany as Record<string, unknown>).filter(([k]) => !["uuid", "id"].includes(k)).map(([key, value]) => (
              <div key={key}>
                <p className="text-[10px] text-muted-foreground capitalize">{key.replace(/_/g, " ")}</p>
                <p className="text-caption mt-0.5">{typeof value === "object" ? JSON.stringify(value) : String(value ?? "—")}</p>
              </div>
            ))}
          </div>
        </CardContent></Card>
      )}
    </div>
  );
}

function TalentTab() {
  const [pools, setPools] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    apiRequest<any>("/admin-api/talent-pools/")
      .then((data) => setPools(data?.results || []))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;
  if (error) return <div className="text-center p-8 text-muted-foreground">Failed to load talent pools.</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Star className="h-5 w-5 text-primary" />
        <h2 className="text-heading-3">Talent Pools</h2>
        <Badge variant="secondary">{pools.length} pools</Badge>
      </div>

      {pools.length > 0 ? (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-caption">
              <thead>
                <tr className="border-b">
                  <th className="text-start p-3 font-medium">Pool Name</th>
                  <th className="text-start p-3 font-medium">Company</th>
                  <th className="text-start p-3 font-medium">Candidates</th>
                  <th className="text-start p-3 font-medium">Created</th>
                </tr>
              </thead>
              <tbody>
                {pools.map((pool: any) => (
                  <tr key={pool.uuid} className="border-b last:border-0">
                    <td className="p-3 font-medium">{pool.name}</td>
                    <td className="p-3 text-muted-foreground">{pool.company_name || "—"}</td>
                    <td className="p-3"><Badge variant="secondary">{pool.candidate_count ?? 0}</Badge></td>
                    <td className="p-3 text-muted-foreground whitespace-nowrap">
                      {pool.created_at ? formatDistanceToNow(new Date(pool.created_at), { addSuffix: true }) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        <Card><CardContent className="p-8 text-center">
          <Star className="h-8 w-8 text-muted-foreground/40 mx-auto mb-2" />
          <p className="text-body text-muted-foreground">No talent pools created yet</p>
        </CardContent></Card>
      )}
    </div>
  );
}

function VerificationTab() {
  const [searchTerm, setSearchTerm] = useState("");
  const [jobResults, setJobResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [verification, setVerification] = useState<any>(null);
  const [verLoading, setVerLoading] = useState(false);
  const [selectedJobUuid, setSelectedJobUuid] = useState<string | null>(null);
  const [overrideScore, setOverrideScore] = useState("");
  const [overrideReason, setOverrideReason] = useState("");
  const [overriding, setOverriding] = useState(false);
  const { toast } = useToast();

  const handleSearch = async () => {
    if (searchTerm.length < 2) return;
    setSearching(true);
    try {
      const data = await apiRequest<any>(`/admin-api/search/?q=${encodeURIComponent(searchTerm)}&limit=20`);
      setJobResults((data?.results || []).filter((r: any) => r.type === "job"));
    } catch {
      setJobResults([]);
    } finally {
      setSearching(false);
    }
  };

  const loadVerification = async (jobUuid: string) => {
    setSelectedJobUuid(jobUuid);
    setVerLoading(true);
    try {
      const data = await apiRequest<any>(`/admin-api/verification/${jobUuid}/`);
      setVerification(data);
    } catch {
      setVerification(null);
    } finally {
      setVerLoading(false);
    }
  };

  const handleOverride = async () => {
    if (!selectedJobUuid || !overrideScore || !overrideReason) return;
    setOverriding(true);
    try {
      await apiRequest<any>(`/admin-api/verification/${selectedJobUuid}/override/`, {
        method: "PATCH",
        body: { trust_score: Number(overrideScore), reason: overrideReason },
      });
      toast({ title: "Override applied successfully" });
      loadVerification(selectedJobUuid);
      setOverrideScore("");
      setOverrideReason("");
    } catch {
      toast({ title: "Override failed", variant: "destructive" });
    } finally {
      setOverriding(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <ShieldCheck className="h-5 w-5 text-primary" />
        <h2 className="text-heading-3">Verification Center</h2>
      </div>

      <Card><CardContent className="p-5 space-y-4">
        <h3 className="text-body font-medium">Search Jobs for Verification</h3>
        <div className="flex gap-2 max-w-lg">
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search job titles..."
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="rounded-xl"
          />
          <Button onClick={handleSearch} disabled={searching || searchTerm.length < 2}>
            {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
          </Button>
        </div>
        {jobResults.length > 0 && (
          <div className="space-y-2">
            {jobResults.map((job: any, i: number) => (
              <div key={job.id || i} className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 cursor-pointer" onClick={() => loadVerification(job.id)}>
                <div>
                  <p className="text-caption font-medium">{job.label}</p>
                  <p className="text-[10px] text-muted-foreground">{job.detail}</p>
                </div>
                <Button variant="outline" size="sm">Check Verification</Button>
              </div>
            ))}
          </div>
        )}
      </CardContent></Card>

      {verLoading && (
        <div className="flex justify-center py-6"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>
      )}
      {verification && !verLoading && (
        <Card><CardContent className="p-5 space-y-4">
          <h3 className="text-body font-medium">Verification Details</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {verification.trust_score != null && (
              <div>
                <p className="text-[10px] text-muted-foreground">Trust Score</p>
                <p className="text-heading-2 mt-1">{verification.trust_score}</p>
              </div>
            )}
            {Object.entries(verification as Record<string, unknown>).filter(([k]) => k !== "trust_score").map(([key, value]) => (
              <div key={key}>
                <p className="text-[10px] text-muted-foreground capitalize">{key.replace(/_/g, " ")}</p>
                <p className="text-caption mt-0.5">{typeof value === "object" ? JSON.stringify(value) : String(value ?? "—")}</p>
              </div>
            ))}
          </div>

          <div className="border-t pt-4 space-y-3">
            <h4 className="text-caption font-medium">Override Trust Score</h4>
            <div className="flex gap-2 max-w-lg">
              <Input
                type="number"
                value={overrideScore}
                onChange={(e) => setOverrideScore(e.target.value)}
                placeholder="New score (0-100)"
                className="rounded-xl w-40"
              />
              <Input
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                placeholder="Reason for override"
                className="rounded-xl flex-1"
              />
              <Button onClick={handleOverride} disabled={overriding || !overrideScore || !overrideReason}>
                {overriding ? <Loader2 className="h-4 w-4 animate-spin" /> : "Override"}
              </Button>
            </div>
          </div>
        </CardContent></Card>
      )}
    </div>
  );
}

function MatchingTab() {
  const [userId, setUserId] = useState("");
  const [jobUuid, setJobUuid] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const handleDiagnose = async () => {
    if (!userId || !jobUuid) return;
    setLoading(true);
    setError(false);
    setResult(null);
    try {
      const data = await apiRequest<any>(`/admin-api/recommendations/diagnostics/?user_id=${encodeURIComponent(userId)}&job_uuid=${encodeURIComponent(jobUuid)}`);
      setResult(data);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <GitCompare className="h-5 w-5 text-primary" />
        <h2 className="text-heading-3">Match Diagnostics</h2>
      </div>

      <Card><CardContent className="p-5 space-y-4">
        <h3 className="text-body font-medium">Diagnose Match</h3>
        <p className="text-caption text-muted-foreground">Enter a user ID and job UUID to see how the matching engine scores them.</p>
        <div className="flex flex-col sm:flex-row gap-2 max-w-2xl">
          <Input
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="User ID"
            className="rounded-xl"
          />
          <Input
            value={jobUuid}
            onChange={(e) => setJobUuid(e.target.value)}
            placeholder="Job UUID"
            className="rounded-xl"
          />
          <Button onClick={handleDiagnose} disabled={loading || !userId || !jobUuid}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Diagnose"}
          </Button>
        </div>
      </CardContent></Card>

      {error && (
        <Card><CardContent className="p-5 text-center">
          <p className="text-caption text-destructive">Failed to load diagnostics. Check that both IDs are valid.</p>
        </CardContent></Card>
      )}

      {result && (
        <div className="space-y-4">
          {result.match_breakdown ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(result.match_breakdown as Record<string, unknown>).map(([key, value]) => (
                <Card key={key}>
                  <CardContent className="p-5">
                    <p className="text-caption text-muted-foreground capitalize">{key.replace(/_/g, " ")}</p>
                    <p className="text-heading-2 mt-1">{typeof value === "number" ? `${Math.round(value * 100)}%` : String(value)}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(result as Record<string, unknown>).map(([key, value]) => (
                <Card key={key}>
                  <CardContent className="p-5">
                    <p className="text-caption text-muted-foreground capitalize">{key.replace(/_/g, " ")}</p>
                    <p className="text-heading-2 mt-1">{typeof value === "object" ? JSON.stringify(value) : String(value)}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function RashidTab() {
  const [rashidStats, setRashidStats] = useState<any>(null);
  const [aiCosts, setAiCosts] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiRequest<any>("/admin-api/rashid/stats/").catch(() => null),
      apiRequest<any>("/admin-api/ai-costs/").catch(() => null),
    ]).then(([rs, ai]) => {
      setRashidStats(rs);
      setAiCosts(ai);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Bot className="h-5 w-5 text-primary" />
        <h2 className="text-heading-3">Rasheed AI Assistant</h2>
      </div>

      {rashidStats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: "Total Conversations", value: rashidStats.total_conversations },
            { label: "Today's AI Cost", value: rashidStats.today_ai_costs?.cost != null ? `$${rashidStats.today_ai_costs.cost.toFixed(2)}` : "—" },
            { label: "Today's AI Calls", value: rashidStats.today_ai_costs?.calls ?? "—" },
          ].map((s) => (
            <Card key={s.label}><CardContent className="p-5">
              <p className="text-caption text-muted-foreground">{s.label}</p>
              <p className="text-heading-2 mt-1">{s.value ?? "—"}</p>
            </CardContent></Card>
          ))}
        </div>
      )}

      {rashidStats?.by_mode && Object.keys(rashidStats.by_mode).length > 0 && (
        <Card><CardContent className="p-5">
          <h3 className="text-body font-medium mb-4">Conversations by Mode</h3>
          <div className="space-y-2">
            {Object.entries(rashidStats.by_mode as Record<string, number>).map(([mode, count]) => (
              <div key={mode} className="flex items-center justify-between py-2 border-b last:border-0">
                <span className="text-caption capitalize">{mode.replace(/_/g, " ")}</span>
                <Badge variant="secondary">{String(count)}</Badge>
              </div>
            ))}
          </div>
        </CardContent></Card>
      )}

      {rashidStats?.recent_conversations?.length > 0 && (
        <Card><CardContent className="p-5">
          <h3 className="text-body font-medium mb-4">Recent Conversations</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-caption">
              <thead><tr className="border-b">
                <th className="text-start p-3 font-medium">User</th>
                <th className="text-start p-3 font-medium">Mode</th>
                <th className="text-start p-3 font-medium">Title</th>
              </tr></thead>
              <tbody>
                {rashidStats.recent_conversations.map((c: any, i: number) => (
                  <tr key={c.id || i} className="border-b last:border-0">
                    <td className="p-3">{c.user_email}</td>
                    <td className="p-3"><Badge variant="outline" className="text-[10px]">{c.mode}</Badge></td>
                    <td className="p-3 text-muted-foreground truncate max-w-[200px]">{c.title || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent></Card>
      )}

      <Card><CardContent className="p-5">
        <h3 className="text-body font-medium mb-4">AI Feature Costs</h3>
        {aiCosts?.feature_costs ? (
          <div className="space-y-3">
            {Object.entries(aiCosts.feature_costs as Record<string, any>).map(([feature, cost]) => (
              <div key={feature} className="flex items-center justify-between py-2 border-b last:border-0">
                <span className="text-caption capitalize">{feature.replace(/_/g, " ")}</span>
                <Badge variant="secondary">${typeof cost === "number" ? cost.toFixed(4) : String(cost)}</Badge>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-caption text-muted-foreground">No AI cost data available</p>
        )}
      </CardContent></Card>
    </div>
  );
}

function InterviewsTab() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiRequest<any>("/admin-api/interviews/stats/")
      .then(setStats)
      .catch(() => null)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Mic className="h-5 w-5 text-primary" />
        <h2 className="text-heading-3">Interview Management</h2>
      </div>

      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: "Total Sessions", value: stats.total_sessions },
            { label: "Completed", value: stats.completed_sessions },
            { label: "Avg Score", value: stats.avg_score != null ? stats.avg_score.toFixed(1) : "—" },
          ].map((s) => (
            <Card key={s.label}><CardContent className="p-5">
              <p className="text-caption text-muted-foreground">{s.label}</p>
              <p className="text-heading-2 mt-1">{s.value ?? "—"}</p>
            </CardContent></Card>
          ))}
        </div>
      )}

      {stats?.by_type && Object.keys(stats.by_type).length > 0 && (
        <Card><CardContent className="p-5">
          <h3 className="text-body font-medium mb-4">Sessions by Type</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {Object.entries(stats.by_type as Record<string, number>).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                <span className="text-caption capitalize">{type.replace(/_/g, " ")}</span>
                <Badge variant="secondary">{String(count)}</Badge>
              </div>
            ))}
          </div>
        </CardContent></Card>
      )}

      {stats?.recent_sessions?.length > 0 && (
        <Card><CardContent className="p-5">
          <h3 className="text-body font-medium mb-4">Recent Sessions</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-caption">
              <thead><tr className="border-b">
                <th className="text-start p-3 font-medium">User</th>
                <th className="text-start p-3 font-medium">Type</th>
                <th className="text-start p-3 font-medium">Status</th>
                <th className="text-start p-3 font-medium">Score</th>
                <th className="text-start p-3 font-medium">Started</th>
              </tr></thead>
              <tbody>
                {stats.recent_sessions.map((s: any, i: number) => (
                  <tr key={s.id || i} className="border-b last:border-0">
                    <td className="p-3">{s.user_email}</td>
                    <td className="p-3"><Badge variant="outline" className="text-[10px]">{s.interview_type}</Badge></td>
                    <td className="p-3"><Badge variant={s.status === "completed" ? "default" : "secondary"} className="text-[10px]">{s.status}</Badge></td>
                    <td className="p-3">{s.overall_score != null ? s.overall_score.toFixed(1) : "—"}</td>
                    <td className="p-3 text-muted-foreground whitespace-nowrap">
                      {s.started_at ? formatDistanceToNow(new Date(s.started_at), { addSuffix: true }) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent></Card>
      )}
    </div>
  );
}

function NotificationsTab() {
  const [notifStats, setNotifStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [broadcastTitle, setBroadcastTitle] = useState("");
  const [broadcastMessage, setBroadcastMessage] = useState("");

  useEffect(() => {
    apiRequest<any>("/admin-api/notifications/stats/")
      .then(setNotifStats)
      .catch(() => null)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Bell className="h-5 w-5 text-primary" />
        <h2 className="text-heading-3">Notification Center</h2>
      </div>

      <Card><CardContent className="p-5 space-y-4">
        <h3 className="text-body font-medium">Broadcast Notification</h3>
        <p className="text-caption text-muted-foreground">Send a notification to all active users.</p>
        <div className="space-y-3 max-w-lg">
          <Input
            value={broadcastTitle}
            onChange={(e) => setBroadcastTitle(e.target.value)}
            placeholder="Notification title"
            className="rounded-xl"
          />
          <Input
            value={broadcastMessage}
            onChange={(e) => setBroadcastMessage(e.target.value)}
            placeholder="Notification message"
            className="rounded-xl"
          />
          <Button
            disabled={!broadcastTitle.trim()}
            onClick={async () => {
              try {
                const res = await apiRequest<any>("/admin-api/notifications/broadcast/", {
                  method: "POST",
                  body: { title: broadcastTitle, body: broadcastMessage },
                });
                setBroadcastTitle("");
                setBroadcastMessage("");
                alert(`Broadcast sent to ${res?.sent_to ?? "all"} users`);
              } catch { alert("Failed to send broadcast"); }
            }}
          >
            <Send className="h-4 w-4 mr-1.5" /> Send Broadcast
          </Button>
        </div>
      </CardContent></Card>

      {notifStats && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {[
            { label: "Total Notifications", value: notifStats.total_notifications },
            { label: "Unread", value: notifStats.unread_count },
          ].map((s) => (
            <Card key={s.label}><CardContent className="p-5">
              <p className="text-caption text-muted-foreground">{s.label}</p>
              <p className="text-heading-2 mt-1">{s.value ?? "—"}</p>
            </CardContent></Card>
          ))}
        </div>
      )}

      {notifStats?.by_type && Object.keys(notifStats.by_type).length > 0 && (
        <Card><CardContent className="p-5">
          <h3 className="text-body font-medium mb-4">By Type</h3>
          <div className="space-y-2">
            {Object.entries(notifStats.by_type as Record<string, number>).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between py-2 border-b last:border-0">
                <span className="text-caption capitalize">{(type || "unknown").replace(/_/g, " ")}</span>
                <Badge variant="secondary">{String(count)}</Badge>
              </div>
            ))}
          </div>
        </CardContent></Card>
      )}

      <Card><CardContent className="p-5">
        <h3 className="text-body font-medium mb-4">Recent Notifications</h3>
        {loading ? (
          <div className="flex justify-center py-6"><Loader2 className="h-5 w-5 animate-spin text-muted-foreground" /></div>
        ) : notifStats?.recent_notifications?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-caption">
              <thead><tr className="border-b">
                <th className="text-start p-3 font-medium">User</th>
                <th className="text-start p-3 font-medium">Title</th>
                <th className="text-start p-3 font-medium">Type</th>
                <th className="text-start p-3 font-medium">Read</th>
                <th className="text-start p-3 font-medium">When</th>
              </tr></thead>
              <tbody>
                {notifStats.recent_notifications.map((n: any, i: number) => (
                  <tr key={n.id || i} className="border-b last:border-0">
                    <td className="p-3">{n.user_email}</td>
                    <td className="p-3 truncate max-w-[200px]">{n.title}</td>
                    <td className="p-3"><Badge variant="outline" className="text-[10px]">{n.type || "—"}</Badge></td>
                    <td className="p-3">{n.is_read ? "Yes" : "No"}</td>
                    <td className="p-3 text-muted-foreground whitespace-nowrap">
                      {n.created_at ? formatDistanceToNow(new Date(n.created_at), { addSuffix: true }) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-caption text-muted-foreground">No notifications yet</p>
        )}
      </CardContent></Card>
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

function CeleryBeatTab() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiRequest<any>("/admin-api/celery-beat/")
      .then(setData)
      .catch(() => null)
      .finally(() => setLoading(false));
  }, []);

  const handleToggle = async (taskId: number, enabled: boolean) => {
    try {
      await apiRequest<any>(`/admin-api/celery-beat/${taskId}/toggle/`, {
        method: "PATCH",
        body: { enabled },
      });
      setData((prev: any) => ({
        ...prev,
        tasks: prev.tasks.map((t: any) => t.id === taskId ? { ...t, enabled } : t),
      }));
    } catch {
      // ignore
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Zap className="h-5 w-5 text-primary" />
        <h2 className="text-heading-3">Automations (Celery Beat)</h2>
      </div>
      {data?.tasks?.length ? (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-start p-3 font-medium">Task</th>
                  <th className="text-start p-3 font-medium">Schedule</th>
                  <th className="text-start p-3 font-medium">Last Run</th>
                  <th className="text-start p-3 font-medium">Runs</th>
                  <th className="text-start p-3 font-medium">Enabled</th>
                </tr>
              </thead>
              <tbody>
                {data.tasks.map((task: any) => (
                  <tr key={task.id} className="border-b last:border-0">
                    <td className="p-3">
                      <p className="font-medium">{task.name}</p>
                      <p className="text-[10px] text-muted-foreground font-mono">{task.task}</p>
                    </td>
                    <td className="p-3 text-muted-foreground font-mono text-xs">{task.schedule}</td>
                    <td className="p-3 text-muted-foreground whitespace-nowrap">
                      {task.last_run_at ? formatDistanceToNow(new Date(task.last_run_at), { addSuffix: true }) : "Never"}
                    </td>
                    <td className="p-3 text-muted-foreground">{task.total_run_count}</td>
                    <td className="p-3">
                      <Switch checked={task.enabled} onCheckedChange={(v) => handleToggle(task.id, v)} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        <Card><CardContent className="p-8 text-center">
          <Zap className="h-8 w-8 text-muted-foreground/40 mx-auto mb-2" />
          <p className="text-body text-muted-foreground">No periodic tasks found</p>
        </CardContent></Card>
      )}
    </div>
  );
}

function AdminSearchTab() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (query.length < 2) return;
    setLoading(true);
    setSearched(true);
    try {
      const data = await apiRequest<any>(`/admin-api/search/?q=${encodeURIComponent(query)}`);
      setResults(data?.results || []);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Search className="h-5 w-5 text-primary" />
        <h2 className="text-heading-3">Global Search</h2>
      </div>
      <div className="flex gap-2 max-w-lg">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search users, companies, jobs..."
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          className="rounded-xl"
        />
        <Button onClick={handleSearch} disabled={loading || query.length < 2}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
        </Button>
      </div>
      {searched && (
        results.length ? (
          <div className="space-y-2">
            {results.map((r, i) => (
              <Card key={i}>
                <CardContent className="p-4 flex items-center gap-4">
                  <Badge variant="outline" className="capitalize">{r.type}</Badge>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{r.label}</p>
                    <p className="text-xs text-muted-foreground truncate">{r.detail}</p>
                  </div>
                  {r.role && <Badge variant="secondary" className="text-[10px]">{r.role}</Badge>}
                  {r.industry && <Badge variant="secondary" className="text-[10px]">{r.industry}</Badge>}
                  {r.status && <Badge variant="secondary" className="text-[10px]">{r.status}</Badge>}
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground">No results found for &quot;{query}&quot;</p>
        )
      )}
    </div>
  );
}

function PackagesTab() {
  const [plans, setPlans] = useState<any[]>([]);
  const [subscriptions, setSubscriptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiRequest<any>("/admin-api/plans/").catch(() => ({ results: [] })),
      apiRequest<any>("/admin-api/subscriptions/").catch(() => ({ results: [] })),
    ]).then(([p, s]) => {
      setPlans(p?.results || p || []);
      setSubscriptions(s?.results || s || []);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Package className="h-5 w-5 text-primary" />
        <h2 className="text-heading-3">Packages &amp; Entitlements</h2>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h3 className="text-body font-medium mb-3">Subscription Plans ({plans.length})</h3>
          {plans.length ? (
            <div className="space-y-2">
              {plans.map((plan: any) => (
                <Card key={plan.uuid}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{plan.name}</p>
                        <p className="text-xs text-muted-foreground">{plan.description || "No description"}</p>
                      </div>
                      <Badge variant={plan.is_active ? "default" : "secondary"}>
                        {plan.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </div>
                    <div className="flex gap-3 mt-2 text-xs text-muted-foreground">
                      <span>Jobs: {plan.job_posting_limit || "∞"}</span>
                      <span>Search: {plan.candidate_search_limit || "∞"}</span>
                      <span>AI: {plan.ai_features_enabled ? "Yes" : "No"}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card><CardContent className="p-6 text-center text-muted-foreground">No plans created yet</CardContent></Card>
          )}
        </div>
        <div>
          <h3 className="text-body font-medium mb-3">Company Subscriptions ({subscriptions.length})</h3>
          {subscriptions.length ? (
            <div className="space-y-2">
              {subscriptions.map((sub: any) => (
                <Card key={sub.uuid}>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{sub.company_name}</p>
                        <p className="text-xs text-muted-foreground">Plan: {sub.plan_name}</p>
                      </div>
                      <Badge variant={sub.status === "active" ? "default" : "secondary"} className="capitalize">
                        {sub.status}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card><CardContent className="p-6 text-center text-muted-foreground">No subscriptions yet</CardContent></Card>
          )}
        </div>
      </div>
    </div>
  );
}

function CopilotTab() {
  const [messages, setMessages] = useState<Array<{ role: "user" | "assistant"; content: string }>>([]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || isProcessing) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setIsProcessing(true);

    try {
      const data = await apiRequest<any>("/admin-api/copilot/chat/", {
        method: "POST",
        body: { message: text },
      });
      setMessages((prev) => [...prev, { role: "assistant", content: data?.response || "No response." }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, the copilot is unavailable right now." }]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <MessageSquare className="h-5 w-5 text-primary" />
        <h2 className="text-heading-3">Admin Copilot</h2>
        <Badge variant="secondary" className="text-[10px]">AI-powered</Badge>
      </div>
      <Card className="flex flex-col" style={{ height: "60vh" }}>
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-3">
          {messages.length === 0 && (
            <div className="text-center text-muted-foreground py-12">
              <MessageSquare className="h-10 w-10 mx-auto mb-3 text-muted-foreground/30" />
              <p className="text-body font-medium">Ask about platform health, scraping status, AI costs, or verification anomalies.</p>
              <p className="text-caption mt-1">The copilot has read-only access to admin data. It cannot modify anything directly.</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] rounded-xl px-4 py-2.5 text-sm whitespace-pre-wrap ${
                msg.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-card border"
              }`}>
                {msg.content}
              </div>
            </div>
          ))}
          {isProcessing && (
            <div className="flex justify-start">
              <div className="bg-card border rounded-xl px-4 py-2.5">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </CardContent>
        <div className="border-t p-3 flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the copilot..."
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
            disabled={isProcessing}
            className="rounded-xl"
          />
          <Button onClick={sendMessage} disabled={isProcessing || !input.trim()} size="icon" className="shrink-0">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </Card>
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
        { icon: Bot, label: "Rasheed", tab: "rashid" as AdminTab },
        { icon: Mic, label: "Interviews", tab: "interviews" as AdminTab },
        { icon: MessageSquare, label: "Copilot", tab: "copilot" as AdminTab },
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

          {/* ADMIN MANAGEMENT TABS */}
          {activeTab === "users" && <UsersTab />}
          {activeTab === "companies" && <CompaniesTab />}
          {activeTab === "talent" && <TalentTab />}
          {activeTab === "verification" && <VerificationTab />}
          {activeTab === "matching" && <MatchingTab />}
          {activeTab === "rashid" && <RashidTab />}
          {activeTab === "interviews" && <InterviewsTab />}
          {activeTab === "automations" && <CeleryBeatTab />}
          {activeTab === "notifications" && <NotificationsTab />}
          {activeTab === "packages" && <PackagesTab />}
          {activeTab === "search-admin" && <AdminSearchTab />}
          {activeTab === "copilot" && <CopilotTab />}
        </div>
      </main>
    </div>
  );
}
