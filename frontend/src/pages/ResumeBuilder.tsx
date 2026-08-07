import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Loader2, Save, Download, Plus, Trash2, CheckCircle } from 'lucide-react';

interface ResumeTemplate {
  id: string;
  title: string;
  description: string;
  category: string;
  preview_image?: string;
  is_premium: boolean;
  is_active: boolean;
  used_count: number;
  rating: number;
}

interface Resume {
  id: string;
  template: ResumeTemplate | null;
  title: string;
  personal_info: {
    full_name: string;
    email: string;
    phone: string;
    location: string;
    linkedin?: string;
    github?: string;
  };
  summary: string;
  experience: Array<{
    id: string;
    company: string;
    title: string;
    start_date: string;
    end_date: string;
    current: boolean;
    description: string;
  }>;
  education: Array<{
    id: string;
    school: string;
    degree: string;
    start_date: string;
    end_date: string;
    current: boolean;
  }>;
  skills: string[];
  projects: Array<{
    id: string;
    name: string;
    description: string;
    url?: string;
  }>;
  certifications: string[];
  languages: string[];
  interests: string[];
  is_public: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export default function ResumeBuilder() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const [activeTab, setActiveTab] = useState('personal');
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);
  const [templates, setTemplates] = useState<ResumeTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  // Fetch templates
  const { data: templatesData } = useQuery({
    queryKey: ['resume-templates'],
    queryFn: async () => {
      const response = await fetch('/api/v1/resume/templates/');
      if (!response.ok) throw new Error('Failed to fetch templates');
      return response.json();
    },
  });

  // Fetch user resumes
  const { data: resumesData } = useQuery({
    queryKey: ['user-resumes'],
    queryFn: async () => {
      const response = await fetch('/api/v1/resume/resumes/');
      if (!response.ok) throw new Error('Failed to fetch resumes');
      return response.json();
    },
  });

  // Create resume mutation
  const createResumeMutation = useMutation({
    mutationFn: async (data: Partial<Resume>) => {
      const response = await fetch('/api/v1/resume/resumes/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to create resume');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-resumes'] });
    },
  });

  // Update resume mutation
  const updateResumeMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Resume> }) => {
      const response = await fetch(`/api/v1/resume/resumes/${id}/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to update resume');
      return response.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['user-resumes'] });
      queryClient.invalidateQueries({ queryKey: ['resume', variables.id] });
    },
  });

  // Export resume mutation
  const exportResumeMutation = useMutation({
    mutationFn: async ({ resumeId, format }: { resumeId: string; format: string }) => {
      const response = await fetch('/api/v1/resume/export/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_id: resumeId, format }),
      });
      if (!response.ok) throw new Error('Failed to export resume');
      return response.json();
    },
  });

  useEffect(() => {
    if (templatesData?.data) {
      setTemplates(templatesData.data);
    }
    if (resumesData?.data) {
      setResumes(resumesData.data);
      if (resumesData.data.length > 0 && !selectedResume) {
        setSelectedResume(resumesData.data[0]);
      }
    }
    setLoading(false);
  }, [templatesData, resumesData, selectedResume]);

  const handleCreateResume = () => {
    createResumeMutation.mutate({
      title: 'My New Resume',
      personal_info: {
        full_name: '',
        email: '',
        phone: '',
        location: '',
      },
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

  const handleUpdateResume = (field: string, value: any) => {
    if (!selectedResume) return;
    
    updateResumeMutation.mutate({
      id: selectedResume.id,
      data: { [field]: value },
    });
  };

  const handleExport = (format: string) => {
    if (!selectedResume) return;
    exportResumeMutation.mutate({ resumeId: selectedResume.id, format });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Resume Builder</h1>
        <Button onClick={handleCreateResume}>
          <Plus className="w-4 h-4 mr-2" />
          Create New Resume
        </Button>
      </div>

      {showSuccess && (
        <Alert className="mb-4">
          <CheckCircle className="w-4 h-4" />
          <AlertTitle>Success</AlertTitle>
          <AlertDescription>Your resume has been saved successfully!</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sidebar - Resume List */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Your Resumes</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {resumes.map((resume) => (
                <div
                  key={resume.id}
                  onClick={() => setSelectedResume(resume)}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    selectedResume?.id === resume.id ? 'bg-blue-100 dark:bg-blue-900' : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  <h3 className="font-medium">{resume.title}</h3>
                  <p className="text-sm text-gray-500">
                    Last updated: {new Date(resume.updated_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
              {resumes.length === 0 && (
                <p className="text-gray-500 text-center py-4">
                  No resumes yet. Create one to get started!
                </p>
              )}
            </CardContent>
          </Card>

          {/* Templates */}
          <Card>
            <CardHeader>
              <CardTitle>Templates</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {templates.map((template) => (
                <div key={template.id} className="p-3 rounded-lg border">
                  <h3 className="font-medium">{template.title}</h3>
                  <p className="text-sm text-gray-500">{template.description}</p>
                  <Badge variant="secondary" className="mt-2">
                    {template.category}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Main Content - Resume Editor */}
        <div className="lg:col-span-2">
          {selectedResume ? (
            <Card>
              <CardHeader className="flex flex-row justify-between items-center">
                <div>
                  <CardTitle>{selectedResume.title}</CardTitle>
                  <p className="text-sm text-gray-500">Edit your resume content</p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => handleExport('pdf')}
                    disabled={exportResumeMutation.isPending}
                  >
                    {exportResumeMutation.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Download className="w-4 h-4 mr-2" />
                    )}
                    Export PDF
                  </Button>
                  <Button
                    onClick={() => {
                      handleUpdateResume('updated_at', new Date().toISOString());
                      setShowSuccess(true);
                      setTimeout(() => setShowSuccess(false), 3000);
                    }}
                    disabled={saving || updateResumeMutation.isPending}
                  >
                    {saving || updateResumeMutation.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Save className="w-4 h-4 mr-2" />
                    )}
                    Save
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <Tabs value={activeTab} onValueChange={setActiveTab}>
                  <TabsList className="grid grid-cols-4 mb-4">
                    <TabsTrigger value="personal">Personal</TabsTrigger>
                    <TabsTrigger value="experience">Experience</TabsTrigger>
                    <TabsTrigger value="education">Education</TabsTrigger>
                    <TabsTrigger value="skills">Skills</TabsTrigger>
                  </TabsList>

                  <TabsContent value="personal" className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Full Name</label>
                      <Input
                        value={selectedResume.personal_info.full_name}
                        onChange={(e) => handleUpdateResume('personal_info', {
                          ...selectedResume.personal_info,
                          full_name: e.target.value,
                        })}
                        placeholder="John Doe"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Email</label>
                        <Input
                          type="email"
                          value={selectedResume.personal_info.email}
                          onChange={(e) => handleUpdateResume('personal_info', {
                            ...selectedResume.personal_info,
                            email: e.target.value,
                          })}
                          placeholder="john@example.com"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Phone</label>
                        <Input
                          value={selectedResume.personal_info.phone}
                          onChange={(e) => handleUpdateResume('personal_info', {
                            ...selectedResume.personal_info,
                            phone: e.target.value,
                          })}
                          placeholder="+1 (555) 000-0000"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Location</label>
                      <Input
                        value={selectedResume.personal_info.location}
                        onChange={(e) => handleUpdateResume('personal_info', {
                          ...selectedResume.personal_info,
                          location: e.target.value,
                        })}
                        placeholder="New York, NY"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Professional Summary</label>
                      <Textarea
                        value={selectedResume.summary}
                        onChange={(e) => handleUpdateResume('summary', e.target.value)}
                        placeholder="Brief summary of your professional background..."
                        className="min-h-[100px]"
                      />
                    </div>
                  </TabsContent>

                  <TabsContent value="experience" className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Experience</label>
                      <p className="text-sm text-gray-500">
                        Add your work experience. Each entry includes company, title, dates, and description.
                      </p>
                    </div>
                    {/* Experience list would go here */}
                    <div className="p-4 border rounded-lg">
                      <p className="text-gray-500">Experience section - Add entries here</p>
                    </div>
                  </TabsContent>

                  <TabsContent value="education" className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Education</label>
                      <p className="text-sm text-gray-500">
                        Add your educational background.
                      </p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <p className="text-gray-500">Education section - Add entries here</p>
                    </div>
                  </TabsContent>

                  <TabsContent value="skills" className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Skills</label>
                      <p className="text-sm text-gray-500">
                        Add your skills. Separate with commas.
                      </p>
                      <Input
                        value={selectedResume.skills.join(', ')}
                        onChange={(e) => handleUpdateResume('skills', e.target.value.split(',').map(s => s.trim()))}
                        placeholder="Python, JavaScript, React, Node.js"
                      />
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-gray-500">Select a resume to edit or create a new one</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}