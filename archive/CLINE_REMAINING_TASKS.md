> **Superseded by MASTER_IMPLEMENTATION_PLAN.md and audit/PHASE_*_COMPLETION_REPORT.md — kept for history only.**

# Remaining Tasks for Cline
## E-Career Platform - Complete Implementation Guide
## August 8, 2026

**Current Status: 95% Complete**  
**Remaining Work: ~20 hours**

---

## PHASE 1: Testing Coverage (High Priority - 6 hours)

### Current State
- Vitest configured and working
- Test setup complete (frontend/src/test/setup.ts)
- 1 example test passing
- Coverage: ~30%
- Target: 70% coverage

### Task 1.1: Backend API Tests (3 hours)

```prompt
In the E-Career Django project at backend/, create comprehensive API tests:

1. Install test dependencies:
   ```bash
   pip install pytest pytest-django pytest-cov factory-boy faker
   ```

2. Create backend/pytest.ini:
   ```ini
   [pytest]
   DJANGO_SETTINGS_MODULE = config.settings.development
   python_files = tests.py test_*.py *_tests.py
   addopts = --cov=apps --cov-report=html --cov-report=term-missing
   ```

3. Create test factories at backend/apps/conftest.py:
   ```python
   import pytest
   from django.contrib.auth import get_user_model
   from rest_framework.test import APIClient
   from factory.django import DjangoModelFactory
   import factory
   
   User = get_user_model()
   
   class UserFactory(DjangoModelFactory):
       class Meta:
           model = User
       
       email = factory.Sequence(lambda n: f'user{n}@test.com')
       username = factory.Sequence(lambda n: f'user{n}')
       is_active = True
   
   @pytest.fixture
   def api_client():
       return APIClient()
   
   @pytest.fixture
   def user(db):
       return UserFactory()
   
   @pytest.fixture
   def authenticated_client(api_client, user):
       api_client.force_authenticate(user=user)
       return api_client
   ```

4. Create backend/apps/jobs/tests/test_api.py:
   Test job listing, filtering, search, save, apply endpoints.
   Mock external services (Typesense, Qdrant).
   
5. Create backend/apps/accounts/tests/test_auth.py:
   Test registration, login, token refresh, password reset.
   
6. Create backend/apps/career/tests/test_api.py:
   Test career profile CRUD, talent scores, goals.
   
7. Create backend/apps/rashid/tests/test_api.py:
   Test conversation creation, message sending (mock Bedrock).
   
8. Create backend/apps/interviews/tests/test_api.py:
   Test interview session start, answer submission, results.

Run tests with:
```bash
cd backend
pytest --cov --cov-report=html
```

Target: 50+ tests, 60% coverage
```

### Task 1.2: Frontend Component Tests (2 hours)

```prompt
In the E-Career React frontend at frontend/, create component tests:

1. Tests already configured with Vitest + Testing Library.

2. Create frontend/src/pages/__tests__/Jobs.test.tsx:
   ```typescript
   import { describe, it, expect, vi } from 'vitest';
   import { render, screen, waitFor } from '@testing-library/react';
   import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
   import { BrowserRouter } from 'react-router-dom';
   import Jobs from '../Jobs';
   
   const queryClient = new QueryClient({
     defaultOptions: { queries: { retry: false } }
   });
   
   const wrapper = ({ children }: { children: React.ReactNode }) => (
     <QueryClientProvider client={queryClient}>
       <BrowserRouter>
         {children}
       </BrowserRouter>
     </QueryClientProvider>
   );
   
   describe('Jobs Page', () => {
     it('renders job listing', async () => {
       render(<Jobs />, { wrapper });
       expect(screen.getByText(/jobs/i)).toBeInTheDocument();
     });
     
     it('displays loading state', () => {
       render(<Jobs />, { wrapper });
       expect(screen.getByText(/loading/i)).toBeInTheDocument();
     });
   });
   ```

3. Create frontend/src/pages/__tests__/Login.test.tsx:
   Test login form rendering, validation, submission.

4. Create frontend/src/hooks/__tests__/use-auth.test.tsx:
   Test useAuth hook: login, logout, token management.

5. Create frontend/src/components/__tests__/RashidWidget.test.tsx:
   Test Rashid widget rendering, opening, closing.

6. Create frontend/src/components/ui/__tests__/Button.test.tsx:
   Test button component variants, click handlers.

Run tests with:
```bash
cd frontend
npm test -- --coverage
```

Target: 30+ component/hook tests
```

### Task 1.3: Integration Tests (1 hour)

```prompt
In the E-Career project, create end-to-end integration tests:

1. Create backend/apps/tests/test_integration.py:
   ```python
   import pytest
   from rest_framework.test import APIClient
   
   @pytest.mark.django_db
   class TestJobSearchFlow:
       def test_complete_job_search_flow(self):
           # User registers
           # User logs in
           # User searches for jobs
           # User saves a job
           # User applies to job
           # Assert each step works
           pass
   
   @pytest.mark.django_db
   class TestRashidFlow:
       def test_rashid_conversation_flow(self):
           # User logs in
           # Creates conversation
           # Sends message (mock Bedrock)
           # Receives response
           pass
   ```

2. Create frontend/src/__tests__/integration/job-flow.test.tsx:
   Test complete user flow from login to job application.

Run with:
```bash
cd backend && pytest -m integration
cd frontend && npm test -- integration
```

Target: 10 integration tests covering critical paths
```

---

## PHASE 2: Import ESCO Data (Medium Priority - 1.5 hours)

### Current State
- Import commands exist and work
- ESCO models created
- Mapping logic implemented
- Data files not downloaded

### Task 2.1: Download ESCO Dataset

```prompt
Download the ESCO skills taxonomy dataset:

1. Go to: https://ec.europa.eu/esco/portal/download

2. Download "ESCO dataset - CSV format" (latest version)
   Files needed:
   - skills_en.csv (13,939 skills)
   - occupations_en.csv
   
3. Or download from ESCO API:
   ```bash
   curl -o esco_skills.csv "https://ec.europa.eu/esco/api/resource/taxonomy?uri=http://data.europa.eu/esco/skill"
   ```

4. Place files in: backend/data/esco/

5. For O*NET data:
   - Go to: https://www.onetcenter.org/database.html
   - Download "Occupation Data" CSV
   - Download "Skills" CSV
   - Place in: backend/data/onet/

Verify files exist:
```bash
ls -lh backend/data/esco/
ls -lh backend/data/onet/
```
```

### Task 2.2: Run Import Commands

```prompt
On the production server at /var/www/usam/backend, import ESCO and O*NET data:

1. Upload data files to server:
   ```bash
   scp backend/data/esco/*.csv ubuntu@13.49.245.174:/var/www/usam/backend/data/esco/
   scp backend/data/onet/*.csv ubuntu@13.49.245.174:/var/www/usam/backend/data/onet/
   ```

2. SSH to server and run imports:
   ```bash
   cd /var/www/usam/backend
   source ../venv/bin/activate
   
   # Import ESCO skills (13,939 skills)
   python3 manage.py import_esco --file data/esco/skills_en.csv
   
   # Import O*NET occupations (3,039)
   python3 manage.py import_onet \
     --file data/onet/Occupation_Data.csv \
     --skills-file data/onet/Skills.csv
   
   # Map ESCO to O*NET
   python3 manage.py map_esco_onet --threshold 0.8
   
   # Generate Arabic translations for top 500 skills
   python3 manage.py generate_arabic_translations --limit 500
   
   # Set up Apache AGE graph extension (optional)
   python3 manage.py setup_age_graph
   ```

3. Verify import:
   ```bash
   python3 manage.py shell
   >>> from apps.skills.models import Skill
   >>> Skill.objects.count()  # Should be ~13,939
   >>> Skill.objects.filter(esco_uri__isnull=False).count()
   ```

Expected output:
- 13,939 ESCO skills imported
- 3,039 O*NET occupations imported
- ~8,000 ESCO-O*NET mappings created
- 500 Arabic translations generated
```

---

## PHASE 3: Generate Embeddings (Medium Priority - 2 hours)

### Current State
- Embedding commands exist
- Qdrant/Cohere configured
- AWS credentials working
- No embeddings generated yet

### Task 3.1: Generate Job Embeddings

```prompt
On the production server, generate embeddings for all 221 jobs:

1. SSH to server:
   ```bash
   ssh ubuntu@13.49.245.174
   cd /var/www/usam/backend
   source ../venv/bin/activate
   ```

2. Set up Qdrant collections:
   ```bash
   python3 manage.py setup_vector_collections
   ```

3. Generate job embeddings in batches:
   ```bash
   # Start with small batch to test
   python3 manage.py embed_jobs --limit 10 --batch-size 5
   
   # If successful, embed all jobs
   python3 manage.py embed_jobs --batch-size 50
   
   # Monitor progress (takes ~5-10 minutes for 221 jobs)
   ```

4. Verify embeddings:
   ```bash
   python3 manage.py shell
   >>> from apps.vectors.service import get_vector_service
   >>> service = get_vector_service()
   >>> stats = service.get_collection_stats('jobs')
   >>> print(f"Total vectors: {stats['vectors_count']}")  # Should be 221
   ```

5. Test semantic search:
   ```bash
   curl "http://localhost:8000/api/v1/vectors/search/semantic/?q=Python+developer+remote&limit=5"
   ```

Expected:
- 221 job embeddings created
- Semantic search returns relevant results
- Vector collection has 221 vectors
```

### Task 3.2: Generate Skill Embeddings

```prompt
Generate embeddings for ESCO skills (after importing ESCO data):

1. Run skill embeddings:
   ```bash
   cd /var/www/usam/backend
   source ../venv/bin/activate
   
   # Embed top 1000 skills first
   python3 manage.py embed_skills --limit 1000 --batch-size 100
   
   # If successful and you have budget, embed all 13,939
   python3 manage.py embed_skills --batch-size 200
   ```

2. This enables:
   - Skill-based job matching
   - Skill similarity search
   - Better CV skill extraction

Note: Embedding 13,939 skills costs ~$0.03 via Bedrock Cohere.
Can be done incrementally (top 1000, top 5000, all).
```

---

## PHASE 4: Grafana Dashboards (Low Priority - 6 hours)

### Current State
- Prometheus metrics code exists
- No Grafana installed
- Logs work fine without dashboards

### Task 4.1: Install Grafana

```prompt
Install Grafana on the production server:

1. SSH to server and install:
   ```bash
   sudo apt-get install -y software-properties-common
   sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
   wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
   sudo apt-get update
   sudo apt-get install grafana
   
   # Start Grafana
   sudo systemctl start grafana-server
   sudo systemctl enable grafana-server
   ```

2. Install Prometheus:
   ```bash
   cd /tmp
   wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
   tar xvfz prometheus-*.tar.gz
   sudo mv prometheus-* /opt/prometheus
   ```

3. Configure Prometheus to scrape Django:
   Create /opt/prometheus/prometheus.yml:
   ```yaml
   global:
     scrape_interval: 15s
   
   scrape_configs:
     - job_name: 'django'
       static_configs:
         - targets: ['localhost:8000']
   ```

4. Start Prometheus:
   ```bash
   cd /opt/prometheus
   ./prometheus --config.file=prometheus.yml &
   ```

5. Access Grafana:
   - URL: http://13.49.245.174:3000
   - Default login: admin/admin
```

### Task 4.2: Create Dashboards

```prompt
Create Grafana dashboards for E-Career monitoring:

1. Log into Grafana (http://SERVER_IP:3000)

2. Add Prometheus data source:
   - Configuration → Data Sources → Add Prometheus
   - URL: http://localhost:9090

3. Import dashboard template:
   - Create → Import
   - Use Grafana ID: 3681 (Django Prometheus dashboard)

4. Create custom E-Career dashboard with panels:
   
   **Panel 1: HTTP Request Rate**
   ```promql
   rate(http_requests_total[5m])
   ```
   
   **Panel 2: API Response Time**
   ```promql
   histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
   ```
   
   **Panel 3: Active Jobs**
   ```python
   # Add to backend/apps/monitoring/metrics.py:
   from prometheus_client import Gauge
   
   active_jobs_gauge = Gauge('ecareer_active_jobs', 'Number of active jobs')
   
   # Update in a periodic task:
   from apps.jobs.models import Job
   active_jobs_gauge.set(Job.objects.filter(status='active').count())
   ```
   
   **Panel 4: Celery Task Success Rate**
   ```promql
   rate(celery_task_success_total[5m]) / rate(celery_task_total[5m])
   ```
   
   **Panel 5: AI Request Cost**
   ```promql
   sum(rate(ai_request_cost_usd[1h]))
   ```

5. Set up alerts:
   - HTTP error rate > 5%
   - Response time > 2s
   - Celery queue length > 100
   - AI costs > $10/hour

Save dashboard as "E-Career Platform Overview"
```

---

## PHASE 5: CI/CD Pipeline (Low Priority - 4 hours)

### Current State
- Manual deployment (git pull + restart)
- No automated testing on push
- No deployment automation

### Task 5.1: GitHub Actions Workflow

```prompt
Create CI/CD pipeline at .github/workflows/deploy.yml:

```yaml
name: Deploy to Production

on:
  push:
    branches: [development]
  workflow_dispatch:

jobs:
  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements/base.txt
          pip install pytest pytest-django pytest-cov
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        run: |
          cd backend
          pytest --cov --cov-fail-under=50
  
  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run tests
        run: |
          cd frontend
          npm test -- --run
      
      - name: Build
        run: |
          cd frontend
          npm run build
  
  deploy:
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/development'
    
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /var/www/usam
            git pull origin development
            
            # Backend
            cd backend
            source ../venv/bin/activate
            pip install -r requirements/production.txt
            python3 manage.py migrate --noinput
            python3 manage.py collectstatic --noinput
            deactivate
            
            # Frontend
            cd ../frontend
            npm install
            npm run build
            
            # Restart services
            sudo systemctl restart usam.service celery-usam.service celery-beat-usam.service
```

Add GitHub secrets:
- SERVER_HOST: 13.49.245.174
- SERVER_USER: ubuntu
- SSH_PRIVATE_KEY: (your SSH private key)

This will:
1. Run tests on every push to development
2. Build frontend
3. Deploy to production if tests pass
4. Restart services automatically
```

---

## PHASE 6: Additional Scrapers (Optional - 10 hours)

### Current State
- Scraper orchestrator exists
- Base scraper pattern established
- Only seed data, no real ATS scrapers

### Task 6.1: SmartRecruiters Scraper

```prompt
Create backend/apps/scraper/scrapers/smartrecruiters.py:

```python
"""
SmartRecruiters ATS Scraper

Company URL pattern: https://careers.smartrecruiters.com/{company_name}
API: https://api.smartrecruiters.com/v1/companies/{id}/postings
"""

import requests
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SmartRecruitersScraper:
    """Scraper for SmartRecruiters ATS platform."""
    
    BASE_API = "https://api.smartrecruiters.com/v1"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'USAM-Career-Compass/1.0',
            'Accept': 'application/json',
        })
    
    def scrape_company(self, company_id: str, company_name: str) -> List[Dict[str, Any]]:
        """
        Scrape all jobs from a SmartRecruiters company page.
        
        Args:
            company_id: SmartRecruiters company ID
            company_name: Company name for metadata
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        offset = 0
        limit = 50
        
        while True:
            url = f"{self.BASE_API}/companies/{company_id}/postings"
            params = {
                'offset': offset,
                'limit': limit,
            }
            
            try:
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                postings = data.get('content', [])
                if not postings:
                    break
                
                for posting in postings:
                    job = self.parse_job(posting, company_name)
                    if job:
                        jobs.append(job)
                
                # Check if there are more pages
                if len(postings) < limit:
                    break
                
                offset += limit
                
            except Exception as e:
                logger.error(f"SmartRecruiters scraping failed for {company_name}: {e}")
                break
        
        logger.info(f"Scraped {len(jobs)} jobs from SmartRecruiters: {company_name}")
        return jobs
    
    def parse_job(self, posting: Dict, company_name: str) -> Dict[str, Any]:
        """Parse a SmartRecruiters posting into our job format."""
        
        return {
            'title': posting.get('name'),
            'company_name': company_name,
            'location': self.parse_location(posting.get('location', {})),
            'description': posting.get('jobAd', {}).get('sections', {}).get('companyDescription', {}).get('text', ''),
            'source_url': posting.get('ref'),
            'source_name': 'smartrecruiters',
            'external_id': posting.get('id'),
            'employment_type': posting.get('typeOfEmployment', {}).get('label'),
            'experience_level': posting.get('experienceLevel', {}).get('label'),
            'department': posting.get('department', {}).get('label'),
            'posted_at': self.parse_date(posting.get('releasedDate')),
        }
    
    def parse_location(self, location: Dict) -> str:
        """Parse location object into string."""
        parts = [
            location.get('city'),
            location.get('region'),
            location.get('country'),
        ]
        return ', '.join(p for p in parts if p)
    
    def parse_date(self, date_str: str) -> datetime:
        """Parse ISO date string."""
        if not date_str:
            return datetime.now()
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))


# Register scraper
SCRAPER_REGISTRY['smartrecruiters'] = SmartRecruitersScraper
```

Add to backend/apps/scraper/tasks.py:
```python
@shared_task
def scrape_smartrecruiters():
    """Scrape all SmartRecruiters companies."""
    from .scrapers.smartrecruiters import SmartRecruitersScraper
    
    scraper = SmartRecruitersScraper()
    
    # List of companies using SmartRecruiters (expand this list)
    companies = [
        ('COMPANY_ID_1', 'Company Name 1'),
        ('COMPANY_ID_2', 'Company Name 2'),
    ]
    
    total_jobs = 0
    for company_id, company_name in companies:
        jobs = scraper.scrape_company(company_id, company_name)
        # Save jobs to database
        total_jobs += len(jobs)
    
    return {'total_jobs': total_jobs}
```

Add to Celery Beat schedule in backend/config/celery.py:
```python
'scrape-smartrecruiters': {
    'task': 'apps.scraper.tasks.scrape_smartrecruiters',
    'schedule': crontab(hour='*/12', minute=0),  # Every 12 hours
},
```
```

### Task 6.2: Workable Scraper

```prompt
Create backend/apps/scraper/scrapers/workable.py:

Similar structure to SmartRecruiters scraper, but for Workable ATS:
- Base URL: https://apply.workable.com/{company}/j/{job_id}
- API: https://{company}.workable.com/spi/v3/jobs
- Parse job listings from Workable job boards
- Handle pagination and rate limiting
- Map Workable fields to our Job model

Follow the same pattern as SmartRecruiters scraper.
Register in SCRAPER_REGISTRY and add Celery task.
```

---

## EXECUTION ORDER

### Immediate (Do First):
1. ✅ **Phase 1: Testing** - Increases confidence, enables CI/CD
2. ✅ **Phase 2: Import ESCO** - Enables full skills taxonomy
3. ✅ **Phase 3: Generate Embeddings** - Enables semantic search

### Soon (Nice to Have):
4. ⏸️ **Phase 4: Grafana** - Better monitoring (logs work fine without it)
5. ⏸️ **Phase 5: CI/CD** - Automated deployment (manual works fine)

### Later (Optional):
6. ⏸️ **Phase 6: More Scrapers** - More jobs (221 is good for MVP)

---

## TIME ESTIMATES

| Phase | Effort | Priority |
|-------|--------|----------|
| 1: Testing | 6h | 🔴 High |
| 2: ESCO Import | 1.5h | 🟡 Medium |
| 3: Embeddings | 2h | 🟡 Medium |
| 4: Grafana | 6h | 🟢 Low |
| 5: CI/CD | 4h | 🟢 Low |
| 6: Scrapers | 10h | 🟢 Low |

**Total: 29.5 hours**
**High Priority: 9.5 hours**

---

## SUCCESS CRITERIA

After completing all phases, you will have:

✅ **70%+ test coverage** (backend + frontend)  
✅ **13,939 ESCO skills** imported and mapped  
✅ **221 job embeddings** for semantic search  
✅ **Grafana dashboards** for real-time monitoring  
✅ **CI/CD pipeline** for automated deployments  
✅ **Multiple ATS scrapers** for job sourcing  

---

## NOTES FOR CLINE

- Each task is self-contained with all commands needed
- No dependencies between phases (can be done in any order)
- All infrastructure already exists (just needs data/config)
- Testing (Phase 1) has the highest ROI
- ESCO import (Phase 2) is fastest to complete
- Scrapers (Phase 6) are most time-consuming

**Current platform status: 95% complete, production ready**

These are optional enhancements, not blockers for launch.
