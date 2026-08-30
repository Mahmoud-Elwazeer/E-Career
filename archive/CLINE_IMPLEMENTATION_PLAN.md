> **Superseded by MASTER_IMPLEMENTATION_PLAN.md and audit/PHASE_*_COMPLETION_REPORT.md — kept for history only.**

# Complete Implementation Plan for Cline
## E-Career Platform - All Remaining Work
## Date: August 7, 2026

---

## Overview

This document contains ALL remaining implementation work split into phases. Each phase has a complete Cline prompt ready to copy-paste. Execute them IN ORDER.

**Total estimated time: 12-15 hours across 6 phases**

---

## PHASE 1: WebSocket + Daphne Deployment (Backend)
**Time: 1-2 hours | Priority: HIGH**

This enables real-time Rashid chat. The ASGI config and WebSocket consumer already exist but the production server runs Gunicorn (HTTP only). We need Daphne for WebSocket OR a REST fallback.

### Cline Prompt:

```
## Task: Add REST API fallback for Rashid chat (production doesn't support WebSocket yet)

### Context:
- The Rashid chat frontend (`src/pages/RashidChat.tsx`) uses WebSocket (`/ws/rashid/`)
- Production runs Gunicorn which doesn't support WebSocket
- The backend already has a REST endpoint: POST `/api/v1/rashid/conversations/{id}/send_message/`
- The floating widget (`src/components/rashid/RashidMiniChat.tsx`) needs to work via REST API
- ASGI + Daphne config already exists at `backend/config/asgi.py` and `backend/apps/rashid/consumers.py`

### Requirements:

#### 1. Update RashidMiniChat to use REST API (not WebSocket)
File: `frontend/src/components/rashid/RashidMiniChat.tsx`

The mini chat should use REST API calls instead of WebSocket:
- POST `/api/v1/rashid/conversations/` to create a conversation (body: `{ "mode": "general" }`)
- GET `/api/v1/rashid/conversations/{id}/messages/` to load messages
- POST `/api/v1/rashid/conversations/{id}/send_message/` to send a message (body: `{ "content": "..." }`)
- The response from send_message contains the AI reply directly

Use TanStack Query mutations for sending messages and queries for loading messages.
Headers: `Authorization: Bearer ${localStorage.getItem('accessToken')}`
Base URL: `import.meta.env.VITE_API_URL || '/api/v1'`

Show a typing indicator while the mutation is pending.
Auto-scroll to bottom on new messages.

#### 2. Update RashidChat page to support both WebSocket and REST fallback
File: `frontend/src/pages/RashidChat.tsx`

Add a fallback mechanism:
- Try WebSocket connection first
- If WebSocket fails to connect within 3 seconds, switch to REST polling mode
- In REST mode: poll GET messages every 2 seconds while waiting for AI response
- Show connection status indicator (WebSocket = green dot, REST = yellow dot)

#### 3. Verify the send_message endpoint works correctly
File: `backend/apps/rashid/views.py`

Check that the `send_message` action:
- Accepts `{ "content": "user message text" }` in request body
- Calls the RashidService to get AI response
- Returns both the user message and AI response
- Handles tool execution if the AI decides to use a tool

If the endpoint doesn't exist or is incomplete, implement it using:
```python
@action(detail=True, methods=['post'], url_path='send_message')
def send_message(self, request, pk=None):
    conversation = self.get_object()
    content = request.data.get('content', '')
    
    if not content:
        return Response({'error': 'Message content required'}, status=400)
    
    from .service import RashidService
    service = RashidService()
    
    # Save user message
    user_msg = conversation.messages.create(
        role='user',
        content=content,
        token_count=service.estimate_tokens(content)
    )
    
    # Get AI response
    ai_response = service.get_response(
        user=request.user,
        conversation=conversation,
        message=content
    )
    
    # Save assistant message
    assistant_msg = conversation.messages.create(
        role='assistant',
        content=ai_response,
        token_count=service.estimate_tokens(ai_response)
    )
    
    return Response({
        'success': True,
        'data': {
            'user_message': {'role': 'user', 'content': content, 'timestamp': user_msg.created_at},
            'assistant_message': {'role': 'assistant', 'content': ai_response, 'timestamp': assistant_msg.created_at},
        }
    })
```

#### 4. Add Daphne systemd service for future WebSocket support
Create file: `deployment/daphne.service`
```ini
[Unit]
Description=E-Career Daphne ASGI Server (WebSocket)
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/var/www/usam/backend
Environment="PATH=/var/www/usam/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings.development"
ExecStart=/var/www/usam/venv/bin/daphne -b 127.0.0.1 -p 8001 config.asgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### 5. Create nginx WebSocket proxy config
Create file: `deployment/nginx-websocket.conf`
```nginx
# Add this to the server block in /etc/nginx/sites-enabled/usam
# WebSocket proxy for Rashid chat
location /ws/ {
    proxy_pass http://127.0.0.1:8001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 86400;
}
```

### Testing:
After implementation, the Rashid mini chat widget should:
1. Open when clicking the floating Rashid character
2. Send messages via REST API and display AI responses
3. Show typing indicator while AI is responding
4. Persist conversation between page navigations
```

---

## PHASE 2: Rashid Character Full Body + Poses (Frontend)
**Time: 2-3 hours | Priority: MEDIUM**

### Cline Prompt:

```
## Task: Create Rashid's full-body SVG character with 6 poses and animations

### Context:
- Rashid is an Egyptian male career mentor, friendly, ~30 years old
- Currently `src/components/rashid/RashidAvatar.tsx` has a simple bust/head SVG
- We need a full character system with multiple poses for different contexts
- Uses framer-motion for animations, Tailwind for sizing

### Character Design Specs:
- Style: Modern flat illustration (like Notion/Lottie characters)
- Skin: warm tan (#D4956A / #f5d0b0)
- Hair/beard: dark brown (#3B2417 / #2d2d2d), short neat hair, light stubble
- Shirt: light blue (#3b82f6), business casual (no tie)
- Pants: dark navy (#1e293b)
- Shoes: brown leather (#6B4C3B)
- Face: Round, warm brown eyes, friendly smile
- Build: Average, approachable

### Requirements:

#### 1. Create character pose components
Directory: `src/components/rashid/character/`

Create these SVG components (each is a self-contained SVG):

**a) `RashidWave.tsx`** - Standing, right hand raised waving
- Full body visible (head to feet)
- Friendly wave gesture
- Used for: greetings, first appearance, empty states

**b) `RashidThinking.tsx`** - Right hand on chin, looking slightly up
- Full body, slight lean
- Contemplative expression (eyebrows slightly raised)
- Used for: while AI is processing/generating

**c) `RashidPresenting.tsx`** - Right hand gesturing forward (palm up, showing something)
- Full body, confident stance
- Open gesture like presenting results
- Used for: showing results, recommendations, tool output

**d) `RashidCelebrating.tsx`** - Both hands raised, big smile
- Full body, slight jump pose
- Celebration expression (wide smile, eyes squinted happy)
- Used for: after applying to job, completing onboarding, earning badge

**e) `RashidListening.tsx`** - Leaning slightly forward, hands relaxed at sides
- Full body, attentive posture
- Focused expression (slight smile, eye contact)
- Used for: while user is typing

**f) `RashidBust.tsx`** - Upper body only (head + shoulders + partial torso)
- Used for: chat header, floating widget, small UI spaces
- This should replace the current RashidAvatar SVG content

#### 2. Create unified character component
File: `src/components/rashid/character/RashidCharacter.tsx`

```tsx
interface RashidCharacterProps {
  pose: 'wave' | 'thinking' | 'presenting' | 'celebrating' | 'listening' | 'bust';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  animated?: boolean;
  className?: string;
}

// Sizes: xs=32px, sm=48px, md=128px, lg=256px, xl=400px
// Animated: adds subtle idle animation (breathing/bobbing)
// Transitions: use framer-motion AnimatePresence for pose changes
```

#### 3. Add blinking animation
All poses should include a blinking effect:
- Eyes close briefly every 3-5 seconds (randomized interval)
- Use CSS keyframes or framer-motion
- The blink is just reducing eye height to a line for 150ms

#### 4. Add subtle idle animations per pose
- Wave: hand oscillates slightly (5 degree rotation back/forth)
- Thinking: slight head tilt oscillation
- Presenting: hand bobs slightly up/down
- Celebrating: subtle bounce
- Listening: very slight lean oscillation
- Bust: gentle breathing (scale Y 1.0 to 1.01)

#### 5. Update RashidWidget to use new character
File: `src/components/rashid/RashidWidget.tsx`

Replace the current RashidAvatar usage with RashidCharacter:
- Collapsed widget: use 'bust' pose, size 'sm'
- While user types in mini chat: switch to 'listening'
- While AI is responding: switch to 'thinking'
- When AI responds: briefly show 'presenting' then back to 'bust'
- On first appearance (page load): show 'wave' for 3 seconds then 'bust'

#### 6. Create an index file
File: `src/components/rashid/character/index.ts`
Export all components for easy importing.

### SVG Guidelines:
- Use viewBox="0 0 200 400" for full body (200 wide, 400 tall)
- Use viewBox="0 0 200 200" for bust
- All colors as constants (importable from a colors.ts file)
- Each SVG part should be a separate group (<g>) for animation targeting
- Keep SVGs clean and optimized (no unnecessary paths)
- Use rounded shapes for friendly appearance

### File Structure:
```
src/components/rashid/character/
├── index.ts
├── RashidCharacter.tsx    (unified component with pose switching)
├── RashidWave.tsx
├── RashidThinking.tsx
├── RashidPresenting.tsx
├── RashidCelebrating.tsx
├── RashidListening.tsx
├── RashidBust.tsx
├── colors.ts              (shared color constants)
└── animations.ts          (shared framer-motion variants)
```
```

---

## PHASE 3: Rashid Context Integrations (Frontend)
**Time: 2-3 hours | Priority: MEDIUM**

### Cline Prompt:

```
## Task: Integrate Rashid into key user interactions across the website

### Context:
- Rashid floating widget exists at `src/components/rashid/RashidWidget.tsx`
- Rashid character poses exist at `src/components/rashid/character/`
- AskRashidButton component exists at `src/components/rashid/AskRashidButton.tsx`
- Backend REST endpoint: POST `/api/v1/rashid/conversations/{id}/send_message/`
- Rashid tools: cv_review, cover_letter, interview_prep, linkedin_optimizer, course_advisor

### Requirements:

#### 1. Job Detail Page - "Ask Rashid" Section
File: `src/pages/JobDetail.tsx`

After the job description section, add a card:
```tsx
<Card className="border-blue-200 bg-blue-50/50 dark:bg-blue-950/20">
  <CardContent className="flex items-center gap-4 p-4">
    <RashidCharacter pose="presenting" size="sm" />
    <div className="flex-1">
      <p className="font-medium">{isAr ? 'عايز أساعدك في الوظيفة دي؟' : 'Need help with this job?'}</p>
      <div className="flex gap-2 mt-2 flex-wrap">
        <AskRashidButton tool="analyze_job" context={{ job_id: job.id, job_title: job.title }} label={isAr ? 'حلل الوظيفة' : 'Analyze Job'} />
        <AskRashidButton tool="cover_letter" context={{ job_id: job.id, company: job.company?.name }} label={isAr ? 'اكتب Cover Letter' : 'Cover Letter'} />
        <AskRashidButton tool="interview_prep" context={{ job_id: job.id, job_title: job.title }} label={isAr ? 'حضرني للمقابلة' : 'Interview Prep'} />
      </div>
    </div>
  </CardContent>
</Card>
```

The AskRashidButton should dispatch a custom event that the RashidWidget listens for:
```tsx
// In AskRashidButton onClick:
window.dispatchEvent(new CustomEvent('rashid:open-tool', { detail: { tool, context } }));
```

```tsx
// In RashidWidget, listen for the event:
useEffect(() => {
  const handler = (e: CustomEvent) => {
    setToolToOpen(e.detail.tool);
    setToolContext(e.detail.context);
    setIsExpanded(true);
  };
  window.addEventListener('rashid:open-tool', handler as EventListener);
  return () => window.removeEventListener('rashid:open-tool', handler as EventListener);
}, []);
```

#### 2. Profile Page - CV Review Prompt
File: `src/pages/Profile.tsx`

After the CV/resume upload section (look for file upload or resume section), add:
```tsx
<div className="flex items-center gap-3 p-3 rounded-lg bg-blue-50 dark:bg-blue-950/20 mt-3">
  <RashidCharacter pose="bust" size="xs" />
  <p className="text-sm flex-1">{isAr ? 'عايز أراجعلك السيرة الذاتية؟' : 'Want me to review your CV?'}</p>
  <AskRashidButton tool="cv_review" size="sm" label={isAr ? 'راجع' : 'Review'} />
</div>
```

#### 3. Empty Search Results - Rashid Helps
File: `src/components/EmptyState.tsx` (or wherever the "no jobs found" state is)

When job search returns 0 results, show Rashid:
```tsx
<div className="flex flex-col items-center py-8">
  <RashidCharacter pose="thinking" size="md" />
  <p className="mt-4 text-muted-foreground">
    {isAr ? 'مفيش نتايج... عايز أساعدك تحسن البحث؟' : 'No results... Want me to help improve your search?'}
  </p>
  <AskRashidButton tool="career_path" className="mt-3" label={isAr ? 'ساعدني' : 'Help me'} />
</div>
```

#### 4. Post-Apply Celebration
File: `src/pages/JobDetail.tsx` (in the apply success handler)

After a user clicks "Apply" and it succeeds, show a toast or small modal:
```tsx
// After successful apply:
toast({
  title: isAr ? 'ممتاز! تم التقديم' : 'Great! Application sent',
  description: isAr ? 'عايز أحضرك للمقابلة؟' : 'Want me to prep you for the interview?',
  action: <AskRashidButton tool="interview_prep" context={{ job_id: job.id }} size="sm" label={isAr ? 'أيوه' : 'Yes'} />,
});
```

#### 5. First-Login Onboarding Flow
File: `src/components/rashid/RashidOnboarding.tsx` (NEW)

Create a full-screen overlay that shows ONCE for new users:

```tsx
interface OnboardingStep {
  question: { en: string; ar: string };
  options?: { value: string; label: { en: string; ar: string } }[];
  type: 'select' | 'text';
}

const STEPS: OnboardingStep[] = [
  {
    question: { en: "What's your career level?", ar: "إيه مستواك المهني؟" },
    options: [
      { value: 'junior', label: { en: 'Junior (0-2 years)', ar: 'مبتدئ (٠-٢ سنة)' } },
      { value: 'mid', label: { en: 'Mid (2-5 years)', ar: 'متوسط (٢-٥ سنوات)' } },
      { value: 'senior', label: { en: 'Senior (5+ years)', ar: 'خبير (٥+ سنوات)' } },
    ],
    type: 'select',
  },
  {
    question: { en: "What field do you work in?", ar: "إيه المجال اللي بتشتغل فيه؟" },
    type: 'text',
  },
  {
    question: { en: "What's your goal right now?", ar: "إيه هدفك دلوقتي؟" },
    options: [
      { value: 'find_job', label: { en: 'Find a job', ar: 'ألاقي شغل' } },
      { value: 'promotion', label: { en: 'Get promoted', ar: 'أترقى' } },
      { value: 'switch', label: { en: 'Switch career', ar: 'أغير مجالي' } },
      { value: 'learn', label: { en: 'Learn new skills', ar: 'أتعلم مهارات جديدة' } },
    ],
    type: 'select',
  },
];
```

Flow:
1. Full-screen overlay with semi-transparent backdrop
2. Rashid character (wave pose, size lg) in the center
3. Speech bubble with the current question
4. Options as buttons below
5. After last step, POST to `/api/v1/rashid/profile/complete_onboarding/` with answers
6. Rashid switches to celebrating pose, then overlay fades out
7. Save `rashid_onboarded: true` in localStorage so it doesn't show again

Mount this in `App.tsx`:
```tsx
{isAuthenticated && !localStorage.getItem('rashid_onboarded') && <RashidOnboarding />}
```

#### 6. Update AskRashidButton component
File: `src/components/rashid/AskRashidButton.tsx`

Make sure it:
- Dispatches the `rashid:open-tool` custom event
- Has variants: `size="sm"` (compact), default (normal)
- Shows the appropriate icon based on tool
- Supports className prop for positioning
```

---

## PHASE 4: Qdrant Vector Search Deployment
**Time: 2-3 hours | Priority: MEDIUM**

### Cline Prompt:

```
## Task: Set up Qdrant vector search and make semantic search functional

### Context:
- Backend app `apps/vectors/` has fully implemented views for semantic search
- `docker-compose.qdrant.yml` already exists at project root
- Management command `backend/apps/vectors/management/commands/index_jobs.py` exists
- The vectors app is registered in URLs at `/api/v1/vectors/`
- Need to verify the vectors service works with Qdrant

### Requirements:

#### 1. Check and fix the vectors service
File: `backend/apps/vectors/service.py`

Read this file and verify:
- It connects to Qdrant (check what env vars it reads: likely QDRANT_URL or QDRANT_HOST)
- It uses an embedding model (likely Cohere or Bedrock Titan)
- The collection name and vector dimensions are configured
- The `search_similar` and `hybrid_search` methods work correctly

If it references Cohere API:
- Add `COHERE_API_KEY` to `.env.example`
- Add a fallback: if no Cohere key, use Bedrock Titan Embeddings instead

If the service is a stub, implement it:
```python
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
COLLECTION_NAME = 'jobs'
VECTOR_SIZE = 1024  # Cohere embed-multilingual-v3.0

class VectorService:
    def __init__(self):
        self.client = QdrantClient(url=QDRANT_URL)
    
    def ensure_collection(self):
        collections = self.client.get_collections().collections
        if COLLECTION_NAME not in [c.name for c in collections]:
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
            )
    
    def index_job(self, job_id, embedding, payload):
        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(id=job_id, vector=embedding, payload=payload)]
        )
    
    def search_similar(self, query_embedding, limit=10, filters=None):
        results = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=limit,
            query_filter=filters
        )
        return results
```

#### 2. Fix the index_jobs management command
File: `backend/apps/vectors/management/commands/index_jobs.py`

Verify it:
- Fetches all active jobs from `apps.jobs.models.Job`
- Generates embeddings for each job (title + description combined)
- Upserts into Qdrant with job metadata as payload
- Handles pagination for large job sets
- Has a `--batch-size` argument

#### 3. Add environment variables
File: `backend/.env.example`

Add:
```
# Vector Search (Qdrant)
QDRANT_URL=http://localhost:6333
COHERE_API_KEY=  # Optional: for embeddings. Falls back to Bedrock Titan if empty.
```

#### 4. Add pip requirements
File: `backend/requirements.txt` (or wherever dependencies are listed)

Add:
```
qdrant-client>=1.7.0
cohere>=5.0.0  # optional, for embeddings
```

#### 5. Add health check for Qdrant
File: `backend/apps/vectors/views.py`

In the `VectorHealthView`, verify it checks Qdrant connectivity:
```python
class VectorHealthView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            from .service import get_vector_service
            service = get_vector_service()
            collections = service.client.get_collections()
            return Response({
                'success': True,
                'data': {
                    'status': 'healthy',
                    'collections': len(collections.collections),
                    'qdrant_url': service.client._client.rest_uri
                }
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=503)
```

#### 6. Deployment instructions
Create file: `deployment/setup-qdrant.sh`
```bash
#!/bin/bash
# Run on the production server to start Qdrant
docker run -d \
  --name qdrant \
  --restart always \
  -p 6333:6333 \
  -p 6334:6334 \
  -v /var/www/usam/qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest

echo "Qdrant running at http://localhost:6333"
echo "Next: cd /var/www/usam/backend && python manage.py index_jobs"
```
```

---

## PHASE 5: Run Scrapers + Seed Data
**Time: 1-2 hours | Priority: HIGH**

### Cline Prompt:

```
## Task: Make the scraper pipeline functional and seed more jobs into the database

### Context:
- Currently only 20 jobs in the database (need 500+ for a real platform)
- `backend/apps/scraper/orchestrator.py` has the scraping logic
- `backend/apps/scraper/tasks.py` has Celery tasks
- `backend/apps/scraper/management/commands/run_scrapers.py` exists
- The scraper uses `apps.jobs.models.Job` and `apps.jobs.models.Source`
- Sources in DB represent job boards/company career pages to scrape

### Requirements:

#### 1. Verify the run_scrapers command works
File: `backend/apps/scraper/management/commands/run_scrapers.py`

Read it and ensure it:
- Imports the orchestrator correctly
- Handles the case where no Sources are configured
- Can run in `--dry-run` mode (shows what would be scraped without saving)
- Has a `--source` flag to run a specific source only

#### 2. Create a seed_jobs management command for demo data
File: `backend/apps/scraper/management/commands/seed_jobs.py` (NEW)

Create a command that generates 200+ realistic job listings WITHOUT scraping:
```python
"""
Generate realistic demo jobs for the E-Career platform.
Covers Egyptian/MENA market: Cairo, Alexandria, Dubai, Riyadh, Remote.
"""
from django.core.management.base import BaseCommand
from apps.jobs.models import Job, Company, Source, Tag
from django.utils import timezone
import random
from datetime import timedelta

COMPANIES = [
    {'name': 'Vodafone Egypt', 'industry': 'Telecommunications', 'website': 'https://careers.vodafone.com.eg'},
    {'name': 'Amazon MENA', 'industry': 'Technology', 'website': 'https://amazon.jobs'},
    {'name': 'Careem', 'industry': 'Technology', 'website': 'https://careers.careem.com'},
    {'name': 'Valeo Egypt', 'industry': 'Automotive', 'website': 'https://valeo.com/en/careers'},
    {'name': 'Orange Egypt', 'industry': 'Telecommunications', 'website': 'https://orange.jobs'},
    {'name': 'Instabug', 'industry': 'Technology', 'website': 'https://instabug.com/careers'},
    {'name': 'Swvl', 'industry': 'Transportation', 'website': 'https://swvl.com/careers'},
    {'name': 'Fawry', 'industry': 'Fintech', 'website': 'https://fawry.com/careers'},
    {'name': 'Noon', 'industry': 'E-commerce', 'website': 'https://noon.com/careers'},
    {'name': 'Talabat', 'industry': 'Food Delivery', 'website': 'https://talabat.com/careers'},
    {'name': 'McKinsey Cairo', 'industry': 'Consulting', 'website': 'https://mckinsey.com/careers'},
    {'name': 'PwC Middle East', 'industry': 'Consulting', 'website': 'https://pwc.com/me/careers'},
    {'name': 'Microsoft Egypt', 'industry': 'Technology', 'website': 'https://careers.microsoft.com'},
    {'name': 'IBM Egypt', 'industry': 'Technology', 'website': 'https://ibm.com/careers'},
    {'name': 'Dell Technologies Egypt', 'industry': 'Technology', 'website': 'https://dell.com/careers'},
    {'name': 'Banque Misr', 'industry': 'Banking', 'website': 'https://banquemisr.com/careers'},
    {'name': 'CIB Egypt', 'industry': 'Banking', 'website': 'https://cibeg.com/careers'},
    {'name': 'Orascom', 'industry': 'Construction', 'website': 'https://orascom.com/careers'},
    {'name': 'Si-Ware Systems', 'industry': 'Hardware', 'website': 'https://si-ware.com/careers'},
    {'name': 'Eventum', 'industry': 'Events', 'website': 'https://eventum.com.eg/careers'},
]

JOB_TEMPLATES = [
    # Engineering
    {'title': 'Senior Backend Engineer', 'tags': ['Python', 'Django', 'PostgreSQL', 'AWS'], 'salary_min': 25000, 'salary_max': 50000},
    {'title': 'Frontend Developer', 'tags': ['React', 'TypeScript', 'Tailwind'], 'salary_min': 15000, 'salary_max': 35000},
    {'title': 'Full Stack Developer', 'tags': ['Node.js', 'React', 'MongoDB'], 'salary_min': 20000, 'salary_max': 45000},
    {'title': 'DevOps Engineer', 'tags': ['Docker', 'Kubernetes', 'AWS', 'CI/CD'], 'salary_min': 30000, 'salary_max': 60000},
    {'title': 'Mobile Developer (Flutter)', 'tags': ['Flutter', 'Dart', 'Firebase'], 'salary_min': 18000, 'salary_max': 40000},
    {'title': 'Data Engineer', 'tags': ['Python', 'Spark', 'Airflow', 'SQL'], 'salary_min': 25000, 'salary_max': 55000},
    {'title': 'Machine Learning Engineer', 'tags': ['Python', 'TensorFlow', 'PyTorch'], 'salary_min': 30000, 'salary_max': 65000},
    {'title': 'QA Engineer', 'tags': ['Selenium', 'Python', 'API Testing'], 'salary_min': 12000, 'salary_max': 25000},
    {'title': 'iOS Developer', 'tags': ['Swift', 'SwiftUI', 'Xcode'], 'salary_min': 20000, 'salary_max': 45000},
    {'title': 'Android Developer', 'tags': ['Kotlin', 'Jetpack Compose', 'Firebase'], 'salary_min': 18000, 'salary_max': 40000},
    # Product/Design
    {'title': 'Product Manager', 'tags': ['Product Strategy', 'Agile', 'Analytics'], 'salary_min': 25000, 'salary_max': 55000},
    {'title': 'UX/UI Designer', 'tags': ['Figma', 'User Research', 'Prototyping'], 'salary_min': 15000, 'salary_max': 35000},
    {'title': 'Technical Product Owner', 'tags': ['Scrum', 'JIRA', 'Technical Writing'], 'salary_min': 22000, 'salary_max': 45000},
    # Business
    {'title': 'Digital Marketing Manager', 'tags': ['SEO', 'Google Ads', 'Social Media'], 'salary_min': 12000, 'salary_max': 30000},
    {'title': 'Business Development Manager', 'tags': ['Sales', 'B2B', 'CRM'], 'salary_min': 18000, 'salary_max': 40000},
    {'title': 'Financial Analyst', 'tags': ['Excel', 'Financial Modeling', 'SQL'], 'salary_min': 15000, 'salary_max': 35000},
    {'title': 'HR Manager', 'tags': ['Recruitment', 'Performance Management', 'HRIS'], 'salary_min': 15000, 'salary_max': 30000},
    {'title': 'Operations Manager', 'tags': ['Logistics', 'Process Improvement', 'KPIs'], 'salary_min': 20000, 'salary_max': 45000},
    # Entry Level
    {'title': 'Junior Software Developer', 'tags': ['JavaScript', 'Python', 'Git'], 'salary_min': 8000, 'salary_max': 15000},
    {'title': 'Customer Support Specialist', 'tags': ['Communication', 'CRM', 'English'], 'salary_min': 6000, 'salary_max': 12000},
]

LOCATIONS = ['Cairo, Egypt', 'Alexandria, Egypt', 'Giza, Egypt', 'Dubai, UAE', 'Riyadh, Saudi Arabia', 'Remote']
EXPERIENCE_LEVELS = ['entry', 'mid', 'senior', 'lead']

class Command(BaseCommand):
    help = 'Seed 200+ realistic job listings for the MENA market'
    
    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=200, help='Number of jobs to create')
        parser.add_argument('--clear', action='store_true', help='Clear existing seeded jobs first')
    
    def handle(self, *args, **options):
        count = options['count']
        
        if options['clear']:
            Job.objects.filter(source__name='seed_data').delete()
            self.stdout.write('Cleared existing seeded jobs')
        
        # Create or get seed source
        source, _ = Source.objects.get_or_create(
            name='seed_data',
            defaults={'url': 'https://jobs.usamif.com', 'source_type': 'manual'}
        )
        
        # Create companies
        companies = []
        for c in COMPANIES:
            company, _ = Company.objects.get_or_create(
                name=c['name'],
                defaults={
                    'industry': c['industry'],
                    'website': c['website'],
                    'is_active': True,
                }
            )
            companies.append(company)
        
        # Create tags
        tags_cache = {}
        for template in JOB_TEMPLATES:
            for tag_name in template['tags']:
                if tag_name not in tags_cache:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    tags_cache[tag_name] = tag
        
        # Generate jobs
        created = 0
        for i in range(count):
            template = random.choice(JOB_TEMPLATES)
            company = random.choice(companies)
            location = random.choice(LOCATIONS)
            exp = random.choice(EXPERIENCE_LEVELS)
            
            # Vary salary based on location
            multiplier = 1.0
            if 'Dubai' in location or 'Riyadh' in location:
                multiplier = 2.5
            
            posted_days_ago = random.randint(1, 30)
            
            job = Job.objects.create(
                title=f"{template['title']} - {company.name}",
                company=company,
                source=source,
                location=location,
                experience_level=exp,
                salary_min=int(template['salary_min'] * multiplier),
                salary_max=int(template['salary_max'] * multiplier),
                salary_currency='EGP' if 'Egypt' in location else ('AED' if 'UAE' in location else 'SAR'),
                description=f"We are looking for a {template['title']} to join {company.name} in {location}. This is a {exp}-level position.",
                direct_apply_url=f"{company.website}/apply/{i}",
                status='active',
                posted_at=timezone.now() - timedelta(days=posted_days_ago),
                expires_at=timezone.now() + timedelta(days=60 - posted_days_ago),
            )
            
            # Add tags
            for tag_name in template['tags']:
                job.tags.add(tags_cache[tag_name])
            
            created += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {created} jobs across {len(companies)} companies'))
```

#### 3. Add more sources for the scraper
File: `backend/apps/scraper/management/commands/setup_sources.py` (NEW)

Create a command that adds scraping sources to the database:
```python
SOURCES = [
    {'name': 'Wuzzuf', 'url': 'https://wuzzuf.net', 'source_type': 'job_board'},
    {'name': 'LinkedIn Egypt', 'url': 'https://linkedin.com/jobs', 'source_type': 'job_board'},
    {'name': 'Bayt', 'url': 'https://bayt.com', 'source_type': 'job_board'},
    {'name': 'Glassdoor', 'url': 'https://glassdoor.com', 'source_type': 'job_board'},
    {'name': 'Indeed Egypt', 'url': 'https://eg.indeed.com', 'source_type': 'job_board'},
]
```

#### 4. Verify seed command works
After creating, test with:
```bash
python manage.py seed_jobs --count 200
python manage.py seed_jobs --count 50 --clear  # clears and re-seeds
```
```

---

## PHASE 6: Production Hardening + Final Polish
**Time: 2-3 hours | Priority: MEDIUM**

### Cline Prompt:

```
## Task: Production hardening - security, error handling, and deployment configs

### Context:
- Server: Ubuntu 22.04, 13.49.245.174, domain jobs.usamif.com
- Services: Gunicorn, Celery, Celery Beat, Redis, PostgreSQL, Typesense, Nginx
- Sentry SDK is installed but no DSN configured
- Django 4.2.16, DRF, drf-spectacular for API docs

### Requirements:

#### 1. Fix open redirect vulnerability in email tracking
File: `backend/apps/emails/views.py`

In the `TrackClickView` (or equivalent click tracking view), the `url` parameter is used to redirect without validation.

Add URL validation:
```python
from urllib.parse import urlparse

ALLOWED_REDIRECT_SCHEMES = ['http', 'https']
BLOCKED_DOMAINS = ['evil.com']  # Add known bad domains

def is_safe_redirect_url(url):
    """Validate redirect URL is safe"""
    if not url:
        return False
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_REDIRECT_SCHEMES:
        return False
    if not parsed.netloc:
        return False
    return True
```

Apply this validation before redirecting. If URL is invalid, redirect to the homepage instead.

#### 2. Add proper error logging with context
File: `backend/apps/core/exceptions.py`

Ensure the custom exception handler:
- Logs the full traceback for 500 errors
- Includes request path, user ID, and timestamp
- Sends to Sentry if configured
- Returns a clean JSON error response to the client (no stack traces exposed)

#### 3. Add management command for health verification
File: `backend/apps/monitoring/management/commands/health_check.py` (NEW)

```python
"""
Run all health checks and report status.
Usage: python manage.py health_check
Exit code 0 = all healthy, 1 = some degraded, 2 = critical failure
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache
import requests

class Command(BaseCommand):
    help = 'Run health checks on all services'
    
    def handle(self, *args, **options):
        checks = {}
        
        # Database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            checks['database'] = 'OK'
        except Exception as e:
            checks['database'] = f'FAIL: {e}'
        
        # Redis
        try:
            cache.set('health', 'ok', 10)
            assert cache.get('health') == 'ok'
            checks['redis'] = 'OK'
        except Exception as e:
            checks['redis'] = f'FAIL: {e}'
        
        # Typesense
        try:
            resp = requests.get('http://localhost:8108/health', timeout=5)
            checks['typesense'] = 'OK' if resp.status_code == 200 else f'FAIL: {resp.status_code}'
        except Exception as e:
            checks['typesense'] = f'FAIL: {e}'
        
        # Print results
        all_ok = True
        for service, status in checks.items():
            icon = '✅' if status == 'OK' else '❌'
            self.stdout.write(f'{icon} {service}: {status}')
            if status != 'OK':
                all_ok = False
        
        if not all_ok:
            raise SystemExit(1)
```

#### 4. Add CORS and security headers verification
File: `backend/config/settings/base.py`

Verify these settings exist (add if missing):
```python
# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# CORS
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='https://jobs.usamif.com',
    cast=Csv()
)
CORS_ALLOW_CREDENTIALS = True
```

#### 5. Add rate limiting to sensitive auth endpoints
File: `backend/apps/accounts/views.py`

Add throttle classes to these views:
```python
from rest_framework.throttling import AnonRateThrottle

class AuthRateThrottle(AnonRateThrottle):
    rate = '5/minute'

class RegisterView(APIView):
    throttle_classes = [AuthRateThrottle]
    # ...

class LoginView(APIView):
    throttle_classes = [AuthRateThrottle]
    # ...

class PasswordResetRequestView(APIView):
    throttle_classes = [AuthRateThrottle]
    # ...
```

#### 6. Create deployment checklist script
File: `deployment/deploy.sh`
```bash
#!/bin/bash
set -e

echo "=== E-Career Deployment Script ==="
echo "Server: $(hostname)"
echo "Date: $(date)"
echo ""

cd /var/www/usam

# Pull latest code
echo ">>> Pulling latest code..."
git pull origin development

# Backend
echo ">>> Installing backend dependencies..."
cd backend
source /var/www/usam/venv/bin/activate
pip install -r requirements.txt --quiet

# Migrations
echo ">>> Running migrations..."
python manage.py migrate --noinput

# Static files
echo ">>> Collecting static files..."
python manage.py collectstatic --noinput --clear

# Frontend
echo ">>> Building frontend..."
cd /var/www/usam/frontend
npm install --silent
npm run build

# Restart services
echo ">>> Restarting services..."
sudo systemctl restart usam celery-usam celery-beat-usam

# Health check
echo ">>> Running health check..."
sleep 3
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/jobs/)
if [ "$STATUS" = "200" ]; then
    echo "✅ API is healthy (HTTP $STATUS)"
else
    echo "❌ API check failed (HTTP $STATUS)"
    sudo journalctl -u usam --since "30 sec ago" --no-pager | tail -10
    exit 1
fi

echo ""
echo "=== Deployment Complete ==="
echo "Site: https://jobs.usamif.com"
```

Make executable: `chmod +x deployment/deploy.sh`

#### 7. Update .env.example with all required variables
File: `backend/.env.example`

Ensure it has ALL environment variables the app needs:
```env
# Core
SECRET_KEY=change-me-in-production
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,jobs.usamif.com
ADMIN_URL=admin/

# Database
DATABASE_URL=postgres://user:pass@localhost:5432/ecareer

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1

# CORS
CORS_ALLOWED_ORIGINS=https://jobs.usamif.com

# JWT
ACCESS_TOKEN_LIFETIME_MINUTES=15
REFRESH_TOKEN_LIFETIME_DAYS=7

# AWS Bedrock (for Rashid AI)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=eu-north-1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@jobs.usamif.com

# Typesense
TYPESENSE_API_KEY=
TYPESENSE_HOST=localhost
TYPESENSE_PORT=8108

# Vector Search (Qdrant)
QDRANT_URL=http://localhost:6333
COHERE_API_KEY=

# Sentry
SENTRY_DSN=

# Google OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Encryption (for Rashid messages)
FIELD_ENCRYPTION_KEY=

# Domain
SITE_URL=https://jobs.usamif.com
```
```

---

## EXECUTION ORDER

| Phase | What | Time | Dependencies |
|-------|------|------|-------------|
| **5** | Seed 200+ jobs | 1-2 hrs | None - DO FIRST for visible impact |
| **1** | REST API for Rashid chat | 1-2 hrs | None |
| **3** | Rashid context integrations | 2-3 hrs | Phase 1 |
| **2** | Rashid character poses | 2-3 hrs | None (visual only) |
| **4** | Qdrant vector search | 2-3 hrs | Needs Docker on server |
| **6** | Production hardening | 2-3 hrs | All others done |

**Recommended:** Run Phase 5 first (seed jobs), then Phase 1 (REST chat), then Phase 3 (integrations). This gives the biggest visible impact fastest.

---

## AFTER ALL PHASES: Final Deployment

```bash
# On Windows:
cd "m:\job already web for jobs\E-Career"
git add -A
git commit -m "Complete all remaining features: Rashid character, vector search, seed data, hardening"
git push origin development

# On Server:
cd /var/www/usam
bash deployment/deploy.sh
```

---

## NOT INCLUDED (Deferred/Not Needed)

- **LightFM recommendations** — can't compile on 2-core server, use vector search instead
- **Daphne WebSocket deployment** — REST fallback is sufficient for now
- **70% test coverage** — too much work for current phase, will add incrementally
- **CI/CD pipeline** — deploy.sh script is sufficient for now
- **UptimeRobot** — just needs a URL to be configured (no code needed)
