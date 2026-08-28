/**
 * Employer Registration Page
 * Phase 3A: Employer Portal
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { Building2, Search, ArrowRight, CheckCircle } from 'lucide-react';
import { createEmployerProfile, searchCompanies, Company } from '../../services/employer';

const EmployerRegister: React.FC = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [formData, setFormData] = useState({
    job_title: '',
    phone: '',
  });
  const [searchResults, setSearchResults] = useState<Company[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // Search companies mutation
  const searchMutation = useMutation({
    mutationFn: searchCompanies,
    onSuccess: (data) => {
      setSearchResults(data.companies);
      setIsSearching(false);
    },
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: createEmployerProfile,
    onSuccess: () => {
      navigate('/app/employer/dashboard');
    },
  });

  // Handle company search
  const handleSearch = (query: string) => {
    setSearchQuery(query);
    if (query.length >= 2) {
      setIsSearching(true);
      searchMutation.mutate(query);
    } else {
      setSearchResults([]);
    }
  };

  // Handle company selection
  const handleSelectCompany = (company: Company) => {
    setSelectedCompany(company);
    setSearchQuery('');
    setSearchResults([]);
    setStep(2);
  };

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCompany) return;

    registerMutation.mutate({
      company_id: selectedCompany.id,
      job_title: formData.job_title,
      phone: formData.phone,
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Register as an Employer</h1>
          <p className="text-gray-600 mt-2">
            Create your employer account to start posting jobs
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center mb-8">
          <div className={`flex items-center ${step >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>
              {step > 1 ? <CheckCircle className="w-5 h-5" /> : '1'}
            </div>
            <span className="ml-2 font-medium">Find Company</span>
          </div>
          <div className={`w-24 h-1 mx-4 ${step >= 2 ? 'bg-blue-600' : 'bg-gray-200'}`} />
          <div className={`flex items-center ${step >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>
              2
            </div>
            <span className="ml-2 font-medium">Your Details</span>
          </div>
        </div>

        {/* Step 1: Find Company */}
        {step === 1 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Find Your Company
            </h2>
            <p className="text-gray-600 mb-6">
              Search for your company. If it doesn't exist, you can request to add it.
            </p>

            <div className="relative">
              <div className="flex items-center gap-2 mb-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => handleSearch(e.target.value)}
                    placeholder="Search for your company..."
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Search Results */}
              {isSearching && (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
                </div>
              )}

              {searchResults.length > 0 && (
                <div className="border border-gray-200 rounded-lg divide-y">
                  {searchResults.map((company) => (
                    <button
                      key={company.id}
                      onClick={() => handleSelectCompany(company)}
                      className="w-full flex items-center gap-4 p-4 hover:bg-gray-50 transition text-left"
                    >
                      <Building2 className="w-10 h-10 text-gray-400" />
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{company.name}</p>
                        <p className="text-sm text-gray-500">
                          {company.website} • {company.industry}
                        </p>
                      </div>
                      <ArrowRight className="w-5 h-5 text-gray-400" />
                    </button>
                  ))}
                </div>
              )}

              {searchQuery.length >= 2 && !isSearching && searchResults.length === 0 && (
                <div className="text-center py-8 bg-gray-50 rounded-lg">
                  <Building2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-2">Company not found?</p>
                  <p className="text-sm text-gray-500">
                    Contact support to add your company to our database.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 2: Your Details */}
        {step === 2 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Your Details
            </h2>
            
            {/* Selected Company */}
            <div className="bg-blue-50 rounded-lg p-4 mb-6">
              <p className="text-sm text-blue-600 font-medium mb-1">Selected Company</p>
              <div className="flex items-center gap-3">
                <Building2 className="w-8 h-8 text-blue-600" />
                <div>
                  <p className="font-semibold text-gray-900">{selectedCompany?.name}</p>
                  <p className="text-sm text-gray-500">{selectedCompany?.industry}</p>
                </div>
              </div>
              <button
                onClick={() => setStep(1)}
                className="text-sm text-blue-600 hover:text-blue-700 mt-2"
              >
                Change company
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                <div>
                  <label htmlFor="job_title" className="block text-sm font-medium text-gray-700 mb-1">
                    Your Job Title *
                  </label>
                  <input
                    type="text"
                    id="job_title"
                    value={formData.job_title}
                    onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
                    placeholder="e.g., HR Manager, Recruiter, CEO"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                    Phone Number (Optional)
                  </label>
                  <input
                    type="tel"
                    id="phone"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder="+20 xxx xxx xxxx"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Error Message */}
              {registerMutation.isError && (
                <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-lg">
                  An error occurred. Please try again.
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={registerMutation.isPending || !formData.job_title}
                className="w-full mt-6 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {registerMutation.isPending ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    Creating Account...
                  </>
                ) : (
                  <>
                    Create Employer Account
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </form>

            <p className="text-sm text-gray-500 text-center mt-4">
              Your account will need to be verified before you can post jobs.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EmployerRegister;