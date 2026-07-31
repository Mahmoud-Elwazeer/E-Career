# Vector Search & Embeddings

## Overview

This app implements semantic search and vector similarity using:
- **Cohere Embed v3** via AWS Bedrock for embedding generation (1024 dimensions)
- **Qdrant** as the primary vector database
- **pgvector** as fallback when Qdrant is unavailable

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Vector Service                         │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Embedding Generation         Vector Storage             │
│  ┌──────────────────┐        ┌──────────────────┐       │
│  │ Cohere Embed v3  │───────▶│    Qdrant DB     │       │
│  │  via Bedrock     │        │   (Primary)      │       │
│  └──────────────────┘        └──────────────────┘       │
│         │                             │                  │
│         │                             │ (fallback)       │
│         │                    ┌────────▼──────────┐       │
│         │                    │   pgvector        │       │
│         │                    │   (PostgreSQL)    │       │
│         │                    └───────────────────┘       │
│         │                                                 │
│         ▼                                                 │
│  ┌──────────────────────────────────────┐               │
│  │         Collections                   │               │
│  │  • jobs (job listings)                │               │
│  │  • users (user profiles)              │               │
│  │  • skills (ESCO taxonomy)             │               │
│  └──────────────────────────────────────┘               │
│                                                           │
│  Search Types                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Semantic    │  │   Similar    │  │   Hybrid     │  │
│  │  (text→vec)  │  │  (vec→vec)   │  │  (keyword+   │  │
│  │              │  │              │  │   semantic)  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Components

### Plugins

**VectorPlugin** (Abstract)
- `QdrantVectorPlugin`: Qdrant implementation
- `PgVectorPlugin`: PostgreSQL fallback

**EmbeddingPlugin** (Abstract)
- `CohereEmbedPlugin`: Cohere Embed v3 via Bedrock

### Collections

1. **jobs** - Job listings with embeddings
   - Payload: job_id, title, company, location, salary, trust_score
   - Filters: location, experience_level, employment_type, trust_score

2. **users** - User profiles with embeddings
   - Payload: user_id, skills, experience, preferences

3. **skills** - ESCO skills with embeddings
   - Payload: skill_id, name, type, category, description

## Management Commands

### Setup Collections

```bash
# Create all collections
python manage.py setup_vector_collections

# Drop and recreate (WARNING: destructive)
python manage.py setup_vector_collections --rebuild
```

### Bulk Embed Jobs

```bash
# Embed all verified jobs
python manage.py embed_jobs

# Test with first 100 jobs
python manage.py embed_jobs --limit 100

# Re-embed existing jobs
python manage.py embed_jobs --force

# Custom batch size
python manage.py embed_jobs --batch-size 100
```

**What it does:**
1. Fetches verified jobs (trust_score >= 0.4)
2. Converts each job to embedding text (title + company + description + metadata)
3. Generates embeddings in batches via Cohere
4. Indexes vectors in Qdrant with payload

**Cost:**
- ~10,000 jobs = ~$0.10 (Cohere pricing: $0.0001 per 1k tokens)
- Batch size 50 = ~200 batches for 10k jobs

### Bulk Embed Skills

```bash
# Embed top 500 skills (by usage)
python manage.py embed_skills --limit 500

# Embed all skills
python manage.py embed_skills

# Custom batch size
python manage.py embed_skills --batch-size 100
```

## API Endpoints

### Semantic Search

```http
GET /api/v1/vectors/search/semantic/?q=Python developer remote
```

**Parameters:**
- `q` (required): Natural language query
- `limit`: Max results (default: 20)
- `threshold`: Minimum similarity score (0-1)
- `location`, `experience_level`, `employment_type`, `salary_min`: Filters

**Response:**
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "id": "uuid",
        "title": "Senior Python Developer",
        "company": "TechCorp",
        "location": "Remote",
        "similarity_score": 0.95
      }
    ],
    "total": 10,
    "query_time_ms": 123,
    "search_type": "semantic"
  }
}
```

### Similar Jobs

```http
GET /api/v1/vectors/jobs/{job_id}/similar/?limit=10
```

**Parameters:**
- `limit`: Max results (default: 10)
- `threshold`: Minimum similarity score

**Response:**
```json
{
  "success": true,
  "data": {
    "similar_jobs": [
      {
        "id": "uuid",
        "title": "Django Developer",
        "company": "StartupX",
        "similarity_score": 0.92
      }
    ],
    "total": 5,
    "query_time_ms": 67
  }
}
```

### Hybrid Search

```http
GET /api/v1/vectors/search/hybrid/?q=backend engineer&keyword_weight=0.5&semantic_weight=0.5
```

**Parameters:**
- `q` (required): Search query
- `keyword_weight`: Weight for keyword results (0-1, default: 0.5)
- `semantic_weight`: Weight for semantic results (0-1, default: 0.5)
- Standard filters: location, experience_level, etc.

**Algorithm:** Reciprocal Rank Fusion (RRF)
- Combines Typesense keyword search + Qdrant semantic search
- RRF formula: `score = Σ(weight / (k + rank))` where k=60
- Returns merged, re-ranked results

**Response:**
```json
{
  "success": true,
  "data": {
    "jobs": [...],
    "total": 15,
    "search_type": "hybrid",
    "keyword_count": 12,
    "semantic_count": 18
  }
}
```

### Health Check

```http
GET /api/v1/vectors/health/
```

**Response:**
```json
{
  "success": true,
  "data": {
    "vector": {
      "healthy": true,
      "collections": 3,
      "host": "localhost",
      "port": 6333
    },
    "embedding": {
      "healthy": true,
      "provider": "bedrock_cohere",
      "dimensions": 1024,
      "region": "us-east-1"
    },
    "collections": {
      "jobs": true,
      "users": true,
      "skills": true
    }
  }
}
```

## Real-Time Synchronization

Django signals automatically embed/remove vectors when jobs/skills are created/updated/deleted:

```python
# Job created/updated → embed_job_task.delay(job_id)
# Job deleted → remove_job_from_vectors_task.delay(job_id)
# Skill created → embed_skill_task.delay(skill_id)
```

**Requirements for auto-embedding:**
- Job must be verified (status="verified")
- Job must have trust_score >= 0.4

## Usage Examples

### Python

```python
from apps.vectors.service import get_vector_service

vector_service = get_vector_service()

# Semantic search
results = vector_service.semantic_search(
    collection="jobs",
    query_text="senior backend engineer with Python",
    limit=20,
    score_threshold=0.7,
    filters={"location": "Cairo", "trust_score": {"gte": 0.4}},
)

for result in results.results:
    print(f"{result.payload['title']} - {result.score}")

# Find similar jobs
similar = vector_service.similar_items(
    collection="jobs",
    item_id="job-uuid",
    limit=10,
    filters={"trust_score": {"gte": 0.4}},
)

# Generate embeddings
embeddings = vector_service.generate_embeddings(
    texts=["Python developer", "Data scientist"],
    input_type="search_document",
)
```

### cURL

```bash
# Semantic search
curl "http://localhost:8000/api/v1/vectors/search/semantic/?q=python%20developer&limit=20"

# Similar jobs
curl "http://localhost:8000/api/v1/vectors/jobs/550e8400-e29b-41d4-a716-446655440000/similar/?limit=10"

# Hybrid search
curl "http://localhost:8000/api/v1/vectors/search/hybrid/?q=backend%20engineer&keyword_weight=0.6&semantic_weight=0.4"

# Health check
curl "http://localhost:8000/api/v1/vectors/health/"
```

## Deployment

### Docker Setup

Qdrant is included in `docker-compose.yml`:

```yaml
qdrant:
  image: qdrant/qdrant:v1.11.3
  ports:
    - "6333:6333"
    - "6334:6334"
  volumes:
    - qdrant_data:/qdrant/storage
  environment:
    QDRANT__SERVICE__API_KEY: ${QDRANT_API_KEY}
```

Start services:
```bash
docker-compose up -d qdrant
```

### Manual Setup

1. **Install Qdrant:**
   ```bash
   docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant:v1.11.3
   ```

2. **Configure environment variables:**
   ```bash
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   QDRANT_API_KEY=your-api-key
   
   # AWS Bedrock for embeddings
   AWS_ACCESS_KEY_ID=your-key
   AWS_SECRET_ACCESS_KEY=your-secret
   AWS_DEFAULT_REGION=us-east-1
   ```

3. **Create collections:**
   ```bash
   python manage.py setup_vector_collections
   ```

4. **Bulk embed existing data:**
   ```bash
   python manage.py embed_jobs
   python manage.py embed_skills --limit 500
   ```

## Performance

### Benchmarks (10,000 jobs indexed)

- **Semantic search:** ~50-150ms
- **Similar jobs:** ~30-80ms
- **Hybrid search:** ~100-250ms (combines both)
- **Embedding generation:** ~200ms per batch of 50 texts

### Cost Estimates

**Cohere Embed v3 via Bedrock:**
- $0.0001 per 1k input tokens
- Average job description: ~200 tokens
- 10,000 jobs: ~$0.20
- 100,000 jobs: ~$2.00

**Qdrant:**
- Self-hosted: Free (resource costs only)
- Cloud: ~$25/month for 1M vectors

## Testing

```bash
# Run all vector tests
python manage.py test apps.vectors.tests

# Run specific test
python manage.py test apps.vectors.tests.test_vector_service

# With coverage
coverage run --source='apps.vectors' manage.py test apps.vectors.tests
coverage report
```

Tests use mocks for Qdrant and Bedrock, so no external services required.

## Troubleshooting

### Qdrant connection failed

```python
# Check health
from apps.vectors.service import get_vector_service
health = get_vector_service().health_check()
print(health)

# Falls back to pgvector automatically
```

### Embeddings generation slow

- Reduce batch size: `--batch-size 25`
- Use Celery for async: Signals handle this automatically
- Check Bedrock region latency

### Out of sync

Re-sync all jobs:
```bash
python manage.py embed_jobs --force
```

## Future Enhancements

- [ ] User profile embeddings for personalized recommendations
- [ ] Skill-based job matching (user skills → relevant jobs)
- [ ] Multimodal search (text + filters + salary range)
- [ ] Query expansion (related terms, synonyms)
- [ ] Re-ranking with user preferences
- [ ] A/B testing keyword vs semantic vs hybrid
