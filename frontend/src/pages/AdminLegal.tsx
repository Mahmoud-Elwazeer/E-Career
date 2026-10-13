/**
 * Admin Legal Control Plane — policy versions, retention matrix, jurisdiction
 * profiles, cookie categories, DSR queue, and the legal-entity singleton.
 * Admin-gated route (RequireAdmin). Every mutation here is already audited by
 * the underlying model (PolicyVersion history, PrivacyRequestEvent, etc.) —
 * no separate audit UI needed, mirroring the Financial Control Center.
 */
import { useEffect, useState } from "react";
import { Loader2, FileText, Clock, Globe2, Cookie, Inbox, Building2, RefreshCw, Server } from "lucide-react";
import { AppShell } from "@/components/shells/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import {
  adminListPolicyVersions, adminTransitionPolicyVersion,
  adminListRetention, adminUpdateRetention,
  adminListJurisdictions, adminListCookieCategories,
  adminListDsrQueue, adminTransitionDsr,
  adminGetLegalEntity, adminUpdateLegalEntity, adminListProcessors,
  type PolicyVersion, type RetentionPolicyRow, type JurisdictionProfile,
  type CookieCategoryDef, type PrivacyRequest, type LegalEntityPublic,
  type ProcessorRecordRow,
} from "@/services/legal";

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    active: "success", approved: "info", draft: "secondary", in_review: "warning",
    scheduled: "soft", retired: "outline", completed: "success", rejected: "destructive",
    open: "soft", in_review_dsr: "warning",
  };
  return <Badge variant={(map[status] as any) || "outline"}>{status}</Badge>;
}

function VersionsPanel() {
  const [versions, setVersions] = useState<PolicyVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  const load = () => {
    setLoading(true);
    adminListPolicyVersions().then(setVersions).catch(() => {}).finally(() => setLoading(false));
  };
  useEffect(load, []);

  const transition = async (uuid: string, status: string) => {
    try {
      await adminTransitionPolicyVersion(uuid, status);
      toast({ title: "Updated" });
      load();
    } catch (e: any) {
      toast({ title: "Error", description: e?.message, variant: "destructive" });
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-5 w-5 animate-spin" /></div>;

  return (
    <div className="space-y-3">
      {versions.map((v) => (
        <Card key={v.uuid}>
          <CardContent className="flex flex-wrap items-center justify-between gap-3 p-4">
            <div>
              <p className="font-medium">{v.document_slug} v{v.version_label} <span className="text-caption text-muted-foreground">({v.locale}/{v.jurisdiction})</span></p>
              <div className="mt-1 flex items-center gap-2">
                <StatusBadge status={v.status} />
                {v.material_change && <Badge variant="warning">material change</Badge>}
              </div>
            </div>
            <div className="flex gap-2">
              {v.status === "draft" && <Button size="sm" onClick={() => transition(v.uuid, "in_review")}>Send to review</Button>}
              {v.status === "in_review" && <Button size="sm" onClick={() => transition(v.uuid, "approved")}>Approve</Button>}
              {(v.status === "approved" || v.status === "scheduled") && (
                <Button size="sm" onClick={() => transition(v.uuid, "active")}>Activate</Button>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
      {versions.length === 0 && <p className="text-body text-muted-foreground">No policy versions yet. Run the seed_legal command.</p>}
    </div>
  );
}

function RetentionPanel() {
  const [rows, setRows] = useState<RetentionPolicyRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<Record<string, string>>({});
  const { toast } = useToast();

  const load = () => {
    setLoading(true);
    adminListRetention().then(setRows).catch(() => {}).finally(() => setLoading(false));
  };
  useEffect(load, []);

  const save = async (row: RetentionPolicyRow) => {
    const raw = editing[row.uuid];
    const days = raw === undefined || raw === "" ? null : Number(raw);
    try {
      await adminUpdateRetention(row.uuid, { retention_period_days: days });
      toast({ title: "Saved" });
      load();
    } catch (e: any) {
      toast({ title: "Error", description: e?.message, variant: "destructive" });
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-5 w-5 animate-spin" /></div>;

  return (
    <div className="space-y-3">
      {rows.map((r) => (
        <Card key={r.uuid}>
          <CardContent className="flex flex-wrap items-center justify-between gap-3 p-4">
            <div className="min-w-0 flex-1">
              <p className="font-medium">{r.data_category}</p>
              <p className="text-caption text-muted-foreground">{r.description}</p>
              {r.requires_legal_review && !r.retention_period_days && (
                <Badge variant="warning" className="mt-1">REQUIRES LEGAL REVIEW</Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Input
                type="number" placeholder="days" className="w-24"
                defaultValue={r.retention_period_days ?? ""}
                onChange={(e) => setEditing((p) => ({ ...p, [r.uuid]: e.target.value }))}
              />
              <Button size="sm" onClick={() => save(r)}>Save</Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function JurisdictionsPanel() {
  const [rows, setRows] = useState<JurisdictionProfile[]>([]);
  useEffect(() => { adminListJurisdictions().then(setRows).catch(() => {}); }, []);
  return (
    <div className="space-y-3">
      {rows.map((j) => (
        <Card key={j.uuid}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <p className="font-medium">{j.jurisdiction} — {j.regulator_name}</p>
              {j.requires_legal_review && <Badge variant="warning">REQUIRES LEGAL REVIEW</Badge>}
            </div>
            <p className="text-caption text-muted-foreground mt-1">{j.law_name}</p>
            <div className="mt-2 flex gap-4 text-caption text-muted-foreground">
              <span>DSR SLA: {j.dsr_sla_days ?? "—"} days</span>
              <span>Breach notice: {j.breach_notification_hours ?? "—"}h</span>
              <span>Minor age: {j.minor_age_threshold ?? "unconfirmed"}</span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function CookieCategoriesPanel() {
  const [rows, setRows] = useState<CookieCategoryDef[]>([]);
  useEffect(() => { adminListCookieCategories().then(setRows).catch(() => {}); }, []);
  return (
    <div className="space-y-3">
      {rows.map((c) => (
        <Card key={c.uuid}>
          <CardContent className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium">{c.label}</p>
              <p className="text-caption text-muted-foreground">{c.description}</p>
            </div>
            {c.is_essential && <Badge variant="soft">always on</Badge>}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function DsrQueuePanel() {
  const [rows, setRows] = useState<PrivacyRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  const load = () => {
    setLoading(true);
    adminListDsrQueue().then(setRows).catch(() => {}).finally(() => setLoading(false));
  };
  useEffect(load, []);

  const transition = async (uuid: string, status: string) => {
    try {
      await adminTransitionDsr(uuid, status);
      toast({ title: "Updated" });
      load();
    } catch (e: any) {
      toast({ title: "Error", description: e?.message, variant: "destructive" });
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-5 w-5 animate-spin" /></div>;

  return (
    <div className="space-y-3">
      {rows.map((r) => (
        <Card key={r.uuid}>
          <CardContent className="flex flex-wrap items-center justify-between gap-3 p-4">
            <div>
              <p className="font-medium">{r.request_type} <span className="text-caption text-muted-foreground">({r.jurisdiction})</span></p>
              <div className="mt-1 flex items-center gap-2">
                <StatusBadge status={r.status} />
                {r.due_at && <span className="text-caption text-muted-foreground">due {new Date(r.due_at).toLocaleDateString()}</span>}
              </div>
              {r.details && <p className="text-caption text-muted-foreground mt-1 max-w-md">{r.details}</p>}
            </div>
            <div className="flex gap-2">
              {r.status === "open" && <Button size="sm" onClick={() => transition(r.uuid, "in_review")}>Start review</Button>}
              {r.status !== "completed" && r.status !== "rejected" && (
                <Button size="sm" onClick={() => transition(r.uuid, "completed")}>Mark completed</Button>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
      {rows.length === 0 && <p className="text-body text-muted-foreground">No open privacy requests.</p>}
    </div>
  );
}

function ProcessorsPanel() {
  const [rows, setRows] = useState<ProcessorRecordRow[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    adminListProcessors().then(setRows).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-5 w-5 animate-spin" /></div>;

  return (
    <div className="space-y-3">
      <p className="text-caption text-muted-foreground">
        Sub-processors confirmed by actual code/infrastructure only — never added on assumption.
        DPA status shows "unconfirmed" until legal verifies it; it is never defaulted to signed or unsigned.
      </p>
      {rows.map((p) => (
        <Card key={p.uuid}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <p className="font-medium">{p.name}</p>
              <Badge variant={p.dpa_signed === true ? "success" : p.dpa_signed === false ? "destructive" : "warning"}>
                DPA: {p.dpa_signed === true ? "signed" : p.dpa_signed === false ? "not signed" : "unconfirmed"}
              </Badge>
            </div>
            <p className="text-caption text-muted-foreground mt-1">{p.purpose}</p>
            <p className="text-caption text-muted-foreground mt-1">Data: {p.data_categories}</p>
            {p.country && <p className="text-caption text-muted-foreground">Location: {p.country}</p>}
          </CardContent>
        </Card>
      ))}
      {rows.length === 0 && <p className="text-body text-muted-foreground">No processors seeded yet. Run the seed_legal command.</p>}
    </div>
  );
}

function LegalEntityPanel() {
  const [entity, setEntity] = useState<LegalEntityPublic | null>(null);
  const [saving, setSaving] = useState(false);
  const { toast } = useToast();

  useEffect(() => { adminGetLegalEntity().then(setEntity).catch(() => {}); }, []);

  const save = async () => {
    if (!entity) return;
    setSaving(true);
    try {
      const updated = await adminUpdateLegalEntity(entity);
      setEntity(updated);
      toast({ title: "Saved" });
    } catch (e: any) {
      toast({ title: "Error", description: e?.message, variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  if (!entity) return <div className="flex justify-center py-12"><Loader2 className="h-5 w-5 animate-spin" /></div>;

  const field = (key: keyof LegalEntityPublic, label: string) => (
    <div>
      <Label>{label}</Label>
      <Input
        className="mt-1"
        value={(entity[key] as string) ?? ""}
        onChange={(e) => setEntity({ ...entity, [key]: e.target.value } as LegalEntityPublic)}
      />
    </div>
  );

  return (
    <Card>
      <CardContent className="space-y-4 p-6">
        {!entity.is_configured && (
          <Badge variant="warning">REQUIRES LEGAL REVIEW / CONFIGURATION — not yet set</Badge>
        )}
        <div className="grid gap-4 sm:grid-cols-2">
          {field("legal_entity_name", "Legal entity name")}
          {field("tax_or_registration_id", "Tax / registration ID")}
          {field("dpo_name", "DPO name")}
          {field("dpo_email", "DPO email")}
          {field("privacy_contact_email", "Privacy contact email")}
          {field("support_contact_email", "Support contact email")}
        </div>
        <div>
          <Label>Registered address</Label>
          <Input className="mt-1" value={entity.registered_address} onChange={(e) => setEntity({ ...entity, registered_address: e.target.value })} />
        </div>
        <div className="max-w-xs">
          <Label>Default refund window (days)</Label>
          <Input
            type="number" className="mt-1"
            value={entity.default_refund_window_days ?? ""}
            onChange={(e) => setEntity({ ...entity, default_refund_window_days: e.target.value ? Number(e.target.value) : null })}
          />
        </div>
        <Button onClick={save} disabled={saving}>{saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Save</Button>
      </CardContent>
    </Card>
  );
}

export default function AdminLegal() {
  return (
    <AppShell>
      <PageHeader title="Legal Control Plane" subtitle="Policy versions, consent config, retention matrix, DSR queue, and legal entity settings." />
      <Tabs defaultValue="versions" className="mt-6">
        <TabsList className="flex-wrap h-auto">
          <TabsTrigger value="versions" className="gap-1.5"><FileText className="h-3.5 w-3.5" />Policy versions</TabsTrigger>
          <TabsTrigger value="retention" className="gap-1.5"><Clock className="h-3.5 w-3.5" />Retention matrix</TabsTrigger>
          <TabsTrigger value="jurisdictions" className="gap-1.5"><Globe2 className="h-3.5 w-3.5" />Jurisdictions</TabsTrigger>
          <TabsTrigger value="cookies" className="gap-1.5"><Cookie className="h-3.5 w-3.5" />Cookie categories</TabsTrigger>
          <TabsTrigger value="dsr" className="gap-1.5"><Inbox className="h-3.5 w-3.5" />DSR queue</TabsTrigger>
          <TabsTrigger value="processors" className="gap-1.5"><Server className="h-3.5 w-3.5" />Processors</TabsTrigger>
          <TabsTrigger value="entity" className="gap-1.5"><Building2 className="h-3.5 w-3.5" />Legal entity</TabsTrigger>
        </TabsList>
        <TabsContent value="versions"><VersionsPanel /></TabsContent>
        <TabsContent value="retention"><RetentionPanel /></TabsContent>
        <TabsContent value="jurisdictions"><JurisdictionsPanel /></TabsContent>
        <TabsContent value="cookies"><CookieCategoriesPanel /></TabsContent>
        <TabsContent value="dsr"><DsrQueuePanel /></TabsContent>
        <TabsContent value="processors"><ProcessorsPanel /></TabsContent>
        <TabsContent value="entity"><LegalEntityPanel /></TabsContent>
      </Tabs>
    </AppShell>
  );
}
