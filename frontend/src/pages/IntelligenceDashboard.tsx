import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Brain, TrendingUp, TrendingDown, Activity, MapPin, Building2,
  BarChart3, Target, Lightbulb, ArrowLeft, Loader2, Globe
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollReveal, StaggerContainer, StaggerItem } from "@/components/motion";
import { intelligenceApi } from "@/services/intelligence";
import { usePageMeta } from "@/hooks/use-seo";
import { getAccessToken } from "@/services/client";

export default function IntelligenceDashboard() {
  usePageMeta({ title: "Intelligence Dashboard" });

  const [health, setHealth] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [emerging, setEmerging] = useState<any[]>([]);
  const [declining, setDeclining] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      intelligenceApi.getHealth().catch(() => null),
      intelligenceApi.getEmergingSkills(30).catch(() => []),
      intelligenceApi.getDecliningSkills(30).catch(() => []),
      fetch("/api/v1/intelligence/admin/metrics/", {
        headers: { Authorization: `Bearer ${getAccessToken()}` },
      }).then(r => r.ok ? r.json() : null).catch(() => null),
    ]).then(([h, em, dec, m]) => {
      setHealth(h);
      setEmerging(em || []);
      setDeclining(dec || []);
      setMetrics(m);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="container max-w-7xl mx-auto px-4 py-8 space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/admin">
            <Button variant="ghost" size="icon"><ArrowLeft className="h-5 w-5" /></Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Brain className="h-6 w-6 text-primary" />
              Intelligence Dashboard
            </h1>
            <p className="text-sm text-muted-foreground">Platform intelligence, trends, and market insights</p>
          </div>
        </div>
      </div>

      {/* Service Health */}
      {health && (
        <ScrollReveal>
          <Card>
            <CardHeader><CardTitle className="text-base flex items-center gap-2"><Activity className="h-4 w-4" /> Service Health</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="flex items-center gap-2">
                  <div className={`h-2.5 w-2.5 rounded-full ${health.ai_service?.available ? "bg-green-500" : "bg-red-500"}`} />
                  <span className="text-sm">AI Service</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className={`h-2.5 w-2.5 rounded-full ${health.circuit_breaker?.available ? "bg-green-500" : "bg-yellow-500"}`} />
                  <span className="text-sm">Circuit Breaker: {health.circuit_breaker?.state}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className={`h-2.5 w-2.5 rounded-full ${health.document_processor?.available ? "bg-green-500" : "bg-gray-400"}`} />
                  <span className="text-sm">Doc Processor: {health.document_processor?.backend || "N/A"}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className={`h-2.5 w-2.5 rounded-full ${health.trend_detection?.available ? "bg-green-500" : "bg-gray-400"}`} />
                  <span className="text-sm">Trend Detection</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </ScrollReveal>
      )}

      {/* Platform Metrics */}
      {metrics && (
        <StaggerContainer className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StaggerItem>
            <Card>
              <CardContent className="p-5 text-center">
                <BarChart3 className="h-5 w-5 mx-auto mb-2 text-primary" />
                <p className="text-2xl font-bold">{metrics.total_jobs?.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground">Active Jobs</p>
                <Badge variant="secondary" className="mt-1 text-xs">+{metrics.jobs_added_7d} this week</Badge>
              </CardContent>
            </Card>
          </StaggerItem>
          <StaggerItem>
            <Card>
              <CardContent className="p-5 text-center">
                <Building2 className="h-5 w-5 mx-auto mb-2 text-primary" />
                <p className="text-2xl font-bold">{metrics.total_companies?.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground">Companies</p>
                <Badge variant="secondary" className="mt-1 text-xs">+{metrics.new_companies_30d} this month</Badge>
              </CardContent>
            </Card>
          </StaggerItem>
          <StaggerItem>
            <Card>
              <CardContent className="p-5 text-center">
                <Globe className="h-5 w-5 mx-auto mb-2 text-primary" />
                <p className="text-2xl font-bold">{metrics.total_users?.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground">Active Users</p>
                <Badge variant="secondary" className="mt-1 text-xs">+{metrics.new_users_30d} this month</Badge>
              </CardContent>
            </Card>
          </StaggerItem>
          <StaggerItem>
            <Card>
              <CardContent className="p-5 text-center">
                <TrendingUp className="h-5 w-5 mx-auto mb-2 text-green-600" />
                <p className="text-2xl font-bold">{metrics.job_growth_rate}%</p>
                <p className="text-xs text-muted-foreground">Job Growth Rate</p>
                <Badge variant="secondary" className="mt-1 text-xs">vs last month</Badge>
              </CardContent>
            </Card>
          </StaggerItem>
        </StaggerContainer>
      )}

      {/* Skill Trends */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ScrollReveal>
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-green-600" /> Emerging Skills
              </CardTitle>
            </CardHeader>
            <CardContent>
              {emerging.length === 0 ? (
                <p className="text-sm text-muted-foreground">No trend data available yet. Run trend detection first.</p>
              ) : (
                <div className="space-y-2">
                  {emerging.slice(0, 10).map((skill, i) => (
                    <div key={i} className="flex items-center justify-between py-1.5 border-b last:border-0">
                      <span className="text-sm font-medium">{skill.skill}</span>
                      <Badge variant="default" className="bg-green-100 text-green-800 text-xs">
                        +{skill.growth_pct?.toFixed(0)}%
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </ScrollReveal>

        <ScrollReveal>
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingDown className="h-4 w-4 text-red-500" /> Declining Skills
              </CardTitle>
            </CardHeader>
            <CardContent>
              {declining.length === 0 ? (
                <p className="text-sm text-muted-foreground">No decline data available yet.</p>
              ) : (
                <div className="space-y-2">
                  {declining.slice(0, 10).map((skill, i) => (
                    <div key={i} className="flex items-center justify-between py-1.5 border-b last:border-0">
                      <span className="text-sm font-medium">{skill.skill}</span>
                      <Badge variant="destructive" className="text-xs">
                        -{skill.decline_pct?.toFixed(0)}%
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </ScrollReveal>
      </div>
    </div>
  );
}
