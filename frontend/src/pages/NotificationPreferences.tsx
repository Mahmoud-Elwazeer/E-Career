import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiRequest } from '@/services/client';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Loader2, Save, CheckCircle, Bell, Mail, Smartphone } from 'lucide-react';

interface NotificationPreference {
  id: string;
  user: string;
  alert_frequency: 'instant' | 'daily' | 'weekly' | 'never';
  email_enabled: boolean;
  email_digest_enabled: boolean;
  email_digest_time: string | null;
  in_app_enabled: boolean;
  push_enabled: boolean;
  notify_job_matches: boolean;
  notify_new_jobs: boolean;
  notify_interview_invites: boolean;
  notify_interview_reminders: boolean;
  notify_profile_views: boolean;
  notify_message_responses: boolean;
  notify_application_updates: boolean;
  notify_skill_badges: boolean;
  notify_score_improvements: boolean;
  notify_weekly_digest: boolean;
  quiet_hours_enabled: boolean;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
  created_at: string;
  updated_at: string;
}

export default function NotificationPreferences() {
  const queryClient = useQueryClient();
  
  const [preference, setPreference] = useState<NotificationPreference | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  // Fetch notification preferences
  const { data: preferenceData } = useQuery({
    queryKey: ['notification-preferences'],
    queryFn: async () => {
      return apiRequest<{ data: NotificationPreference }>('/notifications/preferences/');
    },
  });

  // Update preference mutation
  const updatePreferenceMutation = useMutation({
    mutationFn: async (data: Partial<NotificationPreference>) => {
      return apiRequest('/notifications/preferences/', {
        method: 'PUT',
        body: data,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-preferences'] });
    },
  });

  useEffect(() => {
    if (preferenceData?.data) {
      setPreference(preferenceData.data);
    }
    setLoading(false);
  }, [preferenceData]);

  const handleUpdate = (field: string, value: any) => {
    if (!preference) return;
    
    setPreference({
      ...preference,
      [field]: value,
    });
    
    updatePreferenceMutation.mutate({ [field]: value });
  };

  const handleSaveAll = () => {
    if (!preference) return;
    setSaving(true);
    
    updatePreferenceMutation.mutate(preference, {
      onSuccess: () => {
        setSaving(false);
        setShowSuccess(true);
        setTimeout(() => setShowSuccess(false), 3000);
      },
    });
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
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Notification Preferences</h1>
        <p className="text-gray-500">Manage how and when you receive notifications</p>
      </div>

      {showSuccess && (
        <Alert className="mb-4">
          <CheckCircle className="w-4 h-4" />
          <AlertTitle>Success</AlertTitle>
          <AlertDescription>Your notification preferences have been saved!</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Frequency Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Bell className="w-5 h-5 mr-2" />
              Frequency
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label className="mb-2 block">Alert Frequency</Label>
              <RadioGroup
                value={preference?.alert_frequency || 'instant'}
                onValueChange={(value) => handleUpdate('alert_frequency', value)}
              >
                <div className="flex items-center space-x-2 mb-2">
                  <RadioGroupItem value="instant" id="instant" />
                  <Label htmlFor="instant">Instant</Label>
                </div>
                <div className="flex items-center space-x-2 mb-2">
                  <RadioGroupItem value="daily" id="daily" />
                  <Label htmlFor="daily">Daily Digest</Label>
                </div>
                <div className="flex items-center space-x-2 mb-2">
                  <RadioGroupItem value="weekly" id="weekly" />
                  <Label htmlFor="weekly">Weekly Digest</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="never" id="never" />
                  <Label htmlFor="never">Never</Label>
                </div>
              </RadioGroup>
            </div>

            {preference?.alert_frequency === 'daily' && (
              <div>
                <Label className="mb-2 block">Digest Time</Label>
                <Input
                  type="time"
                  value={preference.email_digest_time || '09:00'}
                  onChange={(e) => handleUpdate('email_digest_time', e.target.value)}
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Channels */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Mail className="w-5 h-5 mr-2" />
              Channels
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Email</Label>
                <p className="text-sm text-gray-500">Receive notifications via email</p>
              </div>
              <Switch
                checked={preference?.email_enabled ?? true}
                onCheckedChange={(checked) => handleUpdate('email_enabled', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label>In-App</Label>
                <p className="text-sm text-gray-500">Show notifications in the app</p>
              </div>
              <Switch
                checked={preference?.in_app_enabled ?? true}
                onCheckedChange={(checked) => handleUpdate('in_app_enabled', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label>Push</Label>
                <p className="text-sm text-gray-500">Browser push notifications</p>
              </div>
              <Switch
                checked={preference?.push_enabled ?? true}
                onCheckedChange={(checked) => handleUpdate('push_enabled', checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Quiet Hours */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Smartphone className="w-5 h-5 mr-2" />
              Quiet Hours
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Enable Quiet Hours</Label>
                <p className="text-sm text-gray-500">Silence notifications during sleep hours</p>
              </div>
              <Switch
                checked={preference?.quiet_hours_enabled ?? false}
                onCheckedChange={(checked) => handleUpdate('quiet_hours_enabled', checked)}
              />
            </div>

            {preference?.quiet_hours_enabled && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="mb-2 block">Start Time</Label>
                  <Input
                    type="time"
                    value={preference.quiet_hours_start || '22:00'}
                    onChange={(e) => handleUpdate('quiet_hours_start', e.target.value)}
                  />
                </div>
                <div>
                  <Label className="mb-2 block">End Time</Label>
                  <Input
                    type="time"
                    value={preference.quiet_hours_end || '07:00'}
                    onChange={(e) => handleUpdate('quiet_hours_end', e.target.value)}
                  />
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Notification Types */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Notification Types</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <NotificationType
            label="Job Matches"
            description="Get notified when new jobs match your profile"
            checked={preference?.notify_job_matches ?? true}
            onChange={(checked) => handleUpdate('notify_job_matches', checked)}
          />
          <NotificationType
            label="New Jobs"
            description="Get notified about new job postings"
            checked={preference?.notify_new_jobs ?? true}
            onChange={(checked) => handleUpdate('notify_new_jobs', checked)}
          />
          <NotificationType
            label="Interview Invites"
            description="Get notified about interview invitations"
            checked={preference?.notify_interview_invites ?? true}
            onChange={(checked) => handleUpdate('notify_interview_invites', checked)}
          />
          <NotificationType
            label="Interview Reminders"
            description="Get reminders before scheduled interviews"
            checked={preference?.notify_interview_reminders ?? true}
            onChange={(checked) => handleUpdate('notify_interview_reminders', checked)}
          />
          <NotificationType
            label="Profile Views"
            description="Get notified when employers view your profile"
            checked={preference?.notify_profile_views ?? true}
            onChange={(checked) => handleUpdate('notify_profile_views', checked)}
          />
          <NotificationType
            label="Message Responses"
            description="Get notified about new messages"
            checked={preference?.notify_message_responses ?? true}
            onChange={(checked) => handleUpdate('notify_message_responses', checked)}
          />
          <NotificationType
            label="Application Updates"
            description="Get updates on your job applications"
            checked={preference?.notify_application_updates ?? true}
            onChange={(checked) => handleUpdate('notify_application_updates', checked)}
          />
          <NotificationType
            label="Skill Badges"
            description="Get notified when you earn skill badges"
            checked={preference?.notify_skill_badges ?? true}
            onChange={(checked) => handleUpdate('notify_skill_badges', checked)}
          />
          <NotificationType
            label="Score Improvements"
            description="Get notified about career score improvements"
            checked={preference?.notify_score_improvements ?? true}
            onChange={(checked) => handleUpdate('notify_score_improvements', checked)}
          />
          <NotificationType
            label="Weekly Digest"
            description="Get a weekly summary of your activity"
            checked={preference?.notify_weekly_digest ?? true}
            onChange={(checked) => handleUpdate('notify_weekly_digest', checked)}
          />
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="mt-6 flex justify-end">
        <Button onClick={handleSaveAll} disabled={saving || updatePreferenceMutation.isPending}>
          {saving || updatePreferenceMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          ) : (
            <Save className="w-4 h-4 mr-2" />
          )}
          Save Preferences
        </Button>
      </div>
    </div>
  );
}

function NotificationType({ label, description, checked, onChange }: { label: string; description: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
      <div>
        <Label className="font-medium">{label}</Label>
        <p className="text-sm text-gray-500">{description}</p>
      </div>
      <Switch checked={checked} onCheckedChange={onChange} />
    </div>
  );
}