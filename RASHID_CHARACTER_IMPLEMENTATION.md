# Rashid Character Implementation - Cline Prompt

## Context

Rashid is an AI career mentor already fully working in the backend (`/api/v1/rashid/`). The frontend has a chat page at `/app/rashid` but:
1. It's NOT in the navbar - users can't find it
2. It has no visual character - just a plain chat interface
3. It should appear ACROSS the entire website as a floating assistant character

## What Rashid Should Be

Rashid is an Egyptian male HR mentor character with:
- A visual avatar/character (face, body, legs) - like a friendly cartoon HR professional
- Appears as a floating widget on ALL pages (bottom-right corner)
- Can be expanded into full chat mode
- Offers contextual help based on which page the user is on
- Speaks Egyptian Arabic dialect

---

## PHASE 1: Add Rashid to Navigation + Floating Widget (Priority: HIGH)

### Cline Prompt:

```
## Task: Add Rashid AI assistant as a floating character widget across the entire website

### Context:
- Frontend: React + Vite + TypeScript + Tailwind + shadcn/ui + framer-motion
- Rashid chat page already exists at `src/pages/RashidChat.tsx`
- Rashid backend is live at `/api/v1/rashid/`
- WebSocket endpoint: `/ws/rashid/`

### Requirements:

#### 1. Create Rashid Floating Widget Component
File: `src/components/rashid/RashidWidget.tsx`

Create a floating character that appears on ALL pages (bottom-right corner):
- Default state: A small animated character avatar (64x64px) with a speech bubble hint
- The character should be an SVG/CSS illustration of a friendly Egyptian man in business attire:
  - Round friendly face with slight smile
  - Short dark hair, light beard/stubble
  - Business shirt (no tie, professional but approachable)
  - Visible from waist up in collapsed state
  - Use CSS animations for subtle idle movement (slight bounce/wave)
- On hover: speech bubble appears with contextual greeting in Egyptian Arabic
- On click: expands into a chat panel (400px wide, 600px tall) sliding up from the corner

#### 2. Contextual Greetings Based on Current Page
The speech bubble should show different hints based on the route:
- `/jobs` or `/app/jobs` → "عايز أساعدك تلاقي وظيفة مناسبة؟" (Want me to help you find a suitable job?)
- `/app/jobs/:id` → "عايز أحللك الوظيفة دي؟" (Want me to analyze this job for you?)
- `/profile` or `/app/profile` → "أراجعلك السيرة الذاتية؟" (Shall I review your CV?)
- `/app/employer/*` → "محتاج مساعدة في التوظيف؟" (Need help with hiring?)
- Default → "أهلاً! أنا راشد، مستشارك المهني" (Hi! I'm Rashid, your career advisor)

#### 3. Mini Chat Panel (Expanded State)
When clicked, show an embedded mini version of the chat:
- Header: Rashid's avatar + name "راشد" + close button
- Message area (scrollable)
- Input field + send button
- "Open full chat" link → navigates to `/app/rashid`
- Connect to the same WebSocket as the full chat page
- Keep conversation state between mini and full views

#### 4. Add to Navbar
File: `src/components/Navbar.tsx`
Add Rashid to the navItems array:
```typescript
{ to: "/app/rashid", label: "Rashid", labelAr: "راشد", icon: MessageSquare },
```
Place it between "Profile" and "About".

#### 5. Mount the Widget Globally
File: `src/App.tsx`
Add the RashidWidget component inside the BrowserRouter but outside Routes, so it appears on every page:
```tsx
<BrowserRouter>
  <AnimatedRoutes />
  <RashidWidget />
</BrowserRouter>
```
Only show if user is authenticated.

#### 6. Character SVG/Illustration
Create `src/components/rashid/RashidAvatar.tsx`:
- Create an SVG component of Rashid's character
- He is a friendly Egyptian man, approximately 30 years old
- Business casual (light blue shirt, dark pants)
- Warm smile, welcoming hand gesture
- The SVG should support 3 states:
  - `idle` - subtle breathing/bobbing animation
  - `talking` - mouth/hand moves slightly
  - `thinking` - hand on chin, dots appear
- Use framer-motion for smooth transitions between states

#### 7. Animations
- Widget entrance: slide up + fade in (on page load, after 2 second delay)
- Speech bubble: pop in with spring animation
- Chat panel: slide up from bottom-right with opacity transition
- Character idle: subtle 2px up/down float (CSS keyframes)
- When Rashid is "typing": the character switches to thinking state

#### 8. Mobile Responsive
- On mobile: widget is smaller (48x48px)
- Chat panel becomes full-screen modal on mobile
- Speech bubble is hidden on mobile (only shows on tap)

#### 9. Persist State
- Save last conversation ID in localStorage
- Resume conversation when widget is reopened
- Remember if user dismissed the widget (don't show greeting again for 24 hours)

### Technical Notes:
- Use the existing auth hook: `import { useAuth } from '@/hooks/use-auth'`
- Use the existing theme hook: `import { useTheme } from '@/hooks/use-theme'` (for lang/RTL)
- WebSocket URL from env: `import.meta.env.VITE_WS_URL || 'ws://localhost:8000'`
- API URL from env: `import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'`
- Token from localStorage: `localStorage.getItem('accessToken')`

### File Structure:
```
src/components/rashid/
├── RashidWidget.tsx       (main floating widget)
├── RashidAvatar.tsx       (SVG character with animations)
├── RashidMiniChat.tsx     (embedded mini chat panel)
├── RashidBubble.tsx       (speech bubble component)
├── ToolSelector.tsx       (already exists)
└── rashid-animations.css  (keyframe animations)
```
```

---

## PHASE 2: Rashid Appears in Key Interactions (Priority: MEDIUM)

### Cline Prompt:

```
## Task: Integrate Rashid character into key user interactions across the website

### Context:
- Rashid floating widget is now implemented (from Phase 1)
- Rashid has tools: cv_review, cover_letter, interview_prep, linkedin_optimizer, course_advisor
- Backend supports these via REST API and WebSocket

### Requirements:

#### 1. Job Detail Page - "Ask Rashid" Section
File: `src/pages/JobDetail.tsx`
Add a card/section after job details:
- Show Rashid's avatar (small, 40px)
- Text: "عايز أساعدك في الوظيفة دي؟" / "Want help with this job?"
- 3 action buttons:
  - "حلل الوظيفة" / "Analyze Job" → opens Rashid widget with job context
  - "اكتب Cover Letter" / "Write Cover Letter" → triggers cover_letter tool
  - "حضرني للمقابلة" / "Prep for Interview" → triggers interview_prep tool
- Clicking any button opens the Rashid mini chat and sends the appropriate tool command

#### 2. Profile Page - CV Review Prompt
File: `src/pages/Profile.tsx`
After the CV upload section, add:
- Rashid avatar + speech bubble: "عايز أراجعلك السيرة الذاتية؟"
- Button: "Review My CV" → opens Rashid with cv_review tool triggered

#### 3. Job Search - No Results State
When job search returns 0 results, show Rashid:
- Full character (upper body)
- Speech: "مفيش نتايج... عايز أساعدك تحسن البحث بتاعك؟"
- Button: "ساعدني" → opens Rashid in career_path mode

#### 4. After Applying to a Job
Show a toast/modal with Rashid:
- "ممتاز! عايز أحضرك للمقابلة؟" / "Great! Want me to prep you for the interview?"
- Button: "أيوه" → opens Rashid with interview_prep + job context

#### 5. Onboarding Flow (First Login)
File: `src/components/rashid/RashidOnboarding.tsx`
When a new user logs in for the first time:
- Full-screen overlay with Rashid character (full body, animated)
- He introduces himself in Egyptian Arabic
- Steps through 3 questions:
  1. "إيه مستواك المهني؟" (What's your career level?) → Junior/Mid/Senior
  2. "إيه المجال اللي بتشتغل فيه؟" (What field do you work in?) → text input
  3. "إيه هدفك دلوقتي؟" (What's your goal now?) → Find job / Get promoted / Switch career / Learn new skills
- Saves to Rashid profile via POST /api/v1/rashid/profile/complete_onboarding/
- After onboarding, Rashid waves and the overlay closes

### Technical Notes:
- To trigger a tool, send WebSocket message: `{ "type": "tool_execute", "tool": "cv_review", "context": {...} }`
- To set job context when opening chat, include job_id in the conversation creation
- The onboarding should only show once (check localStorage or Rashid profile API)
```

---

## PHASE 3: Rashid Full Body Character Design (Priority: MEDIUM)

### Cline Prompt:

```
## Task: Create Rashid's full-body SVG character with multiple poses and animations

### Context:
- Rashid is an Egyptian male career mentor, age ~30
- He appears as an animated character throughout the website
- He needs multiple poses for different contexts

### Requirements:

#### Character Design Specs:
- Style: Modern flat illustration (like Notion/Slack characters but more detailed)
- Colors: 
  - Skin: warm tan (#D4956A)
  - Hair/beard: dark brown (#3B2417)
  - Shirt: light blue (#4A90D9) 
  - Pants: dark navy (#2C3E50)
  - Shoes: brown (#6B4C3B)
- Build: Average, friendly, professional
- Face: Round, warm eyes, friendly smile, short stubble beard
- Hair: Short, neat, side-parted

#### Poses to Create (separate SVG components):

1. **Idle/Wave** (`RashidWave.tsx`) - Standing, one hand raised in greeting
   - Used: First appearance, greetings
   
2. **Thinking** (`RashidThinking.tsx`) - Hand on chin, looking up slightly
   - Used: While processing/generating responses
   
3. **Presenting** (`RashidPresenting.tsx`) - One hand gesturing forward (like showing something)
   - Used: When showing results, recommendations
   
4. **Celebrating** (`RashidCelebrating.tsx`) - Both hands up, big smile
   - Used: When user completes something (apply, onboarding)
   
5. **Listening** (`RashidListening.tsx`) - Leaning slightly forward, attentive expression
   - Used: While user is typing
   
6. **Upper Body Only** (`RashidBust.tsx`) - For small widget/chat header
   - Used: In floating widget, chat header, small contexts

#### Animation Requirements:
- Each pose has subtle idle animation (breathing, slight movement)
- Transitions between poses use framer-motion
- The character blinks every 3-5 seconds (randomized)
- When talking, subtle mouth movement
- All SVGs should be responsive (scale cleanly from 48px to 400px)

#### File Structure:
```
src/components/rashid/character/
├── RashidCharacter.tsx    (main component that switches poses)
├── RashidWave.tsx
├── RashidThinking.tsx
├── RashidPresenting.tsx
├── RashidCelebrating.tsx
├── RashidListening.tsx
├── RashidBust.tsx
├── animations.ts          (shared animation configs)
└── colors.ts              (shared color constants)
```

#### Usage:
```tsx
<RashidCharacter 
  pose="wave" 
  size="lg"  // sm=48px, md=128px, lg=256px, xl=400px
  animated={true}
/>
```
```

---

## Summary: What to Give Cline

1. **Phase 1** (2-3 hours): Floating widget + navbar link + mini chat — Makes Rashid accessible everywhere
2. **Phase 2** (2-3 hours): Context integrations — Rashid helps on job details, profile, search
3. **Phase 3** (2-3 hours): Full character SVGs — Visual personality with poses

**Total: 6-9 hours of frontend work**

---

## Backend Note: WebSocket May Not Be Deployed

The Rashid chat page uses WebSocket (`/ws/rashid/`), but the production server runs **Gunicorn** (HTTP only). WebSocket requires either:
- **Daphne** (ASGI server) - needs to be configured
- OR change frontend to use REST API polling instead of WebSocket

### Quick Fix: Use REST API instead of WebSocket
The backend already has REST endpoints:
- POST `/api/v1/rashid/conversations/{id}/send_message/` - send and get AI response

The mini chat widget should use this REST endpoint (simpler, works with Gunicorn) rather than WebSocket. Only the full chat page would need WebSocket.
