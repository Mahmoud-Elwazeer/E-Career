/**
 * Interview Practice Page
 * AI-powered mock interview practice with scoring and feedback
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Mic, 
  CheckCircle, 
  XCircle, 
  ChevronRight, 
  ChevronLeft, 
  Loader2, 
  BarChart3,
  Award,
  Target,
  MessageSquare,
  ArrowRight
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/hooks/use-auth';
import { useTheme } from '@/hooks/use-theme';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  Radar, 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  ResponsiveContainer,
  Tooltip
} from 'recharts';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

type InterviewType = 'technical' | 'behavioral' | 'coding' | 'system_design' | 'case_study';
type Difficulty = 'easy' | 'medium' | 'hard';

interface Question {
  id: number;
  index: number;
  question: string;
  answer?: string;
  score?: number;
  feedback?: string;
  dimensions?: Record<string, number>;
}

interface InterviewSession {
  id: string;
  interview_type: InterviewType;
  target_role: string;
  difficulty: Difficulty;
  questions: Question[];
  overall_score?: number;
  score_breakdown?: {
    dimensions: Record<string, number>;
    total_questions: number;
    average_score: number;
  };
  feedback_summary?: string;
}

const INTERVIEW_TYPES = [
  { value: 'technical', label: 'Technical', labelAr: 'تقني', icon: CodeIcon },
  { value: 'behavioral', label: 'Behavioral', labelAr: 'سلوكي', icon: UsersIcon },
  { value: 'coding', label: 'Coding', labelAr: 'برمجة', icon: CodeIcon },
  { value: 'system_design', label: 'System Design', labelAr: 'تصميم النظام', icon: LayoutIcon },
  { value: 'case_study', label: 'Case Study', labelAr: 'دراسة حالة', icon: BookIcon },
];

const DIFFICULTIES = [
  { value: 'easy', label: 'Easy', labelAr: 'سهل' },
  { value: 'medium', label: 'Medium', labelAr: 'متوسط' },
  { value: 'hard', label: 'Hard', labelAr: 'صعب' },
];

// Icons
function CodeIcon({ className }: { className?: string }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>;
}
function UsersIcon({ className }: { className?: string }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>;
}
function LayoutIcon({ className }: { className?: string }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" /></svg>;
}
function BookIcon({ className }: { className?: string }) {
  return <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>;
}

export default function InterviewPractice() {
  const { isAuthenticated } = useAuth();
  const { lang } = useTheme();
  const isAr = lang === 'ar';
  const navigate = useNavigate();

  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answer, setAnswer] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [targetRole, setTargetRole] = useState('');
  const [selectedType, setSelectedType] = useState<InterviewType>('technical');
  const [selectedDifficulty, setSelectedDifficulty] = useState<Difficulty>('medium');

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: '/app/interviews' } });
    }
  }, [isAuthenticated, navigate]);

  // Start new interview
  const startInterview = async () => {
    if (!targetRole.trim()) return;
    
    setIsProcessing(true);
    try {
      const response = await fetch(`${API_BASE_URL}/interviews/start/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
        body: JSON.stringify({
          interview_type: selectedType,
          target_role: targetRole,
          difficulty: selectedDifficulty,
          mode: 'text',
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSession({
          id: data.session_id,
          interview_type: data.interview_type,
          target_role: data.target_role,
          difficulty: data.difficulty,
          questions: data.current_question ? [{
            id: data.current_question.id,
            index: data.current_question.index,
            question: data.current_question.question,
          }] : [],
        });
        setStep(2);
        setCurrentQuestionIndex(0);
      }
    } catch (error) {
      console.error('Error starting interview:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Submit answer
  const submitAnswer = async () => {
    if (!answer.trim() || !session) return;
    
    setIsProcessing(true);
    try {
      const response = await fetch(`${API_BASE_URL}/interviews/${session.id}/answer/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
        body: JSON.stringify({ answer }),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Update current question with score
        const updatedQuestions = [...session.questions];
        updatedQuestions[currentQuestionIndex] = {
          ...updatedQuestions[currentQuestionIndex],
          answer,
          score: data.score,
          feedback: data.feedback,
          dimensions: data.dimensions,
        };
        
        setSession({
          ...session,
          questions: updatedQuestions,
        });
        
        if (data.next_question) {
          // Add next question
          const nextQuestion = {
            id: data.next_question.id,
            index: data.next_question.index,
            question: data.next_question.question,
          };
          setSession({
            ...session,
            questions: [...updatedQuestions, nextQuestion],
          });
          setCurrentQuestionIndex(currentQuestionIndex + 1);
          setAnswer('');
        } else {
          // All questions answered, go to results
          await completeInterview();
        }
      }
    } catch (error) {
      console.error('Error submitting answer:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Complete interview
  const completeInterview = async () => {
    if (!session) return;
    
    setIsProcessing(true);
    try {
      const response = await fetch(`${API_BASE_URL}/interviews/${session.id}/complete/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSession({
          ...session,
          overall_score: data.overall_score,
          score_breakdown: data.score_breakdown,
          feedback_summary: data.feedback_summary,
        });
        setStep(3);
      }
    } catch (error) {
      console.error('Error completing interview:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Render step 1: Configuration
  const renderStep1 = () => (
    <div className="max-w-2xl mx-auto space-y-8">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold">
          {isAr ? 'ابدأ مقابلة تدريبية' : 'Start a Mock Interview'}
        </h2>
        <p className="text-gray-500 dark:text-gray-400">
          {isAr 
            ? 'اختر نوع المقابلة والوظيفة المستهدفة لبدء التدريب'
            : 'Select interview type and target role to begin practice'}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            {isAr ? 'إعدادات المقابلة' : 'Interview Settings'}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Target Role */}
          <div className="space-y-2">
            <Label htmlFor="targetRole">
              {isAr ? 'الوظيفة المستهدفة' : 'Target Role'}
            </Label>
            <Input
              id="targetRole"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              placeholder={isAr ? 'مثال: مهندس برمجيات' : 'e.g., Software Engineer'}
              className={isAr ? 'text-right' : ''}
            />
          </div>

          {/* Interview Type */}
          <div className="space-y-2">
            <Label>{isAr ? 'نوع المقابلة' : 'Interview Type'}</Label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {INTERVIEW_TYPES.map((type) => (
                <button
                  key={type.value}
                  onClick={() => setSelectedType(type.value as InterviewType)}
                  className={cn(
                    'flex flex-col items-center justify-center p-4 rounded-lg border-2 transition-all',
                    selectedType === type.value
                      ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-blue-300'
                  )}
                >
                  <type.icon className="w-8 h-8 mb-2 text-blue-600" />
                  <span className="text-sm font-medium">{isAr ? type.labelAr : type.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Difficulty */}
          <div className="space-y-2">
            <Label>{isAr ? 'مستوى الصعوبة' : 'Difficulty Level'}</Label>
            <div className="flex gap-3">
              {DIFFICULTIES.map((diff) => (
                <button
                  key={diff.value}
                  onClick={() => setSelectedDifficulty(diff.value as Difficulty)}
                  className={cn(
                    'flex-1 py-2 px-4 rounded-lg border transition-all',
                    selectedDifficulty === diff.value
                      ? 'border-blue-600 bg-blue-600 text-white'
                      : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'
                  )}
                >
                  {isAr ? diff.labelAr : diff.label}
                </button>
              ))}
            </div>
          </div>

          <Button
            onClick={startInterview}
            disabled={!targetRole.trim() || isProcessing}
            className="w-full"
            size="lg"
          >
            {isProcessing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin mr-2" />
                {isAr ? 'جاري البدء...' : 'Starting...'}
              </>
            ) : (
              <>
                {isAr ? 'ابدأ المقابلة' : 'Start Interview'}
                <ChevronRight className="w-5 h-5 mr-2" />
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );

  // Render step 2: Q&A Flow
  const renderStep2 = () => {
    const currentQuestion = session?.questions[currentQuestionIndex];
    const totalQuestions = session?.questions.length || 0;

    return (
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Progress Header */}
        <div className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => setStep(1)}>
            {isAr ? 'عودة' : 'Back'}
          </Button>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">
              {isAr ? 'سؤال' : 'Question'} {currentQuestionIndex + 1} / {totalQuestions}
            </span>
            <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-600 transition-all duration-300"
                style={{ width: `${((currentQuestionIndex + 1) / totalQuestions) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Question Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-blue-600" />
              {isAr ? 'السؤال' : 'Question'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-medium leading-relaxed">
              {currentQuestion?.question}
            </p>
          </CardContent>
        </Card>

        {/* Answer Area */}
        <Card>
          <CardHeader>
            <CardTitle>
              {isAr ? 'إجابتك' : 'Your Answer'}
            </CardTitle>
            <CardDescription>
              {isAr 
                ? 'اكتب إجابتك بتفصيل كافٍ لتقييمها بدقة'
                : 'Write your answer with enough detail for accurate evaluation'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder={isAr 
                ? 'اكتب إجابتك هنا...' 
                : 'Type your answer here...'}
              className={cn(
                'min-h-[200px] resize-y',
                isAr ? 'text-right' : ''
              )}
            />
            <div className="mt-4 flex justify-end">
              <Button
                onClick={submitAnswer}
                disabled={!answer.trim() || isProcessing}
                size="lg"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin mr-2" />
                    {isAr ? 'جاري التقييم...' : 'Evaluating...'}
                  </>
                ) : (
                  <>
                    {isAr ? 'إرسال الإجابة' : 'Submit Answer'}
                    <ChevronRight className="w-5 h-5 mr-2" />
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Previous Answer (if any) */}
        {currentQuestionIndex > 0 && (
          <Card className="border-green-200 dark:border-green-900">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-green-600">
                <CheckCircle className="w-5 h-5" />
                {isAr ? 'السؤال السابق' : 'Previous Question'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-medium mb-2">
                {session?.questions[currentQuestionIndex - 1]?.question}
              </p>
              <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                <p className="text-sm text-green-800 dark:text-green-200">
                  {isAr ? 'الإجابة:' : 'Answer:'} 
                  {session?.questions[currentQuestionIndex - 1]?.answer}
                </p>
                <p className="text-sm text-green-800 dark:text-green-200 mt-1">
                  {isAr ? 'النتيجة:' : 'Score:'} 
                  {session?.questions[currentQuestionIndex - 1]?.score}/10
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  // Render step 3: Results
  const renderStep3 = () => {
    if (!session?.score_breakdown) return null;

    const dimensions = session.score_breakdown.dimensions;
    const chartData = dimensions ? Object.entries(dimensions).map(([name, value]) => ({
      subject: name,
      A: value,
      fullMark: 10,
    })) : [];

    return (
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Results Header */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-blue-100 dark:bg-blue-900/30">
            <Award className="w-12 h-12 text-blue-600" />
          </div>
          <h2 className="text-4xl font-bold">
            {isAr ? 'نتيجة المقابلة' : 'Interview Results'}
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            {isAr ? 'ممتاز! لقد أتممت المقابلة' : 'Great job! You completed the interview'}
          </p>
        </div>

        {/* Overall Score */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="text-center">
            <CardHeader>
              <CardDescription>
                {isAr ? 'النتيجة الإجمالية' : 'Overall Score'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-5xl font-bold text-blue-600">
                {session.overall_score}/10
              </div>
              <div className="mt-2">
                {session.overall_score! >= 8 ? (
                  <span className="text-green-600 font-medium">
                    {isAr ? 'ممتاز' : 'Excellent'}
                  </span>
                ) : session.overall_score! >= 6 ? (
                  <span className="text-blue-600 font-medium">
                    {isAr ? 'جيد جداً' : 'Very Good'}
                  </span>
                ) : (
                  <span className="text-yellow-600 font-medium">
                    {isAr ? 'جيد' : 'Good'}
                  </span>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <CardDescription>
                {isAr ? 'عدد الأسئلة' : 'Questions'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-5xl font-bold text-gray-900 dark:text-white">
                {session.score_breakdown.total_questions}
              </div>
              <div className="mt-2 text-gray-500">
                {isAr ? 'تمت الإجابة' : 'Answered'}
              </div>
            </CardContent>
          </Card>

          <Card className="text-center">
            <CardHeader>
              <CardDescription>
                {isAr ? 'المجال' : 'Field'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {session.target_role}
              </div>
              <div className="mt-2 text-gray-500 capitalize">
                {isAr 
                  ? INTERVIEW_TYPES.find(t => t.value === session.interview_type)?.labelAr 
                  : INTERVIEW_TYPES.find(t => t.value === session.interview_type)?.label}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Radar Chart */}
        {chartData.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-blue-600" />
                {isAr ? 'تحليل الأداء' : 'Performance Analysis'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
                    <PolarGrid />
                    <PolarAngleAxis 
                      dataKey="subject" 
                      tick={{ fill: '#6b7280', fontSize: 12 }}
                    />
                    <PolarRadiusAxis angle={30} domain={[0, 10]} />
                    <Radar
                      name="Score"
                      dataKey="A"
                      stroke="#3b82f6"
                      fill="#3b82f6"
                      fillOpacity={0.6}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: 'white',
                        borderRadius: '8px',
                        border: '1px solid #e5e7eb'
                      }}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Feedback Summary */}
        {session.feedback_summary && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-blue-600" />
                {isAr ? 'ملخص التغذية الراجعة' : 'Feedback Summary'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-lg leading-relaxed">
                {session.feedback_summary}
              </p>
            </CardContent>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="flex gap-4 justify-center">
          <Button onClick={() => setStep(1)} variant="outline" size="lg">
            {isAr ? 'مقابلة جديدة' : 'New Interview'}
          </Button>
          <Button onClick={() => navigate('/app/profile')} size="lg">
            {isAr ? 'عرض الملف الشخصي' : 'View Profile'}
          </Button>
        </div>
      </div>
    );
  };

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 py-8">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="mb-8">
            <h1 className="text-3xl font-bold">
              {isAr ? 'تدريب المقابلات' : 'Interview Practice'}
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mt-2">
              {isAr 
                ? 'مارس مهاراتك مع الذكاء الاصطناعي' 
                : 'Practice your skills with AI'}
            </p>
          </div>

          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                {renderStep1()}
              </motion.div>
            )}
            {step === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                {renderStep2()}
              </motion.div>
            )}
            {step === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                {renderStep3()}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  );
}