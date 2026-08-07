"""
Natural Language Search Parser

This module provides natural language processing for job search queries.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of search queries."""
    JOB_SEARCH = "job_search"
    SKILL_SEARCH = "skill_search"
    COMPANY_SEARCH = "company_search"
    SALARY_SEARCH = "salary_search"
    LOCATION_SEARCH = "location_search"
    GENERAL = "general"


@dataclass
class ParsedQuery:
    """Parsed search query with extracted components."""
    original_query: str
    query_type: QueryType = QueryType.GENERAL
    keywords: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    companies: List[str] = field(default_factory=list)
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    job_types: List[str] = field(default_factory=list)
    experience_levels: List[str] = field(default_factory=list)
    remote_options: List[str] = field(default_factory=list)
    date_posted: Optional[str] = None
    full_text: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'original_query': self.original_query,
            'query_type': self.query_type.value,
            'keywords': self.keywords,
            'locations': self.locations,
            'skills': self.skills,
            'companies': self.companies,
            'min_salary': self.min_salary,
            'max_salary': self.max_salary,
            'job_types': self.job_types,
            'experience_levels': self.experience_levels,
            'remote_options': self.remote_options,
            'date_posted': self.date_posted,
            'full_text': self.full_text,
        }


class NLSearchParser:
    """
    Natural Language Search Parser for job queries.
    
    This class provides methods to parse natural language queries
    and extract search parameters for job searching.
    """
    
    # Common job titles
    JOB_TITLES = {
        'software engineer': 'software_engineer',
        'frontend developer': 'frontend_developer',
        'backend developer': 'backend_developer',
        'full stack developer': 'full_stack_developer',
        'data scientist': 'data_scientist',
        'machine learning engineer': 'ml_engineer',
        'devops engineer': 'devops_engineer',
        'qa engineer': 'qa_engineer',
        'product manager': 'product_manager',
        'ux designer': 'ux_designer',
        'ui designer': 'ui_designer',
        'technical writer': 'technical_writer',
        'technical lead': 'technical_lead',
        'architect': 'architect',
        'cto': 'cto',
        'ceo': 'ceo',
        'analyst': 'analyst',
        'consultant': 'consultant',
        'manager': 'manager',
        'director': 'director',
        'vp': 'vp',
        'senior': 'senior',
        'junior': 'junior',
        'intern': 'intern',
        'freelance': 'freelance',
        'contract': 'contract',
    }
    
    # Common skills
    SKILLS = {
        'python': 'python',
        'javascript': 'javascript',
        'typescript': 'typescript',
        'java': 'java',
        'c#': 'csharp',
        'c++': 'cpp',
        'ruby': 'ruby',
        'php': 'php',
        'go': 'go',
        'rust': 'rust',
        'swift': 'swift',
        'kotlin': 'kotlin',
        'sql': 'sql',
        'nosql': 'nosql',
        'html': 'html',
        'css': 'css',
        'react': 'react',
        'angular': 'angular',
        'vue': 'vue',
        'node.js': 'nodejs',
        'django': 'django',
        'flask': 'flask',
        'spring': 'spring',
        'express': 'express',
        'aws': 'aws',
        'azure': 'azure',
        'gcp': 'gcp',
        'docker': 'docker',
        'kubernetes': 'kubernetes',
        'terraform': 'terraform',
        'ansible': 'ansible',
        'git': 'git',
        'linux': 'linux',
        'unix': 'unix',
        'mysql': 'mysql',
        'postgresql': 'postgresql',
        'mongodb': 'mongodb',
        'redis': 'redis',
        'elasticsearch': 'elasticsearch',
        'graphql': 'graphql',
        'rest': 'rest',
        'grpc': 'grpc',
        'tensorflow': 'tensorflow',
        'pytorch': 'pytorch',
        'scikit-learn': 'scikitlearn',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'scipy': 'scipy',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
        'jupyter': 'jupyter',
        'pyspark': 'pyspark',
        'hadoop': 'hadoop',
        'spark': 'spark',
        'kafka': 'kafka',
        'rabbitmq': 'rabbitmq',
        'celery': 'celery',
        'redis': 'redis',
        'nginx': 'nginx',
        'apache': 'apache',
        'linux': 'linux',
        'bash': 'bash',
        'shell': 'shell',
        'docker': 'docker',
        'kubernetes': 'kubernetes',
        'ci/cd': 'cicd',
        'jenkins': 'jenkins',
        'gitlab': 'gitlab',
        'github': 'github',
        'bitbucket': 'bitbucket',
        'agile': 'agile',
        'scrum': 'scrum',
        'kanban': 'kanban',
        'tdd': 'tdd',
        'bdd': 'bdd',
        'unit testing': 'unit_testing',
        'integration testing': 'integration_testing',
        'e2e testing': 'e2e_testing',
        'selenium': 'selenium',
        'cypress': 'cypress',
        'jest': 'jest',
        'mocha': 'mocha',
        'pytest': 'pytest',
        'junit': 'junit',
        'spring boot': 'springboot',
        'hibernate': 'hibernate',
        'jpa': 'jpa',
        'mybatis': 'mybatis',
        'orm': 'orm',
        'microservices': 'microservices',
        'monolith': 'monolith',
        'serverless': 'serverless',
        'lambda': 'lambda',
        'cloudformation': 'cloudformation',
        'terraform': 'terraform',
        'ansible': 'ansible',
        'puppet': 'puppet',
        'chef': 'chef',
        'saltstack': 'saltstack',
        'prometheus': 'prometheus',
        'grafana': 'grafana',
        'elk': 'elk',
        'logstash': 'logstash',
        'kibana': 'kibana',
        'fluentd': 'fluentd',
        'splunk': 'splunk',
        'new relic': 'newrelic',
        'datadog': 'datadog',
        'sentry': 'sentry',
        'bugsnag': 'bugsnag',
        'rollbar': 'rollbar',
        'new relic': 'newrelic',
        'datadog': 'datadog',
        'sentry': 'sentry',
        'bugsnag': 'bugsnag',
        'rollbar': 'rollbar',
    }
    
    # Location keywords
    LOCATIONS = {
        'new york': 'New York',
        'san francisco': 'San Francisco',
        'los angeles': 'Los Angeles',
        'chicago': 'Chicago',
        'houston': 'Houston',
        'phoenix': 'Phoenix',
        'philadelphia': 'Philadelphia',
        'san antonio': 'San Antonio',
        'san diego': 'San Diego',
        'dallas': 'Dallas',
        'austin': 'Austin',
        'denver': 'Denver',
        'seattle': 'Seattle',
        'boston': 'Boston',
        'atlanta': 'Atlanta',
        'miami': 'Miami',
        'detroit': 'Detroit',
        'minneapolis': 'Minneapolis',
        'san jose': 'San Jose',
        'tampa': 'Tampa',
        'new jersey': 'New Jersey',
        'california': 'California',
        'texas': 'Texas',
        'florida': 'Florida',
        'illinois': 'Illinois',
        'washington': 'Washington',
        'massachusetts': 'Massachusetts',
        'georgia': 'Georgia',
        'michigan': 'Michigan',
        'arizona': 'Arizona',
        'nevada': 'Nevada',
        'north carolina': 'North Carolina',
        'virginia': 'Virginia',
        'ohio': 'Ohio',
        'pennsylvania': 'Pennsylvania',
        'indiana': 'Indiana',
        'missouri': 'Missouri',
        'tennessee': 'Tennessee',
        'kentucky': 'Kentucky',
        'wisconsin': 'Wisconsin',
        'minnesota': 'Minnesota',
        'oregon': 'Oregon',
        'utah': 'Utah',
        'colorado': 'Colorado',
        'maryland': 'Maryland',
        'connecticut': 'Connecticut',
        'new hampshire': 'New Hampshire',
        'vermont': 'Vermont',
        'maine': 'Maine',
        'rhode island': 'Rhode Island',
        'west virginia': 'West Virginia',
        'south carolina': 'South Carolina',
        'alabama': 'Alabama',
        'louisiana': 'Louisiana',
        'mississippi': 'Mississippi',
        'arkansas': 'Arkansas',
        'oklahoma': 'Oklahoma',
        'new mexico': 'New Mexico',
        'alaska': 'Alaska',
        'hawaii': 'Hawaii',
        'montana': 'Montana',
        'north dakota': 'North Dakota',
        'south dakota': 'South Dakota',
        'nebraska': 'Nebraska',
        'idaho': 'Idaho',
        'wyoming': 'Wyoming',
        'delaware': 'Delaware',
        'district of columbia': 'District of Columbia',
        'washington dc': 'Washington DC',
        'dc': 'Washington DC',
        'remote': 'Remote',
        'work from home': 'Remote',
        'wfh': 'Remote',
        'hybrid': 'Hybrid',
        'on-site': 'On-site',
        'onsite': 'On-site',
    }
    
    # Job types
    JOB_TYPES = {
        'full-time': 'full_time',
        'full time': 'full_time',
        'part-time': 'part_time',
        'part time': 'part_time',
        'contract': 'contract',
        'temporary': 'temporary',
        'internship': 'internship',
        'freelance': 'freelance',
        'per diem': 'per_diem',
        'casual': 'casual',
        'seasonal': 'seasonal',
        'commission': 'commission',
    }
    
    # Experience levels
    EXPERIENCE_LEVELS = {
        'entry level': 'entry',
        'entry-level': 'entry',
        'junior': 'junior',
        'mid-level': 'mid',
        'mid-level': 'mid',
        'senior': 'senior',
        'lead': 'lead',
        'principal': 'principal',
        'staff': 'staff',
        'architect': 'architect',
        'manager': 'manager',
        'director': 'director',
        'vp': 'vp',
        'executive': 'executive',
    }
    
    # Remote options
    REMOTE_OPTIONS = {
        'remote': 'remote',
        'work from home': 'remote',
        'wfh': 'remote',
        'hybrid': 'hybrid',
        'on-site': 'on_site',
        'onsite': 'on_site',
        'office': 'office',
    }
    
    # Date posted keywords
    DATE_POSTED = {
        'today': '1d',
        'last 24 hours': '1d',
        'last 24h': '1d',
        'last day': '1d',
        'last 3 days': '3d',
        'last week': '7d',
        'last 7 days': '7d',
        'last month': '30d',
        'last 30 days': '30d',
        'this month': '30d',
        'this week': '7d',
    }
    
    def __init__(self):
        """Initialize the parser."""
        self._compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for parsing."""
        return {
            'salary_range': re.compile(r'\$?(\d{1,3}(?:,\d{3})*)(?:\s*-\s*\$?(\d{1,3}(?:,\d{3})*))?\s*(k|K)?', re.IGNORECASE),
            'salary_min': re.compile(r'(?:min(?:imum)?|at least|from)\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(k|K)?', re.IGNORECASE),
            'salary_max': re.compile(r'(?:max(?:imum)?|up to|at most|to)\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(k|K)?', re.IGNORECASE),
            'date_posted': re.compile(r'(?:posted\s+(?:within|in|the last)?\s*)(\d+)\s*(day|days|week|weeks|month|months)', re.IGNORECASE),
            'job_type': re.compile(r'\b(full-time|part-time|contract|temporary|internship|freelance)\b', re.IGNORECASE),
            'experience': re.compile(r'\b(entry[-\s]?level|junior|mid[-\s]?level|senior|lead|principal|staff|vp|executive)\b', re.IGNORECASE),
            'remote': re.compile(r'\b(remote|work[-\s]?from[-\s]?home|wfh|hybrid|on[-\s]?site)\b', re.IGNORECASE),
        }
    
    def parse(self, query: str) -> ParsedQuery:
        """
        Parse a natural language query.
        
        Args:
            query: The natural language query string
            
        Returns:
            ParsedQuery with extracted components
        """
        query = query.strip()
        parsed = ParsedQuery(original_query=query)
        
        # Determine query type
        parsed.query_type = self._determine_query_type(query)
        
        # Extract components
        parsed.keywords = self._extract_keywords(query)
        parsed.locations = self._extract_locations(query)
        parsed.skills = self._extract_skills(query)
        parsed.companies = self._extract_companies(query)
        parsed.job_types = self._extract_job_types(query)
        parsed.experience_levels = self._extract_experience_levels(query)
        parsed.remote_options = self._extract_remote_options(query)
        parsed.date_posted = self._extract_date_posted(query)
        
        # Extract salary
        min_salary, max_salary = self._extract_salary(query)
        parsed.min_salary = min_salary
        parsed.max_salary = max_salary
        
        # Build full text (without special keywords)
        parsed.full_text = self._build_full_text(query, parsed)
        
        return parsed
    
    def _determine_query_type(self, query: str) -> QueryType:
        """Determine the type of query."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['salary', 'compensation', 'pay', 'wage', 'income']):
            return QueryType.SALARY_SEARCH
        elif any(word in query_lower for word in ['skill', 'skills', 'ability', 'competency']):
            return QueryType.SKILL_SEARCH
        elif any(word in query_lower for word in ['company', 'employer', 'organization', 'firm']):
            return QueryType.COMPANY_SEARCH
        elif any(word in query_lower for word in ['location', 'city', 'state', 'country', 'area']):
            return QueryType.LOCATION_SEARCH
        else:
            return QueryType.JOB_SEARCH
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract general keywords from query."""
        # Remove special keywords and locations
        keywords = query
        
        # Remove known patterns
        for pattern in self._compiled_patterns.values():
            keywords = pattern.sub('', keywords)
        
        # Remove location names
        for location in self.LOCATIONS.keys():
            keywords = re.sub(re.escape(location), '', keywords, flags=re.IGNORECASE)
        
        # Remove skill names
        for skill in self.SKILLS.keys():
            keywords = re.sub(re.escape(skill), '', keywords, flags=re.IGNORECASE)
        
        # Remove job titles
        for title in self.JOB_TITLES.keys():
            keywords = re.sub(re.escape(title), '', keywords, flags=re.IGNORECASE)
        
        # Extract remaining words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', keywords.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
            'dare', 'ought', 'used', 'it', 'its', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'we', 'they', 'what', 'which', 'who', 'whom',
            'whose', 'where', 'when', 'why', 'how', 'all', 'each', 'every', 'both',
            'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can',
            'just', 'don', 'now'
        }
        
        return [w for w in words if w not in stop_words and len(w) >= 3]
    
    def _extract_locations(self, query: str) -> List[str]:
        """Extract location names from query."""
        locations = []
        query_lower = query.lower()
        
        for location, normalized in self.LOCATIONS.items():
            if location in query_lower:
                if normalized not in locations:
                    locations.append(normalized)
        
        return locations
    
    def _extract_skills(self, query: str) -> List[str]:
        """Extract skills from query."""
        skills = []
        query_lower = query.lower()
        
        for skill, normalized in self.SKILLS.items():
            if skill in query_lower:
                if normalized not in skills:
                    skills.append(normalized)
        
        return skills
    
    def _extract_companies(self, query: str) -> List[str]:
        """Extract company names from query."""
        companies = []
        
        # Look for company patterns
        patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*(?:jobs?|careers?|hiring)?',
            r'\b([A-Z]{2,})\s*(?:jobs?|careers?|hiring)?',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query)
            for match in matches:
                company = match.strip()
                if company and len(company) > 1 and company.lower() not in ['the', 'and', 'for']:
                    if company not in companies:
                        companies.append(company)
        
        return companies
    
    def _extract_job_types(self, query: str) -> List[str]:
        """Extract job types from query."""
        job_types = []
        query_lower = query.lower()
        
        for job_type, normalized in self.JOB_TYPES.items():
            if job_type in query_lower:
                if normalized not in job_types:
                    job_types.append(normalized)
        
        return job_types
    
    def _extract_experience_levels(self, query: str) -> List[str]:
        """Extract experience levels from query."""
        levels = []
        query_lower = query.lower()
        
        for level, normalized in self.EXPERIENCE_LEVELS.items():
            if level in query_lower:
                if normalized not in levels:
                    levels.append(normalized)
        
        return levels
    
    def _extract_remote_options(self, query: str) -> List[str]:
        """Extract remote work options from query."""
        options = []
        query_lower = query.lower()
        
        for option, normalized in self.REMOTE_OPTIONS.items():
            if option in query_lower:
                if normalized not in options:
                    options.append(normalized)
        
        return options
    
    def _extract_date_posted(self, query: str) -> Optional[str]:
        """Extract date posted filter from query."""
        query_lower = query.lower()
        
        # Check for exact matches
        for keyword, value in self.DATE_POSTED.items():
            if keyword in query_lower:
                return value
        
        # Check for patterns
        match = self._compiled_patterns['date_posted'].search(query)
        if match:
            number = int(match.group(1))
            unit = match.group(2).lower()
            
            if unit.startswith('day'):
                return f'{number}d'
            elif unit.startswith('week'):
                return f'{number * 7}d'
            elif unit.startswith('month'):
                return f'{number * 30}d'
        
        return None
    
    def _extract_salary(self, query: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract salary range from query."""
        min_salary = None
        max_salary = None
        
        # Try to find salary range
        match = self._compiled_patterns['salary_range'].search(query)
        if match:
            min_val = int(match.group(1).replace(',', ''))
            max_val = int(match.group(2).replace(',', '')) if match.group(2) else None
            multiplier = 1000 if match.group(3) else 1
            
            min_salary = min_val * multiplier
            if max_val:
                max_salary = max_val * multiplier
            else:
                max_salary = min_salary * 1.5  # Estimate 50% range
        
        # Try to find min salary
        match = self._compiled_patterns['salary_min'].search(query)
        if match:
            min_salary = int(match.group(1).replace(',', '')) * (1000 if match.group(2) else 1)
        
        # Try to find max salary
        match = self._compiled_patterns['salary_max'].search(query)
        if match:
            max_salary = int(match.group(1).replace(',', '')) * (1000 if match.group(2) else 1)
        
        return min_salary, max_salary
    
    def _build_full_text(self, query: str, parsed: ParsedQuery) -> str:
        """Build full text query without special keywords."""
        full_text = query
        
        # Remove known patterns
        for pattern in self._compiled_patterns.values():
            full_text = pattern.sub('', full_text)
        
        # Remove location names
        for location in self.LOCATIONS.keys():
            full_text = re.sub(re.escape(location), '', full_text, flags=re.IGNORECASE)
        
        # Remove skill names
        for skill in self.SKILLS.keys():
            full_text = re.sub(re.escape(skill), '', full_text, flags=re.IGNORECASE)
        
        # Remove job titles
        for title in self.JOB_TITLES.keys():
            full_text = re.sub(re.escape(title), '', full_text, flags=re.IGNORECASE)
        
        # Remove job types
        for job_type in self.JOB_TYPES.keys():
            full_text = re.sub(re.escape(job_type), '', full_text, flags=re.IGNORECASE)
        
        # Remove experience levels
        for level in self.EXPERIENCE_LEVELS.keys():
            full_text = re.sub(re.escape(level), '', full_text, flags=re.IGNORECASE)
        
        # Remove remote options
        for option in self.REMOTE_OPTIONS.keys():
            full_text = re.sub(re.escape(option), '', full_text, flags=re.IGNORECASE)
        
        # Clean up
        full_text = re.sub(r'\s+', ' ', full_text).strip()
        
        return full_text
    
    def to_django_query(self, parsed: ParsedQuery) -> Dict[str, Any]:
        """
        Convert parsed query to Django Q objects.
        
        Args:
            parsed: ParsedQuery object
            
        Returns:
            Dictionary with query parameters
        """
        query = {}
        
        # Full text search
        if parsed.full_text:
            query['search'] = parsed.full_text
        
        # Keywords
        if parsed.keywords:
            query['keywords'] = parsed.keywords
        
        # Locations
        if parsed.locations:
            query['locations'] = parsed.locations
        
        # Skills
        if parsed.skills:
            query['skills'] = parsed.skills
        
        # Companies
        if parsed.companies:
            query['companies'] = parsed.companies
        
        # Job types
        if parsed.job_types:
            query['job_types'] = parsed.job_types
        
        # Experience levels
        if parsed.experience_levels:
            query['experience_levels'] = parsed.experience_levels
        
        # Remote options
        if parsed.remote_options:
            query['remote_options'] = parsed.remote_options
        
        # Date posted
        if parsed.date_posted:
            query['date_posted'] = parsed.date_posted
        
        # Salary
        if parsed.min_salary:
            query['min_salary'] = parsed.min_salary
        if parsed.max_salary:
            query['max_salary'] = parsed.max_salary
        
        return query


def parse_query(query: str) -> ParsedQuery:
    """
    Convenience function to parse a query.
    
    Args:
        query: The natural language query string
        
    Returns:
        ParsedQuery with extracted components
    """
    parser = NLSearchParser()
    return parser.parse(query)


def to_django_query(query: str) -> Dict[str, Any]:
    """
    Convenience function to parse and convert to Django query.
    
    Args:
        query: The natural language query string
        
    Returns:
        Dictionary with query parameters
    """
    parser = NLSearchParser()
    parsed = parser.parse(query)
    return parser.to_django_query(parsed)