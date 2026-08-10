"""
Management command: seed_skills

Populate skills database from a comprehensive predefined list + extraction
from job descriptions using keyword matching (no AI required).

Usage:
    python manage.py seed_skills
    python manage.py seed_skills --from-jobs  # Also extract from job descriptions
"""
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.skills.models import Skill

# Comprehensive skill taxonomy covering tech, business, and soft skills
SKILL_TAXONOMY = {
    "programming_languages": [
        "Python", "JavaScript", "TypeScript", "Java", "C#", "C++", "Go", "Rust",
        "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB", "Dart",
        "Objective-C", "Perl", "Haskell", "Elixir", "Clojure", "Lua",
        "Shell Scripting", "Bash", "PowerShell", "SQL", "HTML", "CSS",
    ],
    "web_frameworks": [
        "React", "Angular", "Vue.js", "Next.js", "Nuxt.js", "Svelte",
        "Django", "Flask", "FastAPI", "Express.js", "NestJS", "Spring Boot",
        "Ruby on Rails", "Laravel", "ASP.NET", "Blazor", "Remix", "Gatsby",
    ],
    "mobile": [
        "React Native", "Flutter", "iOS Development", "Android Development",
        "SwiftUI", "Jetpack Compose", "Xamarin", "Ionic",
    ],
    "databases": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "SQLite", "Oracle", "SQL Server", "DynamoDB", "Cassandra",
        "Neo4j", "InfluxDB", "Supabase", "Firebase", "CouchDB",
    ],
    "cloud_devops": [
        "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes",
        "Terraform", "Ansible", "Jenkins", "GitHub Actions", "GitLab CI",
        "CircleCI", "ArgoCD", "Helm", "Prometheus", "Grafana",
        "CloudFormation", "Pulumi", "Nginx", "Apache", "Linux Administration",
    ],
    "data_ml": [
        "Machine Learning", "Deep Learning", "Natural Language Processing",
        "Computer Vision", "TensorFlow", "PyTorch", "Scikit-learn",
        "Pandas", "NumPy", "Apache Spark", "Hadoop", "Airflow",
        "Data Engineering", "Data Analysis", "Data Visualization",
        "ETL", "Data Warehousing", "Power BI", "Tableau", "Looker",
        "Statistical Analysis", "A/B Testing", "Feature Engineering",
    ],
    "ai_llm": [
        "Large Language Models", "Prompt Engineering", "RAG",
        "Vector Databases", "Embeddings", "Fine-tuning", "LangChain",
        "OpenAI API", "Hugging Face", "Generative AI", "ChatGPT",
        "Claude API", "Stable Diffusion", "MLOps",
    ],
    "security": [
        "Cybersecurity", "Penetration Testing", "OWASP", "Encryption",
        "Identity Management", "OAuth", "JWT", "SSL/TLS",
        "Network Security", "Cloud Security", "SOC", "SIEM",
        "Vulnerability Assessment", "Compliance", "GDPR",
    ],
    "design_ux": [
        "UI Design", "UX Design", "Figma", "Adobe XD", "Sketch",
        "Wireframing", "Prototyping", "User Research", "Usability Testing",
        "Design Systems", "Responsive Design", "Accessibility",
        "Adobe Photoshop", "Adobe Illustrator", "Motion Design",
    ],
    "project_management": [
        "Agile", "Scrum", "Kanban", "Jira", "Confluence",
        "Project Management", "Product Management", "Stakeholder Management",
        "Risk Management", "Budget Management", "Resource Planning",
        "Sprint Planning", "Roadmapping", "OKRs",
    ],
    "soft_skills": [
        "Communication", "Leadership", "Teamwork", "Problem Solving",
        "Critical Thinking", "Time Management", "Adaptability",
        "Presentation Skills", "Mentoring", "Negotiation",
        "Conflict Resolution", "Decision Making", "Creativity",
    ],
    "business": [
        "Business Analysis", "Requirements Gathering", "Process Improvement",
        "Digital Marketing", "SEO", "Content Strategy", "Social Media Marketing",
        "Sales", "Customer Success", "Account Management",
        "Financial Analysis", "Strategic Planning", "Market Research",
    ],
    "qa_testing": [
        "Unit Testing", "Integration Testing", "End-to-End Testing",
        "Selenium", "Cypress", "Jest", "Pytest", "JUnit",
        "Performance Testing", "Load Testing", "API Testing",
        "Test Automation", "Manual Testing", "QA Strategy",
    ],
    "networking_infra": [
        "TCP/IP", "DNS", "Load Balancing", "CDN", "VPN",
        "Microservices", "REST API", "GraphQL", "gRPC", "WebSockets",
        "Message Queues", "RabbitMQ", "Kafka", "MQTT",
    ],
    "version_control": [
        "Git", "GitHub", "GitLab", "Bitbucket", "SVN",
        "Code Review", "Branch Management", "CI/CD",
    ],
    "arabic_regional": [
        "Arabic Language", "Arabic Content Writing", "RTL Design",
        "MENA Market Knowledge", "Bilingual Communication",
        "Cross-cultural Communication",
    ],
}


class Command(BaseCommand):
    help = "Seed skills database with comprehensive taxonomy and extract from jobs"

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-jobs',
            action='store_true',
            help='Also extract skills from job descriptions via keyword matching'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without saving'
        )

    def handle(self, *args, **options):
        from_jobs = options['from_jobs']
        dry_run = options['dry_run']

        all_skills = {}

        # Step 1: Add taxonomy skills
        self.stdout.write("Step 1: Loading skill taxonomy...")
        for category, skills in SKILL_TAXONOMY.items():
            for skill_name in skills:
                all_skills[skill_name.lower()] = {
                    'name': skill_name,
                    'category': category,
                    'skill_type': 'technical' if category not in ['soft_skills', 'business'] else 'soft',
                }

        self.stdout.write(f"  Taxonomy: {len(all_skills)} skills")

        # Step 2: Extract from job descriptions
        if from_jobs:
            self.stdout.write("Step 2: Extracting skills from job descriptions...")
            extracted = self._extract_from_jobs()
            for skill_name, category in extracted.items():
                key = skill_name.lower()
                if key not in all_skills:
                    all_skills[key] = {
                        'name': skill_name,
                        'category': category,
                        'skill_type': 'technical',
                    }
            self.stdout.write(f"  Extracted {len(extracted)} additional skills from jobs")

        self.stdout.write(f"\nTotal unique skills: {len(all_skills)}")

        if dry_run:
            self.stdout.write("\n=== DRY RUN ===")
            for cat in SKILL_TAXONOMY:
                cat_skills = [s for s in all_skills.values() if s['category'] == cat]
                self.stdout.write(f"  {cat}: {len(cat_skills)} skills")
            return

        # Save to database
        created = 0
        existing = 0
        with transaction.atomic():
            for skill_data in all_skills.values():
                obj, is_new = Skill.objects.get_or_create(
                    name=skill_data['name'],
                    defaults={
                        'description': f"{skill_data['name']} - {skill_data['category'].replace('_', ' ')}",
                        'type': skill_data['skill_type'],
                        'category': 'skill',
                        'esco_uri': f"http://data.europa.eu/esco/skill/seed-{skill_data['name'].lower().replace(' ', '-').replace('.', '').replace('/', '-')}",
                    }
                )
                if is_new:
                    created += 1
                else:
                    existing += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Done! Created {created} new skills, {existing} already existed"
            )
        )
        self.stdout.write(f"Total skills in database: {Skill.objects.count()}")

    def _extract_from_jobs(self):
        """Extract skills from job descriptions using keyword matching."""
        from apps.jobs.models import Job

        jobs = Job.objects.filter(status='active').exclude(description='')[:200]
        extracted = {}

        # Build lookup patterns from taxonomy
        all_known = set()
        for skills in SKILL_TAXONOMY.values():
            for s in skills:
                all_known.add(s.lower())

        # Common tech terms to look for in descriptions
        tech_patterns = [
            (r'\b(Node\.?js)\b', 'Node.js', 'web_frameworks'),
            (r'\b(Express\.?js)\b', 'Express.js', 'web_frameworks'),
            (r'\b(Vue\.?js)\b', 'Vue.js', 'web_frameworks'),
            (r'\b(Next\.?js)\b', 'Next.js', 'web_frameworks'),
            (r'\b(React\s*Native)\b', 'React Native', 'mobile'),
            (r'\b(AWS\s+Lambda)\b', 'AWS Lambda', 'cloud_devops'),
            (r'\b(Amazon\s+S3)\b', 'Amazon S3', 'cloud_devops'),
            (r'\b(Amazon\s+EC2)\b', 'Amazon EC2', 'cloud_devops'),
            (r'\b(Google\s+Cloud)\b', 'Google Cloud', 'cloud_devops'),
            (r'\b(Machine\s+Learning)\b', 'Machine Learning', 'data_ml'),
            (r'\b(Deep\s+Learning)\b', 'Deep Learning', 'data_ml'),
            (r'\b(Natural\s+Language\s+Processing|NLP)\b', 'Natural Language Processing', 'data_ml'),
            (r'\b(CI/CD|CI\s*/\s*CD)\b', 'CI/CD', 'version_control'),
            (r'\b(REST\s*API|RESTful)\b', 'REST API', 'networking_infra'),
            (r'\b(GraphQL)\b', 'GraphQL', 'networking_infra'),
            (r'\b(Microservices)\b', 'Microservices', 'networking_infra'),
            (r'\b(Agile|Scrum)\b', 'Agile', 'project_management'),
            (r'\b(Power\s*BI)\b', 'Power BI', 'data_ml'),
            (r'\b(Data\s+Science)\b', 'Data Science', 'data_ml'),
            (r'\b(Big\s+Data)\b', 'Big Data', 'data_ml'),
            (r'\b(DevOps)\b', 'DevOps', 'cloud_devops'),
            (r'\b(SaaS)\b', 'SaaS', 'business'),
            (r'\b(B2B)\b', 'B2B Sales', 'business'),
            (r'\b(CRM)\b', 'CRM', 'business'),
            (r'\b(ERP)\b', 'ERP', 'business'),
            (r'\b(SAP)\b', 'SAP', 'business'),
            (r'\b(Salesforce)\b', 'Salesforce', 'business'),
            (r'\b(Blockchain)\b', 'Blockchain', 'programming_languages'),
            (r'\b(Solidity)\b', 'Solidity', 'programming_languages'),
            (r'\b(Web3)\b', 'Web3', 'programming_languages'),
            (r'\b(Three\.?js)\b', 'Three.js', 'web_frameworks'),
            (r'\b(Tailwind\s*CSS)\b', 'Tailwind CSS', 'web_frameworks'),
            (r'\b(Bootstrap)\b', 'Bootstrap', 'web_frameworks'),
            (r'\b(Material\s*UI|MUI)\b', 'Material UI', 'web_frameworks'),
            (r'\b(Storybook)\b', 'Storybook', 'web_frameworks'),
            (r'\b(Webpack)\b', 'Webpack', 'web_frameworks'),
            (r'\b(Vite)\b', 'Vite', 'web_frameworks'),
            (r'\b(Redis)\b', 'Redis', 'databases'),
            (r'\b(RabbitMQ)\b', 'RabbitMQ', 'networking_infra'),
            (r'\b(Kafka)\b', 'Kafka', 'networking_infra'),
            (r'\b(Celery)\b', 'Celery', 'cloud_devops'),
        ]

        for job in jobs:
            text = f"{job.title} {job.description}".lower()

            # Check regex patterns
            for pattern, name, category in tech_patterns:
                if re.search(pattern, f"{job.title} {job.description}", re.IGNORECASE):
                    if name.lower() not in all_known:
                        extracted[name] = category

        return extracted
