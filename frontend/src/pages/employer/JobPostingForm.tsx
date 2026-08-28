/**
 * Job Posting Form Page
 * Phase 3A: Employer Portal
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ArrowLeft, Save, Send, AlertCircle, Plus, Trash2 } from 'lucide-react';
import { createJobPosting, getJobPosting, updateJobPosting, publishJobPosting, CreateJobPostingData, CustomFormField } from '../../services/employer';

interface JobPostingFormProps {
  jobId?: number; // If provided, we're editing an existing job
}

const JobPostingForm: React.FC<JobPostingFormProps> = ({ jobId }) => {
  const navigate = useNavigate();
  const [showPreview, setShowPreview] = useState(false);
  
  const [formData, setFormData] = useState<CreateJobPostingData>({
    title: '',
    description: '',
    requirements: '',
    employment_type: 'full_time',
    experience_level: 'mid',
    remote_type: 'onsite',
    location: '',
    salary_min: undefined,
    salary_max: undefined,
    salary_currency: 'EGP',
    apply_url: '',
    custom_form_fields: [],
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Load existing job if editing
  useQuery({
    queryKey: ['job-posting', jobId],
    queryFn: () => getJobPosting(jobId!),
    enabled: !!jobId,
    onSuccess: (data: any) => {
      setFormData({
        title: data.title,
        description: data.description || '',
        requirements: data.requirements || '',
        employment_type: data.employment_type,
        experience_level: data.experience_level,
        remote_type: data.remote_type,
        location: data.location,
        salary_min: data.salary_min || undefined,
        salary_max: data.salary_max || undefined,
        salary_currency: data.salary_currency || 'EGP',
        apply_url: data.apply_url || '',
        custom_form_fields: data.custom_form_fields || [],
      });
    },
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: createJobPosting,
    onSuccess: () => {
      navigate('/app/employer/dashboard');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: { id: number; data: Partial<CreateJobPostingData> }) =>
      updateJobPosting(data.id, data.data),
    onSuccess: () => {
      navigate('/app/employer/dashboard');
    },
  });

  // Publish mutation
  const publishMutation = useMutation({
    mutationFn: publishJobPosting,
    onSuccess: () => {
      navigate('/app/employer/dashboard');
    },
  });

  // Handle form validation
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Job title is required';
    }
    if (!formData.description.trim()) {
      newErrors.description = 'Job description is required';
    }
    if (!formData.requirements.trim()) {
      newErrors.requirements = 'Requirements are required';
    }
    if (!formData.location.trim()) {
      newErrors.location = 'Location is required';
    }
    if (!formData.apply_url.trim()) {
      newErrors.apply_url = 'Apply URL is required';
    } else {
      try {
        new URL(formData.apply_url);
      } catch {
        newErrors.apply_url = 'Please enter a valid URL';
      }
    }
    if (formData.salary_min && formData.salary_max && formData.salary_min > formData.salary_max) {
      newErrors.salary_min = 'Minimum salary cannot exceed maximum';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle save as draft
  const handleSaveDraft = () => {
    if (!validateForm()) return;

    if (jobId) {
      updateMutation.mutate({ id: jobId, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  // Handle publish
  const handlePublish = async () => {
    if (!validateForm()) return;

    // First save, then publish
    if (jobId) {
      await updateMutation.mutateAsync({ id: jobId, data: formData });
      publishMutation.mutate(jobId);
    } else {
      const job = await createMutation.mutateAsync(formData);
      publishMutation.mutate(job.id);
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending || publishMutation.isPending;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-gray-200 rounded-lg transition"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {jobId ? 'Edit Job Posting' : 'Create Job Posting'}
            </h1>
            <p className="text-gray-600">
              {jobId ? 'Update your job posting details' : 'Fill in the details for your new job posting'}
            </p>
          </div>
        </div>

        {/* Form */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="space-y-6">
            {/* Basic Info */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Job Title *
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    placeholder="e.g., Senior Software Engineer"
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      errors.title ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {errors.title && (
                    <p className="text-red-500 text-sm mt-1">{errors.title}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Location *
                  </label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    placeholder="e.g., Cairo, Egypt"
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      errors.location ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {errors.location && (
                    <p className="text-red-500 text-sm mt-1">{errors.location}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Classification */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Classification</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Employment Type
                  </label>
                  <select
                    value={formData.employment_type}
                    onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="full_time">Full Time</option>
                    <option value="part_time">Part Time</option>
                    <option value="contract">Contract</option>
                    <option value="internship">Internship</option>
                    <option value="freelance">Freelance</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Experience Level
                  </label>
                  <select
                    value={formData.experience_level}
                    onChange={(e) => setFormData({ ...formData, experience_level: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="student">Student</option>
                    <option value="entry">Entry Level</option>
                    <option value="mid">Mid Level</option>
                    <option value="senior">Senior</option>
                    <option value="director">Director</option>
                    <option value="c_level">C-Level</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Work Type
                  </label>
                  <select
                    value={formData.remote_type}
                    onChange={(e) => setFormData({ ...formData, remote_type: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="remote">Remote</option>
                    <option value="hybrid">Hybrid</option>
                    <option value="onsite">On-site</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Salary */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Salary (Optional)</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Minimum Salary
                  </label>
                  <input
                    type="number"
                    value={formData.salary_min || ''}
                    onChange={(e) => setFormData({ ...formData, salary_min: e.target.value ? parseInt(e.target.value) : undefined })}
                    placeholder="e.g., 15000"
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      errors.salary_min ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {errors.salary_min && (
                    <p className="text-red-500 text-sm mt-1">{errors.salary_min}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Maximum Salary
                  </label>
                  <input
                    type="number"
                    value={formData.salary_max || ''}
                    onChange={(e) => setFormData({ ...formData, salary_max: e.target.value ? parseInt(e.target.value) : undefined })}
                    placeholder="e.g., 25000"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Currency
                  </label>
                  <select
                    value={formData.salary_currency}
                    onChange={(e) => setFormData({ ...formData, salary_currency: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="EGP">EGP</option>
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="SAR">SAR</option>
                    <option value="AED">AED</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Description */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Job Details</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Job Description *
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={6}
                    placeholder="Describe the role, responsibilities, and what makes this opportunity exciting..."
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      errors.description ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {errors.description && (
                    <p className="text-red-500 text-sm mt-1">{errors.description}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Requirements *
                  </label>
                  <textarea
                    value={formData.requirements}
                    onChange={(e) => setFormData({ ...formData, requirements: e.target.value })}
                    rows={6}
                    placeholder="List the required skills, qualifications, and experience..."
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      errors.requirements ? 'border-red-500' : 'border-gray-300'
                    }`}
                  />
                  {errors.requirements && (
                    <p className="text-red-500 text-sm mt-1">{errors.requirements}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Application URL */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Application</h2>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Apply URL *
                </label>
                <input
                  type="url"
                  value={formData.apply_url}
                  onChange={(e) => setFormData({ ...formData, apply_url: e.target.value })}
                  placeholder="https://your-company.com/careers/apply/..."
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.apply_url ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.apply_url && (
                  <p className="text-red-500 text-sm mt-1">{errors.apply_url}</p>
                )}
                <p className="text-sm text-gray-500 mt-1">
                  <AlertCircle className="w-4 h-4 inline mr-1" />
                  URL must be on your company's official domain
                </p>
              </div>
            </div>

            {/* Screening Questions */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">Screening Questions</h2>
              <p className="text-sm text-gray-500 mb-4">
                Add custom questions for candidates. You can set knockout values to auto-reject applicants.
              </p>

              <div className="space-y-4">
                {(formData.custom_form_fields || []).map((field, index) => (
                  <div key={field.id} className="border border-gray-200 rounded-lg p-4 space-y-3">
                    <div className="flex items-start justify-between">
                      <span className="text-sm font-medium text-gray-500">Question {index + 1}</span>
                      <button
                        type="button"
                        onClick={() => {
                          const updated = [...(formData.custom_form_fields || [])];
                          updated.splice(index, 1);
                          setFormData({ ...formData, custom_form_fields: updated });
                        }}
                        className="text-red-500 hover:text-red-700 p-1"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Label</label>
                        <input
                          type="text"
                          value={field.label}
                          onChange={(e) => {
                            const updated = [...(formData.custom_form_fields || [])];
                            updated[index] = { ...updated[index], label: e.target.value };
                            setFormData({ ...formData, custom_form_fields: updated });
                          }}
                          placeholder="e.g., Do you have a valid work permit?"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
                        <select
                          value={field.type}
                          onChange={(e) => {
                            const updated = [...(formData.custom_form_fields || [])];
                            updated[index] = { ...updated[index], type: e.target.value as CustomFormField['type'] };
                            setFormData({ ...formData, custom_form_fields: updated });
                          }}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                          <option value="text">Short Text</option>
                          <option value="textarea">Long Text</option>
                          <option value="yes_no">Yes / No</option>
                          <option value="select">Single Select</option>
                          <option value="multiselect">Multi Select</option>
                          <option value="number">Number</option>
                          <option value="date">Date</option>
                          <option value="url">URL</option>
                        </select>
                      </div>
                    </div>

                    {(field.type === 'select' || field.type === 'multiselect') && (
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Options (comma-separated)
                        </label>
                        <input
                          type="text"
                          value={(field.options || []).join(', ')}
                          onChange={(e) => {
                            const updated = [...(formData.custom_form_fields || [])];
                            updated[index] = {
                              ...updated[index],
                              options: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                            };
                            setFormData({ ...formData, custom_form_fields: updated });
                          }}
                          placeholder="e.g., Option A, Option B, Option C"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          id={`required-${field.id}`}
                          checked={field.required}
                          onChange={(e) => {
                            const updated = [...(formData.custom_form_fields || [])];
                            updated[index] = { ...updated[index], required: e.target.checked };
                            setFormData({ ...formData, custom_form_fields: updated });
                          }}
                          className="rounded border-gray-300"
                        />
                        <label htmlFor={`required-${field.id}`} className="text-xs text-gray-600">Required</label>
                      </div>

                      <div className="md:col-span-2">
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Knockout Value (auto-reject if matched)
                        </label>
                        <input
                          type="text"
                          value={field.knockout_value || ''}
                          onChange={(e) => {
                            const updated = [...(formData.custom_form_fields || [])];
                            updated[index] = {
                              ...updated[index],
                              knockout_value: e.target.value || undefined,
                            };
                            setFormData({ ...formData, custom_form_fields: updated });
                          }}
                          placeholder={field.type === 'yes_no' ? 'e.g., no' : 'Leave empty to disable'}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                    </div>
                  </div>
                ))}

                <button
                  type="button"
                  onClick={() => {
                    const newField: CustomFormField = {
                      id: `field_${Date.now()}`,
                      type: 'yes_no',
                      label: '',
                      required: true,
                    };
                    setFormData({
                      ...formData,
                      custom_form_fields: [...(formData.custom_form_fields || []), newField],
                    });
                  }}
                  className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-blue-400 hover:text-blue-600 transition flex items-center justify-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Add Screening Question
                </button>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between mt-8 pt-6 border-t">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition"
            >
              Cancel
            </button>
            
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleSaveDraft}
                disabled={isLoading}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                Save as Draft
              </button>
              
              <button
                type="button"
                onClick={handlePublish}
                disabled={isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
              >
                <Send className="w-4 h-4" />
                Submit for Review
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobPostingForm;