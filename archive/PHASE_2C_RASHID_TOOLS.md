> **Superseded by MASTER_IMPLEMENTATION_PLAN.md and audit/PHASE_*_COMPLETION_REPORT.md — kept for history only.**

# PHASE 2C: Rashid Tools

> **Dependencies:** Phase 2B complete  
> **Duration:** 4-5 hours  
> **Status:** Ready for GLM execution

---

## 🎯 Objectives

Implement specialized Rashid tools:
- CV Review Mode
- Cover Letter Generator
- Interview Prep with STAR Bank
- LinkedIn Optimizer
- Course Advisor (edu.usamif.com integration)

---

## 🔧 Implementation

### Step 1: Tool Registry

**File:** `backend/rashid/tools.py`

```python
"""
Rashid specialized tools
"""

from typing import Dict, Any
from django.conf import settings
from ai.bedrock_service import bedrock_service
import requests
from bs4 import BeautifulSoup

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
        profile = user.userprofile
        
        if not profile.cv_text:
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

{profile.cv_text[:3000]}

قدم تحليل شامل واقتراحات عملية."""
        
        response = bedrock_service.invoke_model(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=2000,
            temperature=0.5
        )
        
        return response


class CoverLetterTool(RashidTool):
    """Generate cover letter for a specific job"""
    
    name = "cover_letter"
    description = "كتابة cover letter مخصص لوظيفة معينة"
    
    def execute(self, context: Dict[str, Any]) -> str:
        user = context['user']
        job_id = context.get('job_id')
        job_title = context.get('job_title', 'الوظيفة')
        company_name = context.get('company_name', 'الشركة')
        
        profile = user.userprofile
        
        if not profile.cv_text:
            return "عذراً، محتاج السيرة الذاتية بتاعتك عشان أكتب cover letter مناسب. ارفع السيرة الذاتية الأول."
        
        # Get job details if job_id provided
        job_description = ""
        if job_id:
            from jobs.models import Job
            try:
                job = Job.objects.get(id=job_id)
                job_description = f"""
الوظيفة: {job.title}
الشركة: {job.company.name}
الوصف: {job.description[:500]}
المتطلبات: {job.requirements[:500]}
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
{profile.cv_text[:1500]}

اكتب cover letter احترافي يبرز مناسبة المتقدم للوظيفة."""
        
        response = bedrock_service.invoke_model(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=1500,
            temperature=0.7
        )
        
        return response


class InterviewPrepTool(RashidTool):
    """Prepare for job interview with STAR method"""
    
    name = "interview_prep"
    description = "التحضير للمقابلات الوظيفية باستخدام STAR"
    
    def execute(self, context: Dict[str, Any]) -> str:
        user = context['user']
        job_title = context.get('job_title', 'الوظيفة المطلوبة')
        question_type = context.get('question_type', 'general')
        
        profile = user.userprofile
        
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
        if profile.experience.exists():
            experiences = profile.experience.all()[:3]
            experience_summary = "\n".join([
                f"- {exp.title} في {exp.company}" for exp in experiences
            ])
        
        prompt = f"""ساعدني في التحضير لمقابلة وظيفة:

**الوظيفة:** {job_title}

**خبراتي:**
{experience_summary or "لا يوجد خبرات سابقة"}

**المهارات:**
{', '.join(profile.skills[:10]) if profile.skills else 'لم يتم تحديدها'}

قدم:
1. أسئلة متوقعة للوظيفة دي
2. نماذج إجابات بطريقة STAR
3. نصائح عشان أنجح في المقابلة"""
        
        response = bedrock_service.invoke_model(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=2500,
            temperature=0.6
        )
        
        return response


class LinkedInOptimizerTool(RashidTool):
    """Optimize LinkedIn profile"""
    
    name = "linkedin_optimizer"
    description = "تحسين البروفايل على LinkedIn"
    
    def execute(self, context: Dict[str, Any]) -> str:
        user = context['user']
        profile = user.userprofile
        
        system_prompt = """أنت خبير في تحسين بروفايلات LinkedIn.

قدم نصائح محددة لـ:
1. العنوان (Headline) - جذاب ومحسّن للبحث
2. ملخص About - قوي وشخصي
3. قسم الخبرات - كيف تكتب achievements
4. المهارات - أي مهارات تضيفها
5. صورة الملف الشخصي والغلاف
6. بناء الشبكة (Networking)

اكتب بالعامية المصرية. قدم أمثلة واقعية."""
        
        current_position = profile.current_position or "باحث عن عمل"
        skills = ', '.join(profile.skills[:10]) if profile.skills else "لم يتم تحديدها"
        
        prompt = f"""ساعدني في تحسين بروفايل LinkedIn:

**الوظيفة الحالية/المستهدفة:** {current_position}
**المهارات:** {skills}
**سنوات الخبرة:** {profile.years_of_experience or 0}

قدم:
1. اقتراح Headline جذاب
2. نموذج لـ About section
3. كيف أكتب الخبرات بشكل احترافي
4. مهارات مهمة أضيفها
5. نصائح عامة لتحسين الظهور"""
        
        response = bedrock_service.invoke_model(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=2000,
            temperature=0.7
        )
        
        return response


class CourseAdvisorTool(RashidTool):
    """Recommend courses from edu.usamif.com"""
    
    name = "course_advisor"
    description = "ترشيح دورات تدريبية من منصة USAM"
    
    def execute(self, context: Dict[str, Any]) -> str:
        user = context['user']
        skill_gap = context.get('skill_gap', [])
        target_role = context.get('target_role', '')
        
        profile = user.userprofile
        
        # Scrape courses from edu.usamif.com
        courses = self._fetch_courses()
        
        system_prompt = f"""أنت مستشار تدريبي متخصص.

قواعد مهمة:
- رشح دورات من {settings.RASHID_CONFIG['course_platform_url']} فقط
- لا تخترع أسماء دورات
- اعتمد على القائمة المتاحة فعلياً

قدم:
1. أفضل 3-5 دورات مناسبة
2. سبب الترشيح لكل دورة
3. الترتيب حسب الأولوية
4. المسار التعليمي المقترح

اكتب بالعامية المصرية."""
        
        current_skills = ', '.join(profile.skills) if profile.skills else "لا يوجد"
        target_skills = ', '.join(skill_gap) if skill_gap else "غير محدد"
        
        prompt = f"""ساعدني في اختيار دورات تدريبية:

**مهاراتي الحالية:** {current_skills}
**المهارات المطلوبة:** {target_skills}
**الوظيفة المستهدفة:** {target_role or profile.current_position or 'غير محدد'}

**الدورات المتاحة:**
{courses}

رشحلي أفضل دورات من القائمة دي تساعدني أوصل للهدف."""
        
        response = bedrock_service.invoke_model(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=1500,
            temperature=0.5
        )
        
        return response
    
    def _fetch_courses(self) -> str:
        """Fetch available courses from edu.usamif.com"""
        try:
            url = settings.RASHID_CONFIG['course_platform_url']
            response = requests.get(f"{url}/courses", timeout=5)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract course titles and descriptions
                courses = []
                course_elements = soup.find_all('div', class_='course-item')
                
                for elem in course_elements[:20]:  # Limit to 20 courses
                    title = elem.find('h3')
                    desc = elem.find('p', class_='description')
                    
                    if title:
                        course_info = f"- {title.text.strip()}"
                        if desc:
                            course_info += f": {desc.text.strip()[:100]}"
                        courses.append(course_info)
                
                if courses:
                    return '\n'.join(courses)
        
        except Exception as e:
            print(f"Error fetching courses: {e}")
        
        # Fallback: Return placeholder courses
        return """
- أساسيات Python للمبتدئين: تعلم البرمجة من الصفر
- تطوير تطبيقات الويب بـ Django: بناء تطبيقات احترافية
- تحليل البيانات باستخدام Excel: من الأساسيات للاحتراف
- التسويق الرقمي: استراتيجيات فعالة للأعمال
- إدارة المشاريع الاحترافية: PMP Preparation
- تصميم واجهات المستخدم UI/UX: من الفكرة للتنفيذ
- الذكاء الاصطناعي Machine Learning: مقدمة عملية
- أمن المعلومات السيبراني: حماية البيانات والأنظمة
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
        return f"عذراً، حصل خطأ: {str(e)}"
```

### Step 2: Tool API Endpoints

**File:** `backend/rashid/views.py` (add to existing)

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .tools import execute_tool, RASHID_TOOLS

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_tool_endpoint(request):
    """
    Execute a Rashid tool
    
    POST /api/rashid/tools/execute/
    {
        "tool": "cv_review",
        "context": {...}
    }
    """
    tool_name = request.data.get('tool')
    context = request.data.get('context', {})
    
    if not tool_name:
        return Response({'error': 'Tool name required'}, status=400)
    
    if tool_name not in RASHID_TOOLS:
        return Response({'error': 'Invalid tool name'}, status=400)
    
    # Add user to context
    context['user'] = request.user
    
    # Execute tool
    result = execute_tool(tool_name, context)
    
    return Response({
        'tool': tool_name,
        'result': result
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_tools(request):
    """List available Rashid tools"""
    tools = [
        {
            'name': tool.name,
            'description': tool.description
        }
        for tool in RASHID_TOOLS.values()
    ]
    
    return Response({'tools': tools})
```

**Update:** `backend/rashid/urls.py`

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ConversationViewSet, execute_tool_endpoint, list_tools

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')

urlpatterns = [
    path('', include(router.urls)),
    path('tools/', list_tools, name='list-tools'),
    path('tools/execute/', execute_tool_endpoint, name='execute-tool'),
]
```

### Step 3: Update WebSocket Consumer for Tools

**File:** `backend/rashid/consumers.py` (update)

```python
# Add to imports
from .tools import execute_tool

class RashidConsumer(AsyncWebsocketConsumer):
    # ... existing code
    
    async def receive(self, text_data):
        """Handle incoming message"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'tool':
                await self.handle_tool(data)
            elif message_type == 'typing':
                pass
        
        except json.JSONDecodeError:
            await self.send_error("Invalid message format")
        except Exception as e:
            logger.error(f"Error in WebSocket receive: {e}")
            await self.send_error("An error occurred")
    
    async def handle_tool(self, data):
        """Handle tool execution request"""
        tool_name = data.get('tool')
        context = data.get('context', {})
        
        if not tool_name:
            await self.send_error("Tool name required")
            return
        
        # Send processing indicator
        await self.send(text_data=json.dumps({
            'type': 'tool_processing',
            'tool': tool_name
        }))
        
        # Execute tool
        try:
            context['user'] = self.user
            result = await database_sync_to_async(execute_tool)(tool_name, context)
            
            # Send result
            await self.send(text_data=json.dumps({
                'type': 'tool_result',
                'tool': tool_name,
                'result': result,
                'timestamp': str(timezone.now())
            }))
            
            # Save as message
            await database_sync_to_async(Message.objects.create)(
                conversation=self.conversation,
                role='assistant',
                content=f"[Tool: {tool_name}]\n\n{result}"
            )
        
        except Exception as e:
            logger.error(f"Error executing tool: {e}")
            await self.send_error(f"Failed to execute tool: {str(e)}")
```

---

## 🎨 Frontend Implementation

### Step 4: Tool Selection UI

**File:** `frontend/src/components/rashid/ToolSelector.jsx`

```jsx
import React from 'react';
import { FileText, Mail, MessageSquare, Linkedin, GraduationCap } from 'lucide-react';

const tools = [
  {
    name: 'cv_review',
    title: 'مراجعة السيرة الذاتية',
    description: 'احصل على تقييم شامل وملاحظات لتحسين سيرتك الذاتية',
    icon: FileText,
    color: 'blue'
  },
  {
    name: 'cover_letter',
    title: 'كتابة Cover Letter',
    description: 'اكتب خطاب توظيف احترافي مخصص للوظيفة',
    icon: Mail,
    color: 'green'
  },
  {
    name: 'interview_prep',
    title: 'التحضير للمقابلة',
    description: 'استعد للمقابلات بأسئلة متوقعة وإجابات STAR',
    icon: MessageSquare,
    color: 'purple'
  },
  {
    name: 'linkedin_optimizer',
    title: 'تحسين LinkedIn',
    description: 'حسّن بروفايلك على LinkedIn لجذب أصحاب العمل',
    icon: Linkedin,
    color: 'blue'
  },
  {
    name: 'course_advisor',
    title: 'ترشيح دورات',
    description: 'احصل على توصيات لدورات تدريبية مناسبة',
    icon: GraduationCap,
    color: 'orange'
  }
];

const ToolSelector = ({ onSelectTool }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
      {tools.map(tool => {
        const Icon = tool.icon;
        return (
          <button
            key={tool.name}
            onClick={() => onSelectTool(tool.name)}
            className="bg-white rounded-lg border-2 border-gray-200 p-6 hover:border-blue-500 hover:shadow-lg transition text-right"
            dir="rtl"
          >
            <div className="flex items-start gap-4">
              <div className={`p-3 rounded-lg bg-${tool.color}-50`}>
                <Icon className={`w-6 h-6 text-${tool.color}-600`} />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {tool.title}
                </h3>
                <p className="text-sm text-gray-600">
                  {tool.description}
                </p>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
};

export default ToolSelector;
```

### Step 5: Update Chat Page with Tools

**File:** `frontend/src/pages/RashidChatPage.jsx` (update)

```jsx
import React, { useState, useEffect, useRef } from 'react';
import { Wrench } from 'lucide-react';
import ToolSelector from '../components/rashid/ToolSelector';

const RashidChatPage = () => {
  // ... existing state
  const [showTools, setShowTools] = useState(false);
  
  const handleToolSelection = (toolName) => {
    setShowTools(false);
    
    // Send tool execution request
    sendMessage(JSON.stringify({
      type: 'tool',
      tool: toolName,
      context: {}
    }));
    
    // Show processing message
    setMessages(prev => [...prev, {
      role: 'system',
      content: `جاري تنفيذ الأداة: ${toolName}...`,
      timestamp: new Date().toISOString()
    }]);
  };

  // ... existing code

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">رشيد - مستشارك المهني</h1>
          <p className="text-sm text-gray-600">
            {isConnected ? (
              <span className="text-green-600">● متصل</span>
            ) : (
              <span className="text-red-600">● غير متصل</span>
            )}
          </p>
        </div>
        
        <button
          onClick={() => setShowTools(!showTools)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Wrench className="w-5 h-5" />
          الأدوات
        </button>
      </div>

      {/* Tools Panel */}
      {showTools && (
        <div className="bg-gray-100 border-b">
          <ToolSelector onSelectTool={handleToolSelection} />
        </div>
      )}

      {/* Messages ... existing code */}
    </div>
  );
};

export default RashidChatPage;
```

---

## ✅ Phase 2C Verification

### Tests

```bash
# Test CV review
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/rashid/tools/execute/ \
  -d '{"tool": "cv_review", "context": {}}'

# Test cover letter generation
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/rashid/tools/execute/ \
  -d '{"tool": "cover_letter", "context": {"job_title": "Senior Developer"}}'

# List all tools
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/rashid/tools/
```

### Success Criteria

- [ ] All 5 tools work correctly
- [ ] CV review provides detailed feedback
- [ ] Cover letters are personalized
- [ ] Interview prep includes STAR examples
- [ ] LinkedIn suggestions are specific
- [ ] Course recommendations come from edu.usamif.com only
- [ ] Tools accessible via WebSocket and REST API

---

**Phase 2C Complete! ✅**
Proceed to Phase 2D: Email System
