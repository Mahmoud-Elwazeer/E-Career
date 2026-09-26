/**
 * Employer Registration Page
 * Phase 3A: Employer Portal
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { Building2, Search, ArrowRight, CheckCircle } from 'lucide-react';
import { createEmployerProfile, searchCompanies, createCompany, Company } from '../../services/employer';
import { AppShell } from '@/components/shells/AppShell';
import { PlusCircle } from 'lucide-react';

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
  const [creatingCompany, setCreatingCompany] = useState(false);
  const [companyForm, setCompanyForm] = useState({
    name: '', industry: '', size: '', website: '', headquarters: '', description: '',
  });

  const createCompanyMutation = useMutation({
    mutationFn: createCompany,
    onSuccess: () => navigate('/app/employer/dashboard'),
  });

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
    <AppShell>
      <div className="container max-w-2xl py-12">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-heading-1 text-foreground">Register as an Employer</h1>
          <p className="text-muted-foreground mt-2">
            Create your employer account to start posting jobs
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center mb-8">
          <div className={`flex items-center ${step >= 1 ? 'text-primary' : 'text-muted-foreground'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 1 ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
              {step > 1 ? <CheckCircle className="w-5 h-5" /> : '1'}
            </div>
            <span className="ml-2 font-medium">Find Company</span>
          </div>
          <div className={`w-24 h-1 mx-4 ${step >= 2 ? 'bg-primary' : 'bg-muted'}`} />
          <div className={`flex items-center ${step >= 2 ? 'text-primary' : 'text-muted-foreground'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 2 ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
              2
            </div>
            <span className="ml-2 font-medium">Your Details</span>
          </div>
        </div>

        {/* Step 1: Find Company */}
        {step === 1 && (
          <div className="paper-card p-6">
            <h2 className="text-xl font-semibold text-foreground mb-4">
              Find Your Company
            </h2>
            <p className="text-muted-foreground mb-6">
              Search for your company. If it doesn't exist, you can request to add it.
            </p>

            <div className="relative">
              <div className="flex items-center gap-2 mb-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => handleSearch(e.target.value)}
                    placeholder="Search for your company..."
                    className="w-full pl-10 pr-4 py-3 border border-input rounded-lg focus:ring-2 focus:ring-ring focus:border-transparent"
                  />
                </div>
              </div>

              {/* Search Results */}
              {isSearching && (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto"></div>
                </div>
              )}

              {searchResults.length > 0 && (
                <div className="border border-border rounded-lg divide-y">
                  {searchResults.map((company) => (
                    <button
                      key={company.id}
                      onClick={() => handleSelectCompany(company)}
                      className="w-full flex items-center gap-4 p-4 hover:bg-accent transition text-left"
                    >
                      <Building2 className="w-10 h-10 text-muted-foreground" />
                      <div className="flex-1">
                        <p className="font-medium text-foreground">{company.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {company.website} • {company.industry}
                        </p>
                      </div>
                      <ArrowRight className="w-5 h-5 text-muted-foreground" />
                    </button>
                  ))}
                </div>
              )}

              {searchQuery.length >= 2 && !isSearching && searchResults.length === 0 && (
                <div className="text-center py-8 bg-background rounded-lg">
                  <Building2 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground mb-4">Company not found?</p>
                  <button
                    onClick={() => { setCompanyForm((f) => ({ ...f, name: searchQuery })); setCreatingCompany(true); }}
                    className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 h-11 text-body font-medium text-primary-foreground shadow-sm press-feedback"
                  >
                    <PlusCircle className="h-4 w-4" /> Create a new company
                  </button>
                </div>
              )}

              {/* Always-available create option */}
              <div className="mt-4 text-center">
                <button
                  onClick={() => setCreatingCompany(true)}
                  className="inline-flex items-center gap-1.5 text-caption font-medium text-primary link-underline"
                >
                  <PlusCircle className="h-3.5 w-3.5" /> Or create a new company
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Create Company form (opens over step 1) */}
        {step === 1 && creatingCompany && (
          <div className="paper-card p-6 mt-6">
            <h2 className="text-xl font-semibold text-foreground mb-1">Create your company</h2>
            <p className="text-muted-foreground mb-6">You'll become the owner. You can complete more details later.</p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (!companyForm.name.trim()) return;
                createCompanyMutation.mutate({
                  name: companyForm.name.trim(),
                  industry: companyForm.industry || undefined,
                  size: companyForm.size || undefined,
                  website: companyForm.website || undefined,
                  headquarters: companyForm.headquarters || undefined,
                  description: companyForm.description || undefined,
                  job_title: formData.job_title || 'Owner',
                  phone: formData.phone || undefined,
                });
              }}
              className="space-y-4"
            >
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <input required value={companyForm.name} onChange={(e) => setCompanyForm({ ...companyForm, name: e.target.value })}
                  placeholder="Company name *" className="w-full px-4 py-3 border border-input rounded-lg focus:ring-2 focus:ring-ring" />
                <input value={companyForm.industry} onChange={(e) => setCompanyForm({ ...companyForm, industry: e.target.value })}
                  placeholder="Industry (e.g. technology)" className="w-full px-4 py-3 border border-input rounded-lg focus:ring-2 focus:ring-ring" />
                <input value={companyForm.size} onChange={(e) => setCompanyForm({ ...companyForm, size: e.target.value })}
                  placeholder="Company size (e.g. 11-50)" className="w-full px-4 py-3 border border-input rounded-lg focus:ring-2 focus:ring-ring" />
                <input value={companyForm.website} onChange={(e) => setCompanyForm({ ...companyForm, website: e.target.value })}
                  placeholder="Website" className="w-full px-4 py-3 border border-input rounded-lg focus:ring-2 focus:ring-ring" />
                <input value={companyForm.headquarters} onChange={(e) => setCompanyForm({ ...companyForm, headquarters: e.target.value })}
                  placeholder="Headquarters / location" className="w-full px-4 py-3 border border-input rounded-lg focus:ring-2 focus:ring-ring sm:col-span-2" />
                <textarea value={companyForm.description} onChange={(e) => setCompanyForm({ ...companyForm, description: e.target.value })}
                  placeholder="Company description" rows={3} className="w-full px-4 py-3 border border-input rounded-lg focus:ring-2 focus:ring-ring sm:col-span-2" />
              </div>
              {createCompanyMutation.isError && (
                <p className="text-sm text-destructive">{(createCompanyMutation.error as any)?.message ?? 'Failed to create company.'}</p>
              )}
              <div className="flex gap-3">
                <button type="submit" disabled={createCompanyMutation.isPending}
                  className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 h-11 text-body font-medium text-primary-foreground shadow-sm press-feedback disabled:opacity-50">
                  {createCompanyMutation.isPending ? 'Creating…' : 'Create company'}
                </button>
                <button type="button" onClick={() => setCreatingCompany(false)}
                  className="inline-flex items-center rounded-xl border border-border px-6 h-11 text-body font-medium">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Step 2: Your Details */}
        {step === 2 && (
          <div className="paper-card p-6">
            <h2 className="text-xl font-semibold text-foreground mb-4">
              Your Details
            </h2>
            
            {/* Selected Company */}
            <div className="bg-primary/10 rounded-lg p-4 mb-6">
              <p className="text-sm text-primary font-medium mb-1">Selected Company</p>
              <div className="flex items-center gap-3">
                <Building2 className="w-8 h-8 text-primary" />
                <div>
                  <p className="font-semibold text-foreground">{selectedCompany?.name}</p>
                  <p className="text-sm text-muted-foreground">{selectedCompany?.industry}</p>
                </div>
              </div>
              <button
                onClick={() => setStep(1)}
                className="text-sm text-primary hover:text-primary-hover mt-2"
              >
                Change company
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                <div>
                  <label htmlFor="job_title" className="block text-sm font-medium text-foreground mb-1">
                    Your Job Title *
                  </label>
                  <input
                    type="text"
                    id="job_title"
                    value={formData.job_title}
                    onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
                    placeholder="e.g., HR Manager, Recruiter, CEO"
                    className="w-full px-4 py-3 border border-input rounded-lg focus:ring-2 focus:ring-ring focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label htmlFor="phone" className="block text-sm font-medium text-foreground mb-1">
                    Phone Number (Optional)
                  </label>
                  <input
                    type="tel"
                    id="phone"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder="+20 xxx xxx xxxx"
                    className="w-full px-4 py-3 border border-input rounded-lg focus:ring-2 focus:ring-ring focus:border-transparent"
                  />
                </div>
              </div>

              {/* Error Message */}
              {registerMutation.isError && (
                <div className="mt-4 p-4 bg-destructive/10 text-destructive rounded-lg">
                  An error occurred. Please try again.
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={registerMutation.isPending || !formData.job_title}
                className="w-full mt-6 px-4 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
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

            <p className="text-sm text-muted-foreground text-center mt-4">
              Your account will need to be verified before you can post jobs.
            </p>
          </div>
        )}
      </div>
    </AppShell>
  );
};

export default EmployerRegister;