"""
Rashid specialized tools
"""

from typing import Dict, Any
from django.conf import settings
from ai.bedrock import bedrock_service
import logging

logger = logging.getLogger(__name__)


class RashidTool:
    """Base class for Rashid tools"""
    
    name: str = ""
    description: str = ""
    
    def execute(self, context: Dict[str, Any]) -> str:
        raise NotImplementedError


class CVReviewTool(RashidTool):
    """Review user's CV and provide improvement suggestions"""
    
    name = "cv_review"
    description = "مراجعة السيرة الذاتية وتقديم اقتراحات للتحسين"
    
    def execute(self, context: Dict[str, Any]) -> str:
        user = context['user']
        
        # Get user profile
        from apps.profiles.models import UserProfile
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return "عذراً، مش لاقي البروفايل بتاعك. اعمل بروفايل الأول عشان أقدر أراجع سيرتك الذاتية."
        
        # Read CV from uploaded file
        cv_text = ""
        if profile.cv_file:
            try:
                cv_text = profile.cv_file.read().decode('utf-8')
            except Exception:
                # Try reading as binary and decode
                import os
                cv_path = profile.cv_file.path
                if os.path.exists(cv_path):
                    with open(cv_path, 'r', encoding='utf-8', errors='ignore') as f:
                        cv_text = f.read()[:5000]  # Limit to 5000 chars
        
        if not cv_text:
            return "عذراً، مش لاقي السيرة الذاتية بتاعتك. ارفع السيرة الذاتية الأول عشان أقدر أراجعها."
        
        system_prompt = """أنت خبير في مراجعة السير الذاتية.

راجع السيرة الذاتية وقدم:
1. التقييم العام (من 10)
2. نقاط القوة (3-5 نقاط)
3. نقاط تحتاج تحسين (3-5 نقاط)
4. اقتراحات محددة وعملية
5. أمثلة لصياغات أفضل

اكتب بالعامية المصرية. كن صريحاً لكن مشجعاً."""
        
        prompt = f"""راجع السيرة الذاتية دي:

{cv_text[:3000]}

قدم تحليل شامل واقتراحات عملية."""
        
        try:
            response = bedrock_service.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=2000,
                temperature=0.5
            )
            return response
        except Exception as e:
            logger.error(f"Error in CV review tool: {e}")
            return "عذراً، حصل خطأ في مراجعة السيرة الذاتية. حاول تاني بعد شوية."


class CoverLetterTool(RashidTool):
    """Generate cover letter for a specific job"""
    
    name = "cover_letter"
    description = "كتابة cover letter مخصص لوظيفة معينة"
    
    def execute(self, context: Dict[str, Any]) -> str:
        user = context['user']
        job_id = context.get('job_id')
        job_title = context.get('job_title', 'الوظيفة')
        company_name = context.get('company_name', 'الشركة')
        
        # Get user profile
        from apps.profiles.models import UserProfile
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return "عذراً، محتاج البروفايل بتاعك عشان أكتب cover letter مناسب. اعمل بروفايل الأول."
        
        # Read CV from uploaded file
        cv_text = ""
        if profile.cv_file:
            try:
                cv_text = profile.cv_file.read().decode('utf-8')
            except Exception:
                import os
                cv_path = profile.cv_file.path
                if os.path.exists(cv_path):
                    with open(cv_path, 'r', encoding='utf-8', errors='ignore') as f:
                        cv_text = f.read()[:5000]
        
        if not cv_text:
            return "عذراً، محتاج السيرة الذاتية بتاعتك عشان أكتب cover letter مناسب. ارفع السيرة الذاتية الأول."
        
        # Get job details if job_id provided
        job_description = ""
        if job_id:
            from apps.jobs.models import Job
            try:
                job = Job.objects.get(id=job_id)
                job_description = f"""
الوظيفة: {job.title}
الشركة: {job.company.name}
الوصف: {job.description[:500] if job.description else ''}
المتطلبات: {job.requirements[:500] if job.requirements else ''}
"""
                job_title = job.title
                company_name = job.company.name
            except Job.DoesNotExist:
                pass
        
        system_prompt = """أنت خبير في كتابة خطابات التوظيف (cover letters).

اكتب cover letter:
- احترافي لكن شخصي
- يبرز مهارات المتقدم المتعلقة بالوظيفة
- يظهر اهتمام حقيقي بالشركة
- مختصر (250-350 كلمة)
- بصيغة رسمية (عربي فصيح)

التنسيق:
1. التحية
2. المقدمة (لماذا هذه الوظيفة)
3. المهارات والخبرات المتعلقة
4. لماذا هذه الشركة
5. الخاتمة

اكتب Cover Letter كامل جاهز للإرسال."""
        
        prompt = f"""اكتب cover letter لـ:

**الوظيفة:** {job_title}
**الشركة:** {company_name}

{job_description}

**معلومات المتقدم:**
{cv_text[:1500]}

اكتب cover letter احترافي يبرز مناسبة المتقدم للوظيفة."""
        
        try:
            response = bedrock_service.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=1500,
                temperature=0.7
            )
            return response
        except Exception as e:
            logger.error(f"Error in cover letter tool: {e}")
            return "عذراً، حصل خطأ في كتابة الـ cover letter. حاول تاني بعد شوية."


class InterviewPrepTool(RashidTool):
    """Prepare for job interview with STAR method"""
    
    name = "interview_prep"
    description = "التحضير للمقابلات الوظيفية باستخدام STAR"
    
    def execute(self, context: Dict[str, Any]) -> str:
        user = context['user']
        job_title = context.get('job_title', 'الوظيفة المطلوبة')
        question_type = context.get('question_type', 'general')
        
        # Get user profile
        from apps.profiles.models import UserProfile
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            profile = None
        
        system_prompt = """أنت خبير في التحضير للمقابلات الوظيفية.

استخدم منهج STAR:
- Situation (الموقف)
- Task (المهمة)
- Action (الإجراء)
- Result (النتيجة)

قدم:
1. أسئلة متوقعة (5-10 أسئلة)
2. نماذج إجابات باستخدام STAR
3. نصائح عامة للمقابلة
4. أخطاء شائعة يجب تجنبها

اكتب بالعامية المصرية. كن عملياً ومشجعاً."""
        
        experience_summary = ""
        skills_summary = ""
        
        if profile:
            if hasattr(profile, 'experience') and profile.experience.exists():
                experiences = profile.experience.all()[:3]
                experience_summary = "\n".join([
                    f"- {exp.title} في {exp.company}" for exp in experiences
                ])
            if profile.skills:
                skills_summary = ', '.join(profile.skills[:10])
        
        prompt = f"""ساعدني في التحضير لمقابلة وظيفة:

**الوظيفة:** {job_title}

**خبراتي:**
{experience_summary or "لا يوجد خبرات سابقة"}

**المهارات:**
{skills_summary or 'لم يتم تحديدها'}

قدم:
1. أسئلة متوقعة للوظيفة دي
2. نماذج إجابات بطريقة STAR
3. نصائح عشان أنجح في المقابلة"""
        
        try:
            response = bedrock_service.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=2500,
                temperature=0.6
            )
            return response
        except Exception as e:
            logger.error(f"Error in interview prep tool: {e}")
            return "عذراً، حصل خطأ في التحضير للمقابلة. حاول تاني بعد شوية."


class LinkedInOptimizerTool(RashidTool):
    """Optimize LinkedIn profile"""
    
    name = "linkedin_optimizer"
    description = "تحسين البروفايل على LinkedIn"
    
    def execute(self, context: Dict[str, Any]) -> str:
        user = context['user']
        
        # Get user profile
        from apps.profiles.models import UserProfile
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            profile = None
        
        system_prompt = """أنت خبير في تحسين بروفايلات LinkedIn.

قدم نصائح محددة لـ:
1. العنوان (Headline) - جذاب ومحسّن للبحث
2. ملخص About - قوي وشخصي
3. قسم الخبرات - كيف تكتب achievements
4. المهارات - أي مهارات تضيفها
5. صورة الملف الشخصي والغلاف
6. بناء الشبكة (Networking)

اكتب بالعامية المصرية. قدم أمثلة واقعية."""
        
        current_position = ""
        skills = ""
        years_of_experience = 0
        
        if profile:
            current_position = profile.current_position or "باحث عن عمل"
            if profile.skills:
                skills = ', '.join(profile.skills[:10])
            years_of_experience = profile.years_of_experience or 0
        
        prompt = f"""ساعدني في تحسين بروفايل LinkedIn:

**الوظيفة الحالية/المستهدفة:** {current_position or 'غير محدد'}
**المهارات:** {skills or 'لم يتم تحديدها'}
**سنوات الخبرة:** {years_of_experience}

قدم:
1. اقتراح Headline جذاب
2. نموذج لـ About section
3. كيف أكتب الخبرات بشكل احترافي
4. مهارات مهمة أضيفها
5. نصائح عامة لتحسين الظهور"""
        
        try:
            response = bedrock_service.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=2000,
                temperature=0.7
            )
            return response
        except Exception as e:
            logger.error(f"Error in LinkedIn optimizer tool: {e}")
            return "عذراً، حصل خطأ في تحسين الـ LinkedIn. حاول تاني بعد شوية."


class CourseAdvisorTool(RashidTool):
    """Recommend courses from edu.usamif.com"""
    
    name = "course_advisor"
    description = "ترشيح دورات تدريبية من منصة USAM"
    
    def execute(self, context: Dict[str, Any]) -> str:
        user = context['user']
        skill_gap = context.get('skill_gap', [])
        target_role = context.get('target_role', '')
        
        # Get user profile
        from apps.profiles.models import UserProfile
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            profile = None
        
        # Get available courses (fallback list)
        courses = self._get_available_courses()
        
        system_prompt = """أنت مستشار تدريبي متخصص.

قواعد مهمة:
- رشح دورات من القائمة المتاحة فقط
- لا تخترع أسماء دورات
- اعتمد على القائمة المتاحة فعلياً

قدم:
1. أفضل 3-5 دورات مناسبة
2. سبب الترشيح لكل دورة
3. الترتيب حسب الأولوية
4. المسار التعليمي المقترح

اكتب بالعامية المصرية."""
        
        current_skills = ""
        target_skills = ', '.join(skill_gap) if skill_gap else "غير محدد"
        current_position = ""
        
        if profile:
            if profile.skills:
                current_skills = ', '.join(profile.skills)
            current_position = profile.current_position or ''
        
        prompt = f"""ساعدني في اختيار دورات تدريبية:

**مهاراتي الحالية:** {current_skills or "لا يوجد"}
**المهارات المطلوبة:** {target_skills}
**الوظيفة المستهدفة:** {target_role or current_position or 'غير محدد'}

**الدورات المتاحة:**
{courses}

رشحلي أفضل دورات من القائمة دي تساعدني أوصل للهدف."""
        
        try:
            response = bedrock_service.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=1500,
                temperature=0.5
            )
            return response
        except Exception as e:
            logger.error(f"Error in course advisor tool: {e}")
            return "عذراً، حصل خطأ في ترشيح الدورات. حاول تاني بعد شوية."
    
    def _get_available_courses(self) -> str:
        """Get available courses - fallback list"""
        # This would normally fetch from edu.usamif.com
        # For now, return a curated list of courses
        return """
- أساسيات Python للمبتدئين: تعلم البرمجة من الصفر
- تطوير تطبيقات الويب بـ Django: بناء تطبيقات احترافية
- تحليل البيانات باستخدام Excel: من الأساسيات للاحتراف
- التسويق الرقمي: استراتيجيات فعالة للأعمال
- إدارة المشاريع الاحترافية: PMP Preparation
- تصميم واجهات المستخدم UI/UX: من الفكرة للتنفيذ
- الذكاء الاصطناعي Machine Learning: مقدمة عملية
- أمن المعلومات السيبراني: حماية البيانات والأنظمة
- تطوير تطبيقات الموبايل: React Native و Flutter
- إدارة المنتجات الرقمية: Product Management
- تحليل البيانات الضخمة Big Data: أدوات وتقنيات
- الحوسبة السحابية AWS: شهادة Solutions Architect
- اللغة الإنجليزية للأعمال: مهارات التواصل المهني
- مهارات القيادة والإدارة: Leadership Skills
"""


# Tool Registry
RASHID_TOOLS = {
    'cv_review': CVReviewTool(),
    'cover_letter': CoverLetterTool(),
    'interview_prep': InterviewPrepTool(),
    'linkedin_optimizer': LinkedInOptimizerTool(),
    'course_advisor': CourseAdvisorTool(),
}


def get_tool(tool_name: str) -> RashidTool:
    """Get tool by name"""
    return RASHID_TOOLS.get(tool_name)


def execute_tool(tool_name: str, context: Dict[str, Any]) -> str:
    """Execute a Rashid tool"""
    tool = get_tool(tool_name)
    if not tool:
        return f"عذراً، الأداة '{tool_name}' مش موجودة."
    
    try:
        return tool.execute(context)
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        return f"عذراً، حصل خطأ: {str(e)}"


def get_available_tools():
    """Get list of available tools"""
    return [
        {
            'name': tool.name,
            'description': tool.description
        }
        for tool in RASHID_TOOLS.values()
    ]