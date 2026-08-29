"""
Signals for the career app.

Fires CareerBrain.update_from_profile() asynchronously whenever
CareerProfile, CareerUserSkill, or CareerLearning are saved.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='career.CareerProfile')
@receiver(post_save, sender='career.CareerUserSkill')
@receiver(post_save, sender='career.CareerLearning')
def trigger_career_brain_sync(sender, instance, **kwargs):
    from apps.career.tasks import sync_career_brain
    user_id = instance.user_id
    sync_career_brain.delay(user_id)


@receiver(post_save, sender='employers.JobApplication')
def trigger_career_brain_on_application(sender, instance, **kwargs):
    from apps.career.tasks import sync_career_brain
    user_id = instance.user_id
    sync_career_brain.delay(user_id)


@receiver(post_save, sender='interviews.InterviewSession')
def trigger_career_brain_on_interview(sender, instance, **kwargs):
    from apps.career.tasks import sync_career_brain
    user_id = instance.user_id
    sync_career_brain.delay(user_id)
