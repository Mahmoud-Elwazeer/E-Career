import { useQuery } from "@tanstack/react-query";
import { Users, ExternalLink, Loader2, UserCheck, UserMinus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getInsiderConnections } from "@/services/phase5";

interface InsiderConnectionsCardProps {
  companyId: number;
  companyName: string;
  isAr?: boolean;
}

export function InsiderConnectionsCard({ companyId, companyName, isAr }: InsiderConnectionsCardProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["insider-connections", companyId],
    queryFn: () => getInsiderConnections(companyId),
    staleTime: 10 * 60 * 1000,
    enabled: !!companyId,
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-5 flex items-center justify-center py-8">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (error || !data || data.total_connections === 0) return null;

  return (
    <Card className="border-info/30 bg-info/5">
      <CardContent className="p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="h-10 w-10 rounded-full bg-info/15 flex items-center justify-center">
            <Users className="h-5 w-5 text-info" />
          </div>
          <div>
            <h3 className="text-body font-semibold text-foreground">
              {isAr ? "اتصالات داخلية" : "Insider Connections"}
            </h3>
            <p className="text-caption text-muted-foreground">
              {data.total_connections} {isAr ? "جهة اتصال في" : "contacts at"} {companyName}
            </p>
          </div>
        </div>

        {data.ecareer_connections.length > 0 && (
          <div className="space-y-2.5 mb-3">
            {data.ecareer_connections.slice(0, 4).map((conn) => (
              <div key={conn.user_id} className="flex items-center gap-2.5">
                <div className="h-8 w-8 rounded-full bg-info/15 flex items-center justify-center shrink-0">
                  {conn.connection_type === "current_employee" ? (
                    <UserCheck className="h-4 w-4 text-info" />
                  ) : (
                    <UserMinus className="h-4 w-4 text-muted-foreground" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-caption font-medium truncate">{conn.name}</p>
                  <p className="text-caption text-muted-foreground truncate">
                    {conn.current_role || (isAr ? "مستخدم E-Career" : "E-Career user")}
                  </p>
                </div>
                <Badge
                  variant="outline"
                  className="text-[10px] shrink-0 rounded-lg"
                >
                  {conn.connection_type === "current_employee"
                    ? (isAr ? "حالي" : "Current")
                    : (isAr ? "سابق" : "Former")}
                </Badge>
              </div>
            ))}
          </div>
        )}

        {data.github_contributors.length > 0 && (
          <div className="border-t pt-3 space-y-2">
            <p className="text-caption font-medium text-muted-foreground">
              {isAr ? "مساهمون على GitHub" : "GitHub Contributors"}
            </p>
            <div className="flex flex-wrap gap-2">
              {data.github_contributors.slice(0, 5).map((g) => (
                <a
                  key={g.username}
                  href={g.profile_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 px-2 py-1 bg-muted rounded-lg text-caption hover:bg-muted/80 transition-colors"
                >
                  {g.avatar_url && (
                    <img src={g.avatar_url} alt="" className="h-4 w-4 rounded-full" loading="lazy" />
                  )}
                  <span>@{g.username}</span>
                  <ExternalLink className="h-3 w-3 text-muted-foreground" />
                </a>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
