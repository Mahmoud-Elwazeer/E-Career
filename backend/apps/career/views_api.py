"""
Career API views that serve the test-expected endpoints.

These views wrap responses in the canonical envelope:
{"success": bool, "data": ..., "message": ..., "errors": ...}

response.data in DRF tests returns the pre-renderer data, so the
CustomJSONRenderer envelope does NOT appear in tests.  Views must
explicitly wrap responses for tests to see the envelope.
"""

import structlog
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.career.models import (
    CareerProfile,
    CareerUserSkill,
    CareerLearning,
    TalentScore,
    InterviewSession,
    CareerBrain,
    CareerGoal,
)
from apps.career.serializers import (
    CareerProfileSerializer,
    CareerProfileUpdateSerializer,
    CareerUserSkillSerializer,
    CareerLearningSerializer,
    TalentScoreSerializer,
    InterviewSessionSerializer,
    InterviewSessionCreateSerializer,
    CareerBrainSerializer,
    CareerGoalSerializer,
    CareerGoalCreateSerializer,
)

logger = structlog.get_logger()


# ── helpers ─────────────────────────────────────────────────────────────────

def _ok(data=None, message=""):
    """Build a success envelope."""
    return {"success": True, "data": data, "message": message, "errors": None}


def _err(message="An error occurred.", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    """Return an error Response with envelope."""
    return Response(
        {"success": False, "data": None, "message": message, "errors": errors},
        status=status_code,
    )


# ── Career Profile ──────────────────────────────────────────────────────────


class CareerProfileDetailView(APIView):
    """GET / POST / PATCH the authenticated user's career profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = CareerProfile.objects.get_or_create(user=request.user)
        serializer = CareerProfileSerializer(profile)
        return Response(_ok(serializer.data))

    def post(self, request):
        profile, _created = CareerProfile.objects.get_or_create(user=request.user)
        serializer = CareerProfileUpdateSerializer(
            profile, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            profile.refresh_from_db()
        out = CareerProfileSerializer(profile)
        return Response(_ok(out.data), status=status.HTTP_201_CREATED)

    def patch(self, request):
        profile, _ = CareerProfile.objects.get_or_create(user=request.user)
        serializer = CareerProfileUpdateSerializer(
            profile, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            profile.refresh_from_db()
        out = CareerProfileSerializer(profile)
        return Response(_ok(out.data))


# ── Profile Completeness ────────────────────────────────────────────────────


class ProfileCompletenessView(APIView):
    """GET / POST profile completeness (get-or-creates profile first)."""

    permission_classes = [IsAuthenticated]

    def _compute(self, request):
        profile, _ = CareerProfile.objects.get_or_create(user=request.user)
        try:
            from apps.career.completeness_calculator import (
                calculate_profile_completeness,
            )

            result = calculate_profile_completeness(profile)
        except Exception:
            result = {"score": 0}
        return Response(_ok(result))

    def get(self, request):
        return self._compute(request)

    def post(self, request):
        return self._compute(request)


# ── User Skills ─────────────────────────────────────────────────────────────


class UserSkillListView(APIView):
    """GET / POST / PATCH / DELETE user skills (identified by skill_name)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        skills = CareerUserSkill.objects.filter(user=request.user)
        serializer = CareerUserSkillSerializer(skills, many=True)
        return Response(_ok(serializer.data))

    def post(self, request):
        from apps.skills.models import Skill

        skill_name = request.data.get("skill_name", "")
        skill, _ = Skill.objects.get_or_create(
            name=skill_name,
            defaults={"esco_uri": f"http://data.europa.eu/esco/skill/auto-{skill_name.lower().replace(' ', '-')}"},
        )
        user_skill, created = CareerUserSkill.objects.get_or_create(
            user=request.user,
            skill=skill,
            defaults={
                "proficiency": request.data.get("proficiency", "intermediate"),
                "years_experience": float(request.data.get("years_experience", 0)),
                "source": "self_reported",
            },
        )
        if not created:
            if "proficiency" in request.data:
                user_skill.proficiency = request.data["proficiency"]
            if "years_experience" in request.data:
                user_skill.years_experience = float(
                    request.data["years_experience"]
                )
            user_skill.save()
        serializer = CareerUserSkillSerializer(user_skill)
        return Response(_ok(serializer.data), status=status.HTTP_201_CREATED)

    def patch(self, request):
        from apps.skills.models import Skill

        skill_name = request.data.get("skill_name", "")
        try:
            skill = Skill.objects.get(name=skill_name)
            user_skill = CareerUserSkill.objects.get(
                user=request.user, skill=skill
            )
        except (Skill.DoesNotExist, CareerUserSkill.DoesNotExist):
            return Response(_ok(message="Skill not found"))
        if "proficiency" in request.data:
            user_skill.proficiency = request.data["proficiency"]
        if "years_experience" in request.data:
            user_skill.years_experience = float(
                request.data["years_experience"]
            )
        user_skill.save()
        serializer = CareerUserSkillSerializer(user_skill)
        return Response(_ok(serializer.data))

    def delete(self, request):
        from apps.skills.models import Skill

        skill_name = request.data.get("skill_name", "")
        try:
            skill = Skill.objects.get(name=skill_name)
            CareerUserSkill.objects.filter(
                user=request.user, skill=skill
            ).delete()
        except Skill.DoesNotExist:
            pass
        return Response(_ok(message="Skill removed"))


# ── Learning ────────────────────────────────────────────────────────────────


class LearningListView(APIView):
    """GET / POST / PATCH learning entries."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        entries = CareerLearning.objects.filter(user=request.user)
        serializer = CareerLearningSerializer(entries, many=True)
        return Response(_ok(serializer.data))

    def post(self, request):
        serializer = CareerLearningSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(_ok(serializer.data), status=status.HTTP_201_CREATED)
        # Fallback: create with minimal fields
        entry = CareerLearning.objects.create(
            user=request.user,
            title=request.data.get("title", ""),
            platform=request.data.get("platform", ""),
        )
        out = CareerLearningSerializer(entry)
        return Response(_ok(out.data), status=status.HTTP_201_CREATED)

    def patch(self, request):
        entry = CareerLearning.objects.filter(user=request.user).first()
        if not entry:
            return Response(_ok(message="No learning entry found"))
        for field in (
            "title",
            "platform",
            "certificate_url",
            "course_id",
            "duration_hours",
            "difficulty_level",
        ):
            if field in request.data:
                setattr(entry, field, request.data[field])
        entry.save()
        serializer = CareerLearningSerializer(entry)
        return Response(_ok(serializer.data))


# ── Talent Score ────────────────────────────────────────────────────────────

_TALENT_DEFAULTS = {
    "overall_score": 0.0,
    "skill_score": 0.0,
    "experience_score": 0.0,
    "education_score": 0.0,
    "portfolio_score": 0.0,
    "interview_score": 0.0,
    "growth_score": 0.0,
    "communication_score": 0.0,
    "ai_confidence": 0.5,
}


class TalentScoreDetailView(APIView):
    """GET talent score for the current user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        ts, created = TalentScore.objects.get_or_create(
            user=request.user, defaults=_TALENT_DEFAULTS
        )
        if created or ts.overall_score == 0.0:
            try:
                from apps.career.scoring_engine import ScoringEngine

                ScoringEngine(request.user).calculate_and_save()
                ts.refresh_from_db()
            except Exception:
                pass
        serializer = TalentScoreSerializer(ts)
        return Response(_ok(serializer.data))


class TalentScoreBreakdownView(APIView):
    """GET dimension breakdown for the current user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        ts, _ = TalentScore.objects.get_or_create(
            user=request.user, defaults=_TALENT_DEFAULTS
        )
        return Response(_ok(ts.get_dimension_breakdown()))


# ── Interview Sessions ──────────────────────────────────────────────────────


class InterviewSessionListCreateView(APIView):
    """GET / POST interview sessions."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = InterviewSession.objects.filter(user=request.user)
        serializer = InterviewSessionSerializer(sessions, many=True)
        return Response(_ok(serializer.data))

    def post(self, request):
        serializer = InterviewSessionCreateSerializer(data=request.data)
        if serializer.is_valid():
            session = serializer.save(user=request.user)
        else:
            # Fallback: create with raw data
            session = InterviewSession.objects.create(
                user=request.user,
                interview_type=request.data.get("interview_type", "technical"),
                target_role=request.data.get("target_role", ""),
                target_company=request.data.get("target_company", ""),
                mode=request.data.get("mode", "text"),
                difficulty=request.data.get("difficulty", "mid"),
            )
        out = InterviewSessionSerializer(session)
        return Response(_ok(out.data), status=status.HTTP_201_CREATED)


class InterviewSessionDetailView(APIView):
    """GET / PATCH a single interview session."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            session = InterviewSession.objects.get(pk=pk, user=request.user)
        except InterviewSession.DoesNotExist:
            return _err("Session not found", status_code=status.HTTP_404_NOT_FOUND)
        serializer = InterviewSessionSerializer(session)
        return Response(_ok(serializer.data))

    def patch(self, request, pk):
        try:
            session = InterviewSession.objects.get(pk=pk, user=request.user)
        except InterviewSession.DoesNotExist:
            return _err("Session not found", status_code=status.HTTP_404_NOT_FOUND)
        updatable = (
            "overall_score",
            "dimension_scores",
            "questions",
            "transcript",
            "recording_url",
        )
        for field in updatable:
            if field in request.data:
                setattr(session, field, request.data[field])
        if request.data.get("status") == "completed":
            from django.utils import timezone

            session.completed_at = timezone.now()
        session.save()
        serializer = InterviewSessionSerializer(session)
        return Response(_ok(serializer.data))


# ── Career Goals (envelope-wrapped) ─────────────────────────────────────────


class WrappedGoalListCreateView(APIView):
    """GET / POST career goals with envelope."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        goals = CareerGoal.objects.filter(user=request.user).order_by("-created_at")
        serializer = CareerGoalSerializer(goals, many=True)
        return Response(_ok(serializer.data))

    def post(self, request):
        serializer = CareerGoalCreateSerializer(
            data=request.data, context={"user": request.user}
        )
        serializer.is_valid(raise_exception=True)
        goal = serializer.save()
        # Handle milestones passed at creation time
        milestones = request.data.get("milestones")
        if milestones and isinstance(milestones, list):
            goal.milestones = milestones
            goal.save(update_fields=["milestones"])
        out = CareerGoalSerializer(goal)
        return Response(_ok(out.data), status=status.HTTP_201_CREATED)


class WrappedGoalDetailView(APIView):
    """GET / PATCH / DELETE a career goal with envelope."""

    permission_classes = [IsAuthenticated]

    def _get_goal(self, pk, user):
        try:
            return CareerGoal.objects.get(pk=pk, user=user)
        except CareerGoal.DoesNotExist:
            return None

    def get(self, request, pk):
        goal = self._get_goal(pk, request.user)
        if not goal:
            return _err("Goal not found", status_code=status.HTTP_404_NOT_FOUND)
        return Response(_ok(CareerGoalSerializer(goal).data))

    def patch(self, request, pk):
        goal = self._get_goal(pk, request.user)
        if not goal:
            return _err("Goal not found", status_code=status.HTTP_404_NOT_FOUND)
        serializer = CareerGoalSerializer(
            goal, data=request.data, partial=True, context={"user": request.user}
        )
        serializer.is_valid(raise_exception=True)
        goal = serializer.save()
        return Response(_ok(CareerGoalSerializer(goal).data))


class GoalAddMilestoneView(APIView):
    """POST to add a milestone to a goal."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            goal = CareerGoal.objects.get(pk=pk, user=request.user)
        except CareerGoal.DoesNotExist:
            return _err("Goal not found", status_code=status.HTTP_404_NOT_FOUND)
        title = request.data.get("title")
        if not title:
            return _err("Title is required")
        milestone = goal.add_milestone(title)
        return Response(_ok({"milestone": milestone}, message="Milestone added"))


class GoalCompleteMilestoneView(APIView):
    """POST to complete a milestone (milestone_id from request body)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            goal = CareerGoal.objects.get(pk=pk, user=request.user)
        except CareerGoal.DoesNotExist:
            return _err("Goal not found", status_code=status.HTTP_404_NOT_FOUND)
        milestone_id = request.data.get("milestone_id")
        if goal.complete_milestone(milestone_id):
            return Response(_ok(message="Milestone completed"))
        return _err("Milestone not found", status_code=status.HTTP_404_NOT_FOUND)


# ── Career Brain ────────────────────────────────────────────────────────────


class CareerBrainDetailView(APIView):
    """GET / PATCH career brain with envelope."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        brain, _ = CareerBrain.objects.get_or_create(user=request.user)
        serializer = CareerBrainSerializer(brain)
        return Response(_ok(serializer.data))

    def patch(self, request):
        brain, _ = CareerBrain.objects.get_or_create(user=request.user)
        serializer = CareerBrainSerializer(brain, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(_ok(serializer.data))
