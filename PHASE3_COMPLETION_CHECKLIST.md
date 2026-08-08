# Phase 3 Completion Checklist

## Pre-Flight Check ✈️

Before starting, verify:
- [ ] You have SSH access to `ubuntu@13.49.245.174`
- [ ] AWS credentials are configured on server (check from Step 2)
- [ ] Qdrant is running on server
- [ ] You have 15 minutes available

---

## Execution Steps

### ☐ Step 1: Connect to Server (30 seconds)
```bash
ssh ubuntu@13.49.245.174
```

**Verify:** Terminal shows `ubuntu@ip-172-31-XX-XX:~$`

---

### ☐ Step 2: Check Prerequisites (1 minute)

```bash
# Navigate to backend
cd /var/www/usam/backend
source ../venv/bin/activate

# Check AWS credentials
grep -E "AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|AWS_REGION" .env

# Check Qdrant
sudo systemctl status qdrant | head -3

# Check active jobs count
python3 manage.py shell -c "from apps.jobs.models import Job; print(f'Active jobs: {Job.objects.filter(status=\"active\").count()}')"
```

**Expected:**
- AWS credentials present (AWS_ACCESS_KEY_ID=AKIA...)
- Qdrant: active (running)
- Active jobs: 221

**If AWS credentials missing:**
```bash
echo "AWS_ACCESS_KEY_ID=AKIAYKFQRAGEN2ZKTGPY" >> .env
echo "AWS_SECRET_ACCESS_KEY=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" >> .env
echo "AWS_REGION=eu-north-1" >> .env
sudo systemctl restart gunicorn celery celerybeat
```

**If Qdrant not running:**
```bash
sudo systemctl start qdrant
sudo systemctl enable qdrant
```

---

### ☐ Step 3: Test Embeddings (1 minute)

```bash
python3 manage.py embed_jobs --limit 10 --batch-size 5
```

**Expected Output:**
```
Starting job embedding process...
Found 10 jobs to embed
Batch 1/2: Processing jobs 1-5...
  ✓ Job #1: Software Engineer at TechCorp
  ✓ Job #2: Backend Developer at StartupXYZ
  ✓ Job #3: Frontend Developer at WebCo
  ✓ Job #4: DevOps Engineer at CloudInc
  ✓ Job #5: Data Scientist at AILabs
Batch 2/2: Processing jobs 6-10...
  ✓ Job #6: Project Manager at ConsultCo
  ✓ Job #7: Product Manager at ProductCo
  ✓ Job #8: UX Designer at DesignStudio
  ✓ Job #9: QA Engineer at TestLab
  ✓ Job #10: Full Stack Developer at CodeShop

Summary:
✓ Successfully embedded: 10
✗ Failed: 0
⏱ Time taken: 45 seconds
```

**If you see errors:**
- Check error message carefully
- Most common: AWS credentials issue (see Step 2)
- Second most common: Qdrant not running (see Step 2)
- If other error, paste it and I'll help debug

---

### ☐ Step 4: Generate All Embeddings (10 minutes)

```bash
python3 manage.py embed_jobs --batch-size 50
```

**What to expect:**
- Process will take 8-10 minutes for 221 jobs
- You'll see progress for each batch
- Each batch takes ~2 minutes (50 jobs)
- Don't interrupt the process

**Expected Output:**
```
Starting job embedding process...
Found 221 jobs to embed

Batch 1/5: Processing jobs 1-50... ✓ (120 seconds)
Batch 2/5: Processing jobs 51-100... ✓ (118 seconds)
Batch 3/5: Processing jobs 101-150... ✓ (125 seconds)
Batch 4/5: Processing jobs 151-200... ✓ (122 seconds)
Batch 5/5: Processing jobs 201-221... ✓ (52 seconds)

Summary:
✓ Successfully embedded: 221
✗ Failed: 0
⏱ Total time: 537 seconds (8.9 minutes)

Qdrant collection updated:
  Collection: jobs
  Vectors: 221
  Dimension: 1024
```

**If process stops mid-way:**
- Don't worry! Already-embedded jobs won't be re-processed
- Just run the same command again: `python3 manage.py embed_jobs --batch-size 50`
- It will resume from where it stopped

**If you hit AWS rate limits:**
- Wait 1 minute
- Resume with smaller batches: `python3 manage.py embed_jobs --batch-size 20`

---

### ☐ Step 5: Verify Embeddings (30 seconds)

```bash
python3 manage.py shell
```

Then paste this:
```python
from apps.jobs.models import Job

total = Job.objects.filter(status='active').count()
embedded = Job.objects.filter(status='active', embedding__isnull=False).count()

print("=" * 50)
print("EMBEDDINGS VERIFICATION")
print("=" * 50)
print(f"Total active jobs: {total}")
print(f"Jobs with embeddings: {embedded}")
print(f"Coverage: {embedded/total*100:.1f}%")
print("=" * 50)

if embedded == total:
    print("✅ SUCCESS! All jobs have embeddings!")
else:
    print(f"⚠️  Missing embeddings for {total - embedded} jobs")

exit()
```

**Expected:**
```
==================================================
EMBEDDINGS VERIFICATION
==================================================
Total active jobs: 221
Jobs with embeddings: 221
Coverage: 100.0%
==================================================
✅ SUCCESS! All jobs have embeddings!
```

---

### ☐ Step 6: Test Semantic Search (30 seconds)

```bash
# Test 1: Python developer search
curl -s "http://localhost:8000/api/v1/vectors/search/semantic/?q=Python+developer+remote&limit=3" | python3 -m json.tool | head -30

# Test 2: Machine learning search
curl -s "http://localhost:8000/api/v1/vectors/search/semantic/?q=Machine+learning+engineer&limit=3" | python3 -m json.tool | head -30
```

**Expected:** Returns JSON with relevant job results, each containing:
- Job title
- Company name
- Location
- Similarity score
- Description snippet

---

### ☐ Step 7: Check Qdrant Collection (30 seconds)

```bash
curl -s http://localhost:6333/collections/jobs | python3 -m json.tool
```

**Expected:**
```json
{
  "result": {
    "status": "green",
    "vectors_count": 221,
    "indexed_vectors_count": 221,
    "points_count": 221,
    "segments_count": 1,
    "config": {
      "params": {
        "vectors": {
          "size": 1024,
          "distance": "Cosine"
        }
      }
    }
  }
}
```

**Key metrics:**
- `vectors_count`: 221 ✅
- `indexed_vectors_count`: 221 ✅
- `status`: "green" ✅

---

### ☐ Step 8: Exit Server

```bash
exit
```

---

## Post-Completion Verification 🎯

### ☐ Test on Production Website

1. Open browser: https://jobs.usamif.com

2. Test semantic search with these queries:
   - [ ] "Machine learning engineer with cloud experience"
   - [ ] "Remote JavaScript developer"
   - [ ] "Senior backend engineer Python Django"
   - [ ] "DevOps engineer AWS Kubernetes"
   - [ ] "Frontend React TypeScript developer"

3. Verify results are semantically relevant (not just keyword matches)

**Example:**
- Query: "ML engineer with AWS"
- Good results: Data Scientist, ML Engineer, AI Researcher (even if job description doesn't have exact words)
- Bad results: Completely unrelated jobs

---

### ☐ Test Proactive Rashid

1. Log in to https://jobs.usamif.com
2. Go to Dashboard
3. Check "Recommended Jobs" section
4. Verify recommendations are more relevant than before

---

### ☐ Test Career Brain

1. Go to https://jobs.usamif.com/career-brain
2. Ask: "What jobs are similar to a Python developer?"
3. Verify Career Brain can now find semantically similar jobs

---

## Troubleshooting Guide 🔧

### Issue: "AWS credentials not found"

**Solution:**
```bash
cd /var/www/usam/backend
echo "AWS_ACCESS_KEY_ID=AKIAYKFQRAGEN2ZKTGPY" >> .env
echo "AWS_SECRET_ACCESS_KEY=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" >> .env
echo "AWS_REGION=eu-north-1" >> .env
sudo systemctl restart gunicorn celery celerybeat
```

---

### Issue: "Qdrant connection failed"

**Solution:**
```bash
sudo systemctl start qdrant
sudo systemctl enable qdrant
curl http://localhost:6333/collections  # Verify it's running
```

---

### Issue: "Rate limit exceeded"

**Solution:**
```bash
# Wait 1 minute, then resume with smaller batches
python3 manage.py embed_jobs --batch-size 20
```

---

### Issue: "Some jobs failed to embed"

**Solution:**
```bash
# Check which jobs failed
python3 manage.py shell -c "from apps.jobs.models import Job; failed = Job.objects.filter(status='active', embedding__isnull=True); print(f'Failed: {failed.count()}'); [print(f'  - {j.id}: {j.title}') for j in failed[:10]]"

# Re-run embeddings (will only process jobs without embeddings)
python3 manage.py embed_jobs --batch-size 50
```

---

### Issue: "Process taking too long"

**Normal timing:**
- 10 jobs: 45 seconds
- 50 jobs: 2 minutes
- 221 jobs: 8-10 minutes

**If slower:**
- Check server load: `top` (should have idle CPU)
- Check network: `ping 8.8.8.8` (should be <50ms)
- Check AWS connectivity: `curl https://bedrock.eu-north-1.amazonaws.com` (should return response)

---

## Success Criteria ✅

Phase 3 is complete when:

- [x] All 221 jobs have embeddings (verify with Step 5)
- [x] Qdrant shows 221 vectors (verify with Step 7)
- [x] Semantic search returns relevant results (verify with Step 6)
- [x] Website semantic search works (verify with Post-Completion)
- [x] No errors in logs

---

## Impact of Completion 🎉

**Before Phase 3:**
- ❌ Semantic search unavailable
- ❌ Keyword-only matching ("Python" won't find "ML" jobs)
- ❌ Proactive Rashid uses basic filtering
- ❌ Career Brain limited recommendations

**After Phase 3:**
- ✅ Semantic search enabled
- ✅ Intent-based matching ("ML engineer" finds AI/Data Science jobs)
- ✅ Proactive Rashid uses vector similarity
- ✅ Career Brain finds semantically similar jobs
- ✅ Better user experience

---

## Time Breakdown ⏱️

| Step | Time | Cumulative |
|------|------|------------|
| Connect to server | 30s | 0.5 min |
| Check prerequisites | 1m | 1.5 min |
| Test embeddings (10 jobs) | 1m | 2.5 min |
| Generate all embeddings (221 jobs) | 10m | 12.5 min |
| Verify embeddings | 30s | 13 min |
| Test semantic search | 30s | 13.5 min |
| Check Qdrant | 30s | 14 min |
| Test on website | 2m | 16 min |

**Total: 16 minutes**

---

## Next Steps After Phase 3 🚀

Once embeddings are complete:

1. **Phase 2: Import ESCO Data** (optional)
   - 20 skills and 10 occupations (sample)
   - Or 13,939 skills (full taxonomy)
   - Enables richer Career Brain responses

2. **Monitor Performance**
   - Check semantic search results
   - Gather user feedback
   - Adjust similarity thresholds if needed

3. **Optional Enhancements**
   - Generate skill embeddings (after ESCO import)
   - Add more job scrapers
   - Set up Grafana monitoring

---

## Commands Quick Reference 📋

```bash
# Connect
ssh ubuntu@13.49.245.174
cd /var/www/usam/backend && source ../venv/bin/activate

# Test (10 jobs)
python3 manage.py embed_jobs --limit 10 --batch-size 5

# Generate all (221 jobs)
python3 manage.py embed_jobs --batch-size 50

# Verify count
python3 manage.py shell -c "from apps.jobs.models import Job; print(Job.objects.filter(embedding__isnull=False).count())"

# Test search
curl "http://localhost:8000/api/v1/vectors/search/semantic/?q=Python+developer&limit=5" | python3 -m json.tool

# Check Qdrant
curl http://localhost:6333/collections/jobs | python3 -m json.tool
```

---

**Ready to start? Begin with Step 1! 🚀**

Print this checklist and mark off each step as you complete it.
