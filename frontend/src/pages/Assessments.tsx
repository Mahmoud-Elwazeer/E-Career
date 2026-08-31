import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AuthNavbar } from '@/components/AuthNavbar';
import { apiRequest } from '@/services/client';
import { useTheme } from '@/hooks/use-theme';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Award, Clock, CheckCircle2, XCircle, Play, Trophy,
  BookOpen, Target, ChevronRight, Star, BarChart3,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface AssessmentTemplate {
  id: number;
  name: string;
  description: string;
  skill_area: string;
  difficulty: string;
  estimated_minutes: number;
}

interface Assessment {
  id: number;
  title: string;
  description: string;
  skill_area: string;
  difficulty: string;
  duration_minutes: number;
  passing_score: number;
  is_active: boolean;
}

interface AssessmentAttempt {
  id: number;
  assessment: Assessment;
  started_at: string;
  completed_at: string | null;
  score: number | null;
  passed: boolean | null;
}

interface SkillBadge {
  id: number;
  skill_name: string;
  badge_level: string;
  earned_at: string;
  evidence: string;
}

interface ActiveSession {
  id: number;
  questions: { question_text: string; question_type: string; options: string[]; points: number }[];
}

const difficultyColor: Record<string, string> = {
  easy: 'bg-green-500/10 text-green-600 border-green-500/20',
  medium: 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20',
  hard: 'bg-red-500/10 text-red-600 border-red-500/20',
};

const badgeLevelColor: Record<string, string> = {
  bronze: 'from-orange-700 to-orange-500',
  silver: 'from-gray-400 to-gray-300',
  gold: 'from-yellow-500 to-yellow-400',
  platinum: 'from-cyan-400 to-blue-400',
};

export default function AssessmentsPage() {
  const { lang } = useTheme();
  const isAr = lang === 'ar';
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'templates' | 'attempts' | 'badges'>('templates');
  const [activeSession, setActiveSession] = useState<ActiveSession | null>(null);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});

  const { data: templates } = useQuery({
    queryKey: ['assessment-templates'],
    queryFn: () => apiRequest<AssessmentTemplate[]>('/assessment/templates/'),
  });

  const { data: attempts } = useQuery({
    queryKey: ['assessment-attempts'],
    queryFn: () => apiRequest<AssessmentAttempt[]>('/assessment/attempts/'),
  });

  const { data: badges } = useQuery({
    queryKey: ['skill-badges'],
    queryFn: () => apiRequest<SkillBadge[]>('/assessment/badges/'),
  });

  const startAssessment = useMutation({
    mutationFn: (templateId: number) =>
      apiRequest<ActiveSession>('/assessment/assessments/start/', {
        method: 'POST',
        body: { template_id: templateId },
      }),
    onSuccess: (data) => {
      setActiveSession(data);
      setCurrentQ(0);
      setAnswers({});
    },
  });

  const submitAssessment = useMutation({
    mutationFn: () =>
      apiRequest(`/assessment/assessments/${activeSession?.id}/submit/`, {
        method: 'POST',
        body: {
          answers: Object.entries(answers).map(([qi, answer]) => ({
            question_index: Number(qi),
            answer,
          })),
        },
      }),
    onSuccess: () => {
      setActiveSession(null);
      setCurrentQ(0);
      setAnswers({});
      queryClient.invalidateQueries({ queryKey: ['assessment-attempts'] });
      queryClient.invalidateQueries({ queryKey: ['skill-badges'] });
      setActiveTab('attempts');
    },
  });

  const tabs = [
    { key: 'templates' as const, label: isAr ? 'التقييمات المتاحة' : 'Available', icon: BookOpen },
    { key: 'attempts' as const, label: isAr ? 'محاولاتي' : 'My Attempts', icon: BarChart3 },
    { key: 'badges' as const, label: isAr ? 'الشارات' : 'Badges', icon: Trophy },
  ];

  if (activeSession) {
    const questions = activeSession.questions || [];
    const q = questions[currentQ];
    const total = questions.length;

    return (
      <div className="min-h-screen bg-background">
        <AuthNavbar />
        <main className="container py-8 max-w-2xl">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>{isAr ? 'التقييم' : 'Assessment'}</CardTitle>
                <span className="text-sm text-muted-foreground">
                  {currentQ + 1} / {total}
                </span>
              </div>
              <div className="w-full bg-muted rounded-full h-2 mt-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all"
                  style={{ width: `${((currentQ + 1) / total) * 100}%` }}
                />
              </div>
            </CardHeader>
            <CardContent>
              {q ? (
                <div className="space-y-6">
                  <h3 className="text-lg font-medium">{q.question_text}</h3>
                  <div className="space-y-3">
                    {(q.options || []).map((option: string, i: number) => (
                      <button
                        key={i}
                        onClick={() => setAnswers(p => ({ ...p, [currentQ]: option }))}
                        className={`w-full text-start p-4 rounded-lg border transition-all ${
                          answers[currentQ] === option
                            ? 'border-primary bg-primary/10 ring-2 ring-primary/20'
                            : 'border-border hover:bg-accent'
                        }`}
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                  <div className="flex justify-between pt-4">
                    <Button
                      variant="outline"
                      onClick={() => setCurrentQ(p => Math.max(0, p - 1))}
                      disabled={currentQ === 0}
                    >
                      {isAr ? 'السابق' : 'Previous'}
                    </Button>
                    {currentQ < total - 1 ? (
                      <Button
                        onClick={() => setCurrentQ(p => p + 1)}
                        disabled={!answers[currentQ]}
                      >
                        {isAr ? 'التالي' : 'Next'}
                        <ChevronRight className="h-4 w-4 ms-1" />
                      </Button>
                    ) : (
                      <Button
                        onClick={() => submitAssessment.mutate()}
                        disabled={!answers[currentQ] || submitAssessment.isPending}
                      >
                        {submitAssessment.isPending
                          ? (isAr ? 'جاري الإرسال...' : 'Submitting...')
                          : (isAr ? 'إرسال الإجابات' : 'Submit')}
                      </Button>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  {isAr ? 'لا توجد أسئلة' : 'No questions available'}
                </div>
              )}
            </CardContent>
          </Card>
          <div className="text-center mt-4">
            <Button variant="ghost" onClick={() => setActiveSession(null)}>
              {isAr ? 'إلغاء والعودة' : 'Cancel & Go Back'}
            </Button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <AuthNavbar />
      <main className="container py-8 space-y-6">
        <div>
          <h1 className="text-3xl font-bold">
            <Award className="inline h-8 w-8 text-primary me-2" />
            {isAr ? 'التقييمات والشارات' : 'Assessments & Badges'}
          </h1>
          <p className="text-muted-foreground mt-1">
            {isAr ? 'أثبت مهاراتك واحصل على شارات تميزك' : 'Prove your skills and earn badges that set you apart'}
          </p>
        </div>

        {/* Badge summary */}
        {badges && badges.length > 0 && (
          <div className="flex flex-wrap gap-3">
            {badges.map((badge) => (
              <div
                key={badge.id}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r ${badgeLevelColor[badge.badge_level] || badgeLevelColor['bronze']} text-white text-sm font-medium`}
              >
                <Star className="h-3.5 w-3.5" />
                {badge.skill_name}
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 border-b">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {activeTab === 'templates' && (
            <motion.div
              key="templates"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
            >
              {!templates || templates.length === 0 ? (
                <div className="col-span-full text-center py-12 text-muted-foreground">
                  {isAr ? 'لا توجد تقييمات متاحة حالياً' : 'No assessments available yet'}
                </div>
              ) : (
                templates.map((t) => (
                  <Card key={t.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between mb-3">
                        <Target className="h-8 w-8 text-primary" />
                        <span className={`text-xs px-2 py-0.5 rounded-full border ${difficultyColor[t.difficulty] || ''}`}>
                          {t.difficulty}
                        </span>
                      </div>
                      <h3 className="font-semibold text-lg mb-1">{t.name}</h3>
                      <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{t.description}</p>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground mb-4">
                        <span className="flex items-center gap-1">
                          <BookOpen className="h-3.5 w-3.5" /> {t.skill_area}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5" /> {t.estimated_minutes} {isAr ? 'دقيقة' : 'min'}
                        </span>
                      </div>
                      <Button
                        className="w-full"
                        onClick={() => startAssessment.mutate(t.id)}
                        disabled={startAssessment.isPending}
                      >
                        <Play className="h-4 w-4 me-2" />
                        {startAssessment.isPending ? (isAr ? 'جاري البدء...' : 'Starting...') : (isAr ? 'ابدأ التقييم' : 'Start Assessment')}
                      </Button>
                    </CardContent>
                  </Card>
                ))
              )}
            </motion.div>
          )}

          {activeTab === 'attempts' && (
            <motion.div
              key="attempts"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-3"
            >
              {!attempts || attempts.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  {isAr ? 'لم تقم بأي تقييم بعد' : "You haven't taken any assessments yet"}
                </div>
              ) : (
                attempts.map((a) => (
                  <Card key={a.id}>
                    <CardContent className="py-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-medium">{a.assessment?.title || `Assessment #${a.id}`}</h4>
                          <p className="text-sm text-muted-foreground">
                            {new Date(a.started_at).toLocaleDateString(isAr ? 'ar-EG' : 'en-US', {
                              year: 'numeric', month: 'short', day: 'numeric',
                            })}
                            {a.assessment?.skill_area && ` · ${a.assessment.skill_area}`}
                          </p>
                        </div>
                        <div className="flex items-center gap-3">
                          {a.score !== null && (
                            <div className="text-end">
                              <p className="text-2xl font-bold">{a.score}%</p>
                            </div>
                          )}
                          {a.passed !== null && (
                            a.passed ? (
                              <CheckCircle2 className="h-6 w-6 text-green-500" />
                            ) : (
                              <XCircle className="h-6 w-6 text-red-500" />
                            )
                          )}
                          {!a.completed_at && (
                            <span className="text-xs px-2 py-1 rounded-full bg-yellow-500/10 text-yellow-600">
                              {isAr ? 'قيد التنفيذ' : 'In Progress'}
                            </span>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </motion.div>
          )}

          {activeTab === 'badges' && (
            <motion.div
              key="badges"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
            >
              {!badges || badges.length === 0 ? (
                <div className="col-span-full text-center py-12 text-muted-foreground">
                  <Trophy className="h-12 w-12 mx-auto mb-3 text-muted-foreground/30" />
                  <p>{isAr ? 'لم تحصل على شارات بعد. أكمل تقييماً لتبدأ!' : 'No badges yet. Complete an assessment to earn your first!'}</p>
                </div>
              ) : (
                badges.map((badge) => (
                  <Card key={badge.id} className="overflow-hidden">
                    <div className={`h-2 bg-gradient-to-r ${badgeLevelColor[badge.badge_level] || badgeLevelColor['bronze']}`} />
                    <CardContent className="pt-5">
                      <div className="flex items-center gap-3">
                        <div className={`h-12 w-12 rounded-full flex items-center justify-center bg-gradient-to-br ${badgeLevelColor[badge.badge_level] || badgeLevelColor['bronze']}`}>
                          <Award className="h-6 w-6 text-white" />
                        </div>
                        <div>
                          <h4 className="font-semibold">{badge.skill_name}</h4>
                          <p className="text-sm text-muted-foreground capitalize">{badge.badge_level}</p>
                        </div>
                      </div>
                      <p className="text-xs text-muted-foreground mt-3">
                        {isAr ? 'حصلت عليها' : 'Earned'}{' '}
                        {new Date(badge.earned_at).toLocaleDateString(isAr ? 'ar-EG' : 'en-US', {
                          year: 'numeric', month: 'short', day: 'numeric',
                        })}
                      </p>
                    </CardContent>
                  </Card>
                ))
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
