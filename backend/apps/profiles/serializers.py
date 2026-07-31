"""
Profile serializers for API endpoints
"""

import logging
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.users.models import UserProfile, JobMatchScore
from .cv_parser import CVParser
from apps.events.emitter import emit
from apps.events.types import CV_UPLOADED, CV_PARSED

User = get_user_model()
logger = logging.getLogger(__name__)


class UserProfileSerializer(serializers.ModelSerializer):
    """Full user profile serializer"""

    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    completion_percentage = serializers.SerializerMethodField()
    is_complete = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'id', 'email', 'full_name',
            'cv_file', 'cv_uploaded_at', 'cv_parse_status',
            'portfolio_url',
            'skills', 'experience_years', 'education',
            'languages', 'certifications', 'current_role',
            'desired_roles', 'desired_locations',
            'preferred_type', 'open_to_remote',
            'min_salary', 'salary_currency',
            'email_alerts', 'alert_frequency', 'min_match_score',
            'completion_percentage', 'is_complete',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'email', 'full_name',
            'cv_uploaded_at', 'cv_parse_status',
            'skills', 'experience_years', 'education',
            'languages', 'certifications', 'current_role',
            'created_at', 'updated_at'
        ]

    def get_completion_percentage(self, obj):
        """Calculate profile completion percentage"""
        score = 0

        # CV uploaded (30%)
        if obj.cv_file:
            score += 30

        # Skills (20%)
        if obj.skills and len(obj.skills) >= 5:
            score += 20
        elif obj.skills and len(obj.skills) > 0:
            score += 10

        # Experience (15%)
        if obj.experience_years and obj.experience_years > 0:
            score += 15

        # Education (15%)
        if obj.education and len(obj.education) > 0:
            score += 15

        # Job preferences (10%)
        if obj.desired_roles and len(obj.desired_roles) > 0:
            score += 5
        if obj.desired_locations and len(obj.desired_locations) > 0:
            score += 5

        # Portfolio (5%)
        if obj.portfolio_url:
            score += 5

        # Languages (5%)
        if obj.languages and len(obj.languages) > 0:
            score += 5

        return min(score, 100)

    def get_is_complete(self, obj):
        """Check if profile is complete enough for matching"""
        return self.get_completion_percentage(obj) >= 60


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""

    class Meta:
        model = UserProfile
        fields = [
            'portfolio_url',
            'desired_roles', 'desired_locations',
            'preferred_type', 'open_to_remote',
            'min_salary', 'salary_currency',
            'email_alerts', 'alert_frequency', 'min_match_score'
        ]


class CVUploadSerializer(serializers.Serializer):
    """Handles CV file upload and parsing"""

    cv_file = serializers.FileField()

    def validate_cv_file(self, value):
        """Validate CV file"""
        try:
            # Check file format by attempting extraction
            CVParser.extract_text(value)
            value.seek(0)  # Reset file pointer
            return value
        except ValueError as e:
            raise serializers.ValidationError(str(e))
        except Exception as e:
            raise serializers.ValidationError(f"Invalid file: {str(e)}")

    def save(self, user):
        """Parse CV and update profile"""
        cv_file = self.validated_data['cv_file']

        # Get or create profile
        profile, created = UserProfile.objects.get_or_create(user=user)

        # Emit CV_UPLOADED event
        try:
            emit(
                event_type=CV_UPLOADED,
                category="user",
                user=user,
                target_type="cv",
                target_id=str(profile.id) if profile.id else "new",
                data={"filename": cv_file.name, "size": cv_file.size},
                request=None,
            )
        except Exception:
            pass

        # Extract text
        try:
            cv_text = CVParser.extract_text(cv_file)
            cv_file.seek(0)
        except Exception as e:
            raise serializers.ValidationError(f"Failed to extract text from CV: {str(e)}")

        # Parse with AWS Bedrock (if available)
        parsed_data = None
        try:
            from ai.bedrock import bedrock_service
            if bedrock_service.is_available:
                parsed_data = bedrock_service.parse_cv(cv_text)
        except Exception as e:
            logger.warning(f"Bedrock parsing failed, using basic extraction: {e}")

        # Emit CV_PARSED event
        try:
            emit(
                event_type=CV_PARSED,
                category="user",
                user=user,
                target_type="cv",
                target_id=str(profile.id) if profile.id else "new",
                data={
                    "parser_used": CVParser().parse_cv(cv_file).parser_used,
                    "has_parsed_data": parsed_data is not None,
                    "skills_extracted": len(parsed_data.get('skills', {}).get('technical', [])) if parsed_data else 0,
                },
                request=None,
            )
        except Exception:
            pass

        # Update profile
        profile.cv_file = cv_file
        profile.cv_uploaded_at = timezone.now()
        profile.cv_parse_status = 'done' if parsed_data else 'pending'

        # Auto-fill profile fields from parsed data
        if parsed_data:
            self._update_from_parsed_data(profile, parsed_data)

        profile.save()

        return profile

    def _update_from_parsed_data(self, profile, parsed_data):
        """Update profile from parsed CV data"""

        # Personal info
        if parsed_data.get('personal'):
            personal = parsed_data['personal']
            if personal.get('portfolio'):
                profile.portfolio_url = personal['portfolio']

        # Skills
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

        # Experience
        if parsed_data.get('experience'):
            profile.education = parsed_data.get('education', [])

            # Calculate years of experience
            from datetime import datetime
            total_months = 0

            for exp in parsed_data['experience']:
                try:
                    start_str = exp.get('start_date')
                    end_str = exp.get('end_date')

                    if not start_str:
                        continue

                    start = datetime.strptime(start_str, '%Y-%m')

                    if end_str == 'Present' or not end_str:
                        end = datetime.now()
                    else:
                        end = datetime.strptime(end_str, '%Y-%m')

                    delta_months = (end.year - start.year) * 12 + (end.month - start.month)
                    total_months += max(0, delta_months)
                except Exception as e:
                    logger.warning(f"Failed to parse experience dates: {e}")

            profile.experience_years = total_months / 12

            # Set current role
            if parsed_data['experience']:
                current_exp = next(
                    (e for e in parsed_data['experience'] if e.get('end_date') == 'Present'),
                    parsed_data['experience'][0]
                )
                profile.current_role = current_exp.get('title', '')

        # Education
        if parsed_data.get('education'):
            profile.education = parsed_data['education']

        # Certifications
        if parsed_data.get('certifications'):
            profile.certifications = parsed_data['certifications']


class JobMatchScoreSerializer(serializers.ModelSerializer):
    """Serializer for job match scores"""

    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company.name', read_only=True)
    job_slug = serializers.CharField(source='job.slug', read_only=True)

    class Meta:
        model = JobMatchScore
        fields = [
            'id', 'job', 'job_title', 'company_name', 'job_slug',
            'score', 'breakdown', 'calculated_at'
        ]


class ProfileCompletionSerializer(serializers.Serializer):
    """Serializer for profile completion status"""

    total_score = serializers.IntegerField()
    is_complete = serializers.BooleanField()
    sections = serializers.DictField(child=serializers.DictField())

    class Meta:
        fields = ['total_score', 'is_complete', 'sections']


class SkillsUpdateSerializer(serializers.Serializer):
    """Serializer for updating skills manually"""

    skills = serializers.ListField(
        child=serializers.CharField(max_length=100),
        allow_empty=False
    )

    def validate_skills(self, value):
        """Validate skills list"""
        if len(value) > 50:
            raise serializers.ValidationError("Maximum 50 skills allowed")
        return [skill.strip() for skill in value if skill.strip()]


class PreferencesUpdateSerializer(serializers.Serializer):
    """Serializer for updating job preferences"""

    desired_roles = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_null=True
    )
    desired_locations = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_null=True
    )
    preferred_type = serializers.CharField(max_length=20, required=False, allow_null=True)
    open_to_remote = serializers.BooleanField(required=False)
    min_salary = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    salary_currency = serializers.CharField(max_length=3, required=False)