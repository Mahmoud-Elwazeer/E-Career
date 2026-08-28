/**
 * Talent Score Dashboard
 * 
 * A comprehensive dashboard showing multi-dimensional talent scores with:
 * - Radar chart for score breakdown
 * - Trend analysis over time
 * - Recommended actions for improvement
 * - Detailed explanations for each dimension
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Trophy, 
  TrendingUp, 
  TrendingDown, 
  Target, 
  BookOpen, 
  Code, 
  Briefcase, 
  GraduationCap, 
  MessageSquare,
  Activity,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  RefreshCw
} from 'lucide-react';
import { 
  Radar, 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  Cell
} from 'recharts';
import scoresApi, { calculateGrade, getGradeColor, getTrendColor } from '../services/scores';

// Score dimension configuration
const DIMENSION_CONFIG = {
  skill_score: {
    label: 'Skills',
    icon: Code,
    color: '#3b82f6',
    weight: 0.25,
    description: 'Technical depth, breadth, and market demand'
  },
  experience_score: {
    label: 'Experience',
    icon: Briefcase,
    color: '#8b5cf6',
    weight: 0.20,
    description: 'Years relevant to target role and career progression'
  },
  education_score: {
    label: 'Education',
    icon: GraduationCap,
    color: '#10b981',
    weight: 0.15,
    description: 'Degrees relevance and certifications'
  },
  portfolio_score: {
    label: 'Portfolio',
    icon: Target,
    color: '#f59e0b',
    weight: 0.15,
    description: 'GitHub activity and project quality'
  },
  growth_score: {
    label: 'Growth',
    icon: TrendingUp,
    color: '#ec4899',
    weight: 0.15,
    description: 'Learning velocity and skill acquisition'
  },
  communication_score: {
    label: 'Communication',
    icon: MessageSquare,
    color: '#6366f1',
    weight: 0.10,
    description: 'CV clarity and profile writing quality'
  },
  interview_score: {
    label: 'Interview',
    icon: Activity,
    color: '#f97316',
    weight: 0.15,
    description: 'Interview performance and preparation'
  },
};

// Type definitions
interface ScoreDimension {
  dimension: string;
  value: number;
  label: string;
  color: string;
  weight: number;
  description: string;
}

interface ScoreTrend {
  dimension: string;
  current_value: number;
  previous_value: number;
  change: number;
  direction: 'improving' | 'stable' | 'declining';
}

// Main component
export default function TalentScoreDashboard() {
  const [scores, setScores] = useState<any>(null);
  const [trends, setTrends] = useState<any>(null);
  const [actions, setActions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recalculating, setRecalculating] = useState(false);

  // Load scores on mount
  useEffect(() => {
    loadScores();
  }, []);

  const loadScores = async () => {
    try {
      setLoading(true);
      const [scoresRes, trendsRes, actionsRes] = await Promise.all([
        scoresApi.getScores(),
        scoresApi.getScoreTrends(),
        scoresApi.getAllScoresWithActions()
      ]);

      if (scoresRes.success) {
        setScores(scoresRes.data);
      }
      if (trendsRes.success) {
        setTrends(trendsRes.data);
      }
      if (actionsRes.success) {
        setActions(actionsRes.data.actions);
      }
    } catch (err) {
      console.error('Failed to load scores:', err);
      setError('Failed to load talent scores. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRecalculate = async () => {
    try {
      setRecalculating(true);
      await scoresApi.recalculateScores();
      await loadScores();
    } catch (err) {
      console.error('Failed to recalculate scores:', err);
      setError('Failed to recalculate scores. Please try again.');
    } finally {
      setRecalculating(false);
    }
  };

  // Prepare radar chart data
  const radarData = scores 
    ? Object.entries(scores.dimension_breakdown).map(([key, value]) => ({
        subject: DIMENSION_CONFIG[key as keyof typeof DIMENSION_CONFIG]?.label || key,
        A: value * 100,
        fullMark: 100,
      }))
    : [];

  // Prepare trend chart data
  const trendData = trends?.dimension_trends?.map((t: ScoreTrend) => ({
    name: DIMENSION_CONFIG[t.dimension as keyof typeof DIMENSION_CONFIG]?.label || t.dimension,
    current: t.current_value * 100,
    previous: t.previous_value * 100,
    direction: t.direction,
  })) || [];

  // Get overall grade
  const overallGrade = scores ? calculateGrade(scores.overall_score) : 'F';
  const overallGradeColor = getGradeColor(overallGrade);

  // Get trend direction
  const trendDirection = trends?.trend_direction || 'insufficient_data';
  const trendColor = getTrendColor(trendDirection);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-8">
        <AlertCircle className="w-16 h-16 text-red-500 mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Scores</h2>
        <p className="text-gray-600 mb-6">{error}</p>
        <button
          onClick={loadScores}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Talent Score Dashboard</h1>
          <p className="text-gray-600 mt-2">
            Your comprehensive career intelligence profile
          </p>
        </div>

        {/* Overall Score Card */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-lg p-8 mb-8"
        >
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="text-center md:text-left mb-6 md:mb-0">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Overall Career Score</h2>
              <p className="text-gray-600">
                {trendDirection === 'insufficient_data' 
                  ? 'Complete your profile to see trends'
                  : `Overall trend: ${trendDirection}`}
              </p>
            </div>
            
            <div className="flex items-center space-x-8">
              {/* Score Circle */}
              <div className="relative">
                <div 
                  className="w-32 h-32 rounded-full flex items-center justify-center text-5xl font-bold shadow-lg"
                  style={{ backgroundColor: `${overallGradeColor}20`, color: overallGradeColor }}
                >
                  {scores?.overall_score ? (scores.overall_score * 100).toFixed(0) : '-'}
                  <span className="text-2xl ml-1">%</span>
                </div>
                <div 
                  className="absolute inset-0 rounded-full border-4"
                  style={{ borderColor: overallGradeColor }}
                />
                <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2">
                  <span 
                    className="px-3 py-1 rounded-full text-lg font-bold text-white"
                    style={{ backgroundColor: overallGradeColor }}
                  >
                    {overallGrade}
                  </span>
                </div>
              </div>

              {/* Trend Indicator */}
              <div className="text-center">
                <div className="flex items-center justify-center space-x-2 mb-2">
                  {trendDirection === 'improving' && <TrendingUp className="w-8 h-8 text-green-500" />}
                  {trendDirection === 'declining' && <TrendingDown className="w-8 h-8 text-red-500" />}
                  {trendDirection === 'stable' && <Activity className="w-8 h-8 text-gray-500" />}
                  {trendDirection === 'insufficient_data' && <Target className="w-8 h-8 text-gray-500" />}
                </div>
                <p className="text-sm text-gray-600">Trend</p>
                <p className="text-lg font-semibold" style={{ color: trendColor }}>
                  {trendDirection.replace('_', ' ')}
                </p>
              </div>

              {/* Recalculate Button */}
              <button
                onClick={handleRecalculate}
                disabled={recalculating}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
              >
                <RefreshCw className={`w-5 h-5 ${recalculating ? 'animate-spin' : ''}`} />
                <span>Recalculate</span>
              </button>
            </div>
          </div>
        </motion.div>

        {/* Score Breakdown Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Radar Chart */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-2xl shadow-lg p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Score Breakdown</h3>
            <div className="h-[400px]">
              {scores && radarData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                    <PolarGrid stroke="#e5e7eb" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#6b7280', fontSize: 12 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} />
                    <Radar
                      name="Your Score"
                      dataKey="A"
                      stroke="#3b82f6"
                      fill="#3b82f6"
                      fillOpacity={0.6}
                    />
                    <Legend />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-gray-500">
                  No data available
                </div>
              )}
            </div>
          </motion.div>

          {/* Dimension Scores */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-white rounded-2xl shadow-lg p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Dimension Scores</h3>
            <div className="space-y-4">
              {scores && Object.entries(scores.dimension_breakdown).map(([key, value]) => {
                const config = DIMENSION_CONFIG[key as keyof typeof DIMENSION_CONFIG];
                if (!config) return null;
                
                return (
                  <div key={key} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <config.icon className="w-5 h-5" style={{ color: config.color }} />
                        <span className="font-medium text-gray-900">{config.label}</span>
                      </div>
                      <div className="flex items-center space-x-3">
                        <span className="text-sm text-gray-600">
                          {(value * 100).toFixed(0)}%
                        </span>
                        <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full rounded-full transition-all duration-500"
                            style={{ 
                              width: `${value * 100}%`,
                              backgroundColor: config.color 
                            }}
                          />
                        </div>
                      </div>
                    </div>
                    <p className="text-sm text-gray-500">{config.description}</p>
                  </div>
                );
              })}
            </div>
          </motion.div>
        </div>

        {/* Trends Section */}
        {trends?.dimension_trends && trends.dimension_trends.length > 0 && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-2xl shadow-lg p-6 mb-8"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Score Trends</h3>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData}>
                  <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 12 }} />
                  <YAxis domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 12 }} />
                  <Tooltip 
                    formatter={(value) => [`${value}%`, 'Score']}
                    labelFormatter={(label) => `Dimension: ${label}`}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="current" 
                    name="Current" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="previous" 
                    name="Previous" 
                    stroke="#9ca3af" 
                    strokeWidth={2}
                    strokeDasharray="5 5"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        )}

        {/* Recommended Actions */}
        {actions.length > 0 && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-2xl shadow-lg p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommended Actions</h3>
            <div className="space-y-3">
              {actions.slice(0, 5).map((action, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg"
                >
                  <div 
                    className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center"
                    style={{ 
                      backgroundColor: action.priority === 'high' ? '#fee2e2' : 
                                     action.priority === 'medium' ? '#fef3c7' : '#dbeafe',
                      color: action.priority === 'high' ? '#ef4444' : 
                             action.priority === 'medium' ? '#f59e0b' : '#3b82f6'
                    }}
                  >
                    {action.priority === 'high' ? <AlertCircle className="w-4 h-4" /> :
                     action.priority === 'medium' ? <Target className="w-4 h-4" /> :
                     <CheckCircle className="w-4 h-4" />}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="font-medium text-gray-900">{action.title}</h4>
                      <span className="text-xs px-2 py-1 rounded-full"
                        style={{ 
                          backgroundColor: action.priority === 'high' ? '#fee2e2' : 
                                         action.priority === 'medium' ? '#fef3c7' : '#dbeafe',
                          color: action.priority === 'high' ? '#ef4444' : 
                                 action.priority === 'medium' ? '#f59e0b' : '#3b82f6'
                        }}
                      >
                        {action.priority.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{action.description}</p>
                    <div className="flex items-center text-xs text-gray-500">
                      <span className="uppercase font-medium mr-2">
                        {DIMENSION_CONFIG[action.dimension as keyof typeof DIMENSION_CONFIG]?.label || action.dimension}
                      </span>
                      <ArrowRight className="w-3 h-3 mx-1" />
                      <span className="capitalize">{action.type.replace('_', ' ')}</span>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}