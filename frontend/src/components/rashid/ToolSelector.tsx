/**
 * Tool Selector Component for Rashid
 * Provides quick access to specialized Rashid tools
 */

import { FileText, Mail, MessageSquare, Linkedin, GraduationCap, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Tool {
  name: string;
  title: string;
  titleAr: string;
  description: string;
  descriptionAr: string;
  icon: React.ElementType;
  color: string;
}

const tools: Tool[] = [
  {
    name: 'cv_review',
    title: 'CV Review',
    titleAr: 'مراجعة السيرة الذاتية',
    description: 'Get a comprehensive review and improvement suggestions for your CV',
    descriptionAr: 'احصل على تقييم شامل وملاحظات لتحسين سيرتك الذاتية',
    icon: FileText,
    color: 'blue'
  },
  {
    name: 'cover_letter',
    title: 'Cover Letter',
    titleAr: 'كتابة Cover Letter',
    description: 'Generate a professional cover letter tailored to a specific job',
    descriptionAr: 'اكتب خطاب توظيف احترافي مخصص للوظيفة',
    icon: Mail,
    color: 'green'
  },
  {
    name: 'interview_prep',
    title: 'Interview Prep',
    titleAr: 'التحضير للمقابلة',
    description: 'Prepare for interviews with expected questions and STAR method answers',
    descriptionAr: 'استعد للمقابلات بأسئلة متوقعة وإجابات STAR',
    icon: MessageSquare,
    color: 'purple'
  },
  {
    name: 'linkedin_optimizer',
    title: 'LinkedIn Optimizer',
    titleAr: 'تحسين LinkedIn',
    description: 'Get tips to improve your LinkedIn profile and attract employers',
    descriptionAr: 'حسّن بروفايلك على LinkedIn لجذب أصحاب العمل',
    icon: Linkedin,
    color: 'blue'
  },
  {
    name: 'course_advisor',
    title: 'Course Advisor',
    titleAr: 'ترشيح دورات',
    description: 'Get personalized course recommendations from USAM platform',
    descriptionAr: 'احصل على توصيات لدورات تدريبية مناسبة',
    icon: GraduationCap,
    color: 'orange'
  }
];

interface ToolSelectorProps {
  onSelectTool: (toolName: string) => void;
  onClose: () => void;
  isAr?: boolean;
}

export default function ToolSelector({ onSelectTool, onClose, isAr = false }: ToolSelectorProps) {
  const dir = isAr ? 'rtl' : 'ltr';

  return (
    <div className="bg-surface-1 border-b" dir={dir}>
      <div className="max-w-4xl mx-auto p-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">
            {isAr ? 'أدوات رشيد' : 'Rashid Tools'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-surface-2 rounded-lg transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tools Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {tools.map((tool) => {
            const Icon = tool.icon;
            return (
              <button
                key={tool.name}
                onClick={() => onSelectTool(tool.name)}
                className={cn(
                  'flex items-start gap-3 p-4 rounded-xl border-2 border-transparent',
                  'bg-card hover:border-primary hover:shadow-md transition-all text-start',
                  'group'
                )}
              >
                <div className={cn(
                  'p-2.5 rounded-lg transition-colors',
                  `bg-${tool.color}-50 group-hover:bg-${tool.color}-100`
                )}>
                  <Icon className={cn('w-5 h-5', `text-${tool.color}-600`)} />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-sm mb-1">
                    {isAr ? tool.titleAr : tool.title}
                  </h3>
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {isAr ? tool.descriptionAr : tool.description}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// Export tools list for use in other components
export { tools };