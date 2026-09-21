import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Briefcase,
  Clock,
  CheckCircle2,
  XCircle,
  Mail,
  Calendar,
  Building2,
  MapPin,
  Filter,
  Search
} from "lucide-react";
import { Layout } from "@/components/Layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useTheme } from "@/hooks/use-theme";
import { apiRequest } from "@/services/client";
import { formatDistanceToNow } from "date-fns";
import { ApplicationCardSkeleton, StatCardSkeleton } from "@/components/Skeletons";
import { EmptyStates } from "@/components/EmptyState";

interface Application {
  id: string;
  job: {
    id: string;
    title: string;
    company: {
      name: string;
      logo: string;
    };
    location: string;
  };
  status: "pending" | "reviewing" | "interview" | "rejected" | "accepted";
  applied_at: string;
  last_updated: string;
}

const STATUS_CONFIG = {
  pending: { label: "Pending", icon: Clock, color: "text-warning-foreground bg-warning/10 border-warning/30" },
  reviewing: { label: "Under Review", icon: Mail, color: "text-info bg-info/10 border-info/30" },
  interview: { label: "Interview", icon: Calendar, color: "text-primary bg-primary/10 border-primary/30" },
  rejected: { label: "Rejected", icon: XCircle, color: "text-destructive bg-destructive/10 border-destructive/30" },
  accepted: { label: "Accepted", icon: CheckCircle2, color: "text-success bg-success/10 border-success/30" },
};

export default function Applications() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const { data: applications = [], isLoading, isError, refetch } = useQuery({
    queryKey: ["applications"],
    queryFn: async () => {
      // Real endpoint is /users/me/applications/ (DRF-paginated). The old
      // /applications/ path 404'd and silently rendered an empty list.
      const res = await apiRequest<Application[] | { results: Application[] }>(
        "/users/me/applications/"
      );
      return Array.isArray(res) ? res : res?.results ?? [];
    },
  });

  const filteredApplications = applications.filter((app) => {
    const matchesSearch = app.job.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         app.job.company.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || app.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const stats = {
    total: applications.length,
    pending: applications.filter(a => a.status === "pending").length,
    reviewing: applications.filter(a => a.status === "reviewing").length,
    interview: applications.filter(a => a.status === "interview").length,
  };

  return (
    <Layout>
      <div className="container max-w-6xl py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-heading-1 mb-2">
            {isAr ? "طلباتي" : "My Applications"}
          </h1>
          <p className="text-muted-foreground">
            {isAr ? "تتبع حالة طلبات التوظيف" : "Track your job application status"}
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {isLoading ? (
            <>
              <StatCardSkeleton />
              <StatCardSkeleton />
              <StatCardSkeleton />
              <StatCardSkeleton />
            </>
          ) : (
            <>
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-caption text-muted-foreground mb-1">
                        {isAr ? "الإجمالي" : "Total"}
                      </p>
                      <p className="text-2xl font-bold">{stats.total}</p>
                    </div>
                    <Briefcase className="h-8 w-8 text-primary" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-caption text-muted-foreground mb-1">
                        {isAr ? "قيد الانتظار" : "Pending"}
                      </p>
                      <p className="text-2xl font-bold">{stats.pending}</p>
                    </div>
                    <Clock className="h-8 w-8 text-warning-foreground" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-caption text-muted-foreground mb-1">
                        {isAr ? "قيد المراجعة" : "Reviewing"}
                      </p>
                      <p className="text-2xl font-bold">{stats.reviewing}</p>
                    </div>
                    <Mail className="h-8 w-8 text-primary" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-caption text-muted-foreground mb-1">
                        {isAr ? "مقابلات" : "Interviews"}
                      </p>
                      <p className="text-2xl font-bold">{stats.interview}</p>
                    </div>
                    <Calendar className="h-8 w-8 text-primary" />
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={isAr ? "ابحث عن وظيفة أو شركة..." : "Search job or company..."}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>

              <div className="flex gap-2">
                <Button
                  variant={statusFilter === "all" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setStatusFilter("all")}
                >
                  {isAr ? "الكل" : "All"}
                </Button>
                <Button
                  variant={statusFilter === "pending" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setStatusFilter("pending")}
                >
                  {isAr ? "قيد الانتظار" : "Pending"}
                </Button>
                <Button
                  variant={statusFilter === "interview" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setStatusFilter("interview")}
                >
                  {isAr ? "مقابلات" : "Interviews"}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Applications List */}
        <div className="space-y-4">
          {isLoading ? (
            <>
              <ApplicationCardSkeleton />
              <ApplicationCardSkeleton />
              <ApplicationCardSkeleton />
            </>
          ) : isError ? (
            <Card>
              <CardContent className="py-12 text-center">
                <XCircle className="h-10 w-10 text-destructive mx-auto mb-3" />
                <p className="font-medium mb-1">
                  {isAr ? "تعذر تحميل الطلبات" : "Couldn't load your applications"}
                </p>
                <p className="text-sm text-muted-foreground mb-4">
                  {isAr
                    ? "حدث خطأ أثناء جلب البيانات. حاول مرة أخرى."
                    : "Something went wrong fetching your data. Please try again."}
                </p>
                <Button variant="outline" size="sm" onClick={() => refetch()}>
                  {isAr ? "إعادة المحاولة" : "Retry"}
                </Button>
              </CardContent>
            </Card>
          ) : filteredApplications.length === 0 ? (
            <EmptyStates.NoApplications />
          ) : (
            filteredApplications.map((app, idx) => {
              const statusInfo = STATUS_CONFIG[app.status];
              const StatusIcon = statusInfo.icon;

              return (
                <motion.div
                  key={app.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                >
                  <Card className="hover:shadow-md transition-shadow cursor-pointer">
                    <CardContent className="p-6">
                      <div className="flex items-start gap-4">
                        {/* Company Logo */}
                        <div className="flex-shrink-0">
                          {app.job.company.logo ? (
                            <img
                              src={app.job.company.logo}
                              alt={app.job.company.name}
                              className="w-12 h-12 rounded-lg object-cover border"
                            />
                          ) : (
                            <div className="w-12 h-12 rounded-lg bg-muted flex items-center justify-center border">
                              <Building2 className="h-6 w-6 text-muted-foreground" />
                            </div>
                          )}
                        </div>

                        {/* Application Info */}
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-lg mb-1 truncate">
                            {app.job.title}
                          </h3>
                          <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground mb-3">
                            <div className="flex items-center gap-1">
                              <Building2 className="h-4 w-4" />
                              <span>{app.job.company.name}</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <MapPin className="h-4 w-4" />
                              <span>{app.job.location}</span>
                            </div>
                          </div>

                          <div className="flex flex-wrap items-center gap-3">
                            <Badge className={statusInfo.color}>
                              <StatusIcon className="h-3 w-3 mr-1" />
                              {isAr ? statusInfo.label : statusInfo.label}
                            </Badge>
                            <span className="text-caption text-muted-foreground">
                              {isAr ? "تم التقديم" : "Applied"} {formatDistanceToNow(new Date(app.applied_at), { addSuffix: true })}
                            </span>
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex-shrink-0">
                          <Button
                            variant="outline"
                            size="sm"
                            asChild
                          >
                            <a href={`/app/jobs/${app.job.id}`}>
                              {isAr ? "عرض" : "View"}
                            </a>
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })
          )}
        </div>
      </div>
    </Layout>
  );
}
