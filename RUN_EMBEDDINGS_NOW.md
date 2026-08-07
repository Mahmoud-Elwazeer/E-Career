# 🚀 Generate Embeddings - Quick Start Guide

**Time Required:** 15 minutes
**Impact:** Enables semantic search for all 221 jobs

---

## Step 1: Connect to Production Server

Open your terminal and connect:

```bash
ssh ubuntu@13.49.245.174
```

---

## Step 2: Navigate to Backend Directory

```bash
cd /var/www/usam/backend
source ../venv/bin/activate
```

---

## Step 3: Test with Small Batch (2 minutes)

Test that embeddings work with 10 jobs first:

```bash
python3 manage.py embed_jobs --limit 10 --batch-size 5
```

**Expected Output:**
```
Processing 10 jobs...
Batch 1/2: Embedding 5 jobs...
✓ Embedded: Software Engineer at TechCorp
✓ Embedded: Backend Developer at StartupXYZ
✓ Embedded: Frontend Developer at WebCo
✓ Embedded: DevOps Engineer at CloudInc
✓ Embedded: Data Scientist at AILabs
Batch 2/2: Embedding 5 jobs...
✓ Embedded: Project Manager at ConsultCo
✓ Embedded: Product Manager at ProductCo
✓ Embedded: UX Designer at DesignStudio
✓ Embedded: QA Engineer at TestLab
✓ Embedded: Full Stack Developer at CodeShop

Summary:
✓ 10 jobs embedded successfully
✗ 0 jobs failed
Time: 45 seconds
```

---

## Step 4: Generate All Embeddings (10-15 minutes)

If test successful, embed all 221 jobs:

```bash
python3 manage.py embed_jobs --batch-size 50
```

**Expected Output:**
```
Processing 221 jobs...
Batch 1/5: Embedding 50 jobs... ✓ (120s)
Batch 2/5: Embedding 50 jobs... ✓ (118s)
Batch 3/5: Embedding 50 jobs... ✓ (125s)
Batch 4/5: Embedding 50 jobs... ✓ (122s)
Batch 5/5: Embedding 21 jobs... ✓ (52s)

Summary:
✓ 221 jobs embedded successfully
✗ 0 jobs failed
Time: 537 seconds (8.9 minutes)

Qdrant collection updated:
- Collection: jobs
- Vector count: 221
- Dimension: 1024
```

---

## Step 5: Verify Embeddings

Check that embeddings were created:

```bash
python3 manage.py shell
```

Then in the Python shell:

```python
from apps.jobs.models import Job

# Check how many jobs have embeddings
total_jobs = Job.objects.filter(status='active').count()
embedded_jobs = Job.objects.filter(status='active', embedding__isnull=False).count()

print(f"Total active jobs: {total_jobs}")
print(f"Jobs with embeddings: {embedded_jobs}")
print(f"Coverage: {embedded_jobs/total_jobs*100:.1f}%")

# Should output:
# Total active jobs: 221
# Jobs with embeddings: 221
# Coverage: 100.0%

exit()
```

---

## Step 6: Test Semantic Search

Test that semantic search works:

```bash
curl "http://localhost:8000/api/v1/vectors/search/semantic/?q=Python+developer+remote&limit=5" | jq
```

**Expected:** Returns 5 most relevant Python developer jobs based on semantic similarity.

---

## Step 7: Verify on Website

1. Open browser: https://jobs.usamif.com
2. Go to search bar
3. Try semantic searches:
   - "Machine learning engineer with cloud experience"
   - "Remote JavaScript developer"
   - "Senior backend engineer Python Django"
4. Results should be semantically relevant, not just keyword matches

---

## Troubleshooting

### Error: "AWS Bedrock credentials invalid"

Check AWS credentials are set:

```bash
cd /var/www/usam/backend
cat .env | grep AWS
```

Should show:
```
AWS_ACCESS_KEY_ID=AKIAYKFQRAGEN2ZKTGPY
AWS_SECRET_ACCESS_KEY=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
AWS_REGION=eu-north-1
```

If missing, add them:

```bash
echo "AWS_ACCESS_KEY_ID=AKIAYKFQRAGEN2ZKTGPY" >> .env
echo "AWS_SECRET_ACCESS_KEY=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" >> .env
echo "AWS_REGION=eu-north-1" >> .env
```

Then restart services:

```bash
sudo systemctl restart gunicorn celery celerybeat
```

### Error: "Qdrant connection failed"

Check Qdrant is running:

```bash
sudo systemctl status qdrant
```

If not running:

```bash
sudo systemctl start qdrant
```

Check Qdrant is accessible:

```bash
curl http://localhost:6333/collections
```

Should return JSON with collections list.

### Error: "Rate limit exceeded"

AWS Bedrock has rate limits. If you hit them:

1. Wait 1 minute
2. Resume with:
   ```bash
   python3 manage.py embed_jobs --batch-size 20  # Smaller batches
   ```

### Embeddings taking too long

Normal timing:
- 10 jobs: ~45 seconds
- 50 jobs: ~2 minutes
- 221 jobs: ~8-10 minutes

If slower, check:
1. Network connection to AWS
2. Qdrant is running locally
3. No other heavy processes

---

## What This Achieves

### Before Embeddings:
- ❌ Semantic search unavailable
- ❌ Job recommendations basic (keyword matching only)
- ❌ Proactive Rashid limited
- ❌ Career Brain can't find similar jobs

### After Embeddings:
- ✅ Semantic search works ("find me ML jobs" returns relevant results)
- ✅ Job recommendations enhanced (vector similarity)
- ✅ Proactive Rashid uses semantic matching
- ✅ Career Brain finds similar jobs by meaning, not keywords
- ✅ Better user experience (find jobs by intent, not exact words)

---

## Cost

**AWS Bedrock Cohere Embeddings:**
- Cost: $0.0001 per 1,000 tokens
- Average job: ~200 tokens
- 221 jobs: ~44,200 tokens
- **Total cost: ~$0.004 (less than 1 cent)**

Very affordable for major feature enhancement!

---

## Next Steps After Embeddings

1. **Test semantic search** on production website
2. **Import ESCO data** (optional, for skill taxonomy)
3. **Monitor performance** (embeddings improve over time as more users interact)

---

## Quick Command Reference

```bash
# Connect to server
ssh ubuntu@13.49.245.174

# Navigate
cd /var/www/usam/backend
source ../venv/bin/activate

# Test (10 jobs)
python3 manage.py embed_jobs --limit 10 --batch-size 5

# Generate all (221 jobs)
python3 manage.py embed_jobs --batch-size 50

# Verify
python3 manage.py shell -c "from apps.jobs.models import Job; print(f'Embedded: {Job.objects.filter(embedding__isnull=False).count()}/221')"

# Test search
curl "http://localhost:8000/api/v1/vectors/search/semantic/?q=Python+developer&limit=5" | jq
```

---

**Estimated Time:** 15 minutes
**Difficulty:** Easy (just run 3 commands)
**Impact:** HIGH - Enables semantic search for entire platform

🚀 **Ready to run? Start with Step 1!**
