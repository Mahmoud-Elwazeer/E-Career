"""
Interviews Django Models
"""
from django.db import models
from django.conf import settings


class InterviewSession(models.Model):
    """A mock interview session for a user."""
    
    INTERVIEW_TYPES = [
        ('technical', 'Technical'),
        ('behavioral', 'Behavioral'),
        ('coding', 'Coding'),
        ('system_design', 'System Design'),
        ('case_study', 'Case Study'),
    ]
    
    MODES = [('text', 'Text'), ('voice', 'Voice')]
    STATUS = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interview_sessions'
    )
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPES)
    target_role = models.CharField(max_length=200)
    difficulty = models.CharField(
        max_length=10,
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')],
        default='medium'
    )
    mode = models.CharField(max_length=10, choices=MODES, default='text')
    status = models.CharField(max_length=20, choices=STATUS, default='in_progress')
    
    overall_score = models.FloatField(null=True, blank=True)
    score_breakdown = models.JSONField(null=True, blank=True)
    feedback_summary = models.TextField(blank=True)
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = 'Interview Session'
        verbose_name_plural = 'Interview Sessions'
    
    def __str__(self):
        return f"{self.interview_type} - {self.target_role} - {self.user.email}"


class InterviewQuestion(models.Model):
    """A question in an interview session."""
    
    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_index = models.IntegerField()
    question_text = models.TextField()
    answer_text = models.TextField(blank=True)
    
    score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    score_details = models.JSONField(null=True, blank=True)
    
    answered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['question_index']
        unique_together = ('session', 'question_index')
        verbose_name = 'Interview Question'
        verbose_name_plural = 'Interview Questions'
    
    def __str__(self):
        return f"Q{self.question_index}: {self.question_text[:50]}..."