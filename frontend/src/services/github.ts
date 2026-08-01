/**
 * GitHub Service for E-Career Frontend
 * Handles GitHub OAuth flow and connection management
 */

import api from './api';

export interface GitHubConnection {
  id: number;
  uuid: string;
  user_email: string;
  github_id: string;
  username: string;
  avatar_url: string;
  profile_url: string;
  email: string;
  name: string;
  company: string;
  location: string;
  last_synced_at: string | null;
  last_sync_status: 'pending' | 'success' | 'failed';
  last_sync_error: string;
  created_at: string;
  updated_at: string;
}

export interface PortfolioAnalysis {
  id: number;
  uuid: string;
  user_email: string;
  url: string;
  domain: string;
  technologies: string[];
  projects: any[];
  quality_score: number | null;
  completeness_score: number | null;
  tech_stack: any;
  project_count: number;
  star_count: number;
  contribution_count: number;
  observations: any;
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  error_message: string;
  created_at: string;
  updated_at: string;
}

export interface GitHubConnectRequest {
  code: string;
  state: string;
}

export interface PortfolioAnalyzeRequest {
  url: string;
}

/**
 * Get all GitHub connections for the current user
 */
export async function getGitHubConnections(): Promise<GitHubConnection[]> {
  const response = await api.get('/core/github/');
  return response.data.data;
}

/**
 * Connect GitHub account
 */
export async function connectGitHub(code: string, state: string): Promise<GitHubConnection> {
  const response = await api.post('/core/github/', { code, state });
  return response.data.data;
}

/**
 * Get all portfolio analyses for the current user
 */
export async function getPortfolioAnalyses(): Promise<PortfolioAnalysis[]> {
  const response = await api.get('/core/portfolio/');
  return response.data.data;
}

/**
 * Analyze a portfolio URL
 */
export async function analyzePortfolio(url: string): Promise<PortfolioAnalysis> {
  const response = await api.post('/core/portfolio/', { url });
  return response.data.data;
}

/**
 * Get GitHub user profile information
 */
export async function getGitHubProfile(username: string): Promise<any> {
  const response = await api.get(`/core/github/profile/${username}/`);
  return response.data;
}

/**
 * Get GitHub repository information
 */
export async function getGitHubRepo(owner: string, repo: string): Promise<any> {
  const response = await api.get(`/core/github/repo/${owner}/${repo}/`);
  return response.data;
}