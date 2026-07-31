"""
Skill Extraction Pipeline Stage

Extracts skills from job descriptions using AI (Haiku/Claude) and maps them
to the ESCO taxonomy.
"""
import hashlib
import json
import logging
from typing import List, Dict, Optional, Tuple
from django.core.cache import cache
from django.db import transaction

from apps.jobs.models import Job
from apps.skills.models import Skill, JobSkill

logger = logging.getLogger(__name__)


class SkillExtractor:
    """
    Extracts skills from job descriptions and maps them to ESCO taxonomy.
    
    Features:
    - Uses Haiku/Claude AI for skill extraction
    - Caches extractions by job description hash
    - Maps extracted skills to ESCO taxonomy
    - Stores results in jobs_job_skills table
    """
    
    # Cache timeout: 7 days
    CACHE_TIMEOUT = 60 * 60 * 24 * 7
    
    # Maximum skills to extract per job
    MAX_SKILLS = 20
    
    def __init__(self):
        self._bedrock = None
    
    @property
    def bedrock(self):
        """Lazy load Bedrock service"""
        if self._bedrock is None:
            try:
                from ai.bedrock import bedrock_service
                self._bedrock = bedrock_service
            except ImportError:
                self._bedrock = None
        return self._bedrock
    
    def extract_skills(self, job: Job) -> List[Dict]:
        """
        Extract skills from a job description.
        
        Args:
            job: Job instance
            
        Returns:
            List of skill dictionaries with ESCO mapping
        """
        description = job.description or ''
        
        if not description:
            logger.warning(f"No description for job {job.id}")
            return []
        
        # Generate cache key from description hash
        cache_key = self._get_cache_key(description)
        
        # Try to get from cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for job {job.id}")
            return cached_result
        
        # Extract skills using AI
        extracted_skills = self._extract_skills_from_description(description)
        
        # Map to ESCO taxonomy
        mapped_skills = self._map_to_esco(extracted_skills)
        
        # Cache the result
        cache.set(cache_key, mapped_skills, self.CACHE_TIMEOUT)
        
        return mapped_skills
    
    def _get_cache_key(self, description: str) -> str:
        """Generate cache key from description hash"""
        description_hash = hashlib.md5(description.encode()).hexdigest()
        return f"skill_extraction:{description_hash}"
    
    def _extract_skills_from_description(self, description: str) -> List[Dict]:
        """
        Extract skills from job description using AI.
        
        Args:
            description: Job description text
            
        Returns:
            List of extracted skills with metadata
        """
        if not self.bedrock or not self.bedrock.is_available:
            # Fallback: basic keyword matching
            return self._fallback_extraction(description)
        
        system_prompt = """You are an expert job analysis AI. Extract technical and soft skills from job descriptions.

Return a JSON array of skills with the following structure:
[
  {
    "skill": "Python",
    "category": "technical",
    "level": "intermediate",
    "years_required": 3,
    "description": "Python programming language"
  }
]

Skill categories:
- technical: Programming languages, frameworks, tools
- soft: Communication, leadership, problem-solving
- language: Natural languages
- tool: Specific software/tools
- framework: Web frameworks, libraries
- methodology: Agile, Scrum, etc.

Important:
- Extract both hard and soft skills
- Include required experience level
- Be specific (e.g., "Python" not just "programming")
- Limit to most important skills (max 20)
- Return ONLY valid JSON, no additional text
"""
        
        prompt = f"""Extract skills from this job description:

{description[:8000]}  # Limit description length

Return ONLY the JSON array, no additional text."""
        
        try:
            response = self.bedrock.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=4000,
                temperature=0.2
            )
            
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            json_str = response[json_start:json_end]
            
            skills = json.loads(json_str)
            return skills[:self.MAX_SKILLS]  # Limit to max skills
            
        except Exception as e:
            logger.error(f"Error extracting skills: {e}")
            return self._fallback_extraction(description)
    
    def _fallback_extraction(self, description: str) -> List[Dict]:
        """
        Fallback skill extraction using keyword matching.
        
        Args:
            description: Job description text
            
        Returns:
            List of extracted skills
        """
        # Common skills database
        technical_skills = {
            'python': 'Python', 'java': 'Java', 'javascript': 'JavaScript',
            'typescript': 'TypeScript', 'c#': 'C#', 'c++': 'C++',
            'ruby': 'Ruby', 'php': 'PHP', 'go': 'Go', 'rust': 'Rust',
            'sql': 'SQL', 'postgresql': 'PostgreSQL', 'mysql': 'MySQL',
            'mongodb': 'MongoDB', 'redis': 'Redis', 'elasticsearch': 'Elasticsearch',
            'aws': 'AWS', 'azure': 'Azure', 'gcp': 'GCP', 'docker': 'Docker',
            'kubernetes': 'Kubernetes', 'terraform': 'Terraform', 'ansible': 'Ansible',
            'react': 'React', 'vue': 'Vue.js', 'angular': 'Angular', 'node.js': 'Node.js',
            'express': 'Express', 'django': 'Django', 'flask': 'Flask', 'spring': 'Spring',
            'tensorflow': 'TensorFlow', 'pytorch': 'PyTorch', 'scikit-learn': 'scikit-learn',
            'git': 'Git', 'linux': 'Linux', 'bash': 'Bash', 'shell': 'Shell',
            'html': 'HTML', 'css': 'CSS', 'sass': 'Sass', 'less': 'Less',
            'webpack': 'Webpack', 'babel': 'Babel', 'jest': 'Jest', 'cypress': 'Cypress',
            'figma': 'Figma', 'adobe': 'Adobe', 'photoshop': 'Photoshop',
        }
        
        soft_skills = {
            'communication': 'Communication', 'teamwork': 'Teamwork', 'leadership': 'Leadership',
            'problem-solving': 'Problem Solving', 'critical thinking': 'Critical Thinking',
            'time management': 'Time Management', 'adaptability': 'Adaptability',
            'creativity': 'Creativity', 'collaboration': 'Collaboration',
            'conflict resolution': 'Conflict Resolution', 'empathy': 'Empathy',
            'negotiation': 'Negotiation', 'presentation': 'Presentation',
        }
        
        description_lower = description.lower()
        extracted = []
        
        # Match technical skills
        for keyword, skill_name in technical_skills.items():
            if keyword in description_lower:
                extracted.append({
                    'skill': skill_name,
                    'category': 'technical',
                    'level': 'intermediate',
                    'years_required': 2,
                    'description': f'{skill_name} skill'
                })
        
        # Match soft skills
        for keyword, skill_name in soft_skills.items():
            if keyword in description_lower:
                extracted.append({
                    'skill': skill_name,
                    'category': 'soft',
                    'level': 'intermediate',
                    'years_required': 1,
                    'description': f'{skill_name} skill'
                })
        
        return extracted[:self.MAX_SKILLS]
    
    def _map_to_esco(self, skills: List[Dict]) -> List[Dict]:
        """
        Map extracted skills to ESCO taxonomy.
        
        Args:
            skills: List of extracted skills
            
        Returns:
            List of skills with ESCO mapping
        """
        mapped_skills = []
        
        for skill_data in skills:
            skill_name = skill_data.get('skill', '')
            
            # Try to find matching ESCO skill
            esco_skill = self._find_esco_skill(skill_name)
            
            mapped_skill = {
                **skill_data,
                'esco_uri': esco_skill.esco_uri if esco_skill else None,
                'esco_label': esco_skill.name if esco_skill else None,
            }
            
            mapped_skills.append(mapped_skill)
        
        return mapped_skills
    
    def _find_esco_skill(self, skill_name: str) -> Optional[Skill]:
        """
        Find matching ESCO skill for a given skill name.
        
        Args:
            skill_name: Skill name to match
            
        Returns:
            Matching Skill object or None
        """
        # Try exact match first
        try:
            return Skill.objects.get(name__iexact=skill_name)
        except Skill.DoesNotExist:
            pass
        
        # Try partial match
        try:
            return Skill.objects.filter(name__icontains=skill_name).first()
        except Skill.DoesNotExist:
            pass
        
        return None
    
    def store_skills(self, job: Job, skills: List[Dict]) -> int:
        """
        Store extracted skills in jobs_job_skills table.
        
        Args:
            job: Job instance
            skills: List of skill dictionaries
            
        Returns:
            Count of skills stored
        """
        stored_count = 0
        
        with transaction.atomic():
            for skill_data in skills:
                # Get or create the skill in the skills_skill table
                skill_name = skill_data.get('skill', '')
                category = skill_data.get('category', 'technical')
                
                skill, created = Skill.objects.get_or_create(
                    name=skill_name,
                    defaults={
                        'type': category,
                        'esco_uri': skill_data.get('esco_uri', ''),
                        'esco_label': skill_data.get('esco_label', ''),
                    }
                )
                
                # Create job-skill relationship
                JobSkill.objects.get_or_create(
                    job=job,
                    skill=skill,
                    defaults={
                        'importance': 3.0,  # Default importance
                        'level': skill_data.get('level', 'intermediate'),
                    }
                )
                
                stored_count += 1
        
        return stored_count
    
    def process_job(self, job: Job) -> Dict:
        """
        Full skill extraction and storage pipeline for a job.
        
        Args:
            job: Job instance
            
        Returns:
            Dict with extraction results
        """
        try:
            # Extract skills
            skills = self.extract_skills(job)
            
            if not skills:
                return {
                    'status': 'no_skills',
                    'message': 'No skills could be extracted',
                    'count': 0,
                }
            
            # Store skills
            stored_count = self.store_skills(job, skills)
            
            return {
                'status': 'success',
                'count': stored_count,
                'skills': skills[:5],  # Return first 5 skills as sample
            }
            
        except Exception as e:
            logger.error(f"Error processing job {job.id}: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'count': 0,
            }


# Singleton instance
skill_extractor = SkillExtractor()


def extract_skills_for_job(job_id: int) -> Dict:
    """
    Convenience function to extract skills for a job.
    
    Args:
        job_id: Job ID
        
    Returns:
        Dict with extraction results
    """
    try:
        from apps.jobs.models import Job
        job = Job.objects.get(id=job_id)
        return skill_extractor.process_job(job)
    except Job.DoesNotExist:
        return {'status': 'error', 'message': 'Job not found', 'count': 0}