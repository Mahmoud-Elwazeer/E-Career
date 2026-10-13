# USAM Master — E-Career Feature Links Catalogue

Generated: 2026-10-13T16:02:31.541Z

Platform: **E-Career (USAM Jobs / USAM Career Compass)**

Production base URL: `https://jobs.usamif.com`

> **Verification note:** every row below was verified at the CODE level only — the route exists in `frontend/src/App.tsx` and the target page component was read directly during this audit. No live HTTP request or browser test was run against the production domain as part of generating this catalogue. See `USAM-MASTER-INTEGRATION-TEST-RESULTS.md` (or the delivery summary) for what was actually tested (static build/typecheck/unit tests, plus local dev-server HTTP checks) versus what still needs a real browser pass against production.

> **Shared sign-in:** USAM Master and E-Career do **not** currently share a single sign-on session. For any gated feature, Master should link to `https://jobs.usamif.com/login?next=<url-encoded-relative-path>`. E-Career's login page validates `next` server-side — only internal relative paths are honored, any absolute/external URL is rejected — then redirects the authenticated user to that destination. Do not pass credentials or tokens in the URL.

---

## Discover Opportunities

| Feature | EN / AR | Audience | Access | Status | Overview | Direct Link | Related |
|---|---|---|---|---|---|---|---|
| `job-search` | Find Jobs / ابحث عن وظائف | Individuals / job seekers | Requires sign-in (any account type) | live | [Overview](https://jobs.usamif.com/for-individuals) | [Open](https://jobs.usamif.com/app/jobs) | job-matches, saved-jobs, job-alerts |
| `job-matches` | For You Matches / توصيات لك | Individuals / job seekers | Requires sign-in (any account type) | live | [Overview](https://jobs.usamif.com/for-individuals) | [Open](https://jobs.usamif.com/app/recommendations) | job-search, talent-score |
| `saved-jobs` | Saved Jobs / الوظائف المحفوظة | Individuals / job seekers | Requires sign-in (any account type) | live | — | [Open](https://jobs.usamif.com/app/saved) | job-search, applications |
| `job-alerts` | Job Alerts / تنبيهات الوظائف | Individuals / job seekers | Requires sign-in (any account type) | live | — | [Open](https://jobs.usamif.com/app/alerts) | job-search, job-matches |
| `applications` | Applications / طلباتي | Individuals / job seekers | Requires sign-in (any account type) | live | — | [Open](https://jobs.usamif.com/app/applications) | job-search, saved-jobs |
| `companies` | Companies / الشركات | Individuals / job seekers | Requires sign-in (any account type) | live | — | [Open](https://jobs.usamif.com/app/companies) | job-search |

## Career Tools

| Feature | EN / AR | Audience | Access | Status | Overview | Direct Link | Related |
|---|---|---|---|---|---|---|---|
| `resume-builder` | Resume Builder / منشئ السيرة الذاتية | Individuals / job seekers | Requires sign-in (any account type) | live | [Overview](https://jobs.usamif.com/for-individuals) | [Open](https://jobs.usamif.com/app/resume) | cover-letters, talent-score, rashid-coach |
| `cover-letters` | Cover Letters / خطابات التغطية | Individuals / job seekers | Requires sign-in (any account type) | live | — | [Open](https://jobs.usamif.com/app/cover-letters) | resume-builder, job-search |
| `talent-score` | Talent Score / نقاط الموهبة | Individuals / job seekers | Requires sign-in (any account type) | live | [Overview](https://jobs.usamif.com/for-individuals) | [Open](https://jobs.usamif.com/app/talent-score) | career-graph, job-matches, assessments |
| `career-graph` | Career Graph / خريطة المسار المهني | Individuals / job seekers | Requires sign-in (any account type) | live | — | [Open](https://jobs.usamif.com/app/career-graph) | talent-score, skills-explorer |
| `skills-explorer` | Skills Explorer / مستكشف المهارات | Individuals / job seekers | Requires sign-in (any account type) | live | — | [Open](https://jobs.usamif.com/app/skills) | career-graph |

## AI & Preparation

| Feature | EN / AR | Audience | Access | Status | Overview | Direct Link | Related |
|---|---|---|---|---|---|---|---|
| `rashid-coach` | Rasheed — AI Career Coach / رشيد — المساعد المهني الذكي | Individuals / job seekers | Requires sign-in (any account type) | live | [Overview](https://jobs.usamif.com/for-individuals) | [Open](https://jobs.usamif.com/app/rashid) | resume-builder, interview-practice, cover-letters |
| `interview-practice` | Interview Practice / تدريب المقابلات | Individuals / job seekers | Requires sign-in (any account type) | live | [Overview](https://jobs.usamif.com/for-individuals) | [Open](https://jobs.usamif.com/app/interviews) | rashid-coach, coding-practice |
| `coding-practice` | Coding Practice / تدريب على البرمجة | Individuals / job seekers | Requires sign-in (any account type) | live | — | [Open](https://jobs.usamif.com/app/coding-practice) | interview-practice |
| `assessments` | Assessments / التقييمات | Individuals / job seekers | Requires sign-in (any account type) | live | — | [Open](https://jobs.usamif.com/app/assessments) | talent-score |

## Insights

| Feature | EN / AR | Audience | Access | Status | Overview | Direct Link | Related |
|---|---|---|---|---|---|---|---|
| `salary-insights` | Salary Insights / رؤى الرواتب | Individuals / job seekers | Requires sign-in (any account type) | live | [Overview](https://jobs.usamif.com/for-individuals) | [Open](https://jobs.usamif.com/app/salary) | job-search, talent-score |

## Account

| Feature | EN / AR | Audience | Access | Status | Overview | Direct Link | Related |
|---|---|---|---|---|---|---|---|
| `profile` | Profile / الملف الشخصي | Individuals / job seekers | Requires sign-in (any account type) | live | — | [Open](https://jobs.usamif.com/app/profile) | talent-score, resume-builder |
| `notifications` | Notifications / الإشعارات | Everyone (any signed-in account) | Requires sign-in (any account type) | live | — | [Open](https://jobs.usamif.com/app/notifications) | — |
| `settings` | Settings / الإعدادات | Everyone (any signed-in account) | Requires sign-in (any account type) | live | — | [Open](https://jobs.usamif.com/app/settings) | — |
| `billing` | Billing & Plans / الفوترة والباقات | Everyone (any signed-in account) | Requires sign-in (any account type) | live | [Overview](https://jobs.usamif.com/pricing) | [Open](https://jobs.usamif.com/app/billing) | — |

## Hiring (Employer)

| Feature | EN / AR | Audience | Access | Status | Overview | Direct Link | Related |
|---|---|---|---|---|---|---|---|
| `employer-onboarding` | Become an Employer / سجّل كصاحب عمل | Employers / companies | Requires sign-in (any account type) | live | [Overview](https://jobs.usamif.com/for-businesses) | [Open](https://jobs.usamif.com/app/employer/register) | post-job |
| `employer-dashboard` | Employer Dashboard / لوحة تحكم صاحب العمل | Employers / companies | Requires sign-in with an Employer (or Admin) account | live | — | [Open](https://jobs.usamif.com/app/employer/dashboard) | — |
| `post-job` | Post a Job / انشر وظيفة | Employers / companies | Requires sign-in with an Employer (or Admin) account | live | [Overview](https://jobs.usamif.com/for-businesses) | [Open](https://jobs.usamif.com/app/employer/post-job) | employer-dashboard, applicants |
| `applicants` | Applicants / المتقدمون | Employers / companies | Requires sign-in with an Employer (or Admin) account | live | — | [Open](https://jobs.usamif.com/app/employer/applicants) | post-job, talent-search |
| `talent-search` | Search Talent / البحث عن مواهب | Employers / companies | Requires sign-in with an Employer (or Admin) account | live | [Overview](https://jobs.usamif.com/for-businesses) | [Open](https://jobs.usamif.com/app/employer/talent-search) | talent-pools, applicants |
| `talent-pools` | Talent Pools / قوائم المواهب | Employers / companies | Requires sign-in with an Employer (or Admin) account | live | — | [Open](https://jobs.usamif.com/app/employer/talent-pools) | talent-search |
| `employer-analytics` | Hiring Analytics / تحليلات التوظيف | Employers / companies | Requires sign-in with an Employer (or Admin) account | live | — | [Open](https://jobs.usamif.com/app/employer/analytics) | — |
| `company-profile-settings` | Company Profile / ملف الشركة | Employers / companies | Requires sign-in with an Employer (or Admin) account | live | — | [Open](https://jobs.usamif.com/app/employer/company) | — |
| `employer-team` | Team / الفريق | Employers / companies | Requires sign-in with an Employer (or Admin) account | live | — | [Open](https://jobs.usamif.com/app/employer/team) | — |
| `employer-billing` | Employer Billing & Plans / فوترة وباقات أصحاب العمل | Employers / companies | Requires sign-in with an Employer (or Admin) account | live | [Overview](https://jobs.usamif.com/pricing) | [Open](https://jobs.usamif.com/app/employer/billing) | — |

## Platform

| Feature | EN / AR | Audience | Access | Status | Overview | Direct Link | Related |
|---|---|---|---|---|---|---|---|
| `admin-console` | Admin Console / لوحة الإدارة | Platform administrators | Requires sign-in with an Admin account | live | — | [Open](https://jobs.usamif.com/admin) | admin-finance |
| `admin-finance` | Financial Control Center / مركز التحكّم المالي | Platform administrators | Requires sign-in with an Admin account | live | — | [Open](https://jobs.usamif.com/admin/finance) | admin-console |
| `api-docs` | API Documentation / وثائق الواجهة البرمجية | Everyone (any signed-in account) | None — publicly accessible | live | — | [Open](https://jobs.usamif.com/api-docs) | — |

---

## Per-feature detail

### Find Jobs (`job-search`)

- **Arabic name:** ابحث عن وظائف
- **English description:** Search verified, direct-employer roles aggregated across MENA.
- **Arabic description:** ابحث في وظائف موثقة من أصحاب العمل مباشرة عبر المنطقة.
- **Audience:** Individuals / job seekers
- **Navigation category:** discover
- **Public overview URL:** https://jobs.usamif.com/for-individuals
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/jobs
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** job-matches, saved-jobs, job-alerts
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Fjobs`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### For You Matches (`job-matches`)

- **Arabic name:** توصيات لك
- **English description:** Jobs ranked against your profile, with the reasons behind each match.
- **Arabic description:** وظائف مرتّبة حسب ملفك مع أسباب كل مطابقة.
- **Audience:** Individuals / job seekers
- **Navigation category:** discover
- **Public overview URL:** https://jobs.usamif.com/for-individuals
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/recommendations
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** job-search, talent-score
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Frecommendations`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Saved Jobs (`saved-jobs`)

- **Arabic name:** الوظائف المحفوظة
- **English description:** Everything you bookmarked, in one place.
- **Arabic description:** كل ما حفظته في مكان واحد.
- **Audience:** Individuals / job seekers
- **Navigation category:** discover
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/saved
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** job-search, applications
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Fsaved`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Job Alerts (`job-alerts`)

- **Arabic name:** تنبيهات الوظائف
- **English description:** Get notified the moment a matching verified role is posted.
- **Arabic description:** احصل على تنبيه فور نشر وظيفة موثقة مطابقة.
- **Audience:** Individuals / job seekers
- **Navigation category:** discover
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/alerts
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** job-search, job-matches
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Falerts`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Applications (`applications`)

- **Arabic name:** طلباتي
- **English description:** Track the status of every job you've applied to.
- **Arabic description:** تابع حالة كل طلب تقدّمت له.
- **Audience:** Individuals / job seekers
- **Navigation category:** discover
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/applications
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** job-search, saved-jobs
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Fapplications`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Companies (`companies`)

- **Arabic name:** الشركات
- **English description:** Browse employers hiring now, with real open-role counts.
- **Arabic description:** تصفّح الشركات التي توظّف الآن مع عدد وظائفها الحقيقي.
- **Audience:** Individuals / job seekers
- **Navigation category:** discover
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/companies
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** job-search
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Fcompanies`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Resume Builder (`resume-builder`)

- **Arabic name:** منشئ السيرة الذاتية
- **English description:** Build and export an ATS-ready CV that passes applicant tracking systems.
- **Arabic description:** أنشئ وصدّر سيرة ذاتية متوافقة مع أنظمة تتبّع المتقدمين.
- **Audience:** Individuals / job seekers
- **Navigation category:** career-tools
- **Public overview URL:** https://jobs.usamif.com/for-individuals
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/resume
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** cover-letters, talent-score, rashid-coach
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Fresume`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Cover Letters (`cover-letters`)

- **Arabic name:** خطابات التغطية
- **English description:** Generate cover letters tailored to a specific job.
- **Arabic description:** أنشئ رسائل تقديم مخصصة لوظيفة معينة.
- **Audience:** Individuals / job seekers
- **Navigation category:** career-tools
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/cover-letters
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** resume-builder, job-search
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Fcover-letters`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Talent Score (`talent-score`)

- **Arabic name:** نقاط الموهبة
- **English description:** Measure your employability and see exactly how to grow it.
- **Arabic description:** قِس جاهزيتك المهنية واعرف كيف تطوّرها بالضبط.
- **Audience:** Individuals / job seekers
- **Navigation category:** career-tools
- **Public overview URL:** https://jobs.usamif.com/for-individuals
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/talent-score
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** career-graph, job-matches, assessments
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Ftalent-score`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Career Graph (`career-graph`)

- **Arabic name:** خريطة المسار المهني
- **English description:** See your skills, gaps, and the growth paths available to you.
- **Arabic description:** اطّلع على مهاراتك وفجواتك ومسارات نمو متاحة لك.
- **Audience:** Individuals / job seekers
- **Navigation category:** career-tools
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/career-graph
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** talent-score, skills-explorer
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Fcareer-graph`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Skills Explorer (`skills-explorer`)

- **Arabic name:** مستكشف المهارات
- **English description:** Browse the platform's full skills taxonomy and how skills relate.
- **Arabic description:** تصفّح تصنيف المهارات الكامل وعلاقتها ببعضها.
- **Audience:** Individuals / job seekers
- **Navigation category:** career-tools
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/skills
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** career-graph
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Fskills`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Rasheed — AI Career Coach (`rashid-coach`)

- **Arabic name:** رشيد — المساعد المهني الذكي
- **English description:** Chat 24/7 for CV feedback, job matches, cover letters, and interview prep — grounded in your real profile.
- **Arabic description:** دردش على مدار الساعة لمراجعة سيرتك ووظائف مطابقة ورسائل تقديم وتحضير للمقابلات.
- **Audience:** Individuals / job seekers
- **Navigation category:** ai-coaching
- **Public overview URL:** https://jobs.usamif.com/for-individuals
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/rashid
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** resume-builder, interview-practice, cover-letters
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Frashid`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Interview Practice (`interview-practice`)

- **Arabic name:** تدريب المقابلات
- **English description:** Rehearse real questions with an AI voice coach and get feedback.
- **Arabic description:** تدرّب على أسئلة حقيقية مع مدرب صوتي ذكي واحصل على ملاحظات.
- **Audience:** Individuals / job seekers
- **Navigation category:** ai-coaching
- **Public overview URL:** https://jobs.usamif.com/for-individuals
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/interviews
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** rashid-coach, coding-practice
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Finterviews`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Coding Practice (`coding-practice`)

- **Arabic name:** تدريب على البرمجة
- **English description:** AI-evaluated coding interview practice with real code execution.
- **Arabic description:** تدرّب على مقابلات البرمجة بتنفيذ وتقييم فعلي للكود بالذكاء الاصطناعي.
- **Audience:** Individuals / job seekers
- **Navigation category:** ai-coaching
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/coding-practice
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** interview-practice
- **Limitation / note:** Not in main navigation (migrating toward USAM Education) but the route is live.
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Fcoding-practice`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Assessments (`assessments`)

- **Arabic name:** التقييمات
- **English description:** Prove your skills with timed, scored assessments and badges.
- **Arabic description:** أثبت مهاراتك بتقييمات مُقيَّمة ومحدودة بوقت وشارات.
- **Audience:** Individuals / job seekers
- **Navigation category:** ai-coaching
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/assessments
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** talent-score
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Fassessments`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Salary Insights (`salary-insights`)

- **Arabic name:** رؤى الرواتب
- **English description:** Benchmark your market value before you apply or negotiate.
- **Arabic description:** قارن قيمتك السوقية قبل التقديم أو التفاوض.
- **Audience:** Individuals / job seekers
- **Navigation category:** insights
- **Public overview URL:** https://jobs.usamif.com/for-individuals
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/salary
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** job-search, talent-score
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Fsalary`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Profile (`profile`)

- **Arabic name:** الملف الشخصي
- **English description:** Your personal profile — the source of truth for matches and Talent Score.
- **Arabic description:** ملفك الشخصي — المصدر الأساسي للتوصيات ونقاط الموهبة.
- **Audience:** Individuals / job seekers
- **Navigation category:** account
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/profile
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** talent-score, resume-builder
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Fprofile`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Notifications (`notifications`)

- **Arabic name:** الإشعارات
- **English description:** All your platform notifications in one place.
- **Arabic description:** كل إشعاراتك في مكان واحد.
- **Audience:** Everyone (any signed-in account)
- **Navigation category:** account
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/notifications
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** none
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Fnotifications`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Settings (`settings`)

- **Arabic name:** الإعدادات
- **English description:** Manage your account, notification preferences, and privacy.
- **Arabic description:** تحكّم في حسابك وتفضيلات الإشعارات والخصوصية.
- **Audience:** Everyone (any signed-in account)
- **Navigation category:** account
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/settings
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** none
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Fsettings`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Billing & Plans (`billing`)

- **Arabic name:** الفوترة والباقات
- **English description:** Manage your subscription and view transaction history.
- **Arabic description:** تحكّم في اشتراكك واطّلع على سجل العمليات المالية.
- **Audience:** Everyone (any signed-in account)
- **Navigation category:** account
- **Public overview URL:** https://jobs.usamif.com/pricing
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/billing
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** none
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Fbilling`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Become an Employer (`employer-onboarding`)

- **Arabic name:** سجّل كصاحب عمل
- **English description:** Create and verify your company account to start hiring.
- **Arabic description:** أنشئ ووثّق حساب شركتك لتبدأ التوظيف.
- **Audience:** Employers / companies
- **Navigation category:** hiring
- **Public overview URL:** https://jobs.usamif.com/for-businesses
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/employer/register
- **Access requirement:** Requires sign-in (any account type)
- **Availability status:** live
- **Related features:** post-job
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Femployer%2Fregister`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Employer Dashboard (`employer-dashboard`)

- **Arabic name:** لوحة تحكم صاحب العمل
- **English description:** Your hiring control center — job postings, applicants, and stats.
- **Arabic description:** مركز تحكّم التوظيف — الوظائف المنشورة والمتقدمون والإحصائيات.
- **Audience:** Employers / companies
- **Navigation category:** hiring
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/employer/dashboard
- **Access requirement:** Requires sign-in with an Employer (or Admin) account
- **Availability status:** live
- **Related features:** none
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Femployer%2Fdashboard`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Post a Job (`post-job`)

- **Arabic name:** انشر وظيفة
- **English description:** Publish a domain-verified role with screening questions.
- **Arabic description:** انشر وظيفة موثقة بالنطاق مع أسئلة فرز.
- **Audience:** Employers / companies
- **Navigation category:** hiring
- **Public overview URL:** https://jobs.usamif.com/for-businesses
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/employer/post-job
- **Access requirement:** Requires sign-in with an Employer (or Admin) account
- **Availability status:** live
- **Related features:** employer-dashboard, applicants
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Femployer%2Fpost-job`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Applicants (`applicants`)

- **Arabic name:** المتقدمون
- **English description:** Review and manage applicants across all your job postings.
- **Arabic description:** راجع وأدِر المتقدمين على كل وظائفك المنشورة.
- **Audience:** Employers / companies
- **Navigation category:** hiring
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/employer/applicants
- **Access requirement:** Requires sign-in with an Employer (or Admin) account
- **Availability status:** live
- **Related features:** post-job, talent-search
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Femployer%2Fapplicants`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Search Talent (`talent-search`)

- **Arabic name:** البحث عن مواهب
- **English description:** Browse and rank the candidate pool by skill, experience, and fit.
- **Arabic description:** تصفّح ورتّب قاعدة المرشحين بالمهارة والخبرة والملاءمة.
- **Audience:** Employers / companies
- **Navigation category:** hiring
- **Public overview URL:** https://jobs.usamif.com/for-businesses
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/employer/talent-search
- **Access requirement:** Requires sign-in with an Employer (or Admin) account
- **Availability status:** live
- **Related features:** talent-pools, applicants
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Femployer%2Ftalent-search`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Talent Pools (`talent-pools`)

- **Arabic name:** قوائم المواهب
- **English description:** Build and reuse candidate pools across all your open roles.
- **Arabic description:** أنشئ وأعد استخدام قوائم مرشحين عبر كل وظائفك المفتوحة.
- **Audience:** Employers / companies
- **Navigation category:** hiring
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/employer/talent-pools
- **Access requirement:** Requires sign-in with an Employer (or Admin) account
- **Availability status:** live
- **Related features:** talent-search
- **Limitation / note:** Requires the talent_pool entitlement; renders a locked state otherwise.
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Femployer%2Ftalent-pools`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Hiring Analytics (`employer-analytics`)

- **Arabic name:** تحليلات التوظيف
- **English description:** Real metrics on views, applications, and conversion for your roles.
- **Arabic description:** مقاييس حقيقية للمشاهدات والطلبات ومعدل التحويل لوظائفك.
- **Audience:** Employers / companies
- **Navigation category:** hiring
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/employer/analytics
- **Access requirement:** Requires sign-in with an Employer (or Admin) account
- **Availability status:** live
- **Related features:** none
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Femployer%2Fanalytics`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Company Profile (`company-profile-settings`)

- **Arabic name:** ملف الشركة
- **English description:** Manage your company's public profile and branding.
- **Arabic description:** أدِر الملف العام لشركتك وهويتها البصرية.
- **Audience:** Employers / companies
- **Navigation category:** hiring
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/employer/company
- **Access requirement:** Requires sign-in with an Employer (or Admin) account
- **Availability status:** live
- **Related features:** none
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Femployer%2Fcompany`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Team (`employer-team`)

- **Arabic name:** الفريق
- **English description:** Invite and manage your company's hiring team members.
- **Arabic description:** ادعُ وأدِر أعضاء فريق التوظيف في شركتك.
- **Audience:** Employers / companies
- **Navigation category:** hiring
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/employer/team
- **Access requirement:** Requires sign-in with an Employer (or Admin) account
- **Availability status:** live
- **Related features:** none
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Femployer%2Fteam`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Employer Billing & Plans (`employer-billing`)

- **Arabic name:** فوترة وباقات أصحاب العمل
- **English description:** Manage your company's subscription and hiring plan.
- **Arabic description:** أدِر اشتراك شركتك وباقة التوظيف.
- **Audience:** Employers / companies
- **Navigation category:** hiring
- **Public overview URL:** https://jobs.usamif.com/pricing
- **Direct application / deep-link URL:** https://jobs.usamif.com/app/employer/billing
- **Access requirement:** Requires sign-in with an Employer (or Admin) account
- **Availability status:** live
- **Related features:** none
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fapp%2Femployer%2Fbilling`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Admin Console (`admin-console`)

- **Arabic name:** لوحة الإدارة
- **English description:** Platform-wide operations: users, companies, jobs, verification, AI, analytics.
- **Arabic description:** عمليات شاملة للمنصة: المستخدمون والشركات والوظائف والتحقق والذكاء الاصطناعي والتحليلات.
- **Audience:** Platform administrators
- **Navigation category:** platform
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/admin
- **Access requirement:** Requires sign-in with an Admin account
- **Availability status:** live
- **Related features:** admin-finance
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fadmin`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### Financial Control Center (`admin-finance`)

- **Arabic name:** مركز التحكّم المالي
- **English description:** Revenue, transactions, and reconciliation exceptions from the real ledger.
- **Arabic description:** الإيرادات والمعاملات وحالات التسوية من السجل المالي الحقيقي.
- **Audience:** Platform administrators
- **Navigation category:** platform
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/admin/finance
- **Access requirement:** Requires sign-in with an Admin account
- **Availability status:** live
- **Related features:** admin-console
- **How Master should link to this:** Link to `https://jobs.usamif.com/login?next=%2Fadmin%2Ffinance`. There is no shared sign-in between USAM Master and this platform today — the visitor authenticates on THIS platform's /login, which then redirects to the real destination. The `next` value is validated server-side (internal relative paths only; absolute/external URLs are rejected) to prevent open-redirect abuse.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

### API Documentation (`api-docs`)

- **Arabic name:** وثائق الواجهة البرمجية
- **English description:** Interactive OpenAPI 3.0 reference for the USAM Careers API.
- **Arabic description:** مرجع تفاعلي بمعيار OpenAPI 3.0 لواجهة USAM البرمجية.
- **Audience:** Everyone (any signed-in account)
- **Navigation category:** platform
- **Public overview URL:** _(none — no dedicated explainer page; see /features)_
- **Direct application / deep-link URL:** https://jobs.usamif.com/api-docs
- **Access requirement:** None — publicly accessible
- **Availability status:** live
- **Related features:** none
- **How Master should link to this:** Link directly — no authentication required.
- **Verification status:** code-verified (route + page component read during audit); not a live/browser check.

