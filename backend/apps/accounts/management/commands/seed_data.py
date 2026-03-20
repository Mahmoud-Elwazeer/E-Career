"""
Management command: python manage.py seed_data

Creates:
  - Superuser admin account
  - Demo regular user
  - All companies, sources, tags from mock data
  - 20 demo jobs
  - Feature flags
  - Demo saved jobs and alerts for the demo user
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from datetime import date, timedelta


COMPANIES = [
    {"name": "TechNova", "logo_url": "https://ui-avatars.com/api/?name=TN&background=0A3836&color=fff&size=64", "snippet": "AI-driven SaaS platform serving 500+ enterprise clients across MENA.", "industry": "technology", "website": "https://technova.example.com"},
    {"name": "FinEdge", "logo_url": "https://ui-avatars.com/api/?name=FE&background=1a5c5a&color=fff&size=64", "snippet": "Fintech startup revolutionizing cross-border payments in the Arab world.", "industry": "finance", "website": "https://finedge.example.com"},
    {"name": "MedCare Plus", "logo_url": "https://ui-avatars.com/api/?name=MC&background=2d7a77&color=fff&size=64", "snippet": "Digital health platform connecting patients with specialists.", "industry": "healthcare", "website": "https://medcareplus.example.com"},
    {"name": "EduSpark", "logo_url": "https://ui-avatars.com/api/?name=ES&background=3a918e&color=fff&size=64", "snippet": "EdTech company offering Arabic-first online learning experiences.", "industry": "education", "website": "https://eduspark.example.com"},
    {"name": "BrandWave", "logo_url": "https://ui-avatars.com/api/?name=BW&background=0A3836&color=fff&size=64", "snippet": "Full-service digital marketing agency with offices in Dubai and Cairo.", "industry": "marketing", "website": "https://brandwave.example.com"},
    {"name": "BuildRight", "logo_url": "https://ui-avatars.com/api/?name=BR&background=1a5c5a&color=fff&size=64", "snippet": "Civil engineering & construction firm with major projects across GCC.", "industry": "engineering", "website": "https://buildright.example.com"},
    {"name": "PixelCraft", "logo_url": "https://ui-avatars.com/api/?name=PC&background=2d7a77&color=fff&size=64", "snippet": "Award-winning UX/UI design studio based in Amman.", "industry": "design", "website": "https://pixelcraft.example.com"},
    {"name": "SalesForce Arabia", "logo_url": "https://ui-avatars.com/api/?name=SA&background=3a918e&color=fff&size=64", "snippet": "B2B sales enablement platform for the MENA market.", "industry": "sales", "website": "https://salesforcearabia.example.com"},
]

SOURCES = [
    {"name": "LinkedIn", "slug": "linkedin", "url": "https://linkedin.com", "logo_url": "https://cdn-icons-png.flaticon.com/512/174/174857.png"},
    {"name": "Bayt", "slug": "bayt", "url": "https://bayt.com", "logo_url": "https://ui-avatars.com/api/?name=BY&background=00a651&color=fff&size=64"},
    {"name": "Wuzzuf", "slug": "wuzzuf", "url": "https://wuzzuf.net", "logo_url": "https://ui-avatars.com/api/?name=WZ&background=ff6600&color=fff&size=64"},
    {"name": "GulfTalent", "slug": "gulftalent", "url": "https://gulftalent.com", "logo_url": "https://ui-avatars.com/api/?name=GT&background=003366&color=fff&size=64"},
]

TAGS = [
    ("React", "framework"), ("TypeScript", "language"), ("Tailwind CSS", "framework"),
    ("SQL", "skill"), ("Python", "language"), ("Excel", "tool"),
    ("Figma", "tool"), ("User Research", "skill"), ("Prototyping", "skill"),
    ("Node.js", "framework"), ("Go", "language"), ("AWS", "tool"), ("Microservices", "skill"),
    ("SEO", "skill"), ("Social Media", "skill"), ("Google Ads", "tool"),
    ("Patient Care", "skill"), ("Telemedicine", "skill"), ("Clinical", "skill"),
    ("Curriculum Design", "skill"), ("Arabic", "skill"), ("STEM", "skill"), ("E-Learning", "skill"),
    ("Structural Design", "skill"), ("AutoCAD", "tool"), ("Project Management", "skill"),
    ("B2B Sales", "skill"), ("CRM", "tool"),
    ("Product Strategy", "skill"), ("Agile", "skill"), ("AI/ML", "skill"),
    ("Flutter", "framework"), ("Dart", "language"), ("Mobile", "skill"), ("Firebase", "tool"),
    ("Adobe Illustrator", "tool"), ("Photoshop", "tool"), ("Branding", "skill"),
    ("Kubernetes", "tool"), ("Docker", "tool"), ("CI/CD", "skill"),
    ("Financial Modeling", "skill"), ("CFA", "skill"),
    ("Arabic Content", "skill"), ("Copywriting", "skill"),
    ("Cypress", "tool"), ("Playwright", "tool"), ("Automation", "skill"), ("Testing", "skill"),
    ("Recruitment", "skill"), ("Onboarding", "skill"), ("HRIS", "tool"),
    ("TensorFlow", "framework"), ("MLOps", "skill"), ("NLP", "skill"),
    ("Pharmacy", "skill"), ("Inventory", "skill"),
    ("Account Management", "skill"), ("Client Relations", "skill"), ("SaaS", "skill"),
]

JOBS = [
    {"title": "Frontend Developer", "company": "TechNova", "location": "Dubai, UAE", "location_type": "hybrid", "industry": "technology", "experience_level": "mid", "description": "Join TechNova's product team to build cutting-edge React applications. You'll work on our flagship SaaS dashboard used by 500+ enterprises. Responsibilities include component architecture, performance optimization, and collaborating with designers on pixel-perfect UIs. We use TypeScript, React, Tailwind CSS, and GraphQL.", "tags": ["React", "TypeScript", "Tailwind CSS"], "salary_min": 8000, "salary_max": 12000, "salary_currency": "AED", "source": "LinkedIn", "source_url": "https://linkedin.com/jobs/1", "days_ago": 14, "deadline_days": 16},
    {"title": "Data Analyst", "company": "FinEdge", "location": "Cairo, Egypt", "location_type": "remote", "industry": "finance", "experience_level": "entry", "description": "FinEdge is looking for a sharp data analyst to join our growing analytics team. You'll analyze transaction data, build dashboards in Metabase, and provide insights to product and compliance teams.", "tags": ["SQL", "Python", "Excel"], "salary_min": 15000, "salary_max": 25000, "salary_currency": "EGP", "source": "Wuzzuf", "source_url": "https://wuzzuf.net/jobs/2", "days_ago": 17},
    {"title": "UX Designer", "company": "PixelCraft", "location": "Amman, Jordan", "location_type": "onsite", "industry": "design", "experience_level": "mid", "description": "PixelCraft seeks a talented UX designer to lead user research and wireframing for our client projects. You'll conduct usability tests, create user flows, and deliver high-fidelity prototypes in Figma. Portfolio required.", "tags": ["Figma", "User Research", "Prototyping"], "salary_min": 1500, "salary_max": 2500, "salary_currency": "JOD", "source": "Bayt", "source_url": "https://bayt.com/jobs/3", "days_ago": 15, "deadline_days": 5},
    {"title": "Backend Engineer", "company": "TechNova", "location": "Riyadh, KSA", "location_type": "onsite", "industry": "technology", "experience_level": "senior", "description": "Design and build scalable microservices for TechNova's AI platform. You'll own the API layer, optimize database queries, and implement event-driven architectures. Requires 5+ years with Node.js/Go and cloud infrastructure.", "tags": ["Node.js", "Go", "AWS", "Microservices"], "salary_min": 18000, "salary_max": 28000, "salary_currency": "SAR", "source": "LinkedIn", "source_url": "https://linkedin.com/jobs/4", "days_ago": 22, "deadline_days": 1},
    {"title": "Digital Marketing Specialist", "company": "BrandWave", "location": "Dubai, UAE", "location_type": "hybrid", "industry": "marketing", "experience_level": "entry", "description": "BrandWave is hiring a creative digital marketer to manage social media campaigns, SEO optimization, and content strategy for our portfolio of MENA brands.", "tags": ["SEO", "Social Media", "Google Ads"], "source": "Bayt", "source_url": "https://bayt.com/jobs/5", "days_ago": 11},
    {"title": "Registered Nurse", "company": "MedCare Plus", "location": "Jeddah, KSA", "location_type": "onsite", "industry": "healthcare", "experience_level": "mid", "description": "MedCare Plus is expanding its clinical team. We need experienced registered nurses for our digital health clinics. You'll provide patient care while leveraging our telemedicine platform.", "tags": ["Patient Care", "Telemedicine", "Clinical"], "salary_min": 12000, "salary_max": 18000, "salary_currency": "SAR", "source": "GulfTalent", "source_url": "https://gulftalent.com/jobs/6", "days_ago": 20, "deadline_days": 8},
    {"title": "Curriculum Developer", "company": "EduSpark", "location": "Remote", "location_type": "remote", "industry": "education", "experience_level": "mid", "description": "EduSpark needs a curriculum developer to design Arabic-first STEM courses for K-12 students. You'll work with subject matter experts, create interactive content, and align materials with regional education standards.", "tags": ["Curriculum Design", "Arabic", "STEM", "E-Learning"], "salary_min": 5000, "salary_max": 8000, "salary_currency": "USD", "source": "LinkedIn", "source_url": "https://linkedin.com/jobs/7", "days_ago": 16},
    {"title": "Civil Engineer", "company": "BuildRight", "location": "Doha, Qatar", "location_type": "onsite", "industry": "engineering", "experience_level": "senior", "description": "BuildRight is hiring senior civil engineers for our landmark projects in Qatar. You'll oversee structural design, coordinate with contractors, and ensure compliance with local building codes.", "tags": ["Structural Design", "AutoCAD", "Project Management"], "salary_min": 20000, "salary_max": 35000, "salary_currency": "QAR", "source": "GulfTalent", "source_url": "https://gulftalent.com/jobs/8", "days_ago": 24, "deadline_days": 4},
    {"title": "Sales Executive", "company": "SalesForce Arabia", "location": "Dubai, UAE", "location_type": "hybrid", "industry": "sales", "experience_level": "mid", "description": "SalesForce Arabia seeks a driven sales executive to expand our B2B client base across GCC. You'll manage the full sales cycle, from prospecting to closing. CRM experience and Arabic fluency required.", "tags": ["B2B Sales", "CRM", "Arabic"], "salary_min": 10000, "salary_max": 15000, "salary_currency": "AED", "source": "Bayt", "source_url": "https://bayt.com/jobs/9", "days_ago": 11, "deadline_days": 18},
    {"title": "Product Manager", "company": "TechNova", "location": "Remote", "location_type": "remote", "industry": "technology", "experience_level": "senior", "description": "Lead product strategy for TechNova's AI analytics suite. Define roadmaps, prioritize features, run sprints, and work cross-functionally with engineering, design, and sales. 5+ years PM experience required.", "tags": ["Product Strategy", "Agile", "AI/ML"], "salary_min": 12000, "salary_max": 20000, "salary_currency": "USD", "source": "LinkedIn", "source_url": "https://linkedin.com/jobs/10", "days_ago": 18},
    {"title": "Mobile Developer (Flutter)", "company": "FinEdge", "location": "Cairo, Egypt", "location_type": "hybrid", "industry": "technology", "experience_level": "mid", "description": "Build cross-platform mobile apps for FinEdge's payment platform. You'll implement new features, optimize performance, and ensure seamless UX across iOS and Android using Flutter.", "tags": ["Flutter", "Dart", "Mobile", "Firebase"], "salary_min": 20000, "salary_max": 35000, "salary_currency": "EGP", "source": "Wuzzuf", "source_url": "https://wuzzuf.net/jobs/11", "days_ago": 14},
    {"title": "Graphic Designer", "company": "BrandWave", "location": "Beirut, Lebanon", "location_type": "onsite", "industry": "design", "experience_level": "entry", "description": "BrandWave's Beirut studio needs a creative graphic designer. You'll create visual assets for digital campaigns, brand identities, and print materials. Proficiency in Adobe Creative Suite required.", "tags": ["Adobe Illustrator", "Photoshop", "Branding"], "source": "Bayt", "source_url": "https://bayt.com/jobs/12", "days_ago": 15, "deadline_days": 12},
    {"title": "DevOps Engineer", "company": "TechNova", "location": "Dubai, UAE", "location_type": "onsite", "industry": "technology", "experience_level": "senior", "description": "Manage TechNova's cloud infrastructure on AWS. You'll implement CI/CD pipelines, container orchestration with Kubernetes, monitoring, and incident response.", "tags": ["AWS", "Kubernetes", "Docker", "CI/CD"], "salary_min": 15000, "salary_max": 25000, "salary_currency": "AED", "source": "LinkedIn", "source_url": "https://linkedin.com/jobs/13", "days_ago": 27, "deadline_days": 3},
    {"title": "Financial Analyst", "company": "FinEdge", "location": "Riyadh, KSA", "location_type": "onsite", "industry": "finance", "experience_level": "mid", "description": "Support FinEdge's strategic planning with financial modeling, forecasting, and market analysis. CFA Level 1+ preferred. You'll work closely with the CFO and investor relations team.", "tags": ["Financial Modeling", "Excel", "CFA"], "salary_min": 15000, "salary_max": 22000, "salary_currency": "SAR", "source": "GulfTalent", "source_url": "https://gulftalent.com/jobs/14", "days_ago": 19},
    {"title": "Content Writer (Arabic)", "company": "BrandWave", "location": "Remote", "location_type": "remote", "industry": "marketing", "experience_level": "entry", "description": "Write engaging Arabic content for blogs, social media, and email campaigns. You'll collaborate with the marketing team to create SEO-optimized content that resonates with MENA audiences.", "tags": ["Arabic Content", "SEO", "Copywriting"], "salary_min": 3000, "salary_max": 5000, "salary_currency": "USD", "source": "Wuzzuf", "source_url": "https://wuzzuf.net/jobs/15", "days_ago": 11},
    {"title": "QA Engineer", "company": "TechNova", "location": "Amman, Jordan", "location_type": "hybrid", "industry": "technology", "experience_level": "mid", "description": "Ensure quality across TechNova's product suite. Write automated tests, perform regression testing, and work with developers to identify and resolve bugs. Experience with Cypress or Playwright preferred.", "tags": ["Cypress", "Playwright", "Automation", "Testing"], "salary_min": 1200, "salary_max": 2000, "salary_currency": "JOD", "source": "Bayt", "source_url": "https://bayt.com/jobs/16", "days_ago": 16, "deadline_days": 10},
    {"title": "HR Coordinator", "company": "BuildRight", "location": "Abu Dhabi, UAE", "location_type": "onsite", "industry": "engineering", "experience_level": "entry", "description": "Support BuildRight's HR department with recruitment coordination, onboarding, and employee engagement initiatives. Great entry point into HR for organized, people-oriented graduates.", "tags": ["Recruitment", "Onboarding", "HRIS"], "source": "GulfTalent", "source_url": "https://gulftalent.com/jobs/17", "days_ago": 22},
    {"title": "Machine Learning Engineer", "company": "TechNova", "location": "Remote", "location_type": "remote", "industry": "technology", "experience_level": "lead", "description": "Lead ML initiatives at TechNova. Design and deploy production ML models, mentor junior engineers, and collaborate with product on AI-powered features. PhD or equivalent experience preferred.", "tags": ["Python", "TensorFlow", "MLOps", "NLP"], "salary_min": 15000, "salary_max": 25000, "salary_currency": "USD", "source": "LinkedIn", "source_url": "https://linkedin.com/jobs/18", "days_ago": 20},
    {"title": "Pharmacist", "company": "MedCare Plus", "location": "Kuwait City, Kuwait", "location_type": "onsite", "industry": "healthcare", "experience_level": "mid", "description": "MedCare Plus is looking for licensed pharmacists for our e-pharmacy division. You'll verify prescriptions, provide patient consultations, and manage inventory through our digital platform.", "tags": ["Pharmacy", "Patient Care", "Inventory"], "salary_min": 800, "salary_max": 1200, "salary_currency": "KWD", "source": "Bayt", "source_url": "https://bayt.com/jobs/19", "days_ago": 17, "deadline_days": 8},
    {"title": "Account Manager", "company": "SalesForce Arabia", "location": "Cairo, Egypt", "location_type": "hybrid", "industry": "sales", "experience_level": "mid", "description": "Manage key client accounts for SalesForce Arabia in the Egyptian market. You'll ensure client satisfaction, identify upsell opportunities, and coordinate with product teams on custom solutions.", "tags": ["Account Management", "Client Relations", "SaaS"], "salary_min": 18000, "salary_max": 30000, "salary_currency": "EGP", "source": "Wuzzuf", "source_url": "https://wuzzuf.net/jobs/20", "days_ago": 14},
]

FEATURE_FLAGS = [
    {"key": "smart_search", "label": "Smart Search", "description": "AI-powered search suggestions", "is_enabled": True},
    {"key": "salary_filter", "label": "Salary Filter", "description": "Filter jobs by salary range", "is_enabled": False},
    {"key": "google_oauth", "label": "Google OAuth", "description": "Enable Google social login", "is_enabled": True},
    {"key": "email_alerts", "label": "Email Alerts", "description": "Send email notifications for job alerts", "is_enabled": True},
    {"key": "csv_import", "label": "CSV Import", "description": "Allow CSV bulk import of jobs", "is_enabled": False},
]


class Command(BaseCommand):
    help = "Seed the database with initial demo data"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Clear existing data before seeding")

    def handle(self, *args, **options):
        from apps.accounts.models import User
        from apps.jobs.models import Company, Source, Tag, Job, JobTag
        from apps.core.models import FeatureFlag
        from apps.users.models import SavedJob, Alert, Notification

        if options["reset"]:
            self.stdout.write("🗑  Clearing existing data...")
            Job.objects.all().delete()
            Company.objects.all().delete()
            Source.objects.all().delete()
            Tag.objects.all().delete()
            FeatureFlag.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        # ── Superuser ────────────────────────────────────────────────────
        # ── Superuser ────────────────────────────────────────────────────
        superadmin_email = "admin@gmail.com"
        if not User.objects.filter(email=superadmin_email).exists():
            User.objects.create_superuser(
                email=superadmin_email,
                password="User@123",
                first_name="Super",
                last_name="Admin",
                role="admin",
            )
            self.stdout.write(self.style.SUCCESS(f"✅ Superuser created: {superadmin_email} / SuperAdmin@2025!"))
        else:
            self.stdout.write(f"⚠️  Superuser already exists: {superadmin_email}")

        admin_email = "manager@gmail.com"
        if not User.objects.filter(email=admin_email).exists():
            admin = User.objects.create_user(
                email=admin_email,
                password="User@123",
                first_name="Admin",
                last_name="User",
                role="admin",
                is_staff=True,
            )
            self.stdout.write(self.style.SUCCESS(f"✅ Admin created: {admin_email} / Admin@2025!"))
        else:
            admin = User.objects.get(email=admin_email)
            self.stdout.write(f"⚠️  Admin already exists: {admin_email}")

        # ── Demo user ─────────────────────────────────────────────────────
        demo_email = "user@gmail.com"
        if not User.objects.filter(email=demo_email).exists():
            demo_user = User.objects.create_user(
                email=demo_email,
                password="User@2025!",
                first_name="Test",
                last_name="User",
                role="user",
            )
            self.stdout.write(self.style.SUCCESS(f"✅ Test user created: {demo_email} / User@2025!"))
        else:
            demo_user = User.objects.get(email=demo_email)
            self.stdout.write(f"⚠️  Test user already exists: {demo_email}")

        # ── Companies ─────────────────────────────────────────────────────
        company_map = {}
        for c in COMPANIES:
            slug = slugify(c["name"])
            obj, created = Company.objects.get_or_create(
                slug=slug,
                defaults={**c, "slug": slug},
            )
            company_map[c["name"]] = obj
        self.stdout.write(self.style.SUCCESS(f"✅ {len(COMPANIES)} companies seeded"))

        # ── Sources ───────────────────────────────────────────────────────
        source_map = {}
        for s in SOURCES:
            obj, created = Source.objects.get_or_create(
                slug=s["slug"],
                defaults=s,
            )
            source_map[s["name"]] = obj
        self.stdout.write(self.style.SUCCESS(f"✅ {len(SOURCES)} sources seeded"))

        # ── Tags ──────────────────────────────────────────────────────────
        tag_map = {}
        for name, category in TAGS:
            slug = slugify(name)
            obj, created = Tag.objects.get_or_create(
                name=name,
                defaults={"slug": slug, "category": category},
            )
            tag_map[name] = obj
        self.stdout.write(self.style.SUCCESS(f"✅ {len(TAGS)} tags seeded"))

        # ── Jobs ──────────────────────────────────────────────────────────
        today = date.today()
        jobs_created = 0
        first_job = None
        second_job = None

        for i, jdata in enumerate(JOBS):
            company = company_map[jdata["company"]]
            source = source_map.get(jdata["source"])
            posted_at = today - timedelta(days=jdata["days_ago"])
            deadline = None
            if "deadline_days" in jdata:
                deadline = today + timedelta(days=jdata["deadline_days"])

            base_slug = slugify(jdata["title"])
            slug = base_slug
            counter = 1
            while Job.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            job, created = Job.objects.get_or_create(
                source_url=jdata["source_url"],
                defaults={
                    "title": jdata["title"],
                    "slug": slug,
                    "company": company,
                    "location": jdata["location"],
                    "location_type": jdata["location_type"],
                    "industry": jdata["industry"],
                    "experience_level": jdata["experience_level"],
                    "description": jdata["description"],
                    "salary_min": jdata.get("salary_min"),
                    "salary_max": jdata.get("salary_max"),
                    "salary_currency": jdata.get("salary_currency", "USD"),
                    "source": source,
                    "posted_at": posted_at,
                    "deadline": deadline,
                    "status": "active",
                },
            )

            if created:
                jobs_created += 1
                for tag_name in jdata.get("tags", []):
                    if tag_name in tag_map:
                        JobTag.objects.get_or_create(job=job, tag=tag_map[tag_name])

            if i == 0:
                first_job = job
            if i == 1:
                second_job = job

        self.stdout.write(self.style.SUCCESS(f"✅ {jobs_created} jobs seeded"))

        # ── Feature Flags ─────────────────────────────────────────────────
        for ff in FEATURE_FLAGS:
            FeatureFlag.objects.get_or_create(
                key=ff["key"],
                defaults=ff,
            )
        self.stdout.write(self.style.SUCCESS(f"✅ {len(FEATURE_FLAGS)} feature flags seeded"))

        # ── Demo saved jobs + alerts + notifications ───────────────────────
        if first_job:
            SavedJob.objects.get_or_create(user=demo_user, job=first_job)
        if second_job:
            SavedJob.objects.get_or_create(user=demo_user, job=second_job)

        Alert.objects.get_or_create(
            user=demo_user,
            keyword="React",
            defaults={"work_mode": "remote", "frequency": "daily", "is_active": True},
        )
        Alert.objects.get_or_create(
            user=demo_user,
            keyword="Python",
            defaults={"industry": "technology", "frequency": "weekly", "is_active": True},
        )

        Notification.objects.get_or_create(
            user=demo_user,
            title="Welcome to USAM Career Compass!",
            defaults={
                "body": "Start exploring jobs tailored for the MENA region.",
                "type": "welcome",
                "is_read": False,
            },
        )

        self.stdout.write(self.style.SUCCESS("✅ Demo user data seeded (saved jobs, alerts, notifications)"))
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("🚀 Seed complete!"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"  Superadmin: superadmin@gmail.com  /  SuperAdmin@2025!")
        self.stdout.write(f"  Admin:      admin@gmail.com        /  Admin@2025!")
        self.stdout.write(f"  User:       user@gmail.com         /  User@2025!")
        self.stdout.write(f"  Admin UI:  http://localhost:8000/admin/")
        self.stdout.write(f"  API Docs:  http://localhost:8000/api/docs/")
