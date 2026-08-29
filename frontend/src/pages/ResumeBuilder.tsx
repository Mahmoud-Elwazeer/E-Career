import { useState, useEffect, useCallback, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import {
  Loader2, Save, Download, Plus, Trash2, FileUp, GripVertical,
  User, Briefcase, GraduationCap, Wrench, FolderOpen, Award, Globe, Eye
} from 'lucide-react';
import ResumePreview from '@/components/resume/ResumePreview';

import { getAccessToken } from '@/services/client';

const API_BASE = '/api/v1/resume';

function getAuthHeaders() {
  const token = getAccessToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function apiFetch(url: string, options: RequestInit = {}) {
  const res = await fetch(url, { ...options, headers: { ...getAuthHeaders(), ...options.headers } });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

interface Experience {
  id: string;
  company: string;
  title: string;
  start_date: string;
  end_date: string;
  current: boolean;
  description: string;
}

interface Education {
  id: string;
  school: string;
  degree: string;
  field?: string;
  start_date: string;
  end_date: string;
  current: boolean;
  gpa?: string;
}

interface Project {
  id: string;
  name: string;
  description: string;
  url?: string;
  technologies?: string[];
}

interface PersonalInfo {
  full_name: string;
  email: string;
  phone: string;
  location: string;
  linkedin?: string;
  github?: string;
  website?: string;
}

interface Resume {
  id: string;
  title: string;
  template?: { id: string; title: string; category: string } | null;
  personal_info: PersonalInfo;
  summary: string;
  experience: Experience[];
  education: Education[];
  skills: string[];
  projects: Project[];
  certifications: string[];
  languages: string[];
  interests: string[];
  is_public: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}


function generateId() {
  return crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2);
}

export default function ResumeBuilder() {
  const queryClient = useQueryClient();
  const previewRef = useRef<HTMLDivElement>(null);

  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(null);
  const [localData, setLocalData] = useState<Resume | null>(null);
  const [activeTab, setActiveTab] = useState('personal');
  const [selectedTemplate, setSelectedTemplate] = useState('modern');
  const [autoSaveTimer, setAutoSaveTimer] = useState<NodeJS.Timeout | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);

  const { data: resumesRes, isLoading: resumesLoading } = useQuery({
    queryKey: ['user-resumes'],
    queryFn: () => apiFetch(`${API_BASE}/resumes/`),
  });

  const resumes: Resume[] = resumesRes?.data || [];

  const createMutation = useMutation({
    mutationFn: (data: Partial<Resume>) =>
      apiFetch(`${API_BASE}/resumes/`, { method: 'POST', body: JSON.stringify(data) }),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['user-resumes'] });
      if (res?.data?.id) {
        setSelectedResumeId(res.data.id);
        setLocalData(res.data);
      }
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Resume> }) =>
      apiFetch(`${API_BASE}/resumes/${id}/`, { method: 'PUT', body: JSON.stringify(data) }),
    onSuccess: () => {
      setIsSaving(false);
      setLastSaved(new Date());
      queryClient.invalidateQueries({ queryKey: ['user-resumes'] });
    },
    onError: () => setIsSaving(false),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`${API_BASE}/resumes/${id}/delete/`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-resumes'] });
      setSelectedResumeId(null);
      setLocalData(null);
    },
  });

  const exportMutation = useMutation({
    mutationFn: ({ resumeId, format }: { resumeId: string; format: string }) =>
      apiFetch(`${API_BASE}/export/`, { method: 'POST', body: JSON.stringify({ resume_id: resumeId, format }) }),
  });

  // Select first resume on load
  useEffect(() => {
    if (resumes.length > 0 && !selectedResumeId) {
      setSelectedResumeId(resumes[0].id);
      setLocalData(resumes[0]);
    }
  }, [resumes, selectedResumeId]);

  // Sync selected resume
  useEffect(() => {
    if (selectedResumeId && resumes.length > 0) {
      const found = resumes.find(r => r.id === selectedResumeId);
      if (found && !localData) setLocalData(found);
    }
  }, [selectedResumeId, resumes, localData]);

  // Auto-save with debounce
  const scheduleAutoSave = useCallback((data: Resume) => {
    if (autoSaveTimer) clearTimeout(autoSaveTimer);
    const timer = setTimeout(() => {
      if (data.id) {
        setIsSaving(true);
        updateMutation.mutate({ id: data.id, data });
      }
    }, 1500);
    setAutoSaveTimer(timer);
  }, [autoSaveTimer, updateMutation]);

  const updateField = useCallback(<K extends keyof Resume>(field: K, value: Resume[K]) => {
    setLocalData(prev => {
      if (!prev) return prev;
      const updated = { ...prev, [field]: value };
      scheduleAutoSave(updated);
      return updated;
    });
  }, [scheduleAutoSave]);

  const handleCreate = () => {
    createMutation.mutate({
      title: 'Untitled Resume',
      personal_info: { full_name: '', email: '', phone: '', location: '' },
      summary: '',
      experience: [],
      education: [],
      skills: [],
      projects: [],
      certifications: [],
      languages: [],
      interests: [],
      is_public: false,
    });
  };

  const handleImportFromCV = async () => {
    try {
      const res = await apiFetch('/api/v1/career/cv/status/');
      if (res?.data?.cv_parsed_data) {
        const parsed = res.data.cv_parsed_data;
        setLocalData(prev => {
          if (!prev) return prev;
          const updated = {
            ...prev,
            personal_info: {
              full_name: parsed.name || prev.personal_info.full_name,
              email: parsed.email || prev.personal_info.email,
              phone: parsed.phone || prev.personal_info.phone,
              location: parsed.location || prev.personal_info.location,
              linkedin: parsed.linkedin || prev.personal_info.linkedin,
              github: parsed.github || prev.personal_info.github,
            },
            summary: parsed.summary || prev.summary,
            experience: parsed.experience?.map((e: any) => ({
              id: generateId(),
              company: e.company || '',
              title: e.title || e.position || '',
              start_date: e.start_date || '',
              end_date: e.end_date || '',
              current: e.current || false,
              description: e.description || '',
            })) || prev.experience,
            education: parsed.education?.map((e: any) => ({
              id: generateId(),
              school: e.school || e.institution || '',
              degree: e.degree || '',
              field: e.field || e.major || '',
              start_date: e.start_date || '',
              end_date: e.end_date || '',
              current: false,
              gpa: e.gpa || '',
            })) || prev.education,
            skills: parsed.skills || prev.skills,
            languages: parsed.languages || prev.languages,
            certifications: parsed.certifications || prev.certifications,
          };
          scheduleAutoSave(updated);
          return updated;
        });
      }
    } catch {
      // CV not parsed yet
    }
  };

  if (resumesLoading) {
    return (
      <div className="flex items-center justify-center min-h-[80vh]">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b bg-background">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold">Resume Builder</h1>
          {localData && (
            <Input
              value={localData.title}
              onChange={(e) => updateField('title', e.target.value)}
              className="w-48 h-8 text-sm"
            />
          )}
          {isSaving && <span className="text-xs text-muted-foreground">Saving...</span>}
          {!isSaving && lastSaved && (
            <span className="text-xs text-muted-foreground">
              Saved {lastSaved.toLocaleTimeString()}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleImportFromCV} title="Import from uploaded CV">
            <FileUp className="w-4 h-4 mr-1" />
            Import CV
          </Button>
          <Select value={selectedTemplate} onValueChange={setSelectedTemplate}>
            <SelectTrigger className="w-32 h-8">
              <SelectValue placeholder="Template" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="modern">Modern</SelectItem>
              <SelectItem value="professional">Professional</SelectItem>
              <SelectItem value="creative">Creative</SelectItem>
              <SelectItem value="minimalist">Minimalist</SelectItem>
            </SelectContent>
          </Select>
          {localData && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={() => exportMutation.mutate({ resumeId: localData.id, format: 'pdf' })}
                disabled={exportMutation.isPending}
              >
                <Download className="w-4 h-4 mr-1" />
                PDF
              </Button>
              <Button
                size="sm"
                onClick={() => {
                  setIsSaving(true);
                  updateMutation.mutate({ id: localData.id, data: localData });
                }}
                disabled={isSaving}
              >
                <Save className="w-4 h-4 mr-1" />
                Save
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Main content */}
      <ResizablePanelGroup direction="horizontal" className="flex-1">
        {/* Left: Resume list + Editor */}
        <ResizablePanel defaultSize={55} minSize={35}>
          <div className="h-full flex">
            {/* Resume list sidebar */}
            <div className="w-48 border-r bg-muted/30 flex flex-col">
              <div className="p-2 border-b">
                <Button size="sm" className="w-full" onClick={handleCreate} disabled={createMutation.isPending}>
                  <Plus className="w-3 h-3 mr-1" />
                  New
                </Button>
              </div>
              <ScrollArea className="flex-1">
                <div className="p-2 space-y-1">
                  {resumes.map((r) => (
                    <div
                      key={r.id}
                      onClick={() => { setSelectedResumeId(r.id); setLocalData(r); }}
                      className={`p-2 rounded text-xs cursor-pointer transition-colors ${
                        selectedResumeId === r.id
                          ? 'bg-primary/10 text-primary font-medium'
                          : 'hover:bg-muted'
                      }`}
                    >
                      <p className="truncate">{r.title || 'Untitled'}</p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">
                        {new Date(r.updated_at).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>

            {/* Editor */}
            <div className="flex-1 overflow-hidden">
              {localData ? (
                <ScrollArea className="h-full">
                  <div className="p-4">
                    <Tabs value={activeTab} onValueChange={setActiveTab}>
                      <TabsList className="grid grid-cols-7 mb-4">
                        <TabsTrigger value="personal" className="text-xs"><User className="w-3 h-3" /></TabsTrigger>
                        <TabsTrigger value="experience" className="text-xs"><Briefcase className="w-3 h-3" /></TabsTrigger>
                        <TabsTrigger value="education" className="text-xs"><GraduationCap className="w-3 h-3" /></TabsTrigger>
                        <TabsTrigger value="skills" className="text-xs"><Wrench className="w-3 h-3" /></TabsTrigger>
                        <TabsTrigger value="projects" className="text-xs"><FolderOpen className="w-3 h-3" /></TabsTrigger>
                        <TabsTrigger value="certs" className="text-xs"><Award className="w-3 h-3" /></TabsTrigger>
                        <TabsTrigger value="languages" className="text-xs"><Globe className="w-3 h-3" /></TabsTrigger>
                      </TabsList>

                      {/* Personal Info */}
                      <TabsContent value="personal" className="space-y-3">
                        <h3 className="font-medium text-sm">Personal Information</h3>
                        <Input
                          placeholder="Full Name"
                          value={localData.personal_info.full_name}
                          onChange={(e) => updateField('personal_info', { ...localData.personal_info, full_name: e.target.value })}
                        />
                        <div className="grid grid-cols-2 gap-3">
                          <Input
                            placeholder="Email"
                            type="email"
                            value={localData.personal_info.email}
                            onChange={(e) => updateField('personal_info', { ...localData.personal_info, email: e.target.value })}
                          />
                          <Input
                            placeholder="Phone"
                            value={localData.personal_info.phone}
                            onChange={(e) => updateField('personal_info', { ...localData.personal_info, phone: e.target.value })}
                          />
                        </div>
                        <Input
                          placeholder="Location (e.g. Cairo, Egypt)"
                          value={localData.personal_info.location}
                          onChange={(e) => updateField('personal_info', { ...localData.personal_info, location: e.target.value })}
                        />
                        <div className="grid grid-cols-2 gap-3">
                          <Input
                            placeholder="LinkedIn URL"
                            value={localData.personal_info.linkedin || ''}
                            onChange={(e) => updateField('personal_info', { ...localData.personal_info, linkedin: e.target.value })}
                          />
                          <Input
                            placeholder="GitHub URL"
                            value={localData.personal_info.github || ''}
                            onChange={(e) => updateField('personal_info', { ...localData.personal_info, github: e.target.value })}
                          />
                        </div>
                        <Input
                          placeholder="Website/Portfolio URL"
                          value={localData.personal_info.website || ''}
                          onChange={(e) => updateField('personal_info', { ...localData.personal_info, website: e.target.value })}
                        />
                        <Separator />
                        <h3 className="font-medium text-sm">Professional Summary</h3>
                        <Textarea
                          placeholder="A brief summary of your professional background and goals..."
                          value={localData.summary}
                          onChange={(e) => updateField('summary', e.target.value)}
                          className="min-h-[100px]"
                        />
                      </TabsContent>

                      {/* Experience */}
                      <TabsContent value="experience" className="space-y-3">
                        <div className="flex items-center justify-between">
                          <h3 className="font-medium text-sm">Work Experience</h3>
                          <Button size="sm" variant="outline" onClick={() => {
                            const newExp: Experience = {
                              id: generateId(), company: '', title: '',
                              start_date: '', end_date: '', current: false, description: ''
                            };
                            updateField('experience', [...localData.experience, newExp]);
                          }}>
                            <Plus className="w-3 h-3 mr-1" /> Add
                          </Button>
                        </div>
                        {localData.experience.map((exp, idx) => (
                          <Card key={exp.id} className="p-3">
                            <div className="flex items-start gap-2">
                              <GripVertical className="w-4 h-4 mt-2 text-muted-foreground cursor-grab" />
                              <div className="flex-1 space-y-2">
                                <div className="grid grid-cols-2 gap-2">
                                  <Input
                                    placeholder="Job Title"
                                    value={exp.title}
                                    onChange={(e) => {
                                      const updated = [...localData.experience];
                                      updated[idx] = { ...exp, title: e.target.value };
                                      updateField('experience', updated);
                                    }}
                                  />
                                  <Input
                                    placeholder="Company"
                                    value={exp.company}
                                    onChange={(e) => {
                                      const updated = [...localData.experience];
                                      updated[idx] = { ...exp, company: e.target.value };
                                      updateField('experience', updated);
                                    }}
                                  />
                                </div>
                                <div className="grid grid-cols-3 gap-2 items-center">
                                  <Input
                                    type="month"
                                    value={exp.start_date}
                                    onChange={(e) => {
                                      const updated = [...localData.experience];
                                      updated[idx] = { ...exp, start_date: e.target.value };
                                      updateField('experience', updated);
                                    }}
                                  />
                                  <Input
                                    type="month"
                                    value={exp.end_date}
                                    disabled={exp.current}
                                    onChange={(e) => {
                                      const updated = [...localData.experience];
                                      updated[idx] = { ...exp, end_date: e.target.value };
                                      updateField('experience', updated);
                                    }}
                                  />
                                  <label className="flex items-center gap-1.5 text-xs">
                                    <Switch
                                      checked={exp.current}
                                      onCheckedChange={(checked) => {
                                        const updated = [...localData.experience];
                                        updated[idx] = { ...exp, current: checked, end_date: checked ? '' : exp.end_date };
                                        updateField('experience', updated);
                                      }}
                                    />
                                    Current
                                  </label>
                                </div>
                                <Textarea
                                  placeholder="Describe your responsibilities and achievements..."
                                  value={exp.description}
                                  onChange={(e) => {
                                    const updated = [...localData.experience];
                                    updated[idx] = { ...exp, description: e.target.value };
                                    updateField('experience', updated);
                                  }}
                                  className="min-h-[60px] text-sm"
                                />
                              </div>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-destructive"
                                onClick={() => {
                                  updateField('experience', localData.experience.filter((_, i) => i !== idx));
                                }}
                              >
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            </div>
                          </Card>
                        ))}
                        {localData.experience.length === 0 && (
                          <p className="text-sm text-muted-foreground text-center py-8">
                            No experience entries yet. Click "Add" to create one.
                          </p>
                        )}
                      </TabsContent>

                      {/* Education */}
                      <TabsContent value="education" className="space-y-3">
                        <div className="flex items-center justify-between">
                          <h3 className="font-medium text-sm">Education</h3>
                          <Button size="sm" variant="outline" onClick={() => {
                            const newEdu: Education = {
                              id: generateId(), school: '', degree: '', field: '',
                              start_date: '', end_date: '', current: false, gpa: ''
                            };
                            updateField('education', [...localData.education, newEdu]);
                          }}>
                            <Plus className="w-3 h-3 mr-1" /> Add
                          </Button>
                        </div>
                        {localData.education.map((edu, idx) => (
                          <Card key={edu.id} className="p-3">
                            <div className="flex items-start gap-2">
                              <GripVertical className="w-4 h-4 mt-2 text-muted-foreground cursor-grab" />
                              <div className="flex-1 space-y-2">
                                <Input
                                  placeholder="School / University"
                                  value={edu.school}
                                  onChange={(e) => {
                                    const updated = [...localData.education];
                                    updated[idx] = { ...edu, school: e.target.value };
                                    updateField('education', updated);
                                  }}
                                />
                                <div className="grid grid-cols-2 gap-2">
                                  <Input
                                    placeholder="Degree (e.g. BSc, MSc)"
                                    value={edu.degree}
                                    onChange={(e) => {
                                      const updated = [...localData.education];
                                      updated[idx] = { ...edu, degree: e.target.value };
                                      updateField('education', updated);
                                    }}
                                  />
                                  <Input
                                    placeholder="Field of Study"
                                    value={edu.field || ''}
                                    onChange={(e) => {
                                      const updated = [...localData.education];
                                      updated[idx] = { ...edu, field: e.target.value };
                                      updateField('education', updated);
                                    }}
                                  />
                                </div>
                                <div className="grid grid-cols-3 gap-2 items-center">
                                  <Input
                                    type="month"
                                    value={edu.start_date}
                                    onChange={(e) => {
                                      const updated = [...localData.education];
                                      updated[idx] = { ...edu, start_date: e.target.value };
                                      updateField('education', updated);
                                    }}
                                  />
                                  <Input
                                    type="month"
                                    value={edu.end_date}
                                    disabled={edu.current}
                                    onChange={(e) => {
                                      const updated = [...localData.education];
                                      updated[idx] = { ...edu, end_date: e.target.value };
                                      updateField('education', updated);
                                    }}
                                  />
                                  <Input
                                    placeholder="GPA"
                                    value={edu.gpa || ''}
                                    onChange={(e) => {
                                      const updated = [...localData.education];
                                      updated[idx] = { ...edu, gpa: e.target.value };
                                      updateField('education', updated);
                                    }}
                                  />
                                </div>
                              </div>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-destructive"
                                onClick={() => {
                                  updateField('education', localData.education.filter((_, i) => i !== idx));
                                }}
                              >
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            </div>
                          </Card>
                        ))}
                        {localData.education.length === 0 && (
                          <p className="text-sm text-muted-foreground text-center py-8">
                            No education entries yet. Click "Add" to create one.
                          </p>
                        )}
                      </TabsContent>

                      {/* Skills */}
                      <TabsContent value="skills" className="space-y-3">
                        <h3 className="font-medium text-sm">Skills</h3>
                        <p className="text-xs text-muted-foreground">Type a skill and press Enter to add it.</p>
                        <SkillsInput
                          skills={localData.skills}
                          onChange={(skills) => updateField('skills', skills)}
                        />
                      </TabsContent>

                      {/* Projects */}
                      <TabsContent value="projects" className="space-y-3">
                        <div className="flex items-center justify-between">
                          <h3 className="font-medium text-sm">Projects</h3>
                          <Button size="sm" variant="outline" onClick={() => {
                            const newProj: Project = { id: generateId(), name: '', description: '', url: '', technologies: [] };
                            updateField('projects', [...localData.projects, newProj]);
                          }}>
                            <Plus className="w-3 h-3 mr-1" /> Add
                          </Button>
                        </div>
                        {localData.projects.map((proj, idx) => (
                          <Card key={proj.id} className="p-3">
                            <div className="flex items-start gap-2">
                              <div className="flex-1 space-y-2">
                                <div className="grid grid-cols-2 gap-2">
                                  <Input
                                    placeholder="Project Name"
                                    value={proj.name}
                                    onChange={(e) => {
                                      const updated = [...localData.projects];
                                      updated[idx] = { ...proj, name: e.target.value };
                                      updateField('projects', updated);
                                    }}
                                  />
                                  <Input
                                    placeholder="URL (optional)"
                                    value={proj.url || ''}
                                    onChange={(e) => {
                                      const updated = [...localData.projects];
                                      updated[idx] = { ...proj, url: e.target.value };
                                      updateField('projects', updated);
                                    }}
                                  />
                                </div>
                                <Textarea
                                  placeholder="Project description..."
                                  value={proj.description}
                                  onChange={(e) => {
                                    const updated = [...localData.projects];
                                    updated[idx] = { ...proj, description: e.target.value };
                                    updateField('projects', updated);
                                  }}
                                  className="min-h-[50px] text-sm"
                                />
                                <Input
                                  placeholder="Technologies (comma-separated)"
                                  value={proj.technologies?.join(', ') || ''}
                                  onChange={(e) => {
                                    const updated = [...localData.projects];
                                    updated[idx] = { ...proj, technologies: e.target.value.split(',').map(s => s.trim()).filter(Boolean) };
                                    updateField('projects', updated);
                                  }}
                                />
                              </div>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 text-destructive"
                                onClick={() => {
                                  updateField('projects', localData.projects.filter((_, i) => i !== idx));
                                }}
                              >
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            </div>
                          </Card>
                        ))}
                        {localData.projects.length === 0 && (
                          <p className="text-sm text-muted-foreground text-center py-8">
                            No projects yet. Click "Add" to showcase your work.
                          </p>
                        )}
                      </TabsContent>

                      {/* Certifications */}
                      <TabsContent value="certs" className="space-y-3">
                        <h3 className="font-medium text-sm">Certifications</h3>
                        <TagInput
                          items={localData.certifications}
                          onChange={(certs) => updateField('certifications', certs)}
                          placeholder="Add certification (press Enter)"
                        />
                      </TabsContent>

                      {/* Languages */}
                      <TabsContent value="languages" className="space-y-3">
                        <h3 className="font-medium text-sm">Languages</h3>
                        <TagInput
                          items={localData.languages}
                          onChange={(langs) => updateField('languages', langs)}
                          placeholder="Add language (press Enter)"
                        />
                      </TabsContent>
                    </Tabs>

                    {/* Delete resume */}
                    <Separator className="my-6" />
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Eye className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm">Public</span>
                        <Switch
                          checked={localData.is_public}
                          onCheckedChange={(checked) => updateField('is_public', checked)}
                        />
                      </div>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => { if (confirm('Delete this resume?')) deleteMutation.mutate(localData.id); }}
                      >
                        <Trash2 className="w-3 h-3 mr-1" /> Delete Resume
                      </Button>
                    </div>
                  </div>
                </ScrollArea>
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  <div className="text-center">
                    <p>Select a resume or create a new one</p>
                    <Button className="mt-4" onClick={handleCreate}>
                      <Plus className="w-4 h-4 mr-2" /> Create Resume
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* Right: Live Preview */}
        <ResizablePanel defaultSize={45} minSize={30}>
          <ScrollArea className="h-full bg-muted/20">
            <div className="p-4">
              {localData ? (
                <ResumePreview ref={previewRef} data={localData} template={selectedTemplate} />
              ) : (
                <div className="flex items-center justify-center h-96 text-muted-foreground">
                  Preview will appear here
                </div>
              )}
            </div>
          </ScrollArea>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}

function SkillsInput({ skills, onChange }: { skills: string[]; onChange: (s: string[]) => void }) {
  const [input, setInput] = useState('');

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && input.trim()) {
      e.preventDefault();
      if (!skills.includes(input.trim())) {
        onChange([...skills, input.trim()]);
      }
      setInput('');
    }
  };

  return (
    <div className="space-y-2">
      <Input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type skill and press Enter..."
      />
      <div className="flex flex-wrap gap-1.5">
        {skills.map((skill, i) => (
          <Badge key={i} variant="secondary" className="gap-1">
            {skill}
            <button
              onClick={() => onChange(skills.filter((_, idx) => idx !== i))}
              className="ml-1 hover:text-destructive"
            >
              &times;
            </button>
          </Badge>
        ))}
      </div>
    </div>
  );
}

function TagInput({ items, onChange, placeholder }: { items: string[]; onChange: (s: string[]) => void; placeholder: string }) {
  const [input, setInput] = useState('');

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && input.trim()) {
      e.preventDefault();
      if (!items.includes(input.trim())) {
        onChange([...items, input.trim()]);
      }
      setInput('');
    }
  };

  return (
    <div className="space-y-2">
      <Input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
      />
      <div className="space-y-1">
        {items.map((item, i) => (
          <div key={i} className="flex items-center justify-between p-2 rounded bg-muted/50">
            <span className="text-sm">{item}</span>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 text-destructive"
              onClick={() => onChange(items.filter((_, idx) => idx !== i))}
            >
              <Trash2 className="w-3 h-3" />
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
