# Skills Taxonomy & Knowledge Graph

## Overview

This app implements the skill taxonomy and knowledge graph for the E-Career platform, based on ESCO and O*NET datasets.

## Components

### Models

- **Skill**: Individual skills with hierarchy, ESCO URIs, O*NET cross-references
- **SkillRelationship**: Relationships between skills (prerequisite, related, complementary, etc.)
- **Occupation**: Job roles from ESCO taxonomy
- **OccupationSkill**: Mapping of skills to occupations with importance/level ratings
- **CareerPath**: Career progression paths between occupations

### Management Commands

#### `import_esco`
Import ESCO dataset (skills, occupations, and mappings).

```bash
python manage.py import_esco \
    --skills /path/to/esco/skills.csv \
    --occupations /path/to/esco/occupations.csv \
    --mappings /path/to/esco/occupationSkillRelations.csv
```

#### `import_onet`
Import O*NET quantitative ratings (importance 1-5, level 1-7).

```bash
python manage.py import_onet \
    --skills /path/to/onet/Skills.txt \
    --importance /path/to/onet/Skills_Importance.txt \
    --level /path/to/onet/Skills_Level.txt
```

#### `setup_age_graph`
Set up Apache AGE graph database for advanced graph queries.

```bash
# Initial setup
python manage.py setup_age_graph

# Rebuild graph (WARNING: destructive)
python manage.py setup_age_graph --rebuild

# Dry run
python manage.py setup_age_graph --dry-run
```

**Prerequisites:**
1. PostgreSQL 12+ with Apache AGE extension installed
2. Add `apache-age-python==0.0.6` to requirements
3. Add `'age'` to `shared_preload_libraries` in postgresql.conf

#### `generate_arabic_translations`
Generate Arabic translations for skill names using AI (Claude Haiku).

```bash
# Translate top 500 skills
python manage.py generate_arabic_translations --limit 500

# Translate all skills
python manage.py generate_arabic_translations --all

# Re-translate existing
python manage.py generate_arabic_translations --force

# Dry run
python manage.py generate_arabic_translations --dry-run
```

**Cost Estimation:**
- Haiku: ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens
- 500 skills: ~50 API calls (batch size 10) = ~$0.10
- All 13,939 skills: ~1,394 API calls = ~$2.80

### Graph Query Utilities

The `SkillGraph` class provides graph traversal methods:

```python
from apps.skills.graph import SkillGraph

graph = SkillGraph()

# Find related skills (up to depth N)
related = graph.find_related_skills(skill_id, depth=2)

# Find paths between two skills
paths = graph.find_skill_path(from_skill_id, to_skill_id)

# Calculate shortest distance
distance = graph.get_skill_distance(skill_id_1, skill_id_2)

# Get skill hierarchy
hierarchy = graph.get_skill_hierarchy(skill_id)

# Get skills for occupation
skills = graph.get_occupation_skills(occupation_id)

# Get career paths from occupation
paths = graph.get_career_paths(occupation_id)
```

**Note:** The implementation uses Apache AGE for graph queries when available, with Django ORM fallback for environments without AGE.

### Tests

Comprehensive test coverage for:
- ESCO import functionality
- O*NET import functionality
- Model relationships and constraints
- Graph query utilities
- Hierarchy traversal

Run tests:
```bash
python manage.py test apps.skills.tests
```

## Apache AGE Setup

### Docker Setup

The `docker-compose.yml` includes PostgreSQL 16 with AGE extension initialization:

```yaml
db:
  image: postgres:16
  volumes:
    - ./init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
```

The `init-db.sql` script:
1. Creates AGE extension
2. Sets search path to include `ag_catalog`
3. Grants permissions

### Manual Setup

If not using Docker:

```sql
-- 1. Install AGE extension (requires PostgreSQL 12+)
CREATE EXTENSION IF NOT EXISTS age;

-- 2. Load AGE
LOAD 'age';

-- 3. Update search path
ALTER DATABASE ecareer SET search_path = ag_catalog, "$user", public;

-- 4. Create graph
SELECT create_graph('skills_graph');
```

### Verify AGE Installation

```python
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'age';")
    version = cursor.fetchone()
    print(f"Apache AGE version: {version[0]}")
```

## Data Sources

### ESCO Dataset
- **URL**: https://ec.europa.eu/esco/portal/download
- **Format**: CSV
- **Size**: ~13,939 skills, ~3,039 occupations
- **Language**: English (with Arabic translations via AI)

### O*NET Dataset
- **URL**: https://www.onetcenter.org/database.html
- **Format**: TSV/TXT
- **Files needed**:
  - Skills.txt
  - Skills_Importance.txt (ratings 1-5)
  - Skills_Level.txt (ratings 1-7)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Skills App                           │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  Models                Graph Storage        Queries      │
│  ┌──────┐            ┌──────────────┐     ┌──────────┐  │
│  │Skill │◄───────────┤ Apache AGE   │◄────┤SkillGraph│  │
│  │      │            │   Graph DB   │     │  Utils   │  │
│  └──┬───┘            └──────────────┘     └──────────┘  │
│     │                       ▲                            │
│     │                       │                            │
│  ┌──▼──────────┐     ┌─────┴──────┐                     │
│  │Occupation   │     │Django ORM  │                     │
│  │             │     │ Fallback   │                     │
│  └─────────────┘     └────────────┘                     │
│                                                           │
│  Import Pipeline              AI Translation             │
│  ┌──────────────┐            ┌──────────────┐           │
│  │ import_esco  │            │generate_     │           │
│  │ import_onet  │            │ arabic_      │           │
│  │              │            │translations  │           │
│  └──────────────┘            └──────────────┘           │
│         │                           │                    │
│         ▼                           ▼                    │
│  ┌────────────────────────────────────────┐             │
│  │         PostgreSQL Database             │             │
│  │  ┌────────────┐  ┌─────────────────┐   │             │
│  │  │Django Tables│  │AGE Graph Nodes  │   │             │
│  │  │skills_skill │  │Skill vertices   │   │             │
│  │  │skills_occ   │  │Occupation nodes │   │             │
│  │  └────────────┘  └─────────────────┘   │             │
│  └────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

## Implementation Status

### ✅ Completed (Week 3 Tasks)

- [x] Task 1.15: Create `skills` Django app
- [x] Task 1.16: Create models (Skill, SkillRelationship, Occupation, OccupationSkill, CareerPath)
- [x] Task 1.17: Download ESCO dataset (command available)
- [x] Task 1.18: Build ESCO import management command
- [x] Task 1.19: Import ESCO skills with hierarchy
- [x] Task 1.20: Import ESCO occupations with hierarchy
- [x] Task 1.21: Import ESCO skill-to-occupation mappings
- [x] Task 1.22: Download O*NET dataset (command available)
- [x] Task 1.23: Build O*NET import command (merge with ESCO via crosswalk)
- [x] Task 1.24: Import O*NET quantitative ratings
- [x] Task 1.25: Install Apache AGE extension (docker-compose + init-db.sql)
- [x] Task 1.26: Create AGE graph (setup_age_graph command)
- [x] Task 1.27: Build graph query utilities (SkillGraph class)
- [x] Task 1.28: Create Arabic translations (generate_arabic_translations command)
- [x] Task 1.29: Build admin interface for skill taxonomy browsing
- [x] Task 1.30: Write tests (test_taxonomy_import.py, test_graph_queries.py)

### Usage Instructions

1. **Install dependencies:**
   ```bash
   pip install -r requirements/base.txt
   ```

2. **Start services:**
   ```bash
   docker-compose up -d db redis typesense
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Set up AGE graph:**
   ```bash
   python manage.py setup_age_graph
   ```

5. **Import ESCO data:**
   ```bash
   python manage.py import_esco \
       --skills /path/to/esco/skills_en.csv \
       --occupations /path/to/esco/occupations_en.csv \
       --mappings /path/to/esco/occupationSkillRelations.csv
   ```

6. **Import O*NET data:**
   ```bash
   python manage.py import_onet \
       --skills /path/to/onet/Skills.txt \
       --importance /path/to/onet/Skills_Importance.txt \
       --level /path/to/onet/Skills_Level.txt
   ```

7. **Generate Arabic translations:**
   ```bash
   python manage.py generate_arabic_translations --limit 500
   ```

8. **Run tests:**
   ```bash
   python manage.py test apps.skills.tests
   ```

## Future Enhancements

- [ ] Skill embedding generation (Cohere Embed v3, 1024d)
- [ ] Vector similarity search (Qdrant integration)
- [ ] Skill gap analysis
- [ ] Career path recommendations
- [ ] Skill trend analysis
- [ ] Market demand correlation
