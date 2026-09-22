import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Upload, User, GraduationCap, Code, Settings as SettingsIcon, FileText,
  CheckCircle, AlertCircle, Loader2, RotateCcw, X, Briefcase, Plus,
} from "lucide-react";
import profileApi, { type UserProfile } from "@/services/profile";
import { AppShell } from "@/components/shells/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useTheme } from "@/hooks/use-theme";
import { useToast } from "@/hooks/use-toast";

const MAX_CV_BYTES = 10 * 1024 * 1024; // 10MB
const CV_ACCEPT = ".pdf,.doc,.docx,.txt";
const CV_MIME = [
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
];

export default function ProfilePage() {
  const { lang } = useTheme();
  const isAr = lang === "ar";
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [dragActive, setDragActive] = useState(false);

  const {
    data: profile,
    isLoading,
    isError,
    refetch,
  } = useQuery({ queryKey: ["profile"], queryFn: profileApi.getProfile });

  const { data: completion } = useQuery({
    queryKey: ["profile-completion"],
    queryFn: profileApi.getCompletion,
  });

  const uploadMutation = useMutation({
    mutationFn: profileApi.uploadCV,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["profile-completion"] });
      toast({
        title: isAr ? "تم الرفع" : "Uploaded",
        description: isAr ? "تم رفع سيرتك الذاتية وجارٍ تحليلها." : "Your CV was uploaded and is being parsed.",
      });
    },
    onError: () => {
      toast({
        title: isAr ? "فشل الرفع" : "Upload failed",
        description: isAr ? "تعذّر رفع السيرة الذاتية. حاول مرة أخرى." : "Couldn't upload your CV. Please try again.",
        variant: "destructive",
      });
    },
  });

  const validateAndUpload = (file: File) => {
    if (!CV_MIME.includes(file.type)) {
      toast({
        title: isAr ? "نوع ملف غير مدعوم" : "Unsupported file type",
        description: isAr ? "الصيغ المدعومة: PDF, DOC, DOCX, TXT." : "Supported formats: PDF, DOC, DOCX, TXT.",
        variant: "destructive",
      });
      return;
    }
    if (file.size > MAX_CV_BYTES) {
      toast({
        title: isAr ? "الملف كبير جداً" : "File too large",
        description: isAr ? "الحد الأقصى لحجم الملف هو 10 ميغابايت." : "Maximum file size is 10MB.",
        variant: "destructive",
      });
      return;
    }
    uploadMutation.mutate(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) validateAndUpload(e.dataTransfer.files[0]);
  };

  if (isLoading) {
    return (
      <AppShell>
        <div className="page-shell flex items-center justify-center py-24" role="status" aria-live="polite">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="sr-only">{isAr ? "جاري التحميل" : "Loading"}</span>
        </div>
      </AppShell>
    );
  }

  if (isError || !profile) {
    return (
      <AppShell>
        <div className="page-shell flex flex-col items-center justify-center py-24 text-center">
          <div className="rounded-full bg-destructive/10 p-3 mb-4">
            <AlertCircle className="h-6 w-6 text-destructive" />
          </div>
          <h2 className="text-heading-2 mb-1">{isAr ? "تعذّر تحميل الملف الشخصي" : "Couldn't load your profile"}</h2>
          <p className="text-body text-muted-foreground mb-4 max-w-sm">
            {isAr ? "حدثت مشكلة أثناء جلب بياناتك. حاول مرة أخرى." : "Something went wrong loading your data. Please try again."}
          </p>
          <Button onClick={() => refetch()} className="gap-2">
            <RotateCcw className="h-4 w-4" />
            {isAr ? "إعادة المحاولة" : "Try again"}
          </Button>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="page-shell max-w-5xl">
        <PageHeader
          title={isAr ? "ملفك الشخصي" : "Your Profile"}
          subtitle={isAr ? "أكمل ملفك للحصول على توافق أفضل مع الوظائف" : "Complete your profile to get better job matches"}
        />

        {completion && (
          <Card className="mb-6">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-heading-3">{isAr ? "اكتمال الملف" : "Profile Completion"}</h2>
                <span className={`text-heading-2 font-semibold ${completion.total_score >= 60 ? "text-success" : "text-warning-foreground"}`}>
                  {completion.total_score}%
                </span>
              </div>
              <Progress value={completion.total_score} className="mb-4" />
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {Object.entries(completion.sections).map(([key, section]) => (
                  <div key={key} className="flex items-center gap-2">
                    {section.complete ? (
                      <CheckCircle className="w-4 h-4 text-success shrink-0" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-muted-foreground/40 shrink-0" />
                    )}
                    <span className={`text-caption ${section.complete ? "text-foreground" : "text-muted-foreground"}`}>
                      {section.label}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        <Tabs defaultValue="overview">
          <TabsList className="grid w-full grid-cols-2 sm:grid-cols-4">
            <TabsTrigger value="overview" className="gap-2"><User className="h-4 w-4" />{isAr ? "نظرة عامة" : "Overview"}</TabsTrigger>
            <TabsTrigger value="cv" className="gap-2"><Upload className="h-4 w-4" />{isAr ? "السيرة الذاتية" : "CV Upload"}</TabsTrigger>
            <TabsTrigger value="skills" className="gap-2"><Code className="h-4 w-4" />{isAr ? "المهارات" : "Skills"}</TabsTrigger>
            <TabsTrigger value="preferences" className="gap-2"><SettingsIcon className="h-4 w-4" />{isAr ? "التفضيلات" : "Preferences"}</TabsTrigger>
          </TabsList>

          <Card className="mt-4">
            <CardContent className="p-6">
              <TabsContent value="overview" className="mt-0"><OverviewTab profile={profile} isAr={isAr} /></TabsContent>
              <TabsContent value="cv" className="mt-0">
                <CVUploadTab
                  profile={profile}
                  isAr={isAr}
                  dragActive={dragActive}
                  uploading={uploadMutation.isPending}
                  onDrag={handleDrag}
                  onDrop={handleDrop}
                  onFileSelect={(e) => e.target.files?.[0] && validateAndUpload(e.target.files[0])}
                />
              </TabsContent>
              <TabsContent value="skills" className="mt-0"><SkillsTab profile={profile} isAr={isAr} /></TabsContent>
              <TabsContent value="preferences" className="mt-0"><PreferencesTab profile={profile} isAr={isAr} /></TabsContent>
            </CardContent>
          </Card>
        </Tabs>
      </div>
    </AppShell>
  );
}

function OverviewTab({ profile, isAr }: { profile: UserProfile; isAr: boolean }) {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="section-heading">{isAr ? "المعلومات الأساسية" : "Basic Information"}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label={isAr ? "البريد الإلكتروني" : "Email"} value={profile.email} />
          <Field label={isAr ? "الاسم الكامل" : "Full Name"} value={profile.full_name || (isAr ? "غير محدد" : "Not set")} />
          <Field label={isAr ? "الدور الحالي" : "Current Role"} value={profile.current_role || (isAr ? "غير مكتشف" : "Not detected")} />
          <Field
            label={isAr ? "الخبرة" : "Experience"}
            value={profile.experience_years > 0 ? `${profile.experience_years.toFixed(1)} ${isAr ? "سنة" : "years"}` : (isAr ? "غير مكتشف" : "Not detected")}
          />
        </div>
      </div>

      <div>
        <h3 className="section-heading">{isAr ? "المهارات" : "Skills"} ({profile.skills?.length || 0})</h3>
        <div className="flex flex-wrap gap-2">
          {profile.skills?.slice(0, 12).map((skill, i) => (
            <Badge key={i} variant="secondary">{skill}</Badge>
          ))}
          {profile.skills?.length > 12 && (
            <Badge variant="outline">+{profile.skills.length - 12} {isAr ? "أخرى" : "more"}</Badge>
          )}
        </div>
      </div>

      {profile.education?.length > 0 && (
        <div>
          <h3 className="section-heading">{isAr ? "التعليم" : "Education"}</h3>
          <div className="space-y-3">
            {profile.education.map((edu, i) => (
              <div key={i} className="flex items-start gap-3">
                <GraduationCap className="w-5 h-5 text-muted-foreground mt-0.5 shrink-0" />
                <div>
                  <p className="text-body font-medium text-foreground">{edu.degree}</p>
                  <p className="text-caption text-muted-foreground">{edu.institution}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <Label className="text-caption text-muted-foreground">{label}</Label>
      <p className="mt-1 text-body text-foreground">{value}</p>
    </div>
  );
}

interface CVUploadTabProps {
  profile: UserProfile;
  isAr: boolean;
  dragActive: boolean;
  uploading: boolean;
  onDrag: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

function CVUploadTab({ profile, isAr, dragActive, uploading, onDrag, onDrop, onFileSelect }: CVUploadTabProps) {
  return (
    <div className="space-y-6">
      {profile.cv_file && (
        <div className="rounded-lg border border-success/30 bg-success/10 p-4">
          <div className="flex items-center gap-3">
            <FileText className="w-8 h-8 text-success shrink-0" />
            <div>
              <p className="text-body font-medium text-foreground">{isAr ? "تم رفع السيرة الذاتية" : "CV Uploaded"}</p>
              {profile.cv_uploaded_at && (
                <p className="text-caption text-muted-foreground">
                  {isAr ? "بتاريخ " : "Uploaded on "}{new Date(profile.cv_uploaded_at).toLocaleDateString()}
                </p>
              )}
              <p className="text-caption text-muted-foreground mt-0.5">
                {isAr ? "الحالة: " : "Status: "}{profile.cv_parse_status}
              </p>
            </div>
          </div>
        </div>
      )}

      <div
        className={`rounded-xl border-2 border-dashed p-12 text-center transition-colors ${
          dragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/40"
        }`}
        onDragEnter={onDrag}
        onDragLeave={onDrag}
        onDragOver={onDrag}
        onDrop={onDrop}
      >
        <Upload className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
        <p className="text-body-lg font-medium text-foreground mb-1">
          {isAr ? "اسحب وأفلت سيرتك الذاتية هنا" : "Drag and drop your CV here"}
        </p>
        <p className="text-body text-muted-foreground mb-4">{isAr ? "أو انقر للتصفح" : "or click to browse"}</p>
        <input type="file" accept={CV_ACCEPT} onChange={onFileSelect} className="hidden" id="cv-upload" disabled={uploading} />
        <Button asChild disabled={uploading}>
          <label htmlFor="cv-upload" className="cursor-pointer">
            {uploading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {uploading ? (isAr ? "جارٍ الرفع..." : "Uploading...") : (isAr ? "تصفّح الملفات" : "Browse Files")}
          </label>
        </Button>
        <p className="text-caption text-muted-foreground mt-4">
          {isAr ? "الصيغ المدعومة: PDF, DOC, DOCX, TXT (حد أقصى 10 ميغابايت)" : "Supported: PDF, DOC, DOCX, TXT (max 10MB)"}
        </p>
      </div>
    </div>
  );
}

function SkillsTab({ profile, isAr }: { profile: UserProfile; isAr: boolean }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [skills, setSkills] = useState<string[]>(profile.skills || []);
  const [newSkill, setNewSkill] = useState("");

  // Keep in sync if the profile reloads with new data.
  useEffect(() => {
    setSkills(profile.skills || []);
  }, [profile.skills]);

  const mutation = useMutation({
    mutationFn: () => profileApi.updateSkills(skills),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      toast({ title: isAr ? "تم الحفظ" : "Saved", description: isAr ? "تم تحديث مهاراتك." : "Your skills were updated." });
    },
    onError: () => toast({ title: isAr ? "خطأ" : "Error", description: isAr ? "فشل الحفظ." : "Failed to save.", variant: "destructive" }),
  });

  const addSkill = () => {
    const v = newSkill.trim();
    if (v && !skills.includes(v)) setSkills([...skills, v]);
    setNewSkill("");
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="section-heading">{isAr ? "مهاراتك" : "Your Skills"}</h3>
        <p className="text-body text-muted-foreground -mt-2 mb-4">
          {isAr ? "أضف أو أزل المهارات لتحسين التوافق" : "Add or remove skills to improve job matching"}
        </p>
      </div>

      <div className="flex gap-2">
        <Input
          value={newSkill}
          onChange={(e) => setNewSkill(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addSkill()}
          placeholder={isAr ? "أضف مهارة..." : "Add a skill..."}
        />
        <Button onClick={addSkill} variant="outline" className="gap-1 shrink-0">
          <Plus className="h-4 w-4" /> {isAr ? "إضافة" : "Add"}
        </Button>
      </div>

      <div className="flex flex-wrap gap-2">
        {skills.map((skill, i) => (
          <Badge key={i} variant="secondary" className="gap-1 pe-1">
            {skill}
            <button
              onClick={() => setSkills(skills.filter((s) => s !== skill))}
              className="ms-1 rounded-full hover:bg-foreground/10 p-0.5"
              aria-label={`${isAr ? "إزالة" : "Remove"} ${skill}`}
            >
              <X className="h-3 w-3" />
            </button>
          </Badge>
        ))}
      </div>

      <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
        {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {isAr ? "حفظ المهارات" : "Save Skills"}
      </Button>
    </div>
  );
}

function PreferencesTab({ profile, isAr }: { profile: UserProfile; isAr: boolean }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [prefs, setPrefs] = useState({
    desired_roles: profile.desired_roles || [],
    desired_locations: profile.desired_locations || [],
    open_to_remote: profile.open_to_remote ?? true,
    min_salary: profile.min_salary ?? null,
    salary_currency: profile.salary_currency || "USD",
  });
  const [newRole, setNewRole] = useState("");
  const [newLocation, setNewLocation] = useState("");

  useEffect(() => {
    setPrefs({
      desired_roles: profile.desired_roles || [],
      desired_locations: profile.desired_locations || [],
      open_to_remote: profile.open_to_remote ?? true,
      min_salary: profile.min_salary ?? null,
      salary_currency: profile.salary_currency || "USD",
    });
  }, [profile]);

  const mutation = useMutation({
    mutationFn: () => profileApi.updatePreferences(prefs),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      toast({ title: isAr ? "تم الحفظ" : "Saved", description: isAr ? "تم تحديث تفضيلاتك." : "Your preferences were updated." });
    },
    onError: () => toast({ title: isAr ? "خطأ" : "Error", description: isAr ? "فشل الحفظ." : "Failed to save.", variant: "destructive" }),
  });

  return (
    <div className="space-y-8">
      <TokenChipInput
        title={isAr ? "الأدوار المرغوبة" : "Desired Roles"}
        placeholder={isAr ? "مثال: مهندس برمجيات..." : "e.g., Software Engineer..."}
        value={newRole}
        setValue={setNewRole}
        items={prefs.desired_roles}
        onAdd={(v) => setPrefs({ ...prefs, desired_roles: [...prefs.desired_roles, v] })}
        onRemove={(i) => setPrefs({ ...prefs, desired_roles: prefs.desired_roles.filter((_, x) => x !== i) })}
        icon={Briefcase}
        addLabel={isAr ? "إضافة" : "Add"}
      />
      <TokenChipInput
        title={isAr ? "المواقع المرغوبة" : "Desired Locations"}
        placeholder={isAr ? "مثال: القاهرة، عن بعد..." : "e.g., Cairo, Remote..."}
        value={newLocation}
        setValue={setNewLocation}
        items={prefs.desired_locations}
        onAdd={(v) => setPrefs({ ...prefs, desired_locations: [...prefs.desired_locations, v] })}
        onRemove={(i) => setPrefs({ ...prefs, desired_locations: prefs.desired_locations.filter((_, x) => x !== i) })}
        addLabel={isAr ? "إضافة" : "Add"}
      />

      {/* Minimum salary — was a silent dead field (held in state, no input). */}
      <div className="space-y-2">
        <Label>{isAr ? "الحد الأدنى للراتب المتوقع" : "Minimum expected salary"}</Label>
        <div className="flex gap-2 max-w-sm">
          <Input
            type="number"
            min={0}
            inputMode="numeric"
            value={prefs.min_salary ?? ""}
            onChange={(e) =>
              setPrefs({ ...prefs, min_salary: e.target.value === "" ? null : Number(e.target.value) })
            }
            placeholder={isAr ? "مثال: 5000" : "e.g., 5000"}
            className="flex-1"
          />
          <select
            value={prefs.salary_currency}
            onChange={(e) => setPrefs({ ...prefs, salary_currency: e.target.value })}
            className="rounded-md border border-input bg-background px-3 text-body focus:outline-none focus:ring-2 focus:ring-ring"
            aria-label={isAr ? "العملة" : "Currency"}
          >
            {["USD", "EUR", "GBP", "EGP", "SAR", "AED"].map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
        <p className="text-caption text-muted-foreground">
          {isAr ? "يُستخدم لتصفية التوصيات ومطابقة الوظائف." : "Used to filter recommendations and match jobs."}
        </p>
      </div>

      <div className="flex items-center justify-between max-w-sm rounded-lg border border-border p-3">
        <span className="text-body text-foreground">{isAr ? "منفتح على العمل عن بعد" : "Open to remote work"}</span>
        <Switch
          checked={prefs.open_to_remote}
          onCheckedChange={(v) => setPrefs({ ...prefs, open_to_remote: v })}
          aria-label={isAr ? "منفتح على العمل عن بعد" : "Open to remote work"}
        />
      </div>

      <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
        {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {isAr ? "حفظ التفضيلات" : "Save Preferences"}
      </Button>
    </div>
  );
}

interface TokenChipInputProps {
  title: string;
  placeholder: string;
  value: string;
  setValue: (v: string) => void;
  items: string[];
  onAdd: (v: string) => void;
  onRemove: (i: number) => void;
  icon?: typeof Briefcase;
  addLabel: string;
}

function TokenChipInput({ title, placeholder, value, setValue, items, onAdd, onRemove, icon: Icon, addLabel }: TokenChipInputProps) {
  const add = () => {
    const v = value.trim();
    if (v && !items.includes(v)) onAdd(v);
    setValue("");
  };
  return (
    <div>
      <h3 className="section-heading">{title}</h3>
      <div className="flex gap-2 mb-4">
        <Input value={value} onChange={(e) => setValue(e.target.value)} onKeyDown={(e) => e.key === "Enter" && add()} placeholder={placeholder} />
        <Button onClick={add} variant="outline" className="gap-1 shrink-0"><Plus className="h-4 w-4" /> {addLabel}</Button>
      </div>
      <div className="flex flex-wrap gap-2">
        {items.map((item, i) => (
          <Badge key={i} variant="secondary" className="gap-1 pe-1">
            {Icon && <Icon className="h-3.5 w-3.5" />}
            {item}
            <button onClick={() => onRemove(i)} className="ms-1 rounded-full hover:bg-foreground/10 p-0.5" aria-label={`Remove ${item}`}>
              <X className="h-3 w-3" />
            </button>
          </Badge>
        ))}
      </div>
    </div>
  );
}
