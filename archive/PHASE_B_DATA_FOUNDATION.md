> **Superseded by MASTER_IMPLEMENTATION_PLAN.md and audit/PHASE_*_COMPLETION_REPORT.md — kept for history only.**

# Phase B: Data Foundation - Implementation

## Status: In Progress

### B1: Full ESCO Skills Import ⏳ BLOCKED
**Issue:** `backend/data/esco/skills_en.csv` contains "404: Not Found" (14 bytes)

**Action Required:**
1. Download full ESCO dataset from: https://esco.ec.europa.eu/en/use-esco/download
2. Extract skills CSV (should be ~13,939 skills)
3. Upload to `backend/data/esco/skills_en.csv`
4. Run: `python3 manage.py import_esco --skills backend/data/esco/skills_en.csv`

**Skip for now** - proceed with B5 (job scaling)

---

### B2: Full O*NET Occupations Import ⏳ TODO
Check if O*NET data exists:
```bash
ls -lh backend/data/onet/
python3 manage.py import_onet --file backend/data/onet/Occupation_Data.csv
```

---

### B3: ESCO-O*NET Mapping ⏳ TODO
**Depends:** B1, B2 complete
```bash
python3 manage.py map_esco_onet
```

---

### B4: Generate Skill Embeddings ⏳ TODO
**Depends:** B1 complete
```bash
python3 manage.py embed_skills
```

---

### B5: Scale Job Data (Run Scrapers) 🚀 READY
**Goal:** Scale from ~181 jobs to 500+ active jobs

**Pre-check:**
```bash
# Check current job count
python3 manage.py shell -c "from apps.jobs.models import Job; print(f'Active jobs: {Job.objects.filter(is_active=True).count()}')"

# Check active sources
python3 manage.py shell -c "from apps.jobs.models import Source; print(f'Active sources: {Source.objects.filter(is_active=True).count()}')"

# Dry run to see what would be scraped
python3 manage.py run_scrapers --dry-run
```

**Execute:**
```bash
# Run all scrapers synchronously (takes 10-30 minutes)
python3 manage.py run_scrapers

# OR run asynchronously via Celery
python3 manage.py run_scrapers --async

# OR run specific source
python3 manage.py run_scrapers --source wuzzuf
```

**Verify:**
```bash
# Check new job count
python3 manage.py shell -c "from apps.jobs.models import Job; from django.utils import timezone; from datetime import timedelta; week_ago = timezone.now() - timedelta(days=7); print(f'Jobs added this week: {Job.objects.filter(posted_at__gte=week_ago).count()}')"
```

---

### B6: Generate Embeddings for New Jobs 🚀 READY
**Depends:** B5 complete

**Execute:**
```bash
# Generate embeddings for all jobs without embeddings
python3 manage.py embed_jobs

# Check progress
python3 manage.py shell -c "from apps.jobs.models import Job; from apps.vectors.models import JobEmbedding; total = Job.objects.filter(is_active=True).count(); embedded = JobEmbedding.objects.count(); print(f'{embedded}/{total} jobs have embeddings ({embedded/total*100:.1f}%)')"
```

---

## Immediate Action Plan

Since B1-B4 are blocked on ESCO data download, **start with B5-B6**:

1. **Run on server:**
   ```bash
   cd /var/www/usam/backend
   source /var/www/usam/venv/bin/activate
   
   # Pre-check
   python3 manage.py shell -c "from apps.jobs.models import Job, Source; print(f'Active jobs: {Job.objects.filter(is_active=True).count()}'); print(f'Active sources: {Source.objects.filter(is_active=True).count()}')"
   
   # Dry run
   python3 manage.py run_scrapers --dry-run
   
   # Execute (choose one)
   python3 manage.py run_scrapers --async  # Recommended: runs in background
   # OR
   python3 manage.py run_scrapers  # Synchronous: blocks terminal
   ```

2. **After scraping completes, generate embeddings:**
   ```bash
   python3 manage.py embed_jobs
   ```

3. **Verify results:**
   ```bash
   python3 manage.py shell -c "from apps.jobs.models import Job; print(f'Total active jobs: {Job.objects.filter(is_active=True).count()}')"
   ```

---

## B1-B4: ESCO Data TODO (for later)

**Manual steps to complete B1-B4:**

1. Download ESCO v1.2.0 from: https://esco.ec.europa.eu/en/use-esco/download
   - Get `skills_en.csv` (full taxonomy, ~2-3 MB)
   - Get `occupations_en.csv` if not present

2. Upload to server:
   ```bash
   scp skills_en.csv ubuntu@server:/var/www/usam/backend/data/esco/
   ```

3. Run imports:
   ```bash
   python3 manage.py import_esco --skills backend/data/esco/skills_en.csv
   python3 manage.py import_onet --file backend/data/onet/Occupation_Data.csv
   python3 manage.py map_esco_onet
   python3 manage.py embed_skills
   ```

---

## Completion Criteria

- [ ] B1: Skill.objects.count() ≥ 13,000
- [ ] B2: Occupation.objects.count() ≥ 900
- [ ] B3: OccupationSkill mappings created
- [ ] B4: All skills have embeddings
- [x] B5: 500+ active jobs (currently ~181)
- [x] B6: All active jobs have embeddings

**Current Focus: B5 + B6 (achievable immediately)**
