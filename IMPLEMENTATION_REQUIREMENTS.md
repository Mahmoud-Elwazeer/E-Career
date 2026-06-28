# Implementation Requirements Checklist

## Critical Information Needed Before Implementation

Please provide the following information to complete the implementation plan:

### 1. AWS Bedrock Configuration
- [x] AWS Access Key ID: `AKIAYKFQRAGEN2ZKTGPY`
- [x] AWS Secret Access Key: `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`
- [x] AWS Region: `us-east-1`
- [x] Preferred Bedrock Model ID: `anthropic.claude-sonnet-4-20250514-v1:0`

### 2. Google Workspace Email Accounts
How many email accounts will be used for rotation?
- [x] Account 1: career@usamif.com (credentials from Google OAuth client provided)
- [ ] Account 2: email, app password (add more if needed)
- [ ] Account 3: email, app password (add more if needed)

**Google OAuth Credentials Provided:**
- Client ID: `521069775102-te0aomp91utnaroeeprlir9ej2p21dht.apps.googleusercontent.com`
- Client Secret: `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`
- Project ID: `original-frame-480216-r7`

Daily send limit per account: **500** (default)

### 3. edu.usamif.com Course Platform Integration
**Critical for Rashid course recommendations**

- [x] Platform URL: `https://edu.usamif.com`
- [x] Integration Method: **Web Scraping** (Option B)
- [x] Permission: Assumed (owned by same organization)
- [ ] Course listing page URL: _Need to verify actual URL structure_(just mention the link of the website not coures , mention the feild maybe and he will navgate to the website and explore  )
- [ ] Course detail page structure: _Need to analyze_

**Note:** Will use BeautifulSoup to scrape course catalog during implementation

### 4. Database Configuration
**Production Database**
- [x] PostgreSQL host: `localhost` (development) / TBD (production)
- [x] PostgreSQL port: `5432`
- [x] Database name: `ecareer_dev` (development) / `ecareer_prod` (production)
- [x] Username: `postgres` (development) / TBD (production)
- [x] Password: _Set during development setup_

**Redis Configuration**
- [x] Redis host: `localhost` (development) / TBD (production)
- [x] Redis port: `6379`
- [x] Redis password: None (development) / TBD (production)

### 5. Domain and SSL
- [x] Production domain: `jobs.usamif.com`
- [x] SSL certificate provider: **Let's Encrypt** (recommended, free)
- [x] Email tracking subdomain: `jobs.usamif.com` (same domain, different endpoint)

### 6. Third-Party Services (Optional but Recommended)

**Company Logo Service**
- [ ] Clearbit API key (free tier available) OR
- [ ] Alternative logo service

**Proxy Service** (for LinkedIn/Indeed scraping)
- [ ] Proxy service provider
- [ ] Proxy credentials
- [ ] Number of proxies available

**Monitoring & Error Tracking**
- [ ] Sentry DSN (for error tracking)
- [ ] Monitoring service preference

### 7. Employer Verification Process
How should employers be verified?
- [ ] Automatic approval
- [ ] Manual admin review (recommended)
- [ ] Email domain verification
- [ ] Document upload verification

### 8. Rashid AI Configuration Preferences

**Dialect and Personality**
- [ ] Primary dialect: Egyptian Arabic (default)
- [ ] Formality level: Friendly and professional (default)
- [ ] Tone: Honest and supportive, not motivational (default)

**Token Limits**
- [ ] Daily token limit per user (default: 100,000)
- [ ] Max conversation length in messages (default: 50)
- [ ] Auto-delete conversations after days (default: 90)

**Onboarding Questions** (Rashid's first-time user flow)
Provide 5-7 questions Rashid should ask, for example:
1. "إيه مستواك الحالي في مجالك؟" (What's your current level?)
2. "إيه الوظيفة اللي نفسك توصلها؟" (What role do you want to reach?)
3. ... (add more)

### 9. Job Scraping Configuration

**Scraping Schedule**
- [ ] Full scrape interval: Every ___ hours (default: 6)
- [ ] URL verification interval: Every ___ hours (default: 24)
- [ ] Expire old jobs after: ___ days (default: 90)

**Job Quality Control**
- [ ] Minimum legitimacy score (0.0-1.0, default: 0.6)
- [ ] Require admin review for new jobs? (Yes/No, default: No)

### 10. Recommendation Engine Weights

**Job Match Scoring Weights** (must total 1.0)
- [ ] Title match: 0.25
- [ ] Skills match: 0.30
- [ ] Experience match: 0.15
- [ ] Location match: 0.10
- [ ] Employment type match: 0.08
- [ ] Remote preference match: 0.07
- [ ] Salary match: 0.05

### 11. Email Campaign Settings

**Weekly Digest**
- [ ] Send day: Monday (1=Monday, 7=Sunday)
- [ ] Send time: 9 AM (0-23)

**Re-engagement Email**
- [ ] Send after inactive days: 7

**Job Alert Settings**
- [ ] Max alerts per user per day: 5
- [ ] Minimum match score to trigger alert: 70

### 12. Frontend Configuration

**React App Environment**
- [ ] API base URL: http://localhost:8000/api/v1 (development)
- [ ] API base URL: https://jobs.usamif.com/api/v1 (production)
- [ ] WebSocket URL: ws://localhost:8000/ws/ (development)
- [ ] WebSocket URL: wss://jobs.usamif.com/ws/ (production)

---

## Repositories to Integrate - Confirmed

Based on analysis, the following repositories will be integrated:

1. ✅ **Feashliaa/job-board-aggregator**
   - Purpose: Core ATS scraping logic (Greenhouse, Lever, Ashby, etc.)
   - Integration: Port `scraper.py` to Django management command
   - License: MIT (compatible)

2. ✅ **outscal/OpenJobs** 
   - Purpose: Pre-built company list with 12,000+ companies
   - Integration: Import `companies_v2.json` into Company model
   - License: Open dataset

3. ✅ **JobSpy** (Python library)
   - Purpose: Regional job boards (Bayt, Wuzzuf, GulfTalent)
   - Integration: Install as dependency, wrap in Celery tasks
   - License: MIT

4. ❌ **Masterjx9/OpenPostings**
   - Purpose: 110,000+ companies (too large for MVP)
   - Status: Skip for now, can add later for scale

5. ⚠️ **career-ops Block G** (legitimacy checker)
   - Purpose: Detect scam jobs
   - Integration: Port Node.js logic to Python
   - Status: Custom implementation needed

---

## Next Steps

1. Fill in the checklist above
2. I will generate the complete implementation plan as a single markdown file
3. The plan will be structured for GLM execution with clear phases and tasks
4. Each phase will include specific code, migrations, and configurations

Please provide the information marked with [ ] checkboxes.
