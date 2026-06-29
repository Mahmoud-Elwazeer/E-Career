/**
 * Employer Dashboard Page
 * Phase 3A: Employer Portal
 */
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, Navigate } from 'react-router-dom';
import { Plus, Briefcase, Users, Eye, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { getEmployerProfile, getEmployerStats, getJobPostings } from '../../services/employer';

const EmployerDashboard: React.FC = () => {
  // Get employer profile
  const { data: profile, isLoading: profileLoading, error: profileError } = useQuery({
    queryKey: ['employer-profile'],
    queryFn: getEmployerProfile,
    retry: false,
  });

  // Get employer stats
  const { data: stats } = useQuery({
    queryKey: ['employer-stats'],
    queryFn: getEmployerStats,
    enabled: !!profile?.is_verified,
  });

  // Get job postings
  const { data: jobs } = useQuery({
    queryKey: ['employer-jobs'],
    queryFn: getJobPostings,
    enabled: !!profile?.is_verified,
  });

  // Loading state
  if (profileLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // If no employer profile, redirect to registration
  if (profileError) {
    return <Navigate to="/employer/register" />;
  }

  // If not verified, show pending verification message
  if (!profile?.is_verified) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white p-8 rounded-lg shadow max-w-md text-center">
          <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Clock className="w-8 h-8 text-yellow-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Verification Pending
          </h2>
          <p className="text-gray-600 mb-6">
            Your employer account is pending verification. We'll notify you once approved.
          </p>
          <p className="text-sm text-gray-500">
            Company: <span className="font-medium">{profile?.company?.name}</span>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Employer Dashboard</h1>
            <p className="text-gray-600 mt-2">{profile?.company?.name}</p>
          </div>
          
          <Link
            to="/employer/jobs/new"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 transition"
          >
            <Plus className="w-5 h-5" />
            Post New Job
          </Link>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-50 rounded-lg">
                <Briefcase className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {stats?.jobs?.active_jobs || 0}
                </p>
                <p className="text-gray-600">Active Jobs</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-50 rounded-lg">
                <Users className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {stats?.applications?.total_applications || 0}
                </p>
                <p className="text-gray-600">Total Applicants</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-50 rounded-lg">
                <Eye className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {stats?.engagement?.total_views || 0}
                </p>
                <p className="text-gray-600">Total Views</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-orange-50 rounded-lg">
                <AlertCircle className="w-6 h-6 text-orange-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {stats?.applications?.new_applications || 0}
                </p>
                <p className="text-gray-600">New Applications</p>
              </div>
            </div>
          </div>
        </div>

        {/* Jobs List */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Your Job Postings</h2>
            <Link
              to="/employer/jobs"
              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              View All
            </Link>
          </div>
          
          <div className="divide-y">
            {jobs?.slice(0, 5).map((job) => (
              <Link
                key={job.id}
                to={`/employer/jobs/${job.id}`}
                className="block p-6 hover:bg-gray-50 transition"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
                    <p className="text-gray-600 mt-1">
                      {job.location} • {job.remote_type_display}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                      <span>{job.applications_count} applicants</span>
                      <span>{job.views_count} views</span>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <span className={`
                      px-3 py-1 rounded-full text-sm font-medium
                      ${job.status === 'published' ? 'bg-green-100 text-green-800' : ''}
                      ${job.status === 'pending_review' ? 'bg-yellow-100 text-yellow-800' : ''}
                      ${job.status === 'draft' ? 'bg-gray-100 text-gray-800' : ''}
                      ${job.status === 'closed' ? 'bg-red-100 text-red-800' : ''}
                      ${job.status === 'rejected' ? 'bg-red-100 text-red-800' : ''}
                    `}>
                      {job.status_display}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
            
            {(!jobs || jobs.length === 0) && (
              <div className="p-12 text-center">
                <Briefcase className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 mb-4">No jobs posted yet</p>
                <Link
                  to="/employer/jobs/new"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Plus className="w-5 h-5" />
                  Create Your First Job Posting
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Recent Applications */}
        {stats?.applications?.new_applications > 0 && (
          <div className="mt-8 bg-white rounded-lg shadow">
            <div className="p-6 border-b flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Recent Applications</h2>
              <Link
                to="/employer/applications"
                className="text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                View All
              </Link>
            </div>
            
            <div className="p-6">
              <p className="text-gray-600">
                You have <span className="font-semibold text-orange-600">{stats.applications.new_applications} new applications</span> waiting for review.
              </p>
              <Link
                to="/employer/applications?status=applied"
                className="inline-block mt-4 px-4 py-2 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 transition"
              >
                Review New Applications
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EmployerDashboard;