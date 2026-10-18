"""
Content-Security-Policy-Report-Only middleware (directive item 18).

Report-Only, not enforcing: this platform has never shipped a CSP before,
so switching straight to an enforcing policy risks silently breaking a
legitimate integration this audit missed. Report-Only lets the policy run
in production, collect real violation reports, and be promoted to
enforcing (`Content-Security-Policy`) once a reporting period confirms the
allow-list is complete — a deliberate, reversible rollout step, not a
finished security control yet.

Origin inventory (verified against actual code, not assumed):
  - 'self'                         frontend's own origin (static build + API same-origin via nginx proxy)
  - api (same-origin via nginx /api/ proxy, see deploy/nginx.conf)        — connect-src
  - wss:/ws: same-origin           Django Channels WebSocket (apps/rashid, RashidChat.tsx derives wss://<host> from window.location)
  - https://fonts.googleapis.com   Google Fonts stylesheet (frontend/src/index.css @import)
  - https://fonts.gstatic.com      Google Fonts actual font files (loaded by the stylesheet above)
  - https://checkout.stripe.com    Stripe Hosted Checkout — reached via a full-page
                                    navigation (window.location.href = checkout_url in
                                    Billing.tsx), never an embedded iframe/script, so it
                                    only needs frame-src/navigate-level allowance, not
                                    script-src
  - https://accounts.google.com    Google OAuth (django-allauth SOCIALACCOUNT_PROVIDERS
                                    'google' is configured; the browser redirects here for
                                    the OAuth consent flow)
  - media/S3 (same-origin today): CVs/avatars are served from this platform's own
                                    /media/ path (local disk + nginx alias, confirmed in
                                    apps/core upload pipeline investigation) — NOT a
                                    separate S3/CloudFront origin today, so no additional
                                    img-src/media-src origin is needed for file serving.
                                    AWS S3 IS used server-side (boto3, apps/interviews
                                    voice_service.py and others) but never loaded directly
                                    by the browser — those calls happen in the Django
                                    backend, not from client-side JS, so no browser-facing
                                    CSP origin applies to them.

No other third-party script/style/frame origins were found in the frontend
(confirmed: no analytics/tracking SDKs exist per the Legal/Privacy audit;
no CDN script tags in index.html; AlexBank provider is non-production
SCAFFOLD with no frontend-facing origin).
"""
from __future__ import annotations

CSP_REPORT_ONLY_POLICY = "; ".join([
    "default-src 'self'",
    # 'unsafe-inline'/'unsafe-eval' are intentionally still permitted for
    # script-src/style-src at this Report-Only stage — tightening further
    # requires confirming the frontend build's actual inline-script/style
    # usage first (Vite/React commonly inject inline styles); narrowing
    # this is a follow-up once violation reports are reviewed, not
    # something to guess at here.
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data: blob:",
    "connect-src 'self' wss: ws:",
    "frame-src https://checkout.stripe.com https://accounts.google.com",
    "form-action 'self' https://checkout.stripe.com https://accounts.google.com",
    "object-src 'none'",
    "base-uri 'self'",
])


class ContentSecurityPolicyReportOnlyMiddleware:
    """Adds a `Content-Security-Policy-Report-Only` header to every
    response. Report-only: violations are reported to the browser console
    (and, once `report-uri`/`report-to` is configured with a real
    collection endpoint, to that endpoint) but NOTHING is blocked. This is
    additive — it does not replace or modify any existing security header
    (HSTS, X-Frame-Options, etc. are set elsewhere and untouched).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Content-Security-Policy-Report-Only"] = CSP_REPORT_ONLY_POLICY
        return response
