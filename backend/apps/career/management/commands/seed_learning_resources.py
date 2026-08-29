"""Seed the LearningResource catalog with curated entries."""
from django.core.management.base import BaseCommand
from apps.career.models import LearningResource


RESOURCES = [
    {"title": "Python for Everybody Specialization", "url": "https://www.coursera.org/specializations/python", "platform": "coursera", "skill_tags": ["python", "programming"], "difficulty_level": "beginner", "duration_hours": 80, "is_free": False, "rating": 4.8, "description": "Learn to program and analyze data with Python."},
    {"title": "CS50's Introduction to Computer Science", "url": "https://www.edx.org/course/cs50s-introduction-to-computer-science", "platform": "edx", "skill_tags": ["computer science", "c", "python", "algorithms"], "difficulty_level": "beginner", "duration_hours": 100, "is_free": True, "rating": 4.9, "description": "Harvard's introduction to computer science and programming."},
    {"title": "The Complete JavaScript Course 2024", "url": "https://www.udemy.com/course/the-complete-javascript-course/", "platform": "udemy", "skill_tags": ["javascript", "web development"], "difficulty_level": "beginner", "duration_hours": 69, "is_free": False, "rating": 4.7, "description": "Master JavaScript with projects, challenges, and theory."},
    {"title": "React - The Complete Guide", "url": "https://www.udemy.com/course/react-the-complete-guide-incl-redux/", "platform": "udemy", "skill_tags": ["react", "javascript", "frontend"], "difficulty_level": "intermediate", "duration_hours": 48, "is_free": False, "rating": 4.6, "description": "Dive in and learn React.js from scratch with hooks, Redux, and Next.js."},
    {"title": "Django for Everybody Specialization", "url": "https://www.coursera.org/specializations/django", "platform": "coursera", "skill_tags": ["django", "python", "web development"], "difficulty_level": "intermediate", "duration_hours": 60, "is_free": False, "rating": 4.7, "description": "Build and deploy rich web applications using Django."},
    {"title": "SQL for Data Science", "url": "https://www.coursera.org/learn/sql-for-data-science", "platform": "coursera", "skill_tags": ["sql", "data science", "databases"], "difficulty_level": "beginner", "duration_hours": 16, "is_free": False, "rating": 4.6, "description": "Learn SQL fundamentals for data science applications."},
    {"title": "Machine Learning by Andrew Ng", "url": "https://www.coursera.org/learn/machine-learning", "platform": "coursera", "skill_tags": ["machine learning", "data science", "python"], "difficulty_level": "intermediate", "duration_hours": 60, "is_free": False, "rating": 4.9, "description": "Stanford's foundational machine learning course."},
    {"title": "Data Structures and Algorithms Specialization", "url": "https://www.coursera.org/specializations/data-structures-algorithms", "platform": "coursera", "skill_tags": ["algorithms", "data structures", "programming"], "difficulty_level": "intermediate", "duration_hours": 80, "is_free": False, "rating": 4.5, "description": "Master algorithmic programming techniques."},
    {"title": "AWS Cloud Practitioner Essentials", "url": "https://www.coursera.org/learn/aws-cloud-practitioner-essentials", "platform": "coursera", "skill_tags": ["aws", "cloud computing", "devops"], "difficulty_level": "beginner", "duration_hours": 12, "is_free": False, "rating": 4.7, "description": "Foundational understanding of AWS Cloud concepts."},
    {"title": "Docker Mastery", "url": "https://www.udemy.com/course/docker-mastery/", "platform": "udemy", "skill_tags": ["docker", "devops", "containers"], "difficulty_level": "intermediate", "duration_hours": 20, "is_free": False, "rating": 4.7, "description": "Build, compose, deploy, and manage Docker containers."},
    {"title": "TypeScript: The Complete Developer's Guide", "url": "https://www.udemy.com/course/typescript-the-complete-developers-guide/", "platform": "udemy", "skill_tags": ["typescript", "javascript", "frontend"], "difficulty_level": "intermediate", "duration_hours": 27, "is_free": False, "rating": 4.7, "description": "Master TypeScript by building real-world applications."},
    {"title": "Git & GitHub Crash Course", "url": "https://www.youtube.com/watch?v=RGOj5yH7evk", "platform": "youtube", "skill_tags": ["git", "github", "version control"], "difficulty_level": "beginner", "duration_hours": 1, "is_free": True, "rating": 4.8, "description": "Learn Git and GitHub basics in one video."},
    {"title": "Node.js, Express, MongoDB & More", "url": "https://www.udemy.com/course/nodejs-express-mongodb-bootcamp/", "platform": "udemy", "skill_tags": ["node.js", "express", "mongodb", "backend"], "difficulty_level": "intermediate", "duration_hours": 42, "is_free": False, "rating": 4.7, "description": "Master Node.js by building a real-world RESTful API."},
    {"title": "Kubernetes for the Absolute Beginners", "url": "https://www.udemy.com/course/learn-kubernetes/", "platform": "udemy", "skill_tags": ["kubernetes", "devops", "containers"], "difficulty_level": "beginner", "duration_hours": 5, "is_free": False, "rating": 4.6, "description": "Learn Kubernetes concepts and get hands-on practice."},
    {"title": "Deep Learning Specialization", "url": "https://www.coursera.org/specializations/deep-learning", "platform": "coursera", "skill_tags": ["deep learning", "machine learning", "python", "tensorflow"], "difficulty_level": "advanced", "duration_hours": 80, "is_free": False, "rating": 4.9, "description": "Master deep learning and build neural networks."},
    {"title": "System Design Interview Prep", "url": "https://www.youtube.com/c/SystemDesignInterview", "platform": "youtube", "skill_tags": ["system design", "architecture", "interviews"], "difficulty_level": "advanced", "duration_hours": 20, "is_free": True, "rating": 4.7, "description": "Prepare for system design interviews with real examples."},
    {"title": "Complete Python Developer in 2024", "url": "https://www.udemy.com/course/complete-python-developer-zero-to-mastery/", "platform": "udemy", "skill_tags": ["python", "web development", "automation"], "difficulty_level": "beginner", "duration_hours": 31, "is_free": False, "rating": 4.6, "description": "Become a Python developer with this zero to mastery course."},
    {"title": "PostgreSQL: The Complete Developer's Guide", "url": "https://www.udemy.com/course/sql-and-postgresql/", "platform": "udemy", "skill_tags": ["postgresql", "sql", "databases"], "difficulty_level": "intermediate", "duration_hours": 22, "is_free": False, "rating": 4.7, "description": "Master PostgreSQL for complex queries and database design."},
    {"title": "Agile with Atlassian Jira", "url": "https://www.coursera.org/learn/agile-atlassian-jira", "platform": "coursera", "skill_tags": ["agile", "scrum", "project management", "jira"], "difficulty_level": "beginner", "duration_hours": 8, "is_free": False, "rating": 4.5, "description": "Learn agile methodologies using Atlassian Jira."},
    {"title": "Cybersecurity Specialization", "url": "https://www.coursera.org/specializations/cyber-security", "platform": "coursera", "skill_tags": ["cybersecurity", "networking", "security"], "difficulty_level": "intermediate", "duration_hours": 80, "is_free": False, "rating": 4.5, "description": "Learn the fundamentals of cybersecurity from the University of Maryland."},
]


class Command(BaseCommand):
    help = "Seed the LearningResource catalog with curated entries"

    def handle(self, *args, **options):
        created_count = 0
        for entry in RESOURCES:
            _, created = LearningResource.objects.get_or_create(
                title=entry["title"],
                defaults=entry,
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Seeded {created_count} new learning resources ({len(RESOURCES)} total)")
        )
