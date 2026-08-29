"""
Celery tasks for career intelligence features.

This module contains background tasks for:
- Talent score recalculation
- Profile updates
- Learning progress tracking
"""

from __future__ import annotations

import structlog
from celery import shared_task
from django.utils import timezone

logger = structlog.get_logger()


@shared_task(bind=True, max_retries=3)
def recalculate_talent_score(self, user_id: int) -> dict:
    """
    Recalculate talent score for a user.
    
    Triggered by:
    - CV upload
    - Skill add
    - Interview complete
    - Learning add
    
    Args:
        user_id: User ID to recalculate score for
        
    Returns:
        Dictionary with score calculation results
    """
    from django.contrib.auth import get_user_model
    from apps.career.scoring_engine import ScoringEngine
    
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error("user_not_found", user_id=user_id)
        return {"error": "User not found"}
    
    try:
        # Calculate and save scores
        engine = ScoringEngine(user)
        result = engine.calculate_and_save()
        
        logger.info(
            "talent_score_recalculated",
            user_id=user_id,
            overall_score=result["overall_score"],
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "overall_score": result["overall_score"],
            "dimensions": result["dimensions"],
        }
        
    except Exception as e:
        logger.error(
            "talent_score_calculation_failed",
            user_id=user_id,
            error=str(e),
        )
        raise self.retry(exc=e, countdown=60)  # Retry after 1 minute


@shared_task(bind=True, max_retries=3)
def update_completeness_score(self, user_id: int) -> dict:
    """
    Update profile completeness score for a user.
    
    Args:
        user_id: User ID to update
        
    Returns:
        Dictionary with completeness score
    """
    from django.contrib.auth import get_user_model
    from apps.career.models import CareerProfile
    
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        profile = CareerProfile.objects.get(user=user)
        
        result = profile.update_completeness()
        
        logger.info(
            "completeness_score_updated",
            user_id=user_id,
            score=result["score"],
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "completeness_score": result["score"],
        }
        
    except User.DoesNotExist:
        logger.error("user_not_found", user_id=user_id)
        return {"error": "User not found"}
    except CareerProfile.DoesNotExist:
        logger.error("career_profile_not_found", user_id=user_id)
        return {"error": "Career profile not found"}


@shared_task
def batch_recalculate_talent_scores() -> dict:
    """
    Batch recalculate talent scores for all users.
    
    Use this after major scoring engine updates.
    
    Returns:
        Dictionary with batch processing results
    """
    from django.contrib.auth import get_user_model
    from apps.career.scoring_engine import ScoringEngine
    
    User = get_user_model()
    
    users = User.objects.filter(is_active=True)
    total = users.count()
    success_count = 0
    fail_count = 0
    
    for user in users:
        try:
            engine = ScoringEngine(user)
            engine.calculate_and_save()
            success_count += 1
        except Exception as e:
            logger.error(
                "batch_score_calculation_failed",
                user_id=user.id,
                error=str(e),
            )
            fail_count += 1
    
    logger.info(
        "batch_talent_scores_recalculated",
        total=total,
        success=success_count,
        failed=fail_count,
    )
    
    return {
        "total": total,
        "success": success_count,
        "failed": fail_count,
    }


@shared_task(bind=True, max_retries=3)
def sync_career_brain(self, user_id: int) -> dict:
    """
    Sync CareerBrain from current CareerProfile/skills/learning data.

    Triggered via post_save signals on CareerProfile, CareerUserSkill,
    CareerLearning, JobApplication, and InterviewSession.

    Uses CareerBrainService.update_brain() which aggregates all user data
    and generates AI observations via Bedrock when available.
    """
    from apps.career.models import CareerProfile
    from apps.career.career_brain_service import career_brain_service

    try:
        CareerProfile.objects.get(user_id=user_id)
    except CareerProfile.DoesNotExist:
        logger.warning("career_brain_sync_no_profile", user_id=user_id)
        return {"skipped": True, "reason": "No CareerProfile yet"}

    try:
        result = career_brain_service.update_brain(user_id)
        if 'error' in result:
            logger.error("career_brain_sync_error", user_id=user_id, error=result['error'])
            return result

        logger.info("career_brain_synced", user_id=user_id, confidence=result.get('confidence_score'))
        return {"success": True, "user_id": user_id, **result}

    except Exception as exc:
        logger.error("career_brain_sync_failed", user_id=user_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60)