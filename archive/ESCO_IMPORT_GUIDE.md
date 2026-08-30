# ESCO Data Import Guide
## Step-by-Step Instructions

---

## OPTION A: Quick Sample Data (Testing - 5 minutes)

If you just want to **test** the import commands without downloading 13,939 skills:

### Step 1: Create Sample Data

```bash
cd "m:\job already web for jobs\E-Career"

# Create sample ESCO skills
cat > backend/data/esco/skills_sample.csv << 'EOF'
conceptUri,preferredLabel,altLabels,description,skillType,reuseLevel
http://data.europa.eu/esco/skill/S1,Python programming,"Python,Programming","Programming in Python language",knowledge,cross-sector
http://data.europa.eu/esco/skill/S2,JavaScript,"JS,Javascript","JavaScript programming",knowledge,cross-sector
http://data.europa.eu/esco/skill/S3,Project Management,"PM,Management","Managing projects",skill,transversal
http://data.europa.eu/esco/skill/S4,Communication,"Communicate,Speaking","Communication skills",skill,transversal
http://data.europa.eu/esco/skill/S5,Problem Solving,"Problem-solving,Analysis","Solving problems",skill,transversal
http://data.europa.eu/esco/skill/S6,Django framework,"Django,Web framework","Django web framework",knowledge,sector-specific
http://data.europa.eu/esco/skill/S7,SQL databases,"SQL,Database","SQL database management",knowledge,cross-sector
http://data.europa.eu/esco/skill/S8,React framework,"React,ReactJS","React JavaScript library",knowledge,sector-specific
http://data.europa.eu/esco/skill/S9,Leadership,"Lead,Management","Team leadership",skill,transversal
http://data.europa.eu/esco/skill/S10,Data Analysis,"Analysis,Analytics","Analyzing data",knowledge,cross-sector
EOF

# Create sample ESCO occupations
cat > backend/data/esco/occupations_sample.csv << 'EOF'
conceptUri,preferredLabel,altLabels,description
http://data.europa.eu/esco/occupation/O1,Software Developer,"Developer,Programmer","Develops software applications"
http://data.europa.eu/esco/occupation/O2,Project Manager,"PM,Manager","Manages projects and teams"
http://data.europa.eu/esco/occupation/O3,Data Scientist,"Scientist,Analyst","Analyzes data and builds models"
EOF

# Create sample mappings
cat > backend/data/esco/mappings_sample.csv << 'EOF'
occupationUri,skillUri,relationType,skillType
http://data.europa.eu/esco/occupation/O1,http://data.europa.eu/esco/skill/S1,essential,knowledge
http://data.europa.eu/esco/occupation/O1,http://data.europa.eu/esco/skill/S2,essential,knowledge
http://data.europa.eu/esco/occupation/O1,http://data.europa.eu/esco/skill/S6,optional,knowledge
http://data.europa.eu/esco/occupation/O2,http://data.europa.eu/esco/skill/S3,essential,skill
http://data.europa.eu/esco/occupation/O2,http://data.europa.eu/esco/skill/S9,essential,skill
http://data.europa.eu/esco/occupation/O3,http://data.europa.eu/esco/skill/S10,essential,knowledge
EOF

echo "Sample data created!"
```

### Step 2: Test Import

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Import sample data
python manage.py import_esco \
  --skills data/esco/skills_sample.csv \
  --occupations data/esco/occupations_sample.csv \
  --mappings data/esco/mappings_sample.csv

# Verify
python manage.py shell
>>> from apps.skills.models import Skill, Occupation
>>> Skill.objects.count()  # Should be 10
>>> Occupation.objects.count()  # Should be 3
>>> exit()
```

**Expected Output:**
- 10 skills imported
- 3 occupations imported
- 6 skill-occupation mappings created

---

## OPTION B: Download Real ESCO Data (Production - 30 minutes)

For **production** with full 13,939 skills:

### Step 1: Download from ESCO Portal

**Manual Download (Recommended):**

1. Visit: https://ec.europa.eu/esco/portal/download

2. Select **"ESCO dataset - CSV format v1.2.0"** (or latest version)

3. Download these files:
   - `skills_en.csv` (~13,939 skills)
   - `occupations_en.csv` (~3,039 occupations)
   - `skillsCollection_en.csv` (skill groups)
   - `occupationSkillRelations_en.csv` (mappings)

4. Extract and place in:
   ```
   m:\job already web for jobs\E-Career\backend\data\esco\
   ```

**OR Use ESCO API (Automated):**

```bash
cd "m:\job already web for jobs\E-Career\backend\data\esco"

# Download skills
curl -L -o skills_en.csv \
  "https://ec.europa.eu/esco/api/resource/taxonomy?uri=http://data.europa.eu/esco/skill&language=en&format=csv"

# Download occupations
curl -L -o occupations_en.csv \
  "https://ec.europa.eu/esco/api/resource/taxonomy?uri=http://data.europa.eu/esco/occupation&language=en&format=csv"

# Note: Mappings file might need manual download from portal
```

### Step 2: Download O*NET Data (Optional)

1. Visit: https://www.onetcenter.org/database.html

2. Download:
   - "Occupation Data" → `Occupation Data.xlsx`
   - "Skills" → `Skills.xlsx`

3. Convert to CSV and place in:
   ```
   m:\job already web for jobs\E-Career\backend\data\onet\
   ```

### Step 3: Import Real Data

```bash
cd "m:\job already web for jobs\E-Career\backend"
source venv/bin/activate  # Windows: venv\Scripts\activate

# Import ESCO skills
python manage.py import_esco \
  --skills data/esco/skills_en.csv \
  --occupations data/esco/occupations_en.csv \
  --mappings data/esco/occupationSkillRelations_en.csv

# Import O*NET (if you have the data)
python manage.py import_onet \
  --file data/onet/Occupation_Data.csv \
  --skills-file data/onet/Skills.csv

# Map ESCO to O*NET
python manage.py map_esco_onet --threshold 0.8

# Generate Arabic translations (top 500)
python manage.py generate_arabic_translations --limit 500
```

### Step 4: Verify Import

```bash
python manage.py shell
>>> from apps.skills.models import Skill, Occupation
>>> Skill.objects.count()  # Should be ~13,939
>>> Skill.objects.filter(esco_uri__isnull=False).count()
>>> Occupation.objects.count()  # Should be ~3,039
>>> exit()
```

---

## OPTION C: Deploy to Production Server

After importing locally, deploy to server:

### Step 1: Upload Data Files

```bash
# From local machine
scp -r backend/data/esco/*.csv ubuntu@13.49.245.174:/var/www/usam/backend/data/esco/
```

### Step 2: SSH and Import

```bash
ssh ubuntu@13.49.245.174

cd /var/www/usam/backend
source ../venv/bin/activate

# Import on server
python3 manage.py import_esco \
  --skills data/esco/skills_en.csv \
  --occupations data/esco/occupations_en.csv \
  --mappings data/esco/occupationSkillRelations_en.csv

# Verify
python3 manage.py shell
>>> from apps.skills.models import Skill
>>> Skill.objects.count()
>>> exit()
```

---

## FAQ

### Q: Do I need ESCO data for the platform to work?
**A:** No. The platform works fine with the basic skills already in the database. ESCO just adds the full 13,939 skill taxonomy.

### Q: Which option should I choose?
**A:** 
- **Option A (Sample)**: Quick test, verify import works
- **Option B (Real)**: Full production data
- **Option C (Server)**: After testing locally

### Q: How long does the import take?
**A:**
- Sample data: ~5 seconds
- Real data (13,939 skills): ~5-10 minutes
- O*NET mapping: ~2-3 minutes

### Q: What if the download fails?
**A:** The ESCO portal sometimes has slow downloads. Alternative:
1. Use sample data for now
2. Download overnight
3. Request data files from ESCO support

### Q: Can I import in stages?
**A:** Yes! Import skills first, then occupations, then mappings separately.

---

## Verification Commands

```bash
# Check skill count
python manage.py shell -c "from apps.skills.models import Skill; print(f'Skills: {Skill.objects.count()}')"

# Check occupations
python manage.py shell -c "from apps.skills.models import Occupation; print(f'Occupations: {Occupation.objects.count()}')"

# Check mappings
python manage.py shell -c "from apps.skills.models import OccupationSkill; print(f'Mappings: {OccupationSkill.objects.count()}')"

# List sample skills
python manage.py shell -c "from apps.skills.models import Skill; print(list(Skill.objects.values_list('name', flat=True)[:10]))"
```

---

## Troubleshooting

### Error: "File not found"
```bash
# Check file paths
ls -la backend/data/esco/
ls -la backend/data/onet/
```

### Error: "CSV parsing failed"
- Check file encoding (should be UTF-8)
- Check CSV format matches ESCO spec
- Try with --dry-run first

### Import is slow
- Normal for 13,939 records
- Use --limit 100 to test first
- Import runs in transaction, so it's safe to interrupt

---

## Summary

**Fastest option:** Option A (Sample) - 5 minutes
**Most complete:** Option B (Real) - 30 minutes
**Production deploy:** Option C (Server) - After A or B

**Recommendation:** Start with **Option A** to test, then do **Option B** if you need the full taxonomy.

The platform is **95% complete** without ESCO data. This is an optional enhancement!
