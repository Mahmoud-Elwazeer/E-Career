"""
Email app URL routes.
"""

from django.urls import path
from .views import TrackOpenView, TrackClickView, UnsubscribeView, EmailPreviewView

app_name = 'emails'

urlpatterns = [
    # Email tracking
    path('track/<uuid:tracking_id>/', TrackOpenView.as_view(), name='track_open'),
    path('click/<uuid:tracking_id>/', TrackClickView.as_view(), name='track_click'),
    
    # Unsubscribe
    path('unsubscribe/<int:user_id>/', UnsubscribeView.as_view(), name='unsubscribe'),
    
    # Admin preview
    path('preview/<int:template_id>/', EmailPreviewView.as_view(), name='preview'),
]