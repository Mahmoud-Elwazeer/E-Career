/**
 * Coding Practice Page
 * AI-powered coding interview practice with code execution and evaluation
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Code2,
  Play,
  Send,
  Loader2,
  ChevronRight,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Clock,
  Cpu,
  Lightbulb,
  Terminal,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useMutation } from '@tanstack/react-query';
import { useAuth } from '@/hooks/use-auth';
import { useTheme } from '@/hooks/use-theme';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AuthNavbar } from '@/components/AuthNavbar';
import {
  generateCodingProblem,
  submitCodingSolution,
  evaluateCodingSolution,
  type CodingProblem,
  type ExecutionResult,
  type EvaluationResult,
} from '@/services/interviews';

// ── Constants ────────────────────────────────────────────────────────────────

const DIFFICULTIES = [
  { value: 'easy', label: 'Easy', labelAr: 'سهل', color: 'text-green-600 border-green-600 bg-green-50 dark:bg-green-900/20' },
  { value: 'medium', label: 'Medium', labelAr: 'متوسط', color: 'text-yellow-600 border-yellow-600 bg-yellow-50 dark:bg-yellow-900/20' },
  { value: 'hard', label: 'Hard', labelAr: 'صعب', color: 'text-red-600 border-red-600 bg-red-50 dark:bg-red-900/20' },
];

const LANGUAGES = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'java', label: 'Java' },
  { value: 'c++', label: 'C++' },
];

// ── Component ────────────────────────────────────────────────────────────────

export default function CodingPractice() {
  const { isAuthenticated } = useAuth();
  const { lang } = useTheme();
  const { toast } = useToast();
  const navigate = useNavigate();
  const isAr = lang === 'ar';

  // Form state
  const [difficulty, setDifficulty] = useState('medium');
  const [language, setLanguage] = useState('python');
  const [topic, setTopic] = useState('');

  // Problem / editor state
  const [problem, setProblem] = useState<CodingProblem | null>(null);
  const [code, setCode] = useState('');
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);

  // ── Mutations ──────────────────────────────────────────────────────────────

  const generateMutation = useMutation({
    mutationFn: generateCodingProblem,
    onSuccess: (data) => {
      setProblem(data);
      setCode(data.starter_code || '');
      setExecutionResult(null);
      setEvaluation(null);
      toast({ title: isAr ? 'تم إنشاء المسألة' : 'Problem generated', description: data.title });
    },
    onError: () => {
      toast({ title: isAr ? 'خطأ' : 'Error', description: isAr ? 'فشل في إنشاء المسألة' : 'Failed to generate problem', variant: 'destructive' });
    },
  });

  const runMutation = useMutation({
    mutationFn: submitCodingSolution,
    onSuccess: (data) => {
      setExecutionResult(data);
      setEvaluation(null);
    },
    onError: () => {
      toast({ title: isAr ? 'خطأ' : 'Error', description: isAr ? 'فشل تنفيذ الكود' : 'Failed to execute code', variant: 'destructive' });
    },
  });

  const evaluateMutation = useMutation({
    mutationFn: evaluateCodingSolution,
    onSuccess: (data) => {
      setEvaluation(data);
      toast({ title: isAr ? 'تم التقييم' : 'Evaluated', description: `${isAr ? 'النتيجة' : 'Score'}: ${Math.round(data.score * 100)}%` });
    },
    onError: () => {
      toast({ title: isAr ? 'خطأ' : 'Error', description: isAr ? 'فشل تقييم الحل' : 'Failed to evaluate solution', variant: 'destructive' });
    },
  });

  // ── Handlers ───────────────────────────────────────────────────────────────

  const handleGenerate = () => {
    generateMutation.mutate({ difficulty, language, topic: topic || undefined });
  };

  const handleRun = () => {
    if (!code.trim() || !problem) return;
    runMutation.mutate({ code, language, test_cases: problem.test_cases });
  };

  const handleEvaluate = () => {
    if (!code.trim() || !problem) return;
    // Run first, then evaluate
    if (!executionResult) {
      runMutation.mutate(
        { code, language, test_cases: problem.test_cases },
        {
          onSuccess: (execResult) => {
            evaluateMutation.mutate({ code, language, problem, execution_result: execResult });
          },
        }
      );
    } else {
      evaluateMutation.mutate({ code, language, problem, execution_result: executionResult });
    }
  };

  const handleReset = () => {
    setProblem(null);
    setCode('');
    setExecutionResult(null);
    setEvaluation(null);
  };

  const isLoading = generateMutation.isPending || runMutation.isPending || evaluateMutation.isPending;

  // ── Redirect if not authenticated ──────────────────────────────────────────

  if (!isAuthenticated) {
    navigate('/login', { state: { from: '/app/coding-practice' } });
    return null;
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <AuthNavbar />

      <div className="container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Page header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Code2 className="h-8 w-8 text-blue-600" />
              {isAr ? 'تمرين البرمجة' : 'Coding Practice'}
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mt-2">
              {isAr
                ? 'تدرب على مسائل البرمجة مع تنفيذ وتقييم مدعوم بالذكاء الاصطناعي'
                : 'Practice coding problems with AI-powered execution and evaluation'}
            </p>
          </div>

          {/* Problem generation form — always visible when no problem is loaded */}
          {!problem && (
            <motion.div
              key="form"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <Card className="max-w-2xl mx-auto">
                <CardHeader>
                  <CardTitle>{isAr ? 'إنشاء مسألة' : 'Generate a Problem'}</CardTitle>
                  <CardDescription>
                    {isAr
                      ? 'اختر الصعوبة واللغة والموضوع لإنشاء مسألة جديدة'
                      : 'Choose difficulty, language, and topic to generate a new problem'}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Difficulty */}
                  <div className="space-y-2">
                    <Label>{isAr ? 'مستوى الصعوبة' : 'Difficulty'}</Label>
                    <div className="flex gap-3">
                      {DIFFICULTIES.map((d) => (
                        <button
                          key={d.value}
                          onClick={() => setDifficulty(d.value)}
                          className={cn(
                            'flex-1 py-2 px-4 rounded-lg border-2 font-medium transition-all',
                            difficulty === d.value
                              ? d.color
                              : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'
                          )}
                        >
                          {isAr ? d.labelAr : d.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Language */}
                  <div className="space-y-2">
                    <Label>{isAr ? 'لغة البرمجة' : 'Language'}</Label>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {LANGUAGES.map((l) => (
                        <button
                          key={l.value}
                          onClick={() => setLanguage(l.value)}
                          className={cn(
                            'py-2 px-4 rounded-lg border-2 font-medium transition-all text-center',
                            language === l.value
                              ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20 text-blue-600'
                              : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'
                          )}
                        >
                          {l.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Topic (optional) */}
                  <div className="space-y-2">
                    <Label htmlFor="topic">
                      {isAr ? 'الموضوع (اختياري)' : 'Topic (optional)'}
                    </Label>
                    <Input
                      id="topic"
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      placeholder={isAr ? 'مثال: المصفوفات، الأشجار، البرمجة الديناميكية' : 'e.g., arrays, trees, dynamic programming'}
                      className={isAr ? 'text-right' : ''}
                    />
                  </div>

                  <Button
                    onClick={handleGenerate}
                    disabled={generateMutation.isPending}
                    className="w-full"
                    size="lg"
                  >
                    {generateMutation.isPending ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin me-2" />
                        {isAr ? 'جاري الإنشاء...' : 'Generating...'}
                      </>
                    ) : (
                      <>
                        {isAr ? 'إنشاء المسألة' : 'Generate Problem'}
                        <ChevronRight className="w-5 h-5 ms-2" />
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Problem workspace — shown after generation */}
          {problem && (
            <AnimatePresence mode="wait">
              <motion.div
                key="workspace"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                {/* Top bar */}
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span className={cn(
                      'px-3 py-1 rounded-full text-xs font-semibold uppercase',
                      problem.difficulty === 'easy' && 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
                      problem.difficulty === 'medium' && 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
                      problem.difficulty === 'hard' && 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
                    )}>
                      {problem.difficulty}
                    </span>
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                      {problem.language_name}
                    </span>
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                      {problem.topic}
                    </span>
                  </div>
                  <Button variant="outline" size="sm" onClick={handleReset}>
                    <RotateCcw className="w-4 h-4 me-2" />
                    {isAr ? 'مسألة جديدة' : 'New Problem'}
                  </Button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Left column — problem description */}
                  <div className="space-y-6">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-xl">{problem.title}</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                          {problem.description}
                        </p>

                        {/* Examples */}
                        {problem.examples?.length > 0 && (
                          <div className="space-y-3">
                            <h4 className="font-semibold text-sm uppercase text-gray-500">
                              {isAr ? 'أمثلة' : 'Examples'}
                            </h4>
                            {problem.examples.map((ex, i) => (
                              <div key={i} className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 space-y-1 text-sm font-mono">
                                <div><span className="text-gray-500">{isAr ? 'الإدخال:' : 'Input:'}</span> {ex.input}</div>
                                <div><span className="text-gray-500">{isAr ? 'الإخراج:' : 'Output:'}</span> {ex.output}</div>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Constraints */}
                        {problem.constraints?.length > 0 && (
                          <div className="space-y-2">
                            <h4 className="font-semibold text-sm uppercase text-gray-500">
                              {isAr ? 'القيود' : 'Constraints'}
                            </h4>
                            <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-400 space-y-1">
                              {problem.constraints.map((c, i) => (
                                <li key={i}>{c}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>

                  {/* Right column — code editor + actions */}
                  <div className="space-y-4">
                    {/* Code editor */}
                    <Card className="overflow-hidden">
                      <CardHeader className="pb-2">
                        <CardTitle className="flex items-center gap-2 text-base">
                          <Terminal className="w-4 h-4" />
                          {isAr ? 'محرر الكود' : 'Code Editor'}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="p-0">
                        <textarea
                          value={code}
                          onChange={(e) => setCode(e.target.value)}
                          spellCheck={false}
                          className={cn(
                            'w-full min-h-[350px] p-4 font-mono text-sm leading-relaxed resize-y',
                            'bg-gray-900 text-gray-100 focus:outline-none',
                            'border-0 rounded-none',
                            isAr ? 'text-left' : '' // Code is always LTR
                          )}
                          dir="ltr"
                          placeholder="// Write your solution here..."
                        />
                      </CardContent>
                    </Card>

                    {/* Action buttons */}
                    <div className="flex gap-3">
                      <Button
                        onClick={handleRun}
                        disabled={!code.trim() || isLoading}
                        variant="outline"
                        className="flex-1"
                      >
                        {runMutation.isPending ? (
                          <Loader2 className="w-4 h-4 animate-spin me-2" />
                        ) : (
                          <Play className="w-4 h-4 me-2" />
                        )}
                        {isAr ? 'تشغيل' : 'Run'}
                      </Button>
                      <Button
                        onClick={handleEvaluate}
                        disabled={!code.trim() || isLoading}
                        className="flex-1"
                      >
                        {evaluateMutation.isPending ? (
                          <Loader2 className="w-4 h-4 animate-spin me-2" />
                        ) : (
                          <Send className="w-4 h-4 me-2" />
                        )}
                        {isAr ? 'تقييم' : 'Submit'}
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Results panel */}
                <AnimatePresence>
                  {(executionResult || evaluation) && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="space-y-6"
                    >
                      {/* Execution output */}
                      {executionResult && (
                        <Card>
                          <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-base">
                              <Terminal className="w-4 h-4" />
                              {isAr ? 'نتيجة التنفيذ' : 'Execution Output'}
                              {executionResult.success ? (
                                <CheckCircle2 className="w-4 h-4 text-green-500 ms-auto" />
                              ) : (
                                <XCircle className="w-4 h-4 text-red-500 ms-auto" />
                              )}
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-3">
                            {executionResult.status && (
                              <div className="flex items-center gap-2 text-sm">
                                <span className="text-gray-500">{isAr ? 'الحالة:' : 'Status:'}</span>
                                <span className={cn(
                                  'font-medium',
                                  executionResult.success ? 'text-green-600' : 'text-red-600'
                                )}>
                                  {executionResult.status}
                                </span>
                              </div>
                            )}

                            {executionResult.output && (
                              <div>
                                <p className="text-xs font-semibold text-gray-500 mb-1 uppercase">{isAr ? 'الإخراج' : 'stdout'}</p>
                                <pre className="bg-gray-900 text-gray-100 p-3 rounded-lg text-sm font-mono overflow-x-auto whitespace-pre-wrap">
                                  {executionResult.output}
                                </pre>
                              </div>
                            )}

                            {executionResult.stderr && (
                              <div>
                                <p className="text-xs font-semibold text-red-500 mb-1 uppercase">{isAr ? 'الأخطاء' : 'stderr'}</p>
                                <pre className="bg-red-950 text-red-300 p-3 rounded-lg text-sm font-mono overflow-x-auto whitespace-pre-wrap">
                                  {executionResult.stderr}
                                </pre>
                              </div>
                            )}

                            {executionResult.error && (
                              <div className="text-sm text-red-600 dark:text-red-400">
                                {executionResult.error}
                              </div>
                            )}

                            <div className="flex gap-6 text-xs text-gray-500 pt-2 border-t border-gray-100 dark:border-gray-800">
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {executionResult.execution_time}s
                              </span>
                              <span className="flex items-center gap-1">
                                <Cpu className="w-3 h-3" />
                                {executionResult.memory ? `${Math.round(executionResult.memory / 1024)} KB` : 'N/A'}
                              </span>
                            </div>
                          </CardContent>
                        </Card>
                      )}

                      {/* Evaluation results */}
                      {evaluation && (
                        <Card className="border-blue-200 dark:border-blue-900">
                          <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                              <Lightbulb className="w-5 h-5 text-blue-600" />
                              {isAr ? 'نتيجة التقييم' : 'Evaluation Results'}
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-6">
                            {/* Score cards */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                              <ScoreCard
                                label={isAr ? 'الإجمالي' : 'Overall'}
                                value={evaluation.score}
                                color="blue"
                              />
                              <ScoreCard
                                label={isAr ? 'الدقة' : 'Correctness'}
                                value={evaluation.correctness}
                                color="green"
                              />
                              <ScoreCard
                                label={isAr ? 'الكفاءة' : 'Efficiency'}
                                value={evaluation.efficiency}
                                color="yellow"
                              />
                              <ScoreCard
                                label={isAr ? 'الأسلوب' : 'Style'}
                                value={evaluation.style}
                                color="purple"
                              />
                            </div>

                            {/* Test results */}
                            <div className="flex items-center gap-4 text-sm">
                              <span className="flex items-center gap-1 text-green-600">
                                <CheckCircle2 className="w-4 h-4" />
                                {evaluation.tests_passed} {isAr ? 'نجح' : 'passed'}
                              </span>
                              <span className="flex items-center gap-1 text-red-600">
                                <XCircle className="w-4 h-4" />
                                {evaluation.tests_failed} {isAr ? 'فشل' : 'failed'}
                              </span>
                              <span className="text-gray-500">
                                / {evaluation.total_tests} {isAr ? 'اختبار' : 'tests'}
                              </span>
                            </div>

                            {/* Suggestions */}
                            {evaluation.suggestions?.length > 0 && (
                              <div className="space-y-2">
                                <h4 className="font-semibold text-sm uppercase text-gray-500">
                                  {isAr ? 'اقتراحات التحسين' : 'Suggestions'}
                                </h4>
                                <ul className="space-y-2">
                                  {evaluation.suggestions.map((s, i) => (
                                    <li key={i} className="flex gap-2 text-sm text-gray-700 dark:text-gray-300">
                                      <Lightbulb className="w-4 h-4 text-yellow-500 shrink-0 mt-0.5" />
                                      {s}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            </AnimatePresence>
          )}
        </motion.div>
      </div>
    </div>
  );
}

// ── Helper component ─────────────────────────────────────────────────────────

function ScoreCard({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.round(value * 100);
  const colorMap: Record<string, string> = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    yellow: 'text-yellow-600',
    purple: 'text-purple-600',
  };
  const bgMap: Record<string, string> = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    yellow: 'bg-yellow-600',
    purple: 'bg-purple-600',
  };

  return (
    <div className="text-center space-y-2">
      <p className="text-xs font-semibold text-gray-500 uppercase">{label}</p>
      <p className={cn('text-2xl font-bold', colorMap[color])}>{pct}%</p>
      <div className="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all duration-500', bgMap[color])}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
