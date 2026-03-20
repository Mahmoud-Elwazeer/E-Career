from django.urls import path
from apps.accounts.views import (
    RegisterView,
    LoginView,
    LogoutView,
    TokenRefreshView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    EmailVerifyView,
    ResendVerificationView,
    GoogleAuthView,
    GoogleCallbackView,
)

urlpatterns = [
    # Core auth
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),

    # Password reset
    path("password/reset/", PasswordResetRequestView.as_view(), name="auth-password-reset"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="auth-password-reset-confirm"),

    # Email verification
    path("verify-email/<str:key>/", EmailVerifyView.as_view(), name="auth-verify-email"),
    path("resend-verification/", ResendVerificationView.as_view(), name="auth-resend-verification"),

    # Social auth (Google)
    path("social/google/", GoogleAuthView.as_view(), name="auth-social-google"),
    path("social/google/callback/", GoogleCallbackView.as_view(), name="auth-social-google-callback"),
]
