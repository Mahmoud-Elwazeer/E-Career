> **Superseded by MASTER_IMPLEMENTATION_PLAN.md and audit/PHASE_*_COMPLETION_REPORT.md — kept for history only.**

# PHASE 2A: User Profiles & CV Intelligence

> **Dependencies:** Phase 1A complete, AWS Bedrock configured  
> **Duration:** 3-4 hours  
> **Status:** Ready for GLM execution

---

## 🎯 Objectives

Implement user profile management with CV intelligence:
- CV upload and parsing (AWS Bedrock)
- Profile management (skills, experience, preferences)
- Job match scoring foundation
- Profile completion tracking
- Privacy-first design

---

## 📦 Dependencies

### Backend

```bash
pip install boto3 botocore
pip install pypdf2 python-docx python-magic-bin
pip install pillow
```

### AWS Bedrock Configuration

Add to `backend/.env`:

```env
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-20250514-v1:0
```

---

## 🔧 Backend Implementation

### Step 1: AWS Bedrock Service

**File:** `backend/ai/bedrock_service.py`

```python
"""
AWS Bedrock integration for CV parsing and AI features
"""

import boto3
import json
import logging
from django.conf import settings
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class BedrockService:
    """AWS Bedrock client for AI operations"""
    
    def __init__(self):
        self.client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_DEFAULT_REGION
        )
        self.model_id = settings.BEDROCK_MODEL_ID
    
    def invoke_model(self, prompt, system_prompt=None, max_tokens=4096, temperature=0.3):
        """
        Invoke Claude via AWS Bedrock
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            max_tokens: Maximum response tokens
            temperature: Response creativity (0-1)
        
        Returns:
            str: Model response
        """
        try:
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": messages,
                "temperature": temperature
            }
            
            if system_prompt:
                body["system"] = system_prompt
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
        
        except ClientError as e:
            logger.error(f"Bedrock API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error invoking Bedrock: {e}")
            raise
    
    def parse_cv(self, cv_text):
        """
        Parse CV text and extract structured information
        
        Args:
            cv_text: Raw CV text content
        
        Returns:
            dict: Structured CV data
        """
        system_prompt = """You are an expert CV parser. Extract structured information from the provided CV text.

Return a JSON object with the following structure:
{
  "personal": {
    "name": "Full name",
    "email": "email@example.com",
    "phone": "phone number",
    "location": "City, Country",
    "linkedin": "LinkedIn URL",
    "portfolio": "Portfolio/website URL",
    "summary": "Professional summary"
  },
  "experience": [
    {
      "title": "Job title",
      "company": "Company name",
      "location": "Location",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM or 'Present'",
      "description": "Job description and achievements"
    }
  ],
  "education": [
    {
      "degree": "Degree type and field",
      "institution": "Institution name",
      "location": "Location",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM",
      "gpa": "GPA if mentioned"
    }
  ],
  "skills": {
    "technical": ["List of technical skills"],
    "languages": [{"language": "English", "level": "Native/Fluent/Professional/Basic"}],
    "soft_skills": ["List of soft skills"]
  },
  "certifications": [
    {
      "name": "Certification name",
      "issuer": "Issuing organization",
      "date": "YYYY-MM",
      "credential_id": "ID if provided"
    }
  ],
  "projects": [
    {
      "name": "Project name",
      "description": "Brief description",
      "technologies": ["Tech stack"],
      "url": "Project URL if available"
    }
  ]
}

Important:
- Extract all available information
- Use null for missing fields
- Normalize date formats to YYYY-MM
- Clean up formatting and special characters
- Infer information only when clearly evident
"""
        
        prompt = f"""Parse this CV and extract structured information:

{cv_text}

Return ONLY the JSON object, no additional text."""
        
        try:
            response = self.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=8000,
                temperature=0.1
            )
            
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            
            parsed_data = json.loads(json_str)
            return parsed_data
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Bedrock response: {e}")
            logger.error(f"Response: {response}")
            raise ValueError("Failed to parse CV - invalid JSON response")
        except Exception as e:
            logger.error(f"Error parsing CV: {e}")
            raise
    
    def calculate_match_score(self, profile_data, job_data):
        """
        Calculate how well a profile matches a job using AI
        
        Args:
            profile_data: User profile dict
            job_data: Job dict
        
        Returns:
            dict: Match score and breakdown
        """
        system_prompt = """You are an expert job matching AI. Analyze how well a candidate's profile matches a job posting.

Evaluate across these dimensions:
- Skills match (40%): Required skills vs candidate skills
- Experience match (25%): Years and relevance of experience
- Education match (15%): Required vs actual education level
- Location match (10%): Location preferences and job location
- Cultural fit (10%): Job description vs candidate profile alignment

Return JSON:
{
  "overall_score": 85,
  "breakdown": {
    "skills": {"score": 90, "reasoning": "Strong match with 8/10 required skills"},
    "experience": {"score": 80, "reasoning": "Has 5 years, job requires 3-5 years"},
    "education": {"score": 100, "reasoning": "BS in Computer Science matches requirement"},
    "location": {"score": 50, "reasoning": "Open to relocation but prefers remote"},
    "cultural_fit": {"score": 85, "reasoning": "Strong alignment with company values"}
  },
  "strengths": ["Excellent Python skills", "Relevant industry experience"],
  "gaps": ["Missing AWS certification", "Limited management experience"],
  "recommendation": "Strong candidate - recommended for interview"
}
"""
        
        prompt = f"""Analyze this job match:

CANDIDATE PROFILE:
{json.dumps(profile_data, indent=2)}

JOB POSTING:
{json.dumps(job_data, indent=2)}

Provide match score and detailed analysis."""
        
        try:
            response = self.invoke_model(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=2000,
                temperature=0.2
            )
            
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            
            match_data = json.loads(json_str)
            return match_data
        
        except Exception as e:
            logger.error(f"Error calculating match score: {e}")
            # Fallback to basic algorithm
            return {
                "overall_score": 0,
                "breakdown": {},
                "error": "AI matching temporarily unavailable"
            }


# Singleton instance
bedrock_service = BedrockService()
```

### Step 2: CV Parsing Service

**File:** `backend/profiles/cv_parser.py`

```python
"""
CV file processing and text extraction
"""

import os
import logging
from pathlib import Path
import PyPDF2
import docx
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)

class CVParser:
    """Extract text from CV files (PDF, DOCX, TXT)"""
    
    SUPPORTED_FORMATS = ['.pdf', '.docx', '.doc', '.txt']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    def extract_text(cls, file: UploadedFile) -> str:
        """
        Extract text from uploaded CV file
        
        Args:
            file: Django UploadedFile instance
        
        Returns:
            str: Extracted text content
        
        Raises:
            ValueError: If file format not supported or file too large
        """
        # Validate file size
        if file.size > cls.MAX_FILE_SIZE:
            raise ValueError(f"File too large. Maximum size is {cls.MAX_FILE_SIZE / 1024 / 1024}MB")
        
        # Get file extension
        file_ext = Path(file.name).suffix.lower()
        
        if file_ext not in cls.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format. Supported: {', '.join(cls.SUPPORTED_FORMATS)}")
        
        # Extract text based on format
        try:
            if file_ext == '.pdf':
                return cls._extract_from_pdf(file)
            elif file_ext in ['.docx', '.doc']:
                return cls._extract_from_docx(file)
            elif file_ext == '.txt':
                return cls._extract_from_txt(file)
        except Exception as e:
            logger.error(f"Error extracting text from {file.name}: {e}")
            raise ValueError(f"Failed to extract text from file: {str(e)}")
    
    @staticmethod
    def _extract_from_pdf(file: UploadedFile) -> str:
        """Extract text from PDF"""
        text = []
        
        pdf_reader = PyPDF2.PdfReader(file)
        
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
        
        return '\n\n'.join(text)
    
    @staticmethod
    def _extract_from_docx(file: UploadedFile) -> str:
        """Extract text from DOCX"""
        doc = docx.Document(file)
        
        text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text)
        
        return '\n\n'.join(text)
    
    @staticmethod
    def _extract_from_txt(file: UploadedFile) -> str:
        """Extract text from TXT"""
        try:
            return file.read().decode('utf-8')
        except UnicodeDecodeError:
            # Try other encodings
            file.seek(0)
            return file.read().decode('latin-1')
```

### Step 3: Profile Serializers

**File:** `backend/profiles/serializers.py`

```python
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserProfile, Education, Experience, Certification, Project
from .cv_parser import CVParser
from ai.bedrock_service import bedrock_service

User = get_user_model()

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = [
            'id', 'degree', 'field_of_study', 'institution',
            'location', 'start_date', 'end_date', 'gpa', 'description'
        ]

class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = [
            'id', 'title', 'company', 'location', 'employment_type',
            'start_date', 'end_date', 'is_current', 'description'
        ]

class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = ['id', 'name', 'issuer', 'issue_date', 'credential_id', 'url']

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'technologies', 'url', 'start_date', 'end_date']

class UserProfileSerializer(serializers.ModelSerializer):
    """Full user profile with nested relations"""
    
    education = EducationSerializer(many=True, read_only=True)
    experience = ExperienceSerializer(many=True, read_only=True)
    certifications = CertificationSerializer(many=True, read_only=True)
    projects = ProjectSerializer(many=True, read_only=True)
    
    completion_percentage = serializers.IntegerField(read_only=True)
    is_complete = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'phone', 'location', 'linkedin_url',
            'portfolio_url', 'bio', 'avatar', 'cv_file', 'cv_text',
            'cv_parsed_data', 'skills', 'languages', 'years_of_experience',
            'current_position', 'current_company', 'preferred_job_titles',
            'preferred_locations', 'preferred_industries', 'workplace_preference',
            'employment_type_preference', 'desired_salary_min', 'desired_salary_max',
            'salary_currency', 'available_from', 'notice_period_days',
            'is_available_for_work', 'email_alerts_enabled', 'alert_frequency',
            'education', 'experience', 'certifications', 'projects',
            'completion_percentage', 'is_complete', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'cv_text', 'cv_parsed_data', 'created_at', 'updated_at']

class CVUploadSerializer(serializers.Serializer):
    """Handles CV file upload and parsing"""
    
    cv_file = serializers.FileField()
    
    def validate_cv_file(self, value):
        """Validate CV file"""
        try:
            # Check file format
            CVParser.extract_text(value)
            value.seek(0)  # Reset file pointer
            return value
        except ValueError as e:
            raise serializers.ValidationError(str(e))
    
    def save(self, user):
        """Parse CV and update profile"""
        cv_file = self.validated_data['cv_file']
        
        # Extract text
        cv_text = CVParser.extract_text(cv_file)
        cv_file.seek(0)
        
        # Parse with AWS Bedrock
        try:
            parsed_data = bedrock_service.parse_cv(cv_text)
        except Exception as e:
            raise serializers.ValidationError(f"Failed to parse CV: {str(e)}")
        
        # Update profile
        profile = user.userprofile
        profile.cv_file = cv_file
        profile.cv_text = cv_text
        profile.cv_parsed_data = parsed_data
        
        # Auto-fill profile fields from parsed data
        if parsed_data.get('personal'):
            personal = parsed_data['personal']
            if personal.get('phone'):
                profile.phone = personal['phone']
            if personal.get('location'):
                profile.location = personal['location']
            if personal.get('linkedin'):
                profile.linkedin_url = personal['linkedin']
            if personal.get('portfolio'):
                profile.portfolio_url = personal['portfolio']
            if personal.get('summary'):
                profile.bio = personal['summary']
        
        # Extract skills
        if parsed_data.get('skills'):
            skills_data = parsed_data['skills']
            all_skills = []
            
            if skills_data.get('technical'):
                all_skills.extend(skills_data['technical'])
            if skills_data.get('soft_skills'):
                all_skills.extend(skills_data['soft_skills'])
            
            profile.skills = all_skills
            
            if skills_data.get('languages'):
                profile.languages = skills_data['languages']
        
        # Calculate years of experience
        if parsed_data.get('experience'):
            from datetime import datetime
            from dateutil.relativedelta import relativedelta
            
            total_months = 0
            for exp in parsed_data['experience']:
                try:
                    start = datetime.strptime(exp['start_date'], '%Y-%m')
                    
                    if exp['end_date'] == 'Present':
                        end = datetime.now()
                    else:
                        end = datetime.strptime(exp['end_date'], '%Y-%m')
                    
                    delta = relativedelta(end, start)
                    total_months += delta.years * 12 + delta.months
                except:
                    pass
            
            profile.years_of_experience = total_months / 12
        
        profile.save()
        
        # Create related objects
        self._create_experience(user, parsed_data.get('experience', []))
        self._create_education(user, parsed_data.get('education', []))
        self._create_certifications(user, parsed_data.get('certifications', []))
        self._create_projects(user, parsed_data.get('projects', []))
        
        return profile
    
    def _create_experience(self, user, experience_list):
        """Create Experience objects"""
        for exp_data in experience_list:
            try:
                Experience.objects.create(
                    profile=user.userprofile,
                    title=exp_data.get('title', ''),
                    company=exp_data.get('company', ''),
                    location=exp_data.get('location', ''),
                    start_date=exp_data.get('start_date'),
                    end_date=None if exp_data.get('end_date') == 'Present' else exp_data.get('end_date'),
                    is_current=exp_data.get('end_date') == 'Present',
                    description=exp_data.get('description', '')
                )
            except Exception as e:
                logger.warning(f"Failed to create experience: {e}")
    
    def _create_education(self, user, education_list):
        """Create Education objects"""
        for edu_data in education_list:
            try:
                Education.objects.create(
                    profile=user.userprofile,
                    degree=edu_data.get('degree', ''),
                    institution=edu_data.get('institution', ''),
                    location=edu_data.get('location', ''),
                    start_date=edu_data.get('start_date'),
                    end_date=edu_data.get('end_date'),
                    gpa=edu_data.get('gpa')
                )
            except Exception as e:
                logger.warning(f"Failed to create education: {e}")
    
    def _create_certifications(self, user, cert_list):
        """Create Certification objects"""
        for cert_data in cert_list:
            try:
                Certification.objects.create(
                    profile=user.userprofile,
                    name=cert_data.get('name', ''),
                    issuer=cert_data.get('issuer', ''),
                    issue_date=cert_data.get('date'),
                    credential_id=cert_data.get('credential_id')
                )
            except Exception as e:
                logger.warning(f"Failed to create certification: {e}")
    
    def _create_projects(self, user, project_list):
        """Create Project objects"""
        for proj_data in project_list:
            try:
                Project.objects.create(
                    profile=user.userprofile,
                    name=proj_data.get('name', ''),
                    description=proj_data.get('description', ''),
                    technologies=proj_data.get('technologies', []),
                    url=proj_data.get('url')
                )
            except Exception as e:
                logger.warning(f"Failed to create project: {e}")
```

### Step 4: Profile Views

**File:** `backend/profiles/views.py`

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import UserProfile, Education, Experience, Certification, Project
from .serializers import (
    UserProfileSerializer, CVUploadSerializer,
    EducationSerializer, ExperienceSerializer,
    CertificationSerializer, ProjectSerializer
)

class ProfileViewSet(viewsets.ModelViewSet):
    """
    User profile management
    
    GET /api/profile/ - Get current user profile
    PUT /api/profile/ - Update profile
    POST /api/profile/upload-cv/ - Upload and parse CV
    GET /api/profile/completion/ - Get profile completion status
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_queryset(self):
        return UserProfile.objects.filter(user=self.request.user).select_related(
            'user'
        ).prefetch_related(
            'education', 'experience', 'certifications', 'projects'
        )
    
    def get_object(self):
        return self.request.user.userprofile
    
    def list(self, request, *args, **kwargs):
        """Get current user's profile"""
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def upload_cv(self, request):
        """Upload and parse CV"""
        serializer = CVUploadSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                profile = serializer.save(user=request.user)
                return Response({
                    'status': 'success',
                    'message': 'CV uploaded and parsed successfully',
                    'profile': UserProfileSerializer(profile, context={'request': request}).data
                })
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def completion(self, request):
        """Get profile completion status"""
        profile = self.get_object()
        
        # Calculate completion
        required_fields = {
            'Basic Info': {
                'fields': ['phone', 'location', 'bio'],
                'weight': 20
            },
            'CV': {
                'fields': ['cv_file'],
                'weight': 30
            },
            'Skills': {
                'fields': ['skills'],
                'weight': 20,
                'check': lambda p: len(p.skills or []) >= 5
            },
            'Experience': {
                'relations': 'experience',
                'weight': 15,
                'min_count': 1
            },
            'Education': {
                'relations': 'education',
                'weight': 15,
                'min_count': 1
            }
        }
        
        completion = {}
        total_score = 0
        
        for section, config in required_fields.items():
            if 'fields' in config:
                # Check fields
                if 'check' in config:
                    is_complete = config['check'](profile)
                else:
                    is_complete = all(
                        getattr(profile, field, None)
                        for field in config['fields']
                    )
            else:
                # Check relations
                count = getattr(profile, config['relations']).count()
                is_complete = count >= config.get('min_count', 1)
            
            completion[section] = {
                'complete': is_complete,
                'weight': config['weight']
            }
            
            if is_complete:
                total_score += config['weight']
        
        return Response({
            'total_score': total_score,
            'is_complete': total_score >= 80,
            'sections': completion
        })


class EducationViewSet(viewsets.ModelViewSet):
    serializer_class = EducationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Education.objects.filter(profile__user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.userprofile)


class ExperienceViewSet(viewsets.ModelViewSet):
    serializer_class = ExperienceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Experience.objects.filter(profile__user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.userprofile)


class CertificationViewSet(viewsets.ModelViewSet):
    serializer_class = CertificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Certification.objects.filter(profile__user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.userprofile)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Project.objects.filter(profile__user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.userprofile)
```

### Step 5: URL Configuration

**File:** `backend/profiles/urls.py`

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProfileViewSet, EducationViewSet, ExperienceViewSet,
    CertificationViewSet, ProjectViewSet
)

router = DefaultRouter()
router.register(r'profile', ProfileViewSet, basename='profile')
router.register(r'education', EducationViewSet, basename='education')
router.register(r'experience', ExperienceViewSet, basename='experience')
router.register(r'certifications', CertificationViewSet, basename='certification')
router.register(r'projects', ProjectViewSet, basename='project')

urlpatterns = [
    path('', include(router.urls)),
]
```

**File:** `backend/ecareer/urls.py` (add)

```python
urlpatterns = [
    # ... existing
    path('api/', include('profiles.urls')),
]
```

---

## 🎨 Frontend Implementation

### Step 6: Profile Page

**File:** `frontend/src/pages/ProfilePage.jsx`

```jsx
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, User, Briefcase, GraduationCap, Award, Code } from 'lucide-react';
import axios from 'axios';

import CVUpload from '../components/profile/CVUpload';
import BasicInfo from '../components/profile/BasicInfo';
import ExperienceSection from '../components/profile/ExperienceSection';
import EducationSection from '../components/profile/EducationSection';
import SkillsSection from '../components/profile/SkillsSection';
import ProfileCompletion from '../components/profile/ProfileCompletion';

const ProfilePage = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const queryClient = useQueryClient();

  // Fetch profile
  const { data: profile, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const response = await axios.get('/api/profile/');
      return response.data[0];  // List endpoint returns array
    }
  });

  // Fetch completion status
  const { data: completion } = useQuery({
    queryKey: ['profile-completion'],
    queryFn: async () => {
      const response = await axios.get('/api/profile/completion/');
      return response.data;
    }
  });

  const tabs = [
    { id: 'overview', label: 'Overview', icon: User },
    { id: 'experience', label: 'Experience', icon: Briefcase },
    { id: 'education', label: 'Education', icon: GraduationCap },
    { id: 'skills', label: 'Skills', icon: Code },
    { id: 'cv', label: 'CV Upload', icon: Upload }
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Your Profile</h1>
          <p className="text-gray-600 mt-2">
            Manage your profile to get better job matches
          </p>
        </div>

        {/* Completion Status */}
        <ProfileCompletion completion={completion} />

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b">
            <nav className="flex -mb-px">
              {tabs.map(tab => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      flex-1 py-4 px-6 text-center border-b-2 font-medium text-sm
                      transition flex items-center justify-center gap-2
                      ${activeTab === tab.id
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }
                    `}
                  >
                    <Icon className="w-5 h-5" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'overview' && <BasicInfo profile={profile} />}
            {activeTab === 'experience' && <ExperienceSection profile={profile} />}
            {activeTab === 'education' && <EducationSection profile={profile} />}
            {activeTab === 'skills' && <SkillsSection profile={profile} />}
            {activeTab === 'cv' && <CVUpload profile={profile} />}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
```

### Step 7: CV Upload Component

**File:** `frontend/src/components/profile/CVUpload.jsx`

```jsx
import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const CVUpload = ({ profile }) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: async (file) => {
      const formData = new FormData();
      formData.append('cv_file', file);
      
      const response = await axios.post('/api/profile/upload-cv/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['profile']);
      queryClient.invalidateQueries(['profile-completion']);
      setUploadStatus('success');
    },
    onError: (error) => {
      setUploadStatus('error');
      console.error('Upload failed:', error);
    }
  });

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file) => {
    // Validate file
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    
    if (!validTypes.includes(file.type)) {
      alert('Please upload a PDF, DOCX, or TXT file');
      return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
      alert('File size must be less than 10MB');
      return;
    }
    
    uploadMutation.mutate(file);
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Upload Your CV</h3>
        <p className="text-gray-600">
          Upload your CV and we'll automatically extract your experience, education, and skills.
        </p>
      </div>

      {/* Current CV */}
      {profile?.cv_file && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
          <FileText className="w-5 h-5 text-green-600 mt-0.5" />
          <div className="flex-1">
            <p className="font-medium text-green-900">CV Uploaded</p>
            <p className="text-sm text-green-700 mt-1">
              Uploaded on {new Date(profile.updated_at).toLocaleDateString()}
            </p>
            <a
              href={profile.cv_file}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-green-600 hover:text-green-700 underline mt-2 inline-block"
            >
              View current CV
            </a>
          </div>
        </div>
      )}

      {/* Upload Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-lg p-12 text-center transition
          ${dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
          }
          ${uploadMutation.isLoading ? 'opacity-50 pointer-events-none' : ''}
        `}
      >
        <input
          type="file"
          id="cv-upload"
          accept=".pdf,.docx,.doc,.txt"
          onChange={handleChange}
          className="hidden"
        />
        
        <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        
        <label
          htmlFor="cv-upload"
          className="cursor-pointer"
        >
          <span className="text-blue-600 hover:text-blue-700 font-medium">
            Click to upload
          </span>
          <span className="text-gray-600"> or drag and drop</span>
        </label>
        
        <p className="text-sm text-gray-500 mt-2">
          PDF, DOCX, or TXT (max 10MB)
        </p>
        
        {uploadMutation.isLoading && (
          <div className="mt-4">
            <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto"></div>
            <p className="text-sm text-gray-600 mt-2">Uploading and parsing...</p>
          </div>
        )}
      </div>

      {/* Success Message */}
      {uploadStatus === 'success' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
          <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
          <div>
            <p className="font-medium text-green-900">CV Processed Successfully!</p>
            <p className="text-sm text-green-700 mt-1">
              Your profile has been automatically updated with information from your CV.
            </p>
          </div>
        </div>
      )}

      {/* Error Message */}
      {uploadStatus === 'error' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
          <div>
            <p className="font-medium text-red-900">Upload Failed</p>
            <p className="text-sm text-red-700 mt-1">
              Failed to process your CV. Please try again or contact support.
            </p>
          </div>
        </div>
      )}

      {/* Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">Tips for best results:</h4>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
          <li>Use a standard CV format with clear section headings</li>
          <li>Include dates in YYYY-MM format</li>
          <li>List skills explicitly in a dedicated section</li>
          <li>PDF format usually provides the best results</li>
        </ul>
      </div>
    </div>
  );
};

export default CVUpload;
```

---

## ✅ Phase 2A Verification

### Backend Tests

```bash
# Test profile endpoint
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/profile/

# Test CV upload
curl -X POST -H "Authorization: Bearer <token>" \
  -F "cv_file=@/path/to/cv.pdf" \
  http://localhost:8000/api/profile/upload-cv/

# Test completion status
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/profile/completion/
```

### Success Criteria

- [ ] Profile endpoint returns user profile
- [ ] CV upload extracts text correctly
- [ ] AWS Bedrock parses CV into structured data
- [ ] Profile auto-fills from parsed CV
- [ ] Experience, education, certifications created
- [ ] Profile completion percentage calculates correctly
- [ ] Match scores work with complete profiles (Phase 1C integration)

---

**Phase 2A Complete! ✅**
Proceed to Phase 2B: Rashid AI Core
