/**
 * Talent Search Page
 * Employer talent pool management and candidate ranking
 */
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { Users, Plus, Search, Trophy, AlertCircle, ArrowLeft, Briefcase } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AppShell } from '@/components/shells/AppShell';
import { PageHeader } from '@/components/PageHeader';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  listTalentPools,
  createTalentPool,
  rankCandidates,
  listRankings,
  getJobPostings,
  type TalentPool,
  type CandidateRanking,
  type JobPosting,
} from '@/services/employer';

// Score dimension configuration. Bar color uses semantic-token CLASSES (not raw
// hex) so it themes across light/dark/night. "Overall" gets the brand color;
// the rest use the same primary tint to keep the card calm and on-system.
const RANKING_DIMENSIONS = [
  { key: 'overall_score', label: 'Overall', bar: 'bg-primary' },
  { key: 'skill_match_score', label: 'Skill Match', bar: 'bg-primary/70' },
  { key: 'experience_score', label: 'Experience', bar: 'bg-success' },
  { key: 'education_score', label: 'Education', bar: 'bg-info' },
  { key: 'salary_expectation_score', label: 'Salary Fit', bar: 'bg-signal' },
] as const;

function ScoreBar({ label, value, bar }: { label: string; value: number; bar: string }) {
  const percent = Math.round(value * 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-foreground">{label}</span>
        <span className="font-mono-data text-muted-foreground">{percent}%</span>
      </div>
      <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.5 }}
          className={`h-full rounded-full ${bar}`}
        />
      </div>
    </div>
  );
}

function RankingCard({ ranking }: { ranking: CandidateRanking }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <Card className="mb-4">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">{ranking.user_name}</CardTitle>
              <CardDescription>{ranking.user_email}</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {ranking.knockout_passed ? (
                <Badge className="bg-success/15 text-success border-success/30">Passed</Badge>
              ) : (
                <Badge variant="destructive">Knockout Failed</Badge>
              )}
              <Badge variant="secondary" className="capitalize">{ranking.status}</Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Score breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-3 mb-4">
            {RANKING_DIMENSIONS.map((dim) => (
              <ScoreBar
                key={dim.key}
                label={dim.label}
                value={ranking[dim.key]}
                bar={dim.bar}
              />
            ))}
          </div>

          {/* Knockout failures */}
          {ranking.knockout_failures.length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-medium text-destructive mb-2">Knockout Failures:</p>
              <div className="flex flex-wrap gap-2">
                {ranking.knockout_failures.map((failure, idx) => (
                  <Badge key={idx} variant="destructive" className="text-xs">
                    {failure}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Explanations */}
          {ranking.explanations && Object.keys(ranking.explanations).length > 0 && (
            <div className="mt-4 p-3 bg-background rounded-lg">
              <p className="text-sm font-medium text-foreground mb-2">Evidence:</p>
              <div className="space-y-1">
                {Object.entries(ranking.explanations).map(([key, value]) => (
                  <p key={key} className="text-sm text-muted-foreground">
                    <span className="font-medium capitalize">{key.replace(/_/g, ' ')}:</span>{' '}
                    {value}
                  </p>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

const TalentSearch: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [newPoolName, setNewPoolName] = useState('');
  const [showCreatePool, setShowCreatePool] = useState(false);

  // Fetch talent pools
  const { data: pools, isLoading: poolsLoading } = useQuery({
    queryKey: ['talent-pools'],
    queryFn: listTalentPools,
  });

  // Fetch jobs for the ranking selector
  const { data: jobs } = useQuery({
    queryKey: ['employer-jobs'],
    queryFn: getJobPostings,
  });

  // Fetch rankings when a job is selected
  const { data: rankings, isLoading: rankingsLoading } = useQuery({
    queryKey: ['rankings', selectedJobId],
    queryFn: () => listRankings(Number(selectedJobId)),
    enabled: !!selectedJobId,
  });

  // Create pool mutation
  const createPoolMutation = useMutation({
    mutationFn: (name: string) => createTalentPool({ name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['talent-pools'] });
      setNewPoolName('');
      setShowCreatePool(false);
    },
  });

  // Rank candidates mutation
  const rankMutation = useMutation({
    mutationFn: (jobId: number) => rankCandidates(jobId, undefined, true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rankings', selectedJobId] });
    },
  });

  const handleCreatePool = () => {
    if (newPoolName.trim()) {
      createPoolMutation.mutate(newPoolName.trim());
    }
  };

  const handleRankAll = () => {
    if (selectedJobId) {
      rankMutation.mutate(Number(selectedJobId));
    }
  };

  return (
    <AppShell>
      <div className="page-shell">
        <PageHeader
          title="Talent Pool"
          subtitle="Manage candidate pools and rank talent against your jobs"
          actions={
            <Button asChild variant="outline" size="sm" className="gap-1.5">
              <Link to="/app/employer/dashboard">
                <ArrowLeft className="w-4 h-4" /> Dashboard
              </Link>
            </Button>
          }
        />

        {/* Talent Pools Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Users className="w-6 h-6 text-primary" />
                  <CardTitle className="text-xl">Your Talent Pools</CardTitle>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowCreatePool(!showCreatePool)}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  New Pool
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {/* Create pool form */}
              {showCreatePool && (
                <div className="flex items-center gap-3 mb-6 p-4 bg-primary/10 rounded-lg">
                  <Input
                    placeholder="Pool name..."
                    value={newPoolName}
                    onChange={(e) => setNewPoolName(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleCreatePool()}
                    className="flex-1"
                  />
                  <Button
                    onClick={handleCreatePool}
                    disabled={!newPoolName.trim() || createPoolMutation.isPending}
                  >
                    {createPoolMutation.isPending ? 'Creating...' : 'Create'}
                  </Button>
                  <Button variant="ghost" onClick={() => setShowCreatePool(false)}>
                    Cancel
                  </Button>
                </div>
              )}

              {/* Pool list */}
              {poolsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : pools && pools.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {pools.map((pool) => (
                    <div
                      key={pool.id}
                      className="p-4 border rounded-lg hover:border-primary/40 hover:bg-primary/5 transition"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-foreground">{pool.name}</h4>
                        <Badge variant="secondary">
                          {pool.candidate_count} candidate{pool.candidate_count !== 1 ? 's' : ''}
                        </Badge>
                      </div>
                      {pool.description && (
                        <p className="text-sm text-muted-foreground line-clamp-2">{pool.description}</p>
                      )}
                      <p className="text-xs text-muted-foreground mt-2">
                        Created {new Date(pool.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Users className="w-12 h-12 text-muted-foreground/50 mx-auto mb-3" />
                  <p className="text-muted-foreground">No talent pools yet. Create one to get started.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Rank Candidates Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <Trophy className="w-6 h-6 text-primary" />
                <div>
                  <CardTitle className="text-xl">Rank Candidates</CardTitle>
                  <CardDescription>Select a job and rank all candidates against it</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Job selector and rank button */}
              <div className="flex items-center gap-4 mb-6">
                <div className="flex-1 max-w-sm">
                  <Select value={selectedJobId} onValueChange={setSelectedJobId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a job posting..." />
                    </SelectTrigger>
                    <SelectContent>
                      {jobs?.map((job) => (
                        <SelectItem key={job.id} value={String(job.id)}>
                          {job.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  onClick={handleRankAll}
                  disabled={!selectedJobId || rankMutation.isPending}
                  className="bg-primary hover:bg-primary/90"
                >
                  {rankMutation.isPending ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Ranking...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4 mr-2" />
                      Rank All
                    </>
                  )}
                </Button>
              </div>

              {/* Error state */}
              {rankMutation.isError && (
                <div className="mb-4 p-4 bg-destructive/10 border border-destructive/30 rounded-lg flex items-center gap-3">
                  <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
                  <p className="text-sm text-destructive">
                    Failed to rank candidates. Please try again.
                  </p>
                </div>
              )}

              {/* Rankings display */}
              {rankingsLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : rankings && rankings.length > 0 ? (
                <div>
                  <p className="text-sm text-muted-foreground mb-4">
                    {rankings.length} candidate{rankings.length !== 1 ? 's' : ''} ranked
                  </p>
                  {rankings
                    .sort((a, b) => b.overall_score - a.overall_score)
                    .map((ranking) => (
                      <RankingCard key={ranking.id} ranking={ranking} />
                    ))}
                </div>
              ) : selectedJobId && !rankingsLoading ? (
                <div className="text-center py-12">
                  <Briefcase className="w-12 h-12 text-muted-foreground/50 mx-auto mb-3" />
                  <p className="text-muted-foreground mb-2">No rankings yet for this job.</p>
                  <p className="text-sm text-muted-foreground">Click "Rank All" to generate candidate rankings.</p>
                </div>
              ) : (
                <div className="text-center py-12">
                  <Trophy className="w-12 h-12 text-muted-foreground/50 mx-auto mb-3" />
                  <p className="text-muted-foreground">Select a job to view or generate rankings.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </AppShell>
  );
};

export default TalentSearch;
