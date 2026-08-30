# PHASE 3B: Recommendation Engine

> **Dependencies:** Phase 2A complete  
> **Duration:** 3-4 hours  
> **Status:** Ready for GLM execution

---

## 🎯 Objectives

Implement AI-powered job matching and recommendations:
- Enhanced match scoring algorithm (AWS Bedrock)
- Alert dispatch logic
- Personalized feed
- Match score breakdown with explanations
- Recommended actions for improving matches

---

## 🔧 Implementation

### Step 1: Enhanced Matching Service

**File:** `backend/profiles/services.py` (update)

```python
"""
Enhanced job matching service with AI
"""

from typing import Dict, List
from django.db.models import Q
from jobs.models import Job
from profiles.models import UserProfile
from ai.bedrock_service import bedrock_service
import logging

logger = logging.getLogger(__name__)

class MatchingService:
    """Enhanced job matching with AI"""
    
    def calculate_match_score(self, profile: UserProfile, job: Job) -> float:
        """
        Calculate comprehensive match score using AI
        
        Returns:
            float: Match score 0-100
        """
        # Prepare data for AI
        profile_data = self._serialize_profile(profile)
        job_data = self._serialize_job(job)
        
        try:
            # Use AI for sophisticated matching
            match_result = bedrock_service.calculate_match_score(
                profile_data, job_data
            )
            return match_result.get('overall_score', 0)
        
        except Exception as e:
            logger.error(f"AI matching failed, falling back to basic algorithm: {e}")
            return self._basic_match_score(profile, job)
    
    def get_match_breakdown(self, profile: UserProfile, job: Job) -> Dict:
        """
        Get detailed match breakdown with AI insights
        
        Returns:
            dict: Detailed breakdown with scores and recommendations
        """
        profile_data = self._serialize_profile(profile)
        job_data = self._serialize_job(job)
        
        try:
            match_result = bedrock_service.calculate_match_score(
                profile_data, job_data
            )
            
            return {
                'overall_score': match_result.get('overall_score', 0),
                'breakdown': match_result.get('breakdown', {}),
                'strengths': match_result.get('strengths', []),
                'gaps': match_result.get('gaps', []),
                'recommendation': match_result.get('recommendation', ''),
                'improvement_tips': self._generate_improvement_tips(match_result)
            }
        
        except Exception as e:
            logger.error(f"Error getting match breakdown: {e}")
            return self._basic_match_breakdown(profile, job)
    
    def get_recommended_jobs(
        self,
        profile: UserProfile,
        limit: int = 20,
        min_score: float = 60.0
    ) -> List[Dict]:
        """
        Get personalized job recommendations
        
        Args:
            profile: User profile
            limit: Max number of jobs to return
            min_score: Minimum match score threshold
        
        Returns:
            List of {job, score, reasoning} dicts
        """
        # Build query based on profile preferences
        query = Q(is_active=True, is_legitimate=True)
        
        # Filter by preferred locations
        if profile.preferred_locations:
            location_query = Q()
            for loc in profile.preferred_locations:
                location_query |= Q(location__icontains=loc)
            query &= location_query
        
        # Filter by preferred job titles (fuzzy match)
        if profile.preferred_job_titles:
            title_query = Q()
            for title in profile.preferred_job_titles:
                title_query |= Q(title__icontains=title)
            query &= title_query
        
        # Filter by workplace preference
        if profile.workplace_preference:
            query &= Q(workplace_type=profile.workplace_preference)
        
        # Get candidate jobs
        jobs = Job.objects.filter(query).order_by('-posted_date')[:100]
        
        # Score and rank
        scored_jobs = []
        for job in jobs:
            score = self.calculate_match_score(profile, job)
            
            if score >= min_score:
                scored_jobs.append({
                    'job': job,
                    'score': score,
                    'reasoning': self._generate_match_reasoning(profile, job, score)
                })
        
        # Sort by score
        scored_jobs.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_jobs[:limit]
    
    def get_similar_jobs(self, job: Job, limit: int = 5) -> List[Job]:
        """Get jobs similar to the given job"""
        # Build similarity query
        query = Q(is_active=True, is_legitimate=True)
        query &= ~Q(id=job.id)  # Exclude the job itself
        
        # Same category
        if job.category:
            query &= Q(category=job.category)
        
        # Same location or similar
        if job.location:
            query &= Q(location__icontains=job.location.split(',')[0])
        
        # Similar experience level
        if job.experience_level:
            query &= Q(experience_level=job.experience_level)
        
        similar_jobs = Job.objects.filter(query).order_by('-posted_date')[:limit]
        
        return list(similar_jobs)
    
    def _serialize_profile(self, profile: UserProfile) -> Dict:
        """Serialize profile for AI processing"""
        return {
            'skills': profile.skills or [],
            'years_of_experience': profile.years_of_experience or 0,
            'current_position': profile.current_position or '',
            'education': [
                {
                    'degree': edu.degree,
                    'field': edu.field_of_study,
                    'institution': edu.institution
                }
                for edu in profile.education.all()
            ],
            'experience': [
                {
                    'title': exp.title,
                    'company': exp.company,
                    'duration_months': self._calculate_duration_months(exp)
                }
                for exp in profile.experience.all()
            ],
            'preferred_locations': profile.preferred_locations or [],
            'preferred_industries': profile.preferred_industries or [],
            'desired_salary': profile.desired_salary_min,
            'languages': profile.languages or []
        }
    
    def _serialize_job(self, job: Job) -> Dict:
        """Serialize job for AI processing"""
        return {
            'title': job.title,
            'description': job.description[:500],  # Truncate for API limits
            'requirements': job.requirements[:500],
            'location': job.location,
            'workplace_type': job.workplace_type,
            'employment_type': job.employment_type,
            'experience_level': job.experience_level,
            'salary_min': float(job.salary_min) if job.salary_min else None,
            'salary_max': float(job.salary_max) if job.salary_max else None,
            'company': {
                'name': job.company.name,
                'industry': job.company.industry,
                'size': job.company.size
            },
            'skills_required': [skill.name for skill in job.skills_required.all()],
            'category': job.category.name if job.category else None
        }
    
    def _basic_match_score(self, profile: UserProfile, job: Job) -> float:
        """Fallback basic matching algorithm"""
        score = 0.0
        
        # Skills match (40%)
        if profile.skills and job.skills_required.exists():
            profile_skills = set(skill.lower() for skill in profile.skills)
            job_skills = set(
                skill.name.lower() for skill in job.skills_required.all()
            )
            
            if job_skills:
                skills_match = len(profile_skills & job_skills) / len(job_skills)
                score += skills_match * 40
        
        # Location match (20%)
        if profile.preferred_locations and job.location:
            location_match = any(
                loc.lower() in job.location.lower()
                for loc in profile.preferred_locations
            )
            if location_match:
                score += 20
        
        # Experience match (20%)
        if profile.years_of_experience and job.experience_level:
            exp_mapping = {
                'entry': (0, 2),
                'junior': (1, 3),
                'mid': (3, 6),
                'senior': (6, 10),
                'lead': (8, None),
                'executive': (10, None)
            }
            
            min_exp, max_exp = exp_mapping.get(job.experience_level, (0, None))
            user_exp = profile.years_of_experience
            
            if max_exp is None:
                if user_exp >= min_exp:
                    score += 20
            elif min_exp <= user_exp <= max_exp:
                score += 20
        
        # Salary match (10%)
        if profile.desired_salary_min and job.salary_min:
            if job.salary_min >= profile.desired_salary_min:
                score += 10
        
        # Workplace preference (10%)
        if profile.workplace_preference and job.workplace_type:
            if profile.workplace_preference == job.workplace_type:
                score += 10
        
        return min(score, 100)
    
    def _basic_match_breakdown(self, profile: UserProfile, job: Job) -> Dict:
        """Fallback basic breakdown"""
        return {
            'overall_score': self._basic_match_score(profile, job),
            'breakdown': {
                'skills': {'score': 0, 'reasoning': 'Basic algorithm'},
                'experience': {'score': 0, 'reasoning': 'Basic algorithm'},
                'location': {'score': 0, 'reasoning': 'Basic algorithm'}
            },
            'strengths': [],
            'gaps': [],
            'recommendation': 'Consider applying if interested',
            'improvement_tips': []
        }
    
    def _generate_improvement_tips(self, match_result: Dict) -> List[str]:
        """Generate actionable tips to improve match score"""
        tips = []
        
        gaps = match_result.get('gaps', [])
        breakdown = match_result.get('breakdown', {})
        
        # Skills gaps
        if 'skills' in breakdown:
            skills_score = breakdown['skills'].get('score', 0)
            if skills_score < 70:
                missing_skills = breakdown['skills'].get('missing', [])
                if missing_skills:
                    tips.append(
                        f"Learn these skills to improve your match: {', '.join(missing_skills[:3])}"
                    )
        
        # Experience gaps
        if 'experience' in breakdown:
            exp_score = breakdown['experience'].get('score', 0)
            if exp_score < 70:
                tips.append(
                    "Gain more relevant experience in this field or highlight similar projects"
                )
        
        # Education gaps
        if 'education' in breakdown:
            edu_score = breakdown['education'].get('score', 0)
            if edu_score < 70:
                tips.append(
                    "Consider taking relevant courses or certifications"
                )
        
        return tips
    
    def _generate_match_reasoning(self, profile: UserProfile, job: Job, score: float) -> str:
        """Generate human-readable reasoning for match"""
        if score >= 90:
            return "Excellent match! Your profile aligns very well with this opportunity."
        elif score >= 75:
            return "Strong match. You meet most of the key requirements."
        elif score >= 60:
            return "Good match. Consider applying if the role interests you."
        else:
            return "Partial match. Some skills may need development."
    
    def _calculate_duration_months(self, experience) -> int:
        """Calculate experience duration in months"""
        from dateutil.relativedelta import relativedelta
        from datetime import datetime
        
        try:
            start = experience.start_date
            end = experience.end_date or datetime.now().date()
            
            delta = relativedelta(end, start)
            return delta.years * 12 + delta.months
        except:
            return 0


# Singleton instance
matching_service = MatchingService()
```

### Step 2: Recommendation API

**File:** `backend/profiles/views.py` (add)

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .services import matching_service
from jobs.serializers import JobListSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_recommendations(request):
    """
    Get personalized job recommendations
    
    GET /api/recommendations/?limit=20&min_score=60
    """
    try:
        profile = request.user.userprofile
        
        if not profile.is_complete:
            return Response({
                'error': 'Please complete your profile to get recommendations',
                'completion_url': '/profile/'
            }, status=400)
        
        # Get parameters
        limit = int(request.query_params.get('limit', 20))
        min_score = float(request.query_params.get('min_score', 60))
        
        # Get recommendations
        recommendations = matching_service.get_recommended_jobs(
            profile=profile,
            limit=limit,
            min_score=min_score
        )
        
        # Serialize
        results = []
        for rec in recommendations:
            job_data = JobListSerializer(
                rec['job'],
                context={'request': request}
            ).data
            
            results.append({
                'job': job_data,
                'match_score': rec['score'],
                'reasoning': rec['reasoning']
            })
        
        return Response({
            'count': len(results),
            'recommendations': results
        })
    
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_match_breakdown(request, job_slug):
    """
    Get detailed match breakdown for a specific job
    
    GET /api/jobs/{slug}/match-breakdown/
    """
    from jobs.models import Job
    
    try:
        profile = request.user.userprofile
        job = Job.objects.get(slug=job_slug)
        
        breakdown = matching_service.get_match_breakdown(profile, job)
        
        return Response(breakdown)
    
    except Job.DoesNotExist:
        return Response({'error': 'Job not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
```

**Update:** `backend/profiles/urls.py`

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProfileViewSet, get_job_recommendations, get_job_match_breakdown
)

router = DefaultRouter()
router.register(r'profile', ProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
    path('recommendations/', get_job_recommendations, name='job-recommendations'),
    path('jobs/<slug:job_slug>/match-breakdown/', get_job_match_breakdown, name='job-match-breakdown'),
]
```

---

## 🎨 Frontend Implementation

### Step 3: Recommendations Page

**File:** `frontend/src/pages/RecommendationsPage.jsx`

```jsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Target, TrendingUp, Lightbulb } from 'lucide-react';
import axios from 'axios';
import JobCard from '../components/jobs/JobCard';

const RecommendationsPage = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['recommendations'],
    queryFn: async () => {
      const response = await axios.get('/api/recommendations/?limit=20&min_score=60');
      return response.data;
    }
  });

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Target className="w-8 h-8 text-blue-600" />
            Recommended For You
          </h1>
          <p className="text-gray-600 mt-2">
            Jobs that match your skills and preferences
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-50 rounded-lg">
                <TrendingUp className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {data?.count || 0}
                </p>
                <p className="text-gray-600">Matches Found</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-50 rounded-lg">
                <Target className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {data?.recommendations?.filter(r => r.match_score >= 80).length || 0}
                </p>
                <p className="text-gray-600">Strong Matches</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-50 rounded-lg">
                <Lightbulb className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.round(
                    (data?.recommendations?.reduce((sum, r) => sum + r.match_score, 0) || 0) /
                    (data?.count || 1)
                  )}%
                </p>
                <p className="text-gray-600">Avg Match Score</p>
              </div>
            </div>
          </div>
        </div>

        {/* Recommendations */}
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : data?.count === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <p className="text-gray-600 mb-4">
              No recommendations found. Complete your profile to get better matches!
            </p>
            <a
              href="/profile"
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Complete Profile
            </a>
          </div>
        ) : (
          <div className="space-y-6">
            {data?.recommendations?.map(({ job, match_score, reasoning }) => (
              <div key={job.id} className="relative">
                {/* Match Badge */}
                <div className="absolute -top-3 -right-3 z-10">
                  <div className={`
                    px-4 py-2 rounded-full font-semibold text-sm shadow-lg
                    ${match_score >= 90 ? 'bg-green-500 text-white' : ''}
                    ${match_score >= 75 && match_score < 90 ? 'bg-blue-500 text-white' : ''}
                    ${match_score < 75 ? 'bg-gray-500 text-white' : ''}
                  `}>
                    {match_score}% Match
                  </div>
                </div>

                {/* Job Card */}
                <JobCard job={job} />

                {/* Reasoning */}
                <div className="mt-2 px-6 py-3 bg-blue-50 border border-blue-200 rounded-b-lg">
                  <p className="text-sm text-blue-800">
                    <strong>Why this matches:</strong> {reasoning}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default RecommendationsPage;
```

### Step 4: Match Breakdown Modal

**File:** `frontend/src/components/jobs/MatchBreakdownModal.jsx`

```jsx
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { X, CheckCircle, AlertCircle, Lightbulb } from 'lucide-react';
import axios from 'axios';

const MatchBreakdownModal = ({ jobSlug, onClose }) => {
  const { data, isLoading } = useQuery({
    queryKey: ['match-breakdown', jobSlug],
    queryFn: async () => {
      const response = await axios.get(`/api/jobs/${jobSlug}/match-breakdown/`);
      return response.data;
    }
  });

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="animate-spin w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full mx-auto"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">Match Breakdown</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Overall Score */}
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-32 h-32 rounded-full bg-blue-50 border-4 border-blue-600 mb-4">
              <span className="text-4xl font-bold text-blue-600">
                {data.overall_score}%
              </span>
            </div>
            <p className="text-gray-600">{data.recommendation}</p>
          </div>

          {/* Breakdown */}
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900">Detailed Breakdown</h3>
            
            {Object.entries(data.breakdown || {}).map(([key, value]) => (
              <div key={key} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-900 capitalize">{key}</span>
                  <span className="text-lg font-semibold text-blue-600">
                    {value.score}%
                  </span>
                </div>
                <p className="text-sm text-gray-600">{value.reasoning}</p>
              </div>
            ))}
          </div>

          {/* Strengths */}
          {data.strengths?.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                Your Strengths
              </h3>
              <ul className="space-y-2">
                {data.strengths.map((strength, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-gray-700">
                    <span className="text-green-600 mt-1">✓</span>
                    <span>{strength}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Gaps */}
          {data.gaps?.length > 0 && (
            <div>
              <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-yellow-600" />
                Areas to Improve
              </h3>
              <ul className="space-y-2">
                {data.gaps.map((gap, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-gray-700">
                    <span className="text-yellow-600 mt-1">!</span>
                    <span>{gap}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Improvement Tips */}
          {data.improvement_tips?.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
                <Lightbulb className="w-5 h-5" />
                How to Improve Your Match
              </h3>
              <ul className="space-y-2">
                {data.improvement_tips.map((tip, idx) => (
                  <li key={idx} className="text-sm text-blue-800">
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t flex justify-end gap-4">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Close
          </button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Apply Now
          </button>
        </div>
      </div>
    </div>
  );
};

export default MatchBreakdownModal;
```

---

## ✅ Phase 3B Verification

### Tests

```bash
# Test recommendations
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/recommendations/?limit=10

# Test match breakdown
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/jobs/senior-developer-abc/match-breakdown/
```

### Success Criteria

- [ ] AI-powered matching works
- [ ] Recommendations are personalized
- [ ] Match breakdown shows detailed analysis
- [ ] Improvement tips are actionable
- [ ] Similar jobs feature works
- [ ] Fallback to basic algorithm if AI fails

---

**Phase 3B Complete! ✅**
Proceed to Phase 3C: Admin Dashboard (final phase!)
