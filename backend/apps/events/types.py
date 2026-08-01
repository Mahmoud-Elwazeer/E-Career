"""
Event type constants.
Every event type used in the system must be defined here.
"""

# User Events
USER_REGISTERED = "user_registered"
USER_LOGGED_IN = "user_logged_in"
USER_LOGGED_OUT = "user_logged_out"
USER_PROFILE_UPDATED = "user_profile_updated"
USER_DEACTIVATED = "user_deactivated"

# Job Events
JOB_VIEWED = "job_viewed"
JOB_SAVED = "job_saved"
JOB_UNSAVED = "job_unsaved"
JOB_APPLIED = "job_applied"
JOB_DISMISSED = "job_dismissed"
JOB_SHARED = "job_shared"
JOB_REPORTED = "job_reported"

# Search Events
SEARCH_PERFORMED = "search_performed"
SEARCH_RESULT_CLICKED = "search_result_clicked"
SEARCH_FILTER_APPLIED = "search_filter_applied"

# CV Events
CV_UPLOADED = "cv_uploaded"
CV_PARSED = "cv_parsed"
CV_DELETED = "cv_deleted"

# AI Events
AI_CONVERSATION_STARTED = "ai_conversation_started"
AI_MESSAGE_SENT = "ai_message_sent"
AI_MODEL_CALLED = "ai_model_called"

# Employer Events
EMPLOYER_JOB_POSTED = "employer_job_posted"
EMPLOYER_JOB_UPDATED = "employer_job_updated"
EMPLOYER_JOB_CLOSED = "employer_job_closed"
EMPLOYER_CANDIDATE_VIEWED = "employer_candidate_viewed"
EMPLOYER_CANDIDATE_SHORTLISTED = "employer_candidate_shortlisted"

# System Events
SCRAPER_RUN_STARTED = "scraper_run_started"
SCRAPER_RUN_COMPLETED = "scraper_run_completed"
SCRAPER_RUN_FAILED = "scraper_run_failed"
VERIFICATION_COMPLETED = "verification_completed"
VERIFICATION_REJECTED = "verification_rejected"
SYNC_TYPESENSE_COMPLETED = "sync_typesense_completed"
DAILY_LIVENESS_COMPLETED = "daily_liveness_completed"

# Recommendation Events
RECOMMENDATION_SHOWN = "recommendation_shown"
RECOMMENDATION_CLICKED = "recommendation_clicked"
RECOMMENDATION_DISMISSED = "recommendation_dismissed"

# Interview Events
INTERVIEW_SESSION_STARTED = "interview_session_started"
INTERVIEW_SESSION_COMPLETED = "interview_session_completed"
INTERVIEW_ANSWER_SUBMITTED = "interview_answer_submitted"

# Talent Score Events
TALENT_SCORE_UPDATED = "talent_score_updated"

# Learning Events
LEARNING_COMPLETED = "learning_completed"
LEARNING_STARTED = "learning_started"

# Skill Events
SKILL_ADDED = "skill_added"
SKILL_VERIFIED = "skill_verified"
SKILL_REMOVED = "skill_removed"

# Goal Events
GOAL_SET = "goal_set"
GOAL_UPDATED = "goal_updated"
GOAL_COMPLETED = "goal_completed"

# Career Brain Events
CAREER_BRAIN_UPDATED = "career_brain_updated"
CAREER_BRAIN_CONFIDENCE_UPDATED = "career_brain_confidence_updated"
