import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, User, Briefcase, GraduationCap, Code, Settings, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import profileApi, { UserProfile, ProfileCompletion } from '../services/profile';

const ProfilePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [dragActive, setDragActive] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const queryClient = useQueryClient();

  // Fetch profile
  const { data: profile, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: profileApi.getProfile,
  });

  // Fetch completion status
  const { data: completion } = useQuery({
    queryKey: ['profile-completion'],
    queryFn: profileApi.getCompletion,
  });

  // Upload CV mutation
  const uploadMutation = useMutation({
    mutationFn: profileApi.uploadCV,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      queryClient.invalidateQueries({ queryKey: ['profile-completion'] });
      setUploadStatus('success');
      setTimeout(() => setUploadStatus('idle'), 3000);
    },
    onError: () => {
      setUploadStatus('error');
    },
  });

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFile = (file: File) => {
    const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    if (!validTypes.includes(file.type)) {
      setUploadStatus('error');
      return;
    }

    setUploadStatus('uploading');
    uploadMutation.mutate(file);
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: User },
    { id: 'cv', label: 'CV Upload', icon: Upload },
    { id: 'skills', label: 'Skills', icon: Code },
    { id: 'preferences', label: 'Preferences', icon: Settings },
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Your Profile</h1>
          <p className="text-gray-600 mt-2">
            Manage your profile to get better job matches
          </p>
        </div>

        {/* Completion Status */}
        {completion && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Profile Completion</h2>
              <span className={`text-2xl font-bold ${completion.total_score >= 60 ? 'text-green-600' : 'text-amber-600'}`}>
                {completion.total_score}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${completion.total_score >= 60 ? 'bg-green-500' : 'bg-amber-500'}`}
                style={{ width: `${completion.total_score}%` }}
              />
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(completion.sections).map(([key, section]) => (
                <div key={key} className="flex items-center gap-2">
                  {section.complete ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-gray-300" />
                  )}
                  <span className={`text-sm ${section.complete ? 'text-gray-700' : 'text-gray-400'}`}>
                    {section.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b">
            <nav className="flex -mb-px">
              {tabs.map(tab => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      flex-1 py-4 px-6 text-center border-b-2 font-medium text-sm
                      transition flex items-center justify-center gap-2
                      ${activeTab === tab.id
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }
                    `}
                  >
                    <Icon className="w-5 h-5" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'overview' && <OverviewTab profile={profile} />}
            {activeTab === 'cv' && (
              <CVUploadTab
                profile={profile}
                dragActive={dragActive}
                uploadStatus={uploadStatus}
                onDrag={handleDrag}
                onDrop={handleDrop}
                onFileSelect={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
              />
            )}
            {activeTab === 'skills' && <SkillsTab profile={profile} />}
            {activeTab === 'preferences' && <PreferencesTab profile={profile} />}
          </div>
        </div>
      </div>
    </div>
  );
};

// Overview Tab Component
const OverviewTab: React.FC<{ profile?: UserProfile }> = ({ profile }) => {
  if (!profile) return null;

  return (
    <div className="space-y-6">
      {/* Basic Info */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-500">Email</label>
            <p className="mt-1 text-gray-900">{profile.email}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500">Full Name</label>
            <p className="mt-1 text-gray-900">{profile.full_name || 'Not set'}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500">Current Role</label>
            <p className="mt-1 text-gray-900">{profile.current_role || 'Not detected'}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500">Experience</label>
            <p className="mt-1 text-gray-900">
              {profile.experience_years > 0 ? `${profile.experience_years.toFixed(1)} years` : 'Not detected'}
            </p>
          </div>
        </div>
      </div>

      {/* Skills Summary */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Skills ({profile.skills?.length || 0})</h3>
        <div className="flex flex-wrap gap-2">
          {profile.skills?.slice(0, 10).map((skill, index) => (
            <span
              key={index}
              className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
            >
              {skill}
            </span>
          ))}
          {profile.skills?.length > 10 && (
            <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">
              +{profile.skills.length - 10} more
            </span>
          )}
        </div>
      </div>

      {/* Education */}
      {profile.education?.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Education</h3>
          <div className="space-y-3">
            {profile.education.map((edu, index) => (
              <div key={index} className="flex items-start gap-3">
                <GraduationCap className="w-5 h-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="font-medium text-gray-900">{edu.degree}</p>
                  <p className="text-sm text-gray-500">{edu.institution}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// CV Upload Tab Component
interface CVUploadTabProps {
  profile?: UserProfile;
  dragActive: boolean;
  uploadStatus: 'idle' | 'uploading' | 'success' | 'error';
  onDrag: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent) => void;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const CVUploadTab: React.FC<CVUploadTabProps> = ({
  profile,
  dragActive,
  uploadStatus,
  onDrag,
  onDrop,
  onFileSelect,
}) => {
  return (
    <div className="space-y-6">
      {/* Current CV */}
      {profile?.cv_file && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <FileText className="w-8 h-8 text-green-600" />
            <div>
              <p className="font-medium text-green-900">CV Uploaded</p>
              <p className="text-sm text-green-600">
                Uploaded on {new Date(profile.cv_uploaded_at || '').toLocaleDateString()}
              </p>
              <p className="text-xs text-green-500 mt-1">
                Status: {profile.cv_parse_status}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Upload Area */}
      <div
        className={`
          border-2 border-dashed rounded-lg p-12 text-center transition
          ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
        `}
        onDragEnter={onDrag}
        onDragLeave={onDrag}
        onDragOver={onDrag}
        onDrop={onDrop}
      >
        <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        <p className="text-lg font-medium text-gray-700 mb-2">
          Drag and drop your CV here
        </p>
        <p className="text-sm text-gray-500 mb-4">
          or click to browse
        </p>
        <input
          type="file"
          accept=".pdf,.doc,.docx,.txt"
          onChange={onFileSelect}
          className="hidden"
          id="cv-upload"
        />
        <label
          htmlFor="cv-upload"
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700 transition"
        >
          Browse Files
        </label>
        <p className="text-xs text-gray-400 mt-4">
          Supported formats: PDF, DOC, DOCX, TXT (max 10MB)
        </p>
      </div>

      {/* Upload Status */}
      {uploadStatus === 'uploading' && (
        <div className="flex items-center gap-3 text-blue-600">
          <div className="animate-spin w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full" />
          <span>Uploading and parsing CV...</span>
        </div>
      )}
      {uploadStatus === 'success' && (
        <div className="flex items-center gap-3 text-green-600">
          <CheckCircle className="w-5 h-5" />
          <span>CV uploaded successfully!</span>
        </div>
      )}
      {uploadStatus === 'error' && (
        <div className="flex items-center gap-3 text-red-600">
          <AlertCircle className="w-5 h-5" />
          <span>Failed to upload CV. Please try again.</span>
        </div>
      )}
    </div>
  );
};

// Skills Tab Component
const SkillsTab: React.FC<{ profile?: UserProfile }> = ({ profile }) => {
  const [skills, setSkills] = useState<string[]>(profile?.skills || []);
  const [newSkill, setNewSkill] = useState('');
  const queryClient = useQueryClient();

  const updateSkillsMutation = useMutation({
    mutationFn: () => profileApi.updateSkills(skills),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
  });

  const addSkill = () => {
    if (newSkill.trim() && !skills.includes(newSkill.trim())) {
      setSkills([...skills, newSkill.trim()]);
      setNewSkill('');
    }
  };

  const removeSkill = (skillToRemove: string) => {
    setSkills(skills.filter(s => s !== skillToRemove));
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Skills</h3>
        <p className="text-sm text-gray-500 mb-4">
          Add or remove skills to improve job matching
        </p>
      </div>

      {/* Add Skill */}
      <div className="flex gap-2">
        <input
          type="text"
          value={newSkill}
          onChange={(e) => setNewSkill(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && addSkill()}
          placeholder="Add a skill..."
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button
          onClick={addSkill}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          Add
        </button>
      </div>

      {/* Skills List */}
      <div className="flex flex-wrap gap-2">
        {skills.map((skill, index) => (
          <span
            key={index}
            className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full"
          >
            {skill}
            <button
              onClick={() => removeSkill(skill)}
              className="ml-1 text-blue-600 hover:text-blue-800"
            >
              ×
            </button>
          </span>
        ))}
      </div>

      {/* Save Button */}
      <button
        onClick={() => updateSkillsMutation.mutate()}
        disabled={updateSkillsMutation.isPending}
        className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50"
      >
        {updateSkillsMutation.isPending ? 'Saving...' : 'Save Skills'}
      </button>
    </div>
  );
};

// Preferences Tab Component
const PreferencesTab: React.FC<{ profile?: UserProfile }> = ({ profile }) => {
  const [preferences, setPreferences] = useState({
    desired_roles: profile?.desired_roles || [],
    desired_locations: profile?.desired_locations || [],
    open_to_remote: profile?.open_to_remote ?? true,
    min_salary: profile?.min_salary || null,
  });
  const [newRole, setNewRole] = useState('');
  const [newLocation, setNewLocation] = useState('');
  const queryClient = useQueryClient();

  const updatePreferencesMutation = useMutation({
    mutationFn: () => profileApi.updatePreferences(preferences),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
  });

  const addRole = () => {
    if (newRole.trim() && !preferences.desired_roles.includes(newRole.trim())) {
      setPreferences({
        ...preferences,
        desired_roles: [...preferences.desired_roles, newRole.trim()],
      });
      setNewRole('');
    }
  };

  const addLocation = () => {
    if (newLocation.trim() && !preferences.desired_locations.includes(newLocation.trim())) {
      setPreferences({
        ...preferences,
        desired_locations: [...preferences.desired_locations, newLocation.trim()],
      });
      setNewLocation('');
    }
  };

  return (
    <div className="space-y-8">
      {/* Desired Roles */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Desired Roles</h3>
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={newRole}
            onChange={(e) => setNewRole(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addRole()}
            placeholder="e.g., Software Engineer, Product Manager..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={addRole}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Add
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {preferences.desired_roles.map((role, index) => (
            <span
              key={index}
              className="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 text-purple-800 rounded-full"
            >
              <Briefcase className="w-4 h-4" />
              {role}
              <button
                onClick={() => setPreferences({
                  ...preferences,
                  desired_roles: preferences.desired_roles.filter((_, i) => i !== index),
                })}
                className="ml-1 text-purple-600 hover:text-purple-800"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </div>

      {/* Desired Locations */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Desired Locations</h3>
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={newLocation}
            onChange={(e) => setNewLocation(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addLocation()}
            placeholder="e.g., Cairo, Remote, Dubai..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            onClick={addLocation}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Add
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {preferences.desired_locations.map((location, index) => (
            <span
              key={index}
              className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 rounded-full"
            >
              {location}
              <button
                onClick={() => setPreferences({
                  ...preferences,
                  desired_locations: preferences.desired_locations.filter((_, i) => i !== index),
                })}
                className="ml-1 text-green-600 hover:text-green-800"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </div>

      {/* Remote Work */}
      <div>
        <label className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={preferences.open_to_remote}
            onChange={(e) => setPreferences({ ...preferences, open_to_remote: e.target.checked })}
            className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500"
          />
          <span className="text-gray-700">Open to remote work</span>
        </label>
      </div>

      {/* Save Button */}
      <button
        onClick={() => updatePreferencesMutation.mutate()}
        disabled={updatePreferencesMutation.isPending}
        className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50"
      >
        {updatePreferencesMutation.isPending ? 'Saving...' : 'Save Preferences'}
      </button>
    </div>
  );
};

export default ProfilePage;