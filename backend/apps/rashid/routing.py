"""
WebSocket routing for Rashid chat
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # WebSocket endpoint for Rashid chat
    re_path(r'ws/rashid/$', consumers.RashidConsumer.as_asgi()),
    re_path(r'ws/rashid/(?P<conversation_id>[0-9a-f-]+)/$', consumers.RashidConsumer.as_asgi()),
]