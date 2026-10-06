"""Outreach domain scaffolding (Task #15).

Company -> Contact -> Campaign -> Template -> Message -> Delivery -> Response,
DRY_RUN only. See apps/outreach/service.py for the compliance gate chain
(suppression / do-not-contact / rate limit) every message must pass through
before anything is even logged as "would have been sent" - there is
deliberately NO code path in this app that performs a real SMTP send.
"""
